"""Service layer for BMI and calorie calculators."""

from __future__ import annotations

from app.repositories.base import CompositeRepository
from app.schemas.calculators import (
    BMIRequest,
    BMIResponse,
    CaloriesRequest,
    CaloriesResponse,
    CalculationHistoryItem,
)
from app.services.subscription_service import SubscriptionService


class CalculatorService:
    def __init__(self, repository: CompositeRepository, subscription_service: SubscriptionService | None = None) -> None:
        self.repository = repository
        self.subscription_service = subscription_service

    async def preview_bmi(self, payload: BMIRequest) -> BMIResponse:
        bmi = payload.weight_kg / ((payload.height_cm / 100.0) ** 2)

        if bmi < 18.5:
            category = "underweight"
        elif bmi < 25.0:
            category = "healthy"
        elif bmi < 30.0:
            category = "overweight"
        else:
            category = "obese"

        return BMIResponse(bmi=round(bmi, 1), category=category)

    async def calculate_bmi(
        self,
        clerk_user_id: str,
        payload: BMIRequest,
        *,
        record_metadata: dict | None = None,
    ) -> BMIResponse:
        response = await self.preview_bmi(payload)
        await self.save_bmi_preview(clerk_user_id, payload, response, record_metadata=record_metadata)
        return response

    async def save_bmi_preview(
        self,
        clerk_user_id: str,
        payload: BMIRequest,
        response: BMIResponse,
        *,
        record_metadata: dict | None = None,
    ) -> dict:
        return await self.repository.create_record(
            "calculations",
            clerk_user_id,
            {
                "calculator_type": "bmi",
                "payload": payload.model_dump(),
                "result": response.model_dump(),
                **(record_metadata or {}),
            },
        )

    async def preview_calories(self, payload: CaloriesRequest) -> CaloriesResponse:
        base = (10 * payload.weight_kg) + (6.25 * payload.height_cm) - (5 * payload.age)
        bmr = base if payload.gender == "Male" else base - 161
        maintenance = bmr * payload.activity_multiplier

        return CaloriesResponse(
            bmr=round(bmr, 2),
            maintenance_calories=round(maintenance, 2),
            guidance="Consume less to lose weight, consume more to gain weight.",
        )

    async def calculate_calories(
        self,
        clerk_user_id: str,
        payload: CaloriesRequest,
        *,
        record_metadata: dict | None = None,
    ) -> CaloriesResponse:
        response = await self.preview_calories(payload)
        await self.save_calories_preview(clerk_user_id, payload, response, record_metadata=record_metadata)
        return response

    async def save_calories_preview(
        self,
        clerk_user_id: str,
        payload: CaloriesRequest,
        response: CaloriesResponse,
        *,
        record_metadata: dict | None = None,
    ) -> dict:
        return await self.repository.create_record(
            "calculations",
            clerk_user_id,
            {
                "calculator_type": "calories",
                "payload": payload.model_dump(),
                "result": response.model_dump(),
                **(record_metadata or {}),
            },
        )

    async def get_history(self, clerk_user_id: str, limit: int = 20) -> list[CalculationHistoryItem]:
        rows = await self.repository.list_records("calculations", clerk_user_id, limit)
        if self.subscription_service is not None:
            rows = await self.subscription_service.filter_history_rows(clerk_user_id, rows)
        return [CalculationHistoryItem.model_validate(item) for item in rows]
