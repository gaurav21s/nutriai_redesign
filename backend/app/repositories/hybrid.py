"""Hybrid repository that falls back to in-memory on Convex failures."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from app.core.exceptions import ExternalServiceException
from app.core.logging import get_logger
from app.repositories.base import CompositeRepository

T = TypeVar("T")


class HybridRepository(CompositeRepository):
    def __init__(self, primary: CompositeRepository, fallback: CompositeRepository) -> None:
        self.primary = primary
        self.fallback = fallback
        self.logger = get_logger("app.repositories.hybrid")

    async def _run(self, primary_call: Callable[[], Awaitable[T]], fallback_call: Callable[[], Awaitable[T]]) -> T:
        try:
            return await primary_call()
        except ExternalServiceException as exc:
            self.logger.warning("repository_fallback", extra={"reason": str(exc)})
            return await fallback_call()

    async def create_record(self, feature: str, clerk_user_id: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.create_record(feature, clerk_user_id, payload),
            lambda: self.fallback.create_record(feature, clerk_user_id, payload),
        )

    async def get_record(self, feature: str, clerk_user_id: str, record_id: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_record(feature, clerk_user_id, record_id),
            lambda: self.fallback.get_record(feature, clerk_user_id, record_id),
        )

    async def list_records(self, feature: str, clerk_user_id: str, limit: int = 20) -> list[dict]:
        return await self._run(
            lambda: self.primary.list_records(feature, clerk_user_id, limit),
            lambda: self.fallback.list_records(feature, clerk_user_id, limit),
        )

    async def create_chat_session(self, clerk_user_id: str, title: str) -> dict:
        return await self._run(
            lambda: self.primary.create_chat_session(clerk_user_id, title),
            lambda: self.fallback.create_chat_session(clerk_user_id, title),
        )

    async def get_chat_session(self, clerk_user_id: str, session_id: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_chat_session(clerk_user_id, session_id),
            lambda: self.fallback.get_chat_session(clerk_user_id, session_id),
        )

    async def update_chat_session(self, clerk_user_id: str, session_id: str, payload: dict) -> dict | None:
        return await self._run(
            lambda: self.primary.update_chat_session(clerk_user_id, session_id, payload),
            lambda: self.fallback.update_chat_session(clerk_user_id, session_id, payload),
        )

    async def delete_chat_session(self, clerk_user_id: str, session_id: str) -> dict | None:
        return await self._run(
            lambda: self.primary.delete_chat_session(clerk_user_id, session_id),
            lambda: self.fallback.delete_chat_session(clerk_user_id, session_id),
        )

    async def reserve_chat_sequence(self, clerk_user_id: str, session_id: str) -> int:
        return await self._run(
            lambda: self.primary.reserve_chat_sequence(clerk_user_id, session_id),
            lambda: self.fallback.reserve_chat_sequence(clerk_user_id, session_id),
        )

    async def list_chat_sessions(self, clerk_user_id: str, limit: int = 30) -> list[dict]:
        return await self._run(
            lambda: self.primary.list_chat_sessions(clerk_user_id, limit),
            lambda: self.fallback.list_chat_sessions(clerk_user_id, limit),
        )

    async def add_chat_message(
        self,
        clerk_user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        return await self._run(
            lambda: self.primary.add_chat_message(clerk_user_id, session_id, role, content, metadata),
            lambda: self.fallback.add_chat_message(clerk_user_id, session_id, role, content, metadata),
        )

    async def list_chat_messages(self, clerk_user_id: str, session_id: str, limit: int = 100) -> list[dict]:
        return await self._run(
            lambda: self.primary.list_chat_messages(clerk_user_id, session_id, limit),
            lambda: self.fallback.list_chat_messages(clerk_user_id, session_id, limit),
        )

    async def create_chat_action(self, clerk_user_id: str, session_id: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.create_chat_action(clerk_user_id, session_id, payload),
            lambda: self.fallback.create_chat_action(clerk_user_id, session_id, payload),
        )

    async def get_chat_action(self, clerk_user_id: str, session_id: str, action_id: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_chat_action(clerk_user_id, session_id, action_id),
            lambda: self.fallback.get_chat_action(clerk_user_id, session_id, action_id),
        )

    async def update_chat_action(self, clerk_user_id: str, session_id: str, action_id: str, payload: dict) -> dict | None:
        return await self._run(
            lambda: self.primary.update_chat_action(clerk_user_id, session_id, action_id, payload),
            lambda: self.fallback.update_chat_action(clerk_user_id, session_id, action_id, payload),
        )

    async def create_quiz_session(self, clerk_user_id: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.create_quiz_session(clerk_user_id, payload),
            lambda: self.fallback.create_quiz_session(clerk_user_id, payload),
        )

    async def get_quiz_session(self, clerk_user_id: str, session_id: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_quiz_session(clerk_user_id, session_id),
            lambda: self.fallback.get_quiz_session(clerk_user_id, session_id),
        )

    async def store_quiz_submission(self, clerk_user_id: str, session_id: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.store_quiz_submission(clerk_user_id, session_id, payload),
            lambda: self.fallback.store_quiz_submission(clerk_user_id, session_id, payload),
        )

    async def list_quiz_history(self, clerk_user_id: str, limit: int = 20) -> list[dict]:
        return await self._run(
            lambda: self.primary.list_quiz_history(clerk_user_id, limit),
            lambda: self.fallback.list_quiz_history(clerk_user_id, limit),
        )

    async def list_articles(self, query: str | None = None, limit: int = 50) -> list[dict]:
        return await self._run(
            lambda: self.primary.list_articles(query, limit),
            lambda: self.fallback.list_articles(query, limit),
        )

    async def get_article_by_slug(self, slug: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_article_by_slug(slug),
            lambda: self.fallback.get_article_by_slug(slug),
        )

    async def seed_articles(self, items: list[dict]) -> int:
        return await self._run(
            lambda: self.primary.seed_articles(items),
            lambda: self.fallback.seed_articles(items),
        )

    async def upsert_user(self, clerk_user_id: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.upsert_user(clerk_user_id, payload),
            lambda: self.fallback.upsert_user(clerk_user_id, payload),
        )

    async def get_subscription(self, clerk_user_id: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_subscription(clerk_user_id),
            lambda: self.fallback.get_subscription(clerk_user_id),
        )

    async def upsert_subscription(self, clerk_user_id: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.upsert_subscription(clerk_user_id, payload),
            lambda: self.fallback.upsert_subscription(clerk_user_id, payload),
        )

    async def add_subscription_event(self, clerk_user_id: str, event_type: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.add_subscription_event(clerk_user_id, event_type, payload),
            lambda: self.fallback.add_subscription_event(clerk_user_id, event_type, payload),
        )

    async def list_subscription_events(self, clerk_user_id: str, limit: int = 50) -> list[dict]:
        return await self._run(
            lambda: self.primary.list_subscription_events(clerk_user_id, limit),
            lambda: self.fallback.list_subscription_events(clerk_user_id, limit),
        )

    async def get_subscription_usage(self, clerk_user_id: str, period_key: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_subscription_usage(clerk_user_id, period_key),
            lambda: self.fallback.get_subscription_usage(clerk_user_id, period_key),
        )

    async def upsert_subscription_usage(self, clerk_user_id: str, period_key: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.upsert_subscription_usage(clerk_user_id, period_key, payload),
            lambda: self.fallback.upsert_subscription_usage(clerk_user_id, period_key, payload),
        )

    async def increment_subscription_usage(self, clerk_user_id: str, period_key: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.increment_subscription_usage(clerk_user_id, period_key, payload),
            lambda: self.fallback.increment_subscription_usage(clerk_user_id, period_key, payload),
        )

    async def create_operation(self, clerk_user_id: str, payload: dict) -> dict:
        return await self._run(
            lambda: self.primary.create_operation(clerk_user_id, payload),
            lambda: self.fallback.create_operation(clerk_user_id, payload),
        )

    async def get_operation(self, clerk_user_id: str, operation_id: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_operation(clerk_user_id, operation_id),
            lambda: self.fallback.get_operation(clerk_user_id, operation_id),
        )

    async def get_operation_by_idempotency(self, clerk_user_id: str, feature: str, idempotency_key: str) -> dict | None:
        return await self._run(
            lambda: self.primary.get_operation_by_idempotency(clerk_user_id, feature, idempotency_key),
            lambda: self.fallback.get_operation_by_idempotency(clerk_user_id, feature, idempotency_key),
        )

    async def update_operation(self, clerk_user_id: str, operation_id: str, payload: dict) -> dict | None:
        return await self._run(
            lambda: self.primary.update_operation(clerk_user_id, operation_id, payload),
            lambda: self.fallback.update_operation(clerk_user_id, operation_id, payload),
        )
