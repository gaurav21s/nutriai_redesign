"""Operation/job schemas used for async-capable workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


OperationFeature = Literal[
    "chat_turn",
    "meal_plan_generate",
    "meal_plan_export_pdf",
    "recipe_generate",
    "recommendation_generate",
    "food_insight_analyze",
    "ingredient_check_analyze",
    "quiz_generate",
    "quiz_submit",
]

OperationStatus = Literal["queued", "running", "completed", "failed", "cancelled", "expired"]
OperationQueueTier = Literal["free", "plus", "pro"]


class OperationResultRef(BaseModel):
    resource_type: str
    resource_id: str
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationRecord(BaseModel):
    operation_id: str
    clerk_user_id: str
    feature: OperationFeature
    status: OperationStatus
    queue_tier: OperationQueueTier
    resource_scope: dict[str, str] = Field(default_factory=dict)
    workload_pool: str
    idempotency_key: str | None = None
    request_payload: dict[str, Any] = Field(default_factory=dict)
    response_payload: dict[str, Any] = Field(default_factory=dict)
    result_ref: OperationResultRef | None = None
    sequence_no: int | None = None
    request_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    enqueued_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OperationSubmitRequest(BaseModel):
    feature: OperationFeature
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=200)
    resource_scope: dict[str, str] = Field(default_factory=dict)


class OperationResponse(BaseModel):
    operation: OperationRecord


class OperationStreamEvent(BaseModel):
    type: Literal["queued", "running", "completed", "failed", "heartbeat"]
    operation: OperationRecord
