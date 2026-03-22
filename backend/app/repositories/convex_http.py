"""Convex HTTP action repository implementation."""

from __future__ import annotations

import httpx

from app.core.exceptions import ExternalServiceException
from app.repositories.base import CompositeRepository


class ConvexHttpRepository(CompositeRepository):
    """Persists domain data via Convex HTTP actions."""

    def __init__(self, base_url: str, backend_secret: str, timeout_seconds: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.backend_secret = backend_secret
        self.timeout_seconds = timeout_seconds

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-backend-secret": self.backend_secret,
        }

    async def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=self._headers)
        except Exception as exc:
            raise ExternalServiceException("Unable to reach Convex HTTP actions", details={"reason": str(exc)}) from exc

        if response.status_code >= 400:
            raise ExternalServiceException(
                "Convex HTTP action returned an error",
                details={"status_code": response.status_code, "body": response.text},
            )

        body = response.json()
        if not body.get("ok", False):
            raise ExternalServiceException(
                "Convex HTTP action failed",
                details={"body": body},
            )

        return body.get("data", {})

    async def create_record(self, feature: str, clerk_user_id: str, payload: dict) -> dict:
        return await self._post(
            "/backend/records/create",
            {"feature": feature, "clerkUserId": clerk_user_id, "payload": payload},
        )

    async def get_record(self, feature: str, clerk_user_id: str, record_id: str) -> dict | None:
        result = await self._post(
            "/backend/records/get",
            {
                "feature": feature,
                "clerkUserId": clerk_user_id,
                "recordId": record_id,
            },
        )
        return result or None

    async def list_records(self, feature: str, clerk_user_id: str, limit: int = 20) -> list[dict]:
        result = await self._post(
            "/backend/records/list",
            {"feature": feature, "clerkUserId": clerk_user_id, "limit": limit},
        )
        return result.get("items", [])

    async def create_chat_session(self, clerk_user_id: str, title: str) -> dict:
        return await self._post(
            "/backend/chat/sessions/create",
            {"clerkUserId": clerk_user_id, "title": title},
        )

    async def list_chat_sessions(self, clerk_user_id: str, limit: int = 30) -> list[dict]:
        result = await self._post(
            "/backend/chat/sessions/list",
            {"clerkUserId": clerk_user_id, "limit": limit},
        )
        return result.get("items", [])

    async def add_chat_message(self, clerk_user_id: str, session_id: str, role: str, content: str) -> dict:
        return await self._post(
            "/backend/chat/messages/add",
            {
                "clerkUserId": clerk_user_id,
                "sessionId": session_id,
                "role": role,
                "content": content,
            },
        )

    async def list_chat_messages(self, clerk_user_id: str, session_id: str, limit: int = 100) -> list[dict]:
        result = await self._post(
            "/backend/chat/messages/list",
            {
                "clerkUserId": clerk_user_id,
                "sessionId": session_id,
                "limit": limit,
            },
        )
        return result.get("items", [])

    async def create_quiz_session(self, clerk_user_id: str, payload: dict) -> dict:
        return await self._post(
            "/backend/quizzes/sessions/create",
            {"clerkUserId": clerk_user_id, "payload": payload},
        )

    async def get_quiz_session(self, clerk_user_id: str, session_id: str) -> dict | None:
        result = await self._post(
            "/backend/quizzes/sessions/get",
            {"clerkUserId": clerk_user_id, "sessionId": session_id},
        )
        return result or None

    async def store_quiz_submission(self, clerk_user_id: str, session_id: str, payload: dict) -> dict:
        return await self._post(
            "/backend/quizzes/submissions/create",
            {
                "clerkUserId": clerk_user_id,
                "sessionId": session_id,
                "payload": payload,
            },
        )

    async def list_quiz_history(self, clerk_user_id: str, limit: int = 20) -> list[dict]:
        result = await self._post(
            "/backend/quizzes/history/list",
            {"clerkUserId": clerk_user_id, "limit": limit},
        )
        return result.get("items", [])

    async def list_articles(self, query: str | None = None, limit: int = 50) -> list[dict]:
        result = await self._post(
            "/backend/articles/list",
            {"query": query, "limit": limit},
        )
        return result.get("items", [])

    async def get_article_by_slug(self, slug: str) -> dict | None:
        result = await self._post("/backend/articles/get", {"slug": slug})
        return result or None

    async def seed_articles(self, items: list[dict]) -> int:
        result = await self._post("/backend/articles/seed", {"items": items})
        return int(result.get("inserted", 0))

    async def upsert_user(self, clerk_user_id: str, payload: dict) -> dict:
        return await self._post(
            "/backend/users/upsert",
            {"clerkUserId": clerk_user_id, "payload": payload},
        )

    async def get_subscription(self, clerk_user_id: str) -> dict | None:
        result = await self._post(
            "/backend/subscriptions/get",
            {"clerkUserId": clerk_user_id},
        )
        return result or None

    async def upsert_subscription(self, clerk_user_id: str, payload: dict) -> dict:
        return await self._post(
            "/backend/subscriptions/upsert",
            {"clerkUserId": clerk_user_id, "payload": payload},
        )

    async def add_subscription_event(self, clerk_user_id: str, event_type: str, payload: dict) -> dict:
        return await self._post(
            "/backend/subscriptions/events/add",
            {
                "clerkUserId": clerk_user_id,
                "eventType": event_type,
                "payload": payload,
            },
        )

    async def list_subscription_events(self, clerk_user_id: str, limit: int = 50) -> list[dict]:
        result = await self._post(
            "/backend/subscriptions/events/list",
            {"clerkUserId": clerk_user_id, "limit": limit},
        )
        return result.get("items", [])
