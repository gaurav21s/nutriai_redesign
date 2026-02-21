"""NutriChat endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.security import AuthContext, get_auth_context
from app.dependencies import chat_rate_limit, default_rate_limit, get_nutri_chat_service
from app.schemas.nutri_chat import (
    ChatMessage,
    ChatMessageCreateRequest,
    ChatMessagesResponse,
    ChatSessionCreateRequest,
    ChatSessionResponse,
    ChatSessionsResponse,
)
from app.services.nutri_chat_service import NutriChatService

router = APIRouter(prefix="/nutri-chat", tags=["Nutri Chat"])


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    summary="Create chat session",
    description="Creates a new chat session for the current user.",
    dependencies=[Depends(default_rate_limit)],
)
async def create_chat_session(
    payload: ChatSessionCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatSessionResponse:
    return await service.create_session(auth.clerk_user_id, payload.title)


@router.get(
    "/sessions",
    response_model=ChatSessionsResponse,
    summary="List chat sessions",
    description="Returns chat sessions for the current user.",
    dependencies=[Depends(default_rate_limit)],
)
async def list_chat_sessions(
    limit: int = Query(default=30, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatSessionsResponse:
    items = await service.list_sessions(auth.clerk_user_id, limit)
    return ChatSessionsResponse(items=items)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessage,
    summary="Send chat message",
    description="Sends a user message and returns model-generated assistant response.",
    dependencies=[Depends(chat_rate_limit)],
)
async def send_chat_message(
    session_id: str,
    payload: ChatMessageCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatMessage:
    return await service.send_message(auth.clerk_user_id, session_id, payload.content)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ChatMessagesResponse,
    summary="List chat messages",
    description="Returns message history for one chat session.",
    dependencies=[Depends(default_rate_limit)],
)
async def list_chat_messages(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=300),
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatMessagesResponse:
    items = await service.list_messages(auth.clerk_user_id, session_id, limit)
    return ChatMessagesResponse(session_id=session_id, messages=items)
