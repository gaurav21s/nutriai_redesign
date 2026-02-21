"""Central dependency providers for FastAPI DI."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Callable, Literal

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationException, RateLimitException
from app.core.logging import get_logger
from app.core.rate_limit import InMemoryRateLimiter
from app.core.security import AuthContext, get_optional_auth_context
from app.repositories.base import CompositeRepository
from app.repositories.convex_http import ConvexHttpRepository
from app.repositories.in_memory import InMemoryRepository
from app.services.article_service import ArticleService
from app.services.calculator_service import CalculatorService
from app.services.food_insights_service import FoodInsightsService
from app.services.ingredient_checks_service import IngredientChecksService
from app.services.meal_plan_service import MealPlanService
from app.services.nutri_chat_service import NutriChatService
from app.services.quiz_service import QuizService
from app.services.recipe_service import RecipeService
from app.services.recommendation_service import RecommendationService
from app.utils.ai_clients import GeminiClient, GroqClient, TogetherClient
from app.utils.fallback_ai_clients import (
    FallbackGeminiClient,
    FallbackGroqClient,
    FallbackTogetherClient,
)

logger = get_logger("app.dependencies")


def _can_use_fallback_ai(settings: Settings) -> bool:
    return settings.allow_mock_ai_fallback and settings.environment in {"local", "development"}


def _build_gemini_client(settings: Settings) -> GeminiClient | FallbackGeminiClient:
    if settings.force_mock_ai_fallback and _can_use_fallback_ai(settings):
        logger.warning("Using forced fallback Gemini client")
        return FallbackGeminiClient()
    try:
        return GeminiClient(api_key=settings.google_api_key)
    except ConfigurationException:
        if _can_use_fallback_ai(settings):
            logger.warning("Using fallback Gemini client (missing GOOGLE_API_KEY in development/local)")
            return FallbackGeminiClient()
        raise


def _build_together_client(settings: Settings) -> TogetherClient | FallbackTogetherClient:
    if settings.force_mock_ai_fallback and _can_use_fallback_ai(settings):
        logger.warning("Using forced fallback Together client")
        return FallbackTogetherClient()
    try:
        return TogetherClient(api_key=settings.together_api_key)
    except ConfigurationException:
        if _can_use_fallback_ai(settings):
            logger.warning("Using fallback Together client (missing TOGETHER_API_KEY in development/local)")
            return FallbackTogetherClient()
        raise


def _build_groq_client(settings: Settings) -> GroqClient | FallbackGroqClient:
    if settings.force_mock_ai_fallback and _can_use_fallback_ai(settings):
        logger.warning("Using forced fallback Groq client")
        return FallbackGroqClient()
    try:
        return GroqClient(api_key=settings.groq_api_key)
    except ConfigurationException:
        if _can_use_fallback_ai(settings):
            logger.warning("Using fallback Groq client (missing GROQ_API_KEY in development/local)")
            return FallbackGroqClient()
        raise


@lru_cache(maxsize=1)
def get_rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter()


@lru_cache(maxsize=1)
def get_in_memory_repository() -> InMemoryRepository:
    return InMemoryRepository()


def get_repository(settings: Settings = Depends(get_settings)) -> CompositeRepository:
    if settings.enable_convex_persistence and settings.convex_http_actions_url and settings.convex_backend_secret:
        return ConvexHttpRepository(
            base_url=settings.convex_http_actions_url,
            backend_secret=settings.convex_backend_secret,
            timeout_seconds=settings.request_timeout_seconds,
        )

    logger.warning("Using in-memory repository; Convex persistence is disabled or not configured")
    return get_in_memory_repository()


def get_food_insights_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> FoodInsightsService:
    return FoodInsightsService(
        repository=repository,
        gemini_client=_build_gemini_client(settings),
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )


def get_ingredient_checks_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> IngredientChecksService:
    return IngredientChecksService(
        repository=repository,
        gemini_client=_build_gemini_client(settings),
    )


def get_meal_plan_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> MealPlanService:
    return MealPlanService(
        repository=repository,
        together_client=_build_together_client(settings),
    )


def get_recipe_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> RecipeService:
    return RecipeService(
        repository=repository,
        groq_client=_build_groq_client(settings),
        affiliate_code=settings.affiliate_code,
    )


def get_quiz_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> QuizService:
    return QuizService(
        repository=repository,
        groq_client=_build_groq_client(settings),
    )


def get_nutri_chat_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> NutriChatService:
    return NutriChatService(
        repository=repository,
        together_client=_build_together_client(settings),
    )


def get_calculator_service(
    repository: CompositeRepository = Depends(get_repository),
) -> CalculatorService:
    return CalculatorService(repository=repository)


def get_article_service(
    repository: CompositeRepository = Depends(get_repository),
) -> ArticleService:
    project_root = Path(__file__).resolve().parents[2]
    return ArticleService(repository=repository, project_root=project_root)


def get_recommendation_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> RecommendationService:
    return RecommendationService(
        repository=repository,
        groq_client=_build_groq_client(settings),
    )


def rate_limit_dependency(kind: Literal["ai", "chat", "default"]) -> Callable:
    async def dependency(
        request: Request,
        settings: Settings = Depends(get_settings),
        limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
        auth: AuthContext | None = Depends(get_optional_auth_context),
    ) -> None:
        limit_map = {
            "ai": settings.rate_limit_ai_per_minute,
            "chat": settings.rate_limit_chat_per_minute,
            "default": settings.rate_limit_default_per_minute,
        }
        limit = limit_map[kind]

        identity = auth.clerk_user_id if auth else (request.client.host if request.client else "anonymous")
        key = f"{kind}:{request.url.path}:{identity}"

        allowed = await limiter.hit(key=key, limit=limit, window_seconds=60)
        if not allowed:
            raise RateLimitException(details={"limit": limit, "window_seconds": 60})

    return dependency


ai_rate_limit = rate_limit_dependency("ai")
chat_rate_limit = rate_limit_dependency("chat")
default_rate_limit = rate_limit_dependency("default")
