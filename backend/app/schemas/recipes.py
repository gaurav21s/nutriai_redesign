"""Recipe generation and shopping link schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RecipeType = Literal["normal", "healthier", "new_healthy"]


class RecipeGenerateRequest(BaseModel):
    dish_name: str = Field(..., min_length=2)
    recipe_type: RecipeType


class RecipeIngredient(BaseModel):
    raw: str


class ShoppingLinkPair(BaseModel):
    amazon: str
    blinkit: str


class RecipeResponse(BaseModel):
    id: str
    created_at: datetime
    recipe_name: str
    ingredients: list[RecipeIngredient]
    steps: list[str]
    ingredient_list: list[str]
    shopping_links: dict[str, ShoppingLinkPair] = Field(default_factory=dict)
    explanation: str | None = None
    raw_response: str


class RecipeHistoryResponse(BaseModel):
    items: list[RecipeResponse]


class ShoppingLinksRequest(BaseModel):
    ingredients: list[str] = Field(default_factory=list)


class ShoppingLinksResponse(BaseModel):
    links: dict[str, ShoppingLinkPair]
