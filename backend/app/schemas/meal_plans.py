"""Meal plan schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MealPlanGenerateRequest(BaseModel):
    gender: str = Field(..., examples=["Male", "Female"])
    goal: str = Field(..., examples=["Gain Weight", "Loss fat"])
    diet_choice: str = Field(..., examples=["Vegetarian", "Vegan", "Non-vegetarian"])
    issue: str = Field(default="No issue")
    gym: str = Field(..., examples=["do gym/workout", "do not gym/workout"])
    height: str = Field(..., examples=["180 cm", "5 ft 11 inch"])
    weight: str = Field(..., examples=["69 kg"])
    food_type: str = Field(..., examples=["Indian type"])


class MealPlanSection(BaseModel):
    name: str
    options: list[str]


class MealPlanResponse(BaseModel):
    id: str
    created_at: datetime
    sections: list[MealPlanSection]
    raw_response: str


class MealPlanHistoryResponse(BaseModel):
    items: list[MealPlanResponse]


class MealPlanPdfRequest(BaseModel):
    full_name: str
    age: int


class MealPlanPdfExportResponse(BaseModel):
    id: str
    created_at: datetime
    meal_plan_record_id: str
    full_name: str
    age: int
    file_name: str
    mime_type: str = "application/pdf"
    byte_size: int
    operation_id: str | None = None


class MealPlanPdfExportHistoryResponse(BaseModel):
    items: list[MealPlanPdfExportResponse]
