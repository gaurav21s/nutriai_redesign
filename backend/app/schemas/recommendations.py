"""Recommendation schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RecommendationType = Literal["healthier_alternative", "new_healthy_recipe", "both"]


class RecommendationGenerateRequest(BaseModel):
    query: str = Field(..., min_length=2)
    recommendation_type: RecommendationType = "both"


class RecommendationResponse(BaseModel):
    id: str
    created_at: datetime
    title: str
    recommendations: list[str]
    raw_response: str


class RecommendationHistoryResponse(BaseModel):
    items: list[RecommendationResponse]
