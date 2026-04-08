"""Service layer for meal plan feature."""

from __future__ import annotations

import base64

from app.repositories.base import CompositeRepository
from app.schemas.meal_plans import (
    MealPlanGenerateRequest,
    MealPlanPdfExportResponse,
    MealPlanResponse,
)
from app.services.subscription_service import SubscriptionService
from app.utils.ai_clients import TogetherClient
from app.utils.parsers import parse_meal_plan
from app.utils.pdf_export import build_meal_plan_pdf
from app.utils.prompt_builders import meal_plan_prompt


class MealPlanService:
    def __init__(
        self,
        repository: CompositeRepository,
        together_client: TogetherClient,
        subscription_service: SubscriptionService,
    ) -> None:
        self.repository = repository
        self.together_client = together_client
        self.subscription_service = subscription_service

    async def generate(
        self,
        clerk_user_id: str,
        payload: MealPlanGenerateRequest,
        *,
        record_metadata: dict | None = None,
    ) -> MealPlanResponse:
        await self.subscription_service.consume_nutrition_credits(clerk_user_id, 3, "meal_planner")
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
                **(record_metadata or {}),
            },
        )
        return MealPlanResponse.model_validate(record)

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[MealPlanResponse]:
        records = await self.repository.list_records("mealPlans", clerk_user_id, limit)
        records = await self.subscription_service.filter_history_rows(clerk_user_id, records)
        return [MealPlanResponse.model_validate(item) for item in records]

    async def get_by_id(self, clerk_user_id: str, record_id: str) -> MealPlanResponse | None:
        record = await self.repository.get_record("mealPlans", clerk_user_id, record_id)
        if not await self.subscription_service.can_access_history_row(clerk_user_id, record):
            return None
        return MealPlanResponse.model_validate(record)

    async def build_pdf_bytes(self, clerk_user_id: str, record_id: str, full_name: str, age: int) -> bytes:
        record = await self.repository.get_record("mealPlans", clerk_user_id, record_id)
        if not await self.subscription_service.can_access_history_row(clerk_user_id, record):
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

    async def create_pdf_export(
        self,
        clerk_user_id: str,
        record_id: str,
        full_name: str,
        age: int,
        *,
        operation_id: str | None = None,
        consume_export_quota: bool = True,
    ) -> MealPlanPdfExportResponse:
        if consume_export_quota:
            await self.subscription_service.consume_pdf_export(clerk_user_id)
        pdf_bytes = await self.build_pdf_bytes(clerk_user_id, record_id, full_name, age)
        file_name = f"nutriai_meal_plan_{full_name.replace(' ', '_').lower()}.pdf"
        record = await self.repository.create_record(
            "mealPlanPdfExports",
            clerk_user_id,
            {
                "meal_plan_record_id": record_id,
                "full_name": full_name,
                "age": age,
                "file_name": file_name,
                "mime_type": "application/pdf",
                "byte_size": len(pdf_bytes),
                "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
                "operation_id": operation_id,
            },
        )
        return MealPlanPdfExportResponse.model_validate(record)

    async def list_pdf_exports(
        self,
        clerk_user_id: str,
        record_id: str,
        limit: int = 20,
    ) -> list[MealPlanPdfExportResponse]:
        rows = await self.repository.list_records("mealPlanPdfExports", clerk_user_id, max(limit * 3, limit))
        rows = [row for row in rows if str(row.get("meal_plan_record_id", "")) == record_id]
        rows = await self.subscription_service.filter_history_rows(clerk_user_id, rows)
        return [MealPlanPdfExportResponse.model_validate(row) for row in rows[:limit]]

    async def get_pdf_export(self, clerk_user_id: str, export_id: str) -> MealPlanPdfExportResponse | None:
        record = await self.repository.get_record("mealPlanPdfExports", clerk_user_id, export_id)
        if not await self.subscription_service.can_access_history_row(clerk_user_id, record):
            return None
        return MealPlanPdfExportResponse.model_validate(record)

    async def get_pdf_export_bytes(self, clerk_user_id: str, export_id: str) -> bytes:
        record = await self.repository.get_record("mealPlanPdfExports", clerk_user_id, export_id)
        if not await self.subscription_service.can_access_history_row(clerk_user_id, record):
            raise ValueError("Saved PDF export not found")
        encoded = str(record.get("pdf_base64", "")).strip()
        if not encoded:
            raise ValueError("Saved PDF export is empty")
        return base64.b64decode(encoded)
