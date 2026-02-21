"""Food insight schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class FoodInsightAnalyzeRequest(BaseModel):
    input_mode: Literal["text", "image"] = "text"
    text: str | None = Field(default=None, description="Food items text (e.g., 2 slices pizza, 1 apple)")
    image_base64: str | None = Field(default=None, description="Base64-encoded image payload")
    image_mime_type: str = Field(default="image/png")

    @model_validator(mode="after")
    def validate_payload(self) -> "FoodInsightAnalyzeRequest":
        if self.input_mode == "text" and not self.text:
            raise ValueError("text is required when input_mode is text")
        if self.input_mode == "image" and not self.image_base64:
            raise ValueError("image_base64 is required when input_mode is image")
        return self


class FoodInsightItem(BaseModel):
    name: str
    quantity: str | None = None
    calories_range: str | None = None
    carbs_range: str | None = None
    fiber_range: str | None = None
    protein_range: str | None = None
    fats_range: str | None = None
    details: str | None = None


class FoodInsightTotals(BaseModel):
    calories: str | None = None
    carbs: str | None = None
    fiber: str | None = None
    protein: str | None = None
    fats: str | None = None


class FoodInsightResponse(BaseModel):
    id: str
    created_at: datetime
    items: list[FoodInsightItem]
    totals: FoodInsightTotals
    verdict: str
    facts: list[str]
    raw_response: str


class FoodInsightHistoryResponse(BaseModel):
    items: list[FoodInsightResponse]
