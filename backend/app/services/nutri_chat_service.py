"""Service layer for NutriChat."""

from __future__ import annotations

from datetime import datetime

from app.core.exceptions import NotFoundException
from app.repositories.base import CompositeRepository
from app.schemas.nutri_chat import ChatMessage, ChatSessionResponse
from app.utils.ai_clients import TogetherClient
from app.utils.prompt_builders import chat_system_prompt


class NutriChatService:
    def __init__(self, repository: CompositeRepository, together_client: TogetherClient) -> None:
        self.repository = repository
        self.together_client = together_client

    async def create_session(self, clerk_user_id: str, title: str | None = None) -> ChatSessionResponse:
        payload = await self.repository.create_chat_session(
            clerk_user_id,
            title or "Nutrition Chat",
        )
        return ChatSessionResponse.model_validate(payload)

    async def list_sessions(self, clerk_user_id: str, limit: int = 30) -> list[ChatSessionResponse]:
        rows = await self.repository.list_chat_sessions(clerk_user_id, limit)
        return [ChatSessionResponse.model_validate(item) for item in rows]

    async def list_messages(self, clerk_user_id: str, session_id: str, limit: int = 100) -> list[ChatMessage]:
        rows = await self.repository.list_chat_messages(clerk_user_id, session_id, limit)
        return [ChatMessage.model_validate(item) for item in rows]

    async def send_message(self, clerk_user_id: str, session_id: str, content: str) -> ChatMessage:
        sessions = await self.repository.list_chat_sessions(clerk_user_id, limit=100)
        if not any(session.get("session_id") == session_id for session in sessions):
            raise NotFoundException("Chat session not found")

        await self.repository.add_chat_message(clerk_user_id, session_id, "user", content)
        recent = await self.repository.list_chat_messages(clerk_user_id, session_id, limit=12)

        transcript = []
        for item in recent:
            role = str(item.get("role", "user"))
            text = str(item.get("content", "")).strip()
            if text:
                transcript.append(f"{role.title()}: {text}")

        prompt = "\n".join([
            chat_system_prompt(),
            "Conversation:",
            *transcript,
            f"User: {content}",
            "Assistant:",
        ])

        assistant_text = await self.together_client.generate_text(prompt, temperature=0.6)

        saved = await self.repository.add_chat_message(clerk_user_id, session_id, "assistant", assistant_text)
        return ChatMessage.model_validate(saved)
