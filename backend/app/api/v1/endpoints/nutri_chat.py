"""NutriChat endpoints."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.security import AuthContext, get_auth_context
from app.dependencies import chat_rate_limit, default_rate_limit, get_nutri_chat_service, get_operations_service
from app.schemas.nutri_chat import (
    ChatActionResponse,
    ChatContextResponse,
    ChatMessage,
    ChatMessageCreateRequest,
    ChatMessagesResponse,
    ChatSessionCreateRequest,
    ChatSessionDeleteResponse,
    ChatSessionResponse,
    ChatSessionsResponse,
    ChatSessionUpdateRequest,
)
from app.schemas.operations import OperationSubmitRequest
from app.services.operations_service import OperationsService
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


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Rename chat session",
    description="Updates the title for one chat session.",
    dependencies=[Depends(default_rate_limit)],
)
async def rename_chat_session(
    session_id: str,
    payload: ChatSessionUpdateRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatSessionResponse:
    return await service.rename_session(auth.clerk_user_id, session_id, payload.title)


@router.delete(
    "/sessions/{session_id}",
    response_model=ChatSessionDeleteResponse,
    summary="Delete chat session",
    description="Deletes one chat session and its message history.",
    dependencies=[Depends(default_rate_limit)],
)
async def delete_chat_session(
    session_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatSessionDeleteResponse:
    return await service.delete_session(auth.clerk_user_id, session_id)


@router.get(
    "/context",
    response_model=ChatContextResponse,
    summary="Get chat context snapshot",
    description="Returns a compact summary of the current user's saved NutriAI data used by the agent chat.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_chat_context(
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatContextResponse:
    return await service.get_context(auth.clerk_user_id)


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
    operations_service: OperationsService = Depends(get_operations_service),
) -> ChatMessage:
    operation = await operations_service.submit_and_wait(
        auth.clerk_user_id,
        OperationSubmitRequest(
            feature="chat_turn",
            payload={"session_id": session_id, "content": payload.content},
            idempotency_key=payload.idempotency_key,
            resource_scope={"session_id": session_id},
        ),
    )
    return ChatMessage.model_validate(operation.response_payload)


@router.post(
    "/sessions/{session_id}/turns/stream",
    summary="Stream an agent chat turn",
    description="Streams reasoning updates and the final assistant reply for one text-based chat turn.",
    dependencies=[Depends(chat_rate_limit)],
)
async def stream_chat_turn(
    session_id: str,
    payload: ChatMessageCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_turn(auth.clerk_user_id, session_id, payload.content),
        media_type="application/x-ndjson",
    )


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


@router.post(
    "/sessions/{session_id}/actions/{action_id}/confirm",
    response_model=ChatActionResponse,
    summary="Confirm and save a pending agent action",
    dependencies=[Depends(default_rate_limit)],
)
async def confirm_chat_action(
    session_id: str,
    action_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatActionResponse:
    return await service.confirm_action(auth.clerk_user_id, session_id, action_id)


@router.post(
    "/sessions/{session_id}/actions/{action_id}/reject",
    response_model=ChatActionResponse,
    summary="Reject a pending agent action",
    dependencies=[Depends(default_rate_limit)],
)
async def reject_chat_action(
    session_id: str,
    action_id: str,
    auth: AuthContext = Depends(get_auth_context),
    service: NutriChatService = Depends(get_nutri_chat_service),
) -> ChatActionResponse:
    return await service.reject_action(auth.clerk_user_id, session_id, action_id)
