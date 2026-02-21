"""Error schema definitions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable message")
    details: Any = Field(default_factory=dict, description="Additional error details")
    request_id: str | None = Field(default=None, description="Request correlation ID")


class ErrorResponse(BaseModel):
    error: ErrorBody
