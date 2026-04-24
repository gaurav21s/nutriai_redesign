"""Service layer for Nutri Smart Picks."""

from __future__ import annotations

import asyncio

from app.repositories.base import CompositeRepository
from app.schemas.smart_picks import SmartPickGenerateRequest, SmartPickResponse
from app.services.subscription_service import SubscriptionService
from app.utils.ai_clients import GroqClient
from app.utils.parsers import parse_smart_pick_json
from app.utils.prompt_builders import smart_picks_prompt


class SmartPicksService:
    def __init__(
        self,
        repository: CompositeRepository,
        groq_client: GroqClient,
        subscription_service: SubscriptionService,
    ) -> None:
        self.repository = repository
        self.groq_client = groq_client
        self.subscription_service = subscription_service

    async def _build_context_summary(self, clerk_user_id: str) -> str:
        calculations, meal_plans, recipes, food_insights, smart_picks = await asyncio.gather(
            self.repository.list_records("calculations", clerk_user_id, 2),
            self.repository.list_records("mealPlans", clerk_user_id, 1),
            self.repository.list_records("recipes", clerk_user_id, 1),
            self.repository.list_records("foodInsights", clerk_user_id, 1),
            self.repository.list_records("recommendations", clerk_user_id, 1),
        )

        lines: list[str] = []
        latest_bmi = next((item for item in calculations if item.get("calculator_type") == "bmi"), None)
        latest_calories = next((item for item in calculations if item.get("calculator_type") == "calories"), None)
        if latest_bmi:
            result = latest_bmi.get("result", {})
            lines.append(f"- Latest BMI: {result.get('bmi', 'n/a')} ({result.get('category', 'unknown')})")
        if latest_calories:
            result = latest_calories.get("result", {})
            lines.append(
                f"- Latest maintenance calories: {result.get('maintenance_calories', 'n/a')}; BMR: {result.get('bmr', 'n/a')}"
            )
        if meal_plans:
            lines.append("- Meal Planner: recent meal plan exists")
        if recipes:
            latest_recipe = recipes[0]
            lines.append(f"- Recipe Finder: recent recipe was {latest_recipe.get('recipe_name', 'saved recipe')}")
        if food_insights:
            lines.append(f"- Food Insight: latest verdict was {food_insights[0].get('verdict', 'available')}")
        if smart_picks:
            lines.append(f"- Prior Smart Pick: {smart_picks[0].get('title', 'available')}")
        return "\n".join(lines) if lines else "- No recent NutriAI context available."

    def _coerce_record(self, record: dict) -> SmartPickResponse:
        if record.get("ranked_options"):
            return SmartPickResponse.model_validate(record)

        legacy_options = [
            {
                "label": item,
                "rank": index + 1,
                "verdict": "Legacy suggestion",
                "why": item,
                "tradeoff": "Generated before Nutri Smart Picks introduced richer tradeoff data.",
                "quick_upgrade": "Choose a higher-protein or higher-fiber version when possible.",
                "good_for": "General healthy eating decisions.",
                "avoid_if": "It conflicts with your dietary restrictions.",
            }
            for index, item in enumerate(record.get("recommendations", [])[:5])
        ]
        normalized = {
            "id": record.get("id", "preview"),
            "created_at": record.get("created_at"),
            "title": record.get("title", "Nutri Smart Picks"),
            "decision_summary": "This saved record was created before the Nutri Smart Picks redesign.",
            "best_pick": legacy_options[0]["label"] if legacy_options else "No saved best pick",
            "fallback_rule": "Choose the option with clearer protein, less frying, and fewer sugary add-ons.",
            "ranked_options": legacy_options,
            "raw_response": record.get("raw_response", ""),
        }
        return SmartPickResponse.model_validate(normalized)

    async def preview(self, clerk_user_id: str, payload: SmartPickGenerateRequest) -> SmartPickResponse:
        context_summary = await self._build_context_summary(clerk_user_id)
        raw = await self.groq_client.generate_text(
            smart_picks_prompt(payload, context_summary),
            system_prompt="You are Nutri Smart Picks, a nutrition decision assistant.",
            temperature=0.2,
        )
        parsed = parse_smart_pick_json(raw)

        return SmartPickResponse.model_validate(
            {
                "id": "preview",
                "created_at": "1970-01-01T00:00:00+00:00",
                **parsed,
            }
        )

    async def save_preview(
        self,
        clerk_user_id: str,
        payload: SmartPickGenerateRequest,
        response: SmartPickResponse,
        *,
        record_metadata: dict | None = None,
    ) -> dict:
        return await self.repository.create_record(
            "recommendations",
            clerk_user_id,
            {
                "title": response.title,
                "decision_summary": response.decision_summary,
                "best_pick": response.best_pick,
                "fallback_rule": response.fallback_rule,
                "ranked_options": [item.model_dump() for item in response.ranked_options],
                "recommendations": [item.label for item in response.ranked_options],
                "raw_response": response.raw_response,
                "input": payload.model_dump(),
                **(record_metadata or {}),
            },
        )

    async def generate(
        self,
        clerk_user_id: str,
        payload: SmartPickGenerateRequest,
        *,
        record_metadata: dict | None = None,
    ) -> SmartPickResponse:
        await self.subscription_service.consume_nutrition_credits(clerk_user_id, 2, "recommendations")
        preview = await self.preview(clerk_user_id, payload)
        record = await self.save_preview(clerk_user_id, payload, preview, record_metadata=record_metadata)
        return self._coerce_record(record)

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[SmartPickResponse]:
        rows = await self.repository.list_records("recommendations", clerk_user_id, limit)
        rows = await self.subscription_service.filter_history_rows(clerk_user_id, rows)
        return [self._coerce_record(item) for item in rows]
