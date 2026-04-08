"""Central dependency providers for FastAPI DI."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Callable, Literal

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.coordination import SharedCoordinator, validate_shared_coordination
from app.core.exceptions import AuthorizationException, ConfigurationException, RateLimitException
from app.core.logging import get_logger
from app.core.rate_limit import InMemoryRateLimiter
from app.core.security import get_auth_context
from app.core.subscription import (
    get_default_subscription_payload,
    get_demo_subscription_payload,
    is_local_demo_user,
)
from app.core.security import AuthContext, get_optional_auth_context
from app.repositories.base import CompositeRepository
from app.repositories.convex_http import ConvexHttpRepository
from app.repositories.hybrid import HybridRepository
from app.repositories.in_memory import InMemoryRepository
from app.services.article_service import ArticleService
from app.services.calculator_service import CalculatorService
from app.services.food_insights_service import FoodInsightsService
from app.services.ingredient_checks_service import IngredientChecksService
from app.services.meal_plan_service import MealPlanService
from app.services.nutri_chat_agent import FallbackAgentModel, GroqAgentModel, NutriChatAgentRuntime, OpenRouterAgentModel
from app.services.nutri_chat_service import NutriChatService
from app.services.operations_service import OperationsService
from app.services.quiz_service import QuizService
from app.services.recipe_service import RecipeService
from app.services.recommendation_service import RecommendationService
from app.services.subscription_service import SubscriptionService
from app.utils.ai_clients import GeminiClient, GroqClient, OpenRouterClient, TogetherClient
from app.utils.fallback_ai_clients import (
    FallbackGeminiClient,
    FallbackGroqClient,
    FallbackOpenRouterClient,
    FallbackTogetherClient,
)

logger = get_logger("app.dependencies")


def _looks_like_placeholder_secret(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"", "replace_with_shared_secret", "changeme", "your_secret_here"} or normalized.startswith(
        "replace_with_"
    )


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


def _build_openrouter_client(settings: Settings) -> OpenRouterClient:
    return OpenRouterClient(
        api_key=settings.openrouter_api_key,
        model_name=settings.openrouter_chat_model,
        base_url=settings.openrouter_base_url,
        fallback_models=[],
        site_url=settings.openrouter_site_url,
        app_name=settings.openrouter_app_name,
        timeout_seconds=settings.request_timeout_seconds,
    )


@lru_cache(maxsize=1)
def get_rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter()


@lru_cache(maxsize=1)
def get_in_memory_repository() -> InMemoryRepository:
    return InMemoryRepository()


@lru_cache(maxsize=1)
def _get_cached_convex_repository(base_url: str, backend_secret: str, timeout_seconds: int) -> HybridRepository:
    primary = ConvexHttpRepository(
        base_url=base_url,
        backend_secret=backend_secret,
        timeout_seconds=timeout_seconds,
    )
    return HybridRepository(primary=primary, fallback=get_in_memory_repository())


def get_repository(settings: Settings = Depends(get_settings)) -> CompositeRepository:
    if settings.enable_convex_persistence and settings.convex_http_actions_url and settings.convex_backend_secret:
        if _looks_like_placeholder_secret(settings.convex_backend_secret):
            message = (
                "CONVEX_BACKEND_SECRET looks like a placeholder value; "
                "Convex HTTP actions will reject requests unless BACKEND_CONVEX_SHARED_SECRET matches it exactly"
            )
            if settings.environment == "production":
                raise ConfigurationException(message)
            logger.warning(message)
        return _get_cached_convex_repository(
            settings.convex_http_actions_url,
            settings.convex_backend_secret,
            settings.request_timeout_seconds,
        )

    logger.warning("Using in-memory repository; Convex persistence is disabled or not configured")
    return get_in_memory_repository()


@lru_cache(maxsize=1)
def get_shared_coordinator() -> SharedCoordinator:
    resolved_settings = get_settings()
    validate_shared_coordination(resolved_settings)
    return SharedCoordinator(resolved_settings)


def get_subscription_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> SubscriptionService:
    demo_users_file = Path(__file__).resolve().parent / "data" / "demo_users.json"
    return SubscriptionService(
        repository=repository,
        stripe_secret_key=settings.stripe_secret_key,
        stripe_publishable_key=settings.stripe_publishable_key,
        demo_users_file=demo_users_file,
        environment=settings.environment,
        dev_user_id=settings.dev_user_id,
    )


def get_food_insights_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> FoodInsightsService:
    return FoodInsightsService(
        repository=repository,
        gemini_client=_build_gemini_client(settings),
        cache_ttl_seconds=settings.cache_ttl_seconds,
        subscription_service=subscription_service,
    )


def get_ingredient_checks_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> IngredientChecksService:
    return IngredientChecksService(
        repository=repository,
        gemini_client=_build_gemini_client(settings),
        subscription_service=subscription_service,
    )


def get_meal_plan_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> MealPlanService:
    return MealPlanService(
        repository=repository,
        together_client=_build_together_client(settings),
        subscription_service=subscription_service,
    )


def get_recipe_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> RecipeService:
    return RecipeService(
        repository=repository,
        groq_client=_build_groq_client(settings),
        affiliate_code=settings.affiliate_code,
        subscription_service=subscription_service,
    )


def get_quiz_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> QuizService:
    return QuizService(
        repository=repository,
        groq_client=_build_groq_client(settings),
        subscription_service=subscription_service,
    )


def get_nutri_chat_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> NutriChatService:
    calculator_service = CalculatorService(repository=repository, subscription_service=subscription_service)
    groq_client = _build_groq_client(settings)
    recipe_service = RecipeService(
        repository=repository,
        groq_client=groq_client,  # type: ignore[arg-type]
        affiliate_code=settings.affiliate_code,
        subscription_service=subscription_service,
    )
    recommendation_service = RecommendationService(
        repository=repository,
        groq_client=groq_client,  # type: ignore[arg-type]
        subscription_service=subscription_service,
    )

    if settings.agent_chat_provider == "openrouter":
        agent_model = OpenRouterAgentModel(_build_openrouter_client(settings))
    elif isinstance(groq_client, FallbackGroqClient):
        logger.warning("Using fallback Nutri Chat agent model")
        agent_model = FallbackAgentModel(FallbackOpenRouterClient())
    else:
        agent_model = GroqAgentModel(groq_client)

    service: NutriChatService | None = None

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:  # type: ignore[misc]
        if service is None:
            raise RuntimeError("Nutri chat service is not initialized")
        return await service.execute_tool(tool_name, tool_input, clerk_user_id)

    runtime = NutriChatAgentRuntime(agent_model=agent_model, tool_executor=tool_executor)  # type: ignore[arg-type]
    service = NutriChatService(
        repository=repository,
        agent_runtime=runtime,
        calculator_service=calculator_service,
        recipe_service=recipe_service,
        recommendation_service=recommendation_service,
        subscription_service=subscription_service,
    )
    return service


def get_operations_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> OperationsService:
    calculator_service = CalculatorService(repository=repository, subscription_service=subscription_service)
    groq_client = _build_groq_client(settings)
    recipe_service = RecipeService(
        repository=repository,
        groq_client=groq_client,  # type: ignore[arg-type]
        affiliate_code=settings.affiliate_code,
        subscription_service=subscription_service,
    )
    recommendation_service = RecommendationService(
        repository=repository,
        groq_client=groq_client,  # type: ignore[arg-type]
        subscription_service=subscription_service,
    )
    try:
        gemini_client = _build_gemini_client(settings)
        food_insights_service = FoodInsightsService(
            repository=repository,
            gemini_client=gemini_client,
            cache_ttl_seconds=settings.cache_ttl_seconds,
            subscription_service=subscription_service,
        )
        ingredient_checks_service = IngredientChecksService(
            repository=repository,
            gemini_client=gemini_client,
            subscription_service=subscription_service,
        )
    except ConfigurationException:
        food_insights_service = None
        ingredient_checks_service = None

    try:
        meal_plan_service = MealPlanService(
            repository=repository,
            together_client=_build_together_client(settings),
            subscription_service=subscription_service,
        )
    except ConfigurationException:
        meal_plan_service = None
    quiz_service = QuizService(
        repository=repository,
        groq_client=groq_client,  # type: ignore[arg-type]
        subscription_service=subscription_service,
    )
    nutri_chat_service = get_nutri_chat_service(repository, settings, subscription_service)
    return OperationsService(
        repository=repository,
        settings=settings,
        coordinator=get_shared_coordinator(),
        subscription_service=subscription_service,
        calculator_service=calculator_service,
        recipe_service=recipe_service,
        recommendation_service=recommendation_service,
        food_insights_service=food_insights_service,
        ingredient_checks_service=ingredient_checks_service,
        meal_plan_service=meal_plan_service,
        quiz_service=quiz_service,
        nutri_chat_service=nutri_chat_service,
    )


def get_calculator_service(
    repository: CompositeRepository = Depends(get_repository),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> CalculatorService:
    return CalculatorService(repository=repository, subscription_service=subscription_service)


def get_article_service(
    repository: CompositeRepository = Depends(get_repository),
) -> ArticleService:
    project_root = Path(__file__).resolve().parents[2]
    return ArticleService(repository=repository, project_root=project_root)


def get_recommendation_service(
    repository: CompositeRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> RecommendationService:
    return RecommendationService(
        repository=repository,
        groq_client=_build_groq_client(settings),
        subscription_service=subscription_service,
    )


def require_permission(permission_key: str) -> Callable:
    async def dependency(
        auth: AuthContext = Depends(get_auth_context),
        repository: CompositeRepository = Depends(get_repository),
        settings: Settings = Depends(get_settings),
    ) -> None:
        subscription = await repository.get_subscription(auth.clerk_user_id)
        should_force_demo_access = is_local_demo_user(
            settings.environment,
            auth.clerk_user_id,
            settings.dev_user_id,
        )

        if not subscription:
            subscription = await repository.upsert_subscription(
                auth.clerk_user_id,
                get_demo_subscription_payload() if should_force_demo_access else get_default_subscription_payload(),
            )
        elif should_force_demo_access:
            expected_permissions = get_demo_subscription_payload()["permissions"]
            permissions = subscription.get("permissions", {})
            if not subscription.get("is_demo") or any(
                bool(permissions.get(key)) != expected_permissions[key] for key in expected_permissions
            ):
                subscription = await repository.upsert_subscription(
                    auth.clerk_user_id,
                    get_demo_subscription_payload(),
                )

        permissions = subscription.get("permissions", {})
        if not isinstance(permissions, dict):
            permissions = {}

        if bool(permissions.get(permission_key)) is True:
            return

        raise AuthorizationException(
            "Your current plan does not include this feature",
            details={
                "permission": permission_key,
                "suggested_action": "Upgrade your subscription plan",
            },
        )

    return dependency


def rate_limit_dependency(kind: Literal["ai", "chat", "default"]) -> Callable:
    def _rate_limit_path(request: Request) -> str:
        route = request.scope.get("route")
        path = getattr(route, "path_format", None) or getattr(route, "path", None)
        if isinstance(path, str) and path:
            return path
        return request.url.path

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
        key = f"{kind}:{_rate_limit_path(request)}:{identity}"

        coordinator = get_shared_coordinator()
        allowed = await coordinator.hit_rate_limit(key=key, limit=limit, window_seconds=60)
        if not allowed:
            raise RateLimitException(details={"limit": limit, "window_seconds": 60})

    return dependency


ai_rate_limit = rate_limit_dependency("ai")
chat_rate_limit = rate_limit_dependency("chat")
default_rate_limit = rate_limit_dependency("default")
