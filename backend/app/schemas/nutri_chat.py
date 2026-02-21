"""NutriChat schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ChatRole = Literal["user", "assistant"]


class ChatSessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    last_message_at: datetime | None = None


class ChatSessionsResponse(BaseModel):
    items: list[ChatSessionResponse]


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class ChatMessage(BaseModel):
    id: str
    role: ChatRole
    content: str
    created_at: datetime


class ChatMessagesResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage]
