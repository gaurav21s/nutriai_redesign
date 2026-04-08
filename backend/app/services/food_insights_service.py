"""Service layer for food insight feature."""

from __future__ import annotations

from app.repositories.base import CompositeRepository
from app.schemas.food_insights import FoodInsightResponse
from app.services.subscription_service import SubscriptionService
from app.utils.ai_clients import GeminiClient
from app.utils.caching import TTLCache
from app.utils.parsers import parse_food_insight
from app.utils.prompt_builders import food_image_prompt, food_text_prompt


class FoodInsightsService:
    def __init__(
        self,
        repository: CompositeRepository,
        gemini_client: GeminiClient,
        cache_ttl_seconds: int,
        subscription_service: SubscriptionService,
    ) -> None:
        self.repository = repository
        self.gemini_client = gemini_client
        self.cache = TTLCache(ttl_seconds=cache_ttl_seconds)
        self.subscription_service = subscription_service

    async def analyze_text(
        self,
        clerk_user_id: str,
        text: str,
        *,
        record_metadata: dict | None = None,
    ) -> FoodInsightResponse:
        await self.subscription_service.consume_nutrition_credits(clerk_user_id, 1, "food_insight_text")
        cache_key = ("food_text", text.strip().lower())
        cached = self.cache.get(cache_key)

        if cached is None:
            raw = await self.gemini_client.generate_text(food_text_prompt(text))
            parsed = parse_food_insight(raw)
            self.cache.set(cache_key, parsed)
        else:
            parsed = dict(cached)

        record = await self.repository.create_record(
            "foodInsights",
            clerk_user_id,
            {
                **parsed,
                "input": {"mode": "text", "text": text},
                **(record_metadata or {}),
            },
        )
        return FoodInsightResponse.model_validate(record)

    async def analyze_image(
        self,
        clerk_user_id: str,
        image_bytes: bytes,
        mime_type: str,
        *,
        record_metadata: dict | None = None,
    ) -> FoodInsightResponse:
        await self.subscription_service.consume_nutrition_credits(clerk_user_id, 2, "food_insight_image")
        raw = await self.gemini_client.generate_with_image(food_image_prompt(), image_bytes, mime_type)
        parsed = parse_food_insight(raw)
        record = await self.repository.create_record(
            "foodInsights",
            clerk_user_id,
            {
                **parsed,
                "input": {"mode": "image", "mime_type": mime_type},
                **(record_metadata or {}),
            },
        )
        return FoodInsightResponse.model_validate(record)

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[FoodInsightResponse]:
        records = await self.repository.list_records("foodInsights", clerk_user_id, limit)
        records = await self.subscription_service.filter_history_rows(clerk_user_id, records)
        return [FoodInsightResponse.model_validate(item) for item in records]

    async def get_by_id(self, clerk_user_id: str, record_id: str) -> FoodInsightResponse | None:
        record = await self.repository.get_record("foodInsights", clerk_user_id, record_id)
        if not await self.subscription_service.can_access_history_row(clerk_user_id, record):
            return None
        return FoodInsightResponse.model_validate(record)
