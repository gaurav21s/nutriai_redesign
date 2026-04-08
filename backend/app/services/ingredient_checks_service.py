"""Service layer for ingredient checker feature."""

from __future__ import annotations

from app.repositories.base import CompositeRepository
from app.schemas.ingredient_checks import IngredientCheckResponse
from app.services.subscription_service import SubscriptionService
from app.utils.ai_clients import GeminiClient
from app.utils.parsers import parse_ingredient_json
from app.utils.prompt_builders import ingredient_check_prompt


class IngredientChecksService:
    def __init__(
        self,
        repository: CompositeRepository,
        gemini_client: GeminiClient,
        subscription_service: SubscriptionService,
    ) -> None:
        self.repository = repository
        self.gemini_client = gemini_client
        self.subscription_service = subscription_service

    async def analyze_text(
        self,
        clerk_user_id: str,
        ingredients_text: str,
        *,
        record_metadata: dict | None = None,
    ) -> IngredientCheckResponse:
        await self.subscription_service.consume_nutrition_credits(clerk_user_id, 1, "ingredient_checker")
        ingredients = [item.strip() for item in ingredients_text.split(",") if item.strip()]
        raw = await self.gemini_client.generate_text(ingredient_check_prompt(ingredients))
        parsed = parse_ingredient_json(raw)

        record = await self.repository.create_record(
            "ingredientChecks",
            clerk_user_id,
            {
                **parsed,
                "input": {"mode": "text", "ingredients_text": ingredients_text},
                **(record_metadata or {}),
            },
        )
        return IngredientCheckResponse.model_validate(record)

    async def analyze_image(
        self,
        clerk_user_id: str,
        image_bytes: bytes,
        mime_type: str,
        *,
        record_metadata: dict | None = None,
    ) -> IngredientCheckResponse:
        await self.subscription_service.consume_nutrition_credits(clerk_user_id, 1, "ingredient_checker")
        ingredients_raw = await self.gemini_client.identify_ingredients_from_image(image_bytes, mime_type)
        ingredients = [item.strip() for item in ingredients_raw.split(",") if item.strip()]
        raw = await self.gemini_client.generate_text(ingredient_check_prompt(ingredients))
        parsed = parse_ingredient_json(raw)

        record = await self.repository.create_record(
            "ingredientChecks",
            clerk_user_id,
            {
                **parsed,
                "input": {"mode": "image", "identified_ingredients": ingredients},
                **(record_metadata or {}),
            },
        )
        return IngredientCheckResponse.model_validate(record)

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[IngredientCheckResponse]:
        records = await self.repository.list_records("ingredientChecks", clerk_user_id, limit)
        records = await self.subscription_service.filter_history_rows(clerk_user_id, records)
        return [IngredientCheckResponse.model_validate(item) for item in records]

    async def get_by_id(self, clerk_user_id: str, record_id: str) -> IngredientCheckResponse | None:
        record = await self.repository.get_record("ingredientChecks", clerk_user_id, record_id)
        if not await self.subscription_service.can_access_history_row(clerk_user_id, record):
            return None
        return IngredientCheckResponse.model_validate(record)
