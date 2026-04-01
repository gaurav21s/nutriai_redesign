"""NutriChat schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ChatRole = Literal["user", "assistant"]
PendingActionStatus = Literal["pending", "confirmed", "rejected"]
PendingActionKind = Literal["save_calculation", "save_recommendations", "save_recipe"]


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


class ChatReasoningStep(BaseModel):
    id: str
    label: str
    detail: str
    status: Literal["running", "completed", "info"] = "info"
    created_at: datetime


class ChatSourceReference(BaseModel):
    source_type: Literal["context", "tool", "history"]
    feature: str
    label: str
    record_id: str | None = None


class ChatPendingAction(BaseModel):
    action_id: str
    session_id: str
    kind: PendingActionKind
    title: str
    summary: str
    status: PendingActionStatus
    preview_payload: dict[str, Any]
    created_at: datetime
    resolved_at: datetime | None = None
    saved_record_id: str | None = None


class ChatMessageMetadata(BaseModel):
    reasoning_steps: list[ChatReasoningStep] = Field(default_factory=list)
    source_references: list[ChatSourceReference] = Field(default_factory=list)
    pending_action: ChatPendingAction | None = None


class ChatMessage(BaseModel):
    id: str
    role: ChatRole
    content: str
    created_at: datetime
    metadata: ChatMessageMetadata | None = None


class ChatMessagesResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage]


class ChatContextSection(BaseModel):
    feature: str
    label: str
    item_count: int
    summary: str
    last_updated: datetime | None = None


class ChatContextResponse(BaseModel):
    items: list[ChatContextSection]


class ChatTurnResponse(BaseModel):
    message: ChatMessage
    context: list[ChatContextSection]


class ChatActionResponse(BaseModel):
    action: ChatPendingAction
