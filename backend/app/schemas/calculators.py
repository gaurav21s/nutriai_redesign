"""Calculator schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BMIRequest(BaseModel):
    weight_kg: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class BMIResponse(BaseModel):
    bmi: float
    category: Literal["underweight", "healthy", "overweight", "obese"]


class CaloriesRequest(BaseModel):
    gender: Literal["Male", "Female"]
    weight_kg: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    age: int = Field(..., gt=0)
    activity_multiplier: float = Field(..., gt=0)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)


class CaloriesResponse(BaseModel):
    bmr: float
    maintenance_calories: float
    guidance: str


class CalculationHistoryItem(BaseModel):
    id: str
    created_at: datetime
    calculator_type: Literal["bmi", "calories"]
    payload: dict
    result: dict


class CalculationHistoryResponse(BaseModel):
    items: list[CalculationHistoryItem]
