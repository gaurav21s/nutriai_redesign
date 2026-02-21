"""Shared schemas used across features."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HistoryPageMeta(BaseModel):
    limit: int = Field(default=20)
    next_cursor: str | None = Field(default=None)


class HistoryRecordBase(BaseModel):
    id: str = Field(..., description="Unique record identifier")
    created_at: datetime = Field(..., description="Creation timestamp in UTC")


class MessageResponse(BaseModel):
    message: str
    data: dict[str, Any] | None = None
