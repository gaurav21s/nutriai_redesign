"""Service layer for meal plan feature."""

from __future__ import annotations

from app.repositories.base import CompositeRepository
from app.schemas.meal_plans import MealPlanGenerateRequest, MealPlanResponse
from app.utils.ai_clients import TogetherClient
from app.utils.parsers import parse_meal_plan
from app.utils.pdf_export import build_meal_plan_pdf
from app.utils.prompt_builders import meal_plan_prompt


class MealPlanService:
    def __init__(self, repository: CompositeRepository, together_client: TogetherClient) -> None:
        self.repository = repository
        self.together_client = together_client

    async def generate(self, clerk_user_id: str, payload: MealPlanGenerateRequest) -> MealPlanResponse:
        raw = await self.together_client.generate_text(
            meal_plan_prompt(
                payload.gender,
                payload.goal,
                payload.diet_choice,
                payload.issue,
                payload.gym,
                payload.height,
                payload.weight,
                payload.food_type,
            ),
            temperature=0.1,
        )
        parsed = parse_meal_plan(raw)
        profile = payload.model_dump()

        record = await self.repository.create_record(
            "mealPlans",
            clerk_user_id,
            {
                **parsed,
                "profile": profile,
            },
        )
        return MealPlanResponse.model_validate(record)

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[MealPlanResponse]:
        records = await self.repository.list_records("mealPlans", clerk_user_id, limit)
        return [MealPlanResponse.model_validate(item) for item in records]

    async def get_by_id(self, clerk_user_id: str, record_id: str) -> MealPlanResponse | None:
        record = await self.repository.get_record("mealPlans", clerk_user_id, record_id)
        if record is None:
            return None
        return MealPlanResponse.model_validate(record)

    async def export_pdf(self, clerk_user_id: str, record_id: str, full_name: str, age: int) -> bytes:
        record = await self.repository.get_record("mealPlans", clerk_user_id, record_id)
        if record is None:
            raise ValueError("Meal plan not found")

        profile = record.get("profile", {})
        sections = record.get("sections", [])

        return build_meal_plan_pdf(
            full_name=full_name,
            age=age,
            profile={
                "Gender": str(profile.get("gender", "")),
                "Goal": str(profile.get("goal", "")),
                "Diet": str(profile.get("diet_choice", "")),
                "Issue": str(profile.get("issue", "")),
                "Workout": str(profile.get("gym", "")),
                "Height": str(profile.get("height", "")),
                "Weight": str(profile.get("weight", "")),
                "Cuisine": str(profile.get("food_type", "")),
            },
            sections=sections,
        )
