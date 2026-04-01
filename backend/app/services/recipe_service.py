"""Service layer for recipe and shopping links features."""

from __future__ import annotations

from app.repositories.base import CompositeRepository
from app.schemas.recipes import RecipeGenerateRequest, RecipeResponse
from app.utils.ai_clients import GroqClient
from app.utils.parsers import parse_recipe
from app.utils.prompt_builders import recipe_prompt
from app.utils.shopping_links import build_shopping_links


class RecipeService:
    def __init__(self, repository: CompositeRepository, groq_client: GroqClient, affiliate_code: str) -> None:
        self.repository = repository
        self.groq_client = groq_client
        self.affiliate_code = affiliate_code

    async def preview(self, payload: RecipeGenerateRequest) -> RecipeResponse:
        raw = await self.groq_client.generate_text(
            recipe_prompt(payload.dish_name, payload.recipe_type),
            system_prompt="You are a helpful culinary assistant specialized in healthy cooking.",
            temperature=0.2,
        )
        parsed = parse_recipe(raw)
        shopping_links = build_shopping_links(parsed.get("ingredient_list", []), self.affiliate_code)

        return RecipeResponse.model_validate(
            {
                "id": "preview",
                "created_at": "1970-01-01T00:00:00+00:00",
                **parsed,
                "shopping_links": shopping_links,
                "raw_response": raw,
            }
        )

    async def save_preview(self, clerk_user_id: str, payload: RecipeGenerateRequest, response: RecipeResponse) -> dict:
        return await self.repository.create_record(
            "recipes",
            clerk_user_id,
            {
                "recipe_name": response.recipe_name,
                "ingredients": [item.model_dump() for item in response.ingredients],
                "steps": response.steps,
                "ingredient_list": response.ingredient_list,
                "shopping_links": response.shopping_links,
                "explanation": response.explanation,
                "raw_response": response.raw_response,
                "input": payload.model_dump(),
            },
        )

    async def generate(self, clerk_user_id: str, payload: RecipeGenerateRequest) -> RecipeResponse:
        preview = await self.preview(payload)
        record = await self.save_preview(clerk_user_id, payload, preview)
        return RecipeResponse.model_validate(record)

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[RecipeResponse]:
        records = await self.repository.list_records("recipes", clerk_user_id, limit)
        return [RecipeResponse.model_validate(item) for item in records]

    async def get_by_id(self, clerk_user_id: str, record_id: str) -> RecipeResponse | None:
        record = await self.repository.get_record("recipes", clerk_user_id, record_id)
        if record is None:
            return None
        return RecipeResponse.model_validate(record)

    async def get_shopping_links(self, ingredients: list[str]) -> dict[str, dict[str, str]]:
        return build_shopping_links(ingredients, self.affiliate_code)
