"""Ingredient checker schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class IngredientCheckRequest(BaseModel):
    input_mode: Literal["text", "image"] = "text"
    ingredients_text: str | None = Field(default=None, description="Comma-separated ingredient list")
    image_base64: str | None = None
    image_mime_type: str = "image/png"

    @model_validator(mode="after")
    def validate_payload(self) -> "IngredientCheckRequest":
        if self.input_mode == "text" and not self.ingredients_text:
            raise ValueError("ingredients_text is required when input_mode is text")
        if self.input_mode == "image" and not self.image_base64:
            raise ValueError("image_base64 is required when input_mode is image")
        return self


class IngredientCheckResponse(BaseModel):
    id: str
    created_at: datetime
    healthy_ingredients: list[str]
    unhealthy_ingredients: list[str]
    health_issues: dict[str, list[str]]
    raw_response: str


class IngredientCheckHistoryResponse(BaseModel):
    items: list[IngredientCheckResponse]
