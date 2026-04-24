"""Nutri Smart Picks schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from pydantic import model_validator


SmartPickMode = Literal["compare_options", "situation_pick", "swap_current_choice"]
SmartPickGoal = Literal["fat_loss", "muscle_gain", "maintenance", "energy_focus", "recovery", "healthy_lifestyle"]


class SmartPickGenerateRequest(BaseModel):
    goal: SmartPickGoal = "healthy_lifestyle"
    mode: SmartPickMode = "situation_pick"
    situation: str | None = Field(default=None, min_length=2)
    options: list[str] = Field(default_factory=list)
    current_choice: str | None = Field(default=None, min_length=2)
    constraints: list[str] = Field(default_factory=list)
    diet_preference: str | None = Field(default=None, min_length=2)
    budget: str | None = Field(default=None, min_length=2)
    time_available: str | None = Field(default=None, min_length=1)
    cooking_access: str | None = Field(default=None, min_length=2)
    context: str | None = Field(default=None, min_length=2)

    @model_validator(mode="after")
    def validate_mode_requirements(self) -> "SmartPickGenerateRequest":
        if self.mode == "compare_options" and len([item for item in self.options if item.strip()]) < 2:
            raise ValueError("compare_options requires at least two options")
        if self.mode == "swap_current_choice" and not (self.current_choice or "").strip():
            raise ValueError("swap_current_choice requires current_choice")
        if self.mode == "situation_pick" and not any(
            [
                (self.situation or "").strip(),
                (self.context or "").strip(),
                len([item for item in self.constraints if item.strip()]) > 0,
            ]
        ):
            raise ValueError("situation_pick requires situation, context, or constraints")
        return self


class SmartPickOption(BaseModel):
    label: str
    rank: int
    verdict: str
    why: str
    tradeoff: str
    quick_upgrade: str
    good_for: str
    avoid_if: str


class SmartPickResponse(BaseModel):
    id: str
    created_at: datetime
    title: str
    decision_summary: str
    best_pick: str
    fallback_rule: str
    ranked_options: list[SmartPickOption]
    raw_response: str


class SmartPickHistoryResponse(BaseModel):
    items: list[SmartPickResponse]


# Backward-compatible aliases for existing internal imports.
RecommendationGenerateRequest = SmartPickGenerateRequest
RecommendationResponse = SmartPickResponse
RecommendationHistoryResponse = SmartPickHistoryResponse
RecommendationType = SmartPickMode
