"""In-memory repository for local development and tests."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.base import CompositeRepository


class InMemoryRepository(CompositeRepository):
    """Simple process-local persistence."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, dict]] = defaultdict(dict)
        self._quiz_sessions: dict[str, dict] = {}
        self._quiz_attempts: dict[str, list[dict]] = defaultdict(list)
        self._chat_sessions: dict[str, dict] = {}
        self._chat_messages: dict[str, list[dict]] = defaultdict(list)
        self._articles: dict[str, dict] = {}
        self._users: dict[str, dict] = {}
        self._subscriptions: dict[str, dict] = {}
        self._subscription_events: dict[str, list[dict]] = defaultdict(list)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    async def create_record(self, feature: str, clerk_user_id: str, payload: dict) -> dict:
        record_id = str(uuid4())
        created_at = payload.get("created_at") or self._now_iso()
        record = {
            "id": record_id,
            "clerk_user_id": clerk_user_id,
            "feature": feature,
            "created_at": created_at,
            **payload,
        }
        self._records[feature][record_id] = record
        return record

    async def get_record(self, feature: str, clerk_user_id: str, record_id: str) -> dict | None:
        record = self._records[feature].get(record_id)
        if not record:
            return None
        if record.get("clerk_user_id") != clerk_user_id:
            return None
        return record

    async def list_records(self, feature: str, clerk_user_id: str, limit: int = 20) -> list[dict]:
        items = [
            item
            for item in self._records[feature].values()
            if item.get("clerk_user_id") == clerk_user_id
        ]
        items.sort(key=lambda value: value.get("created_at", ""), reverse=True)
        return items[:limit]

    async def create_chat_session(self, clerk_user_id: str, title: str) -> dict:
        session_id = str(uuid4())
        session = {
            "session_id": session_id,
            "clerk_user_id": clerk_user_id,
            "title": title,
            "created_at": self._now_iso(),
            "last_message_at": None,
        }
        self._chat_sessions[session_id] = session
        return session

    async def list_chat_sessions(self, clerk_user_id: str, limit: int = 30) -> list[dict]:
        sessions = [
            session
            for session in self._chat_sessions.values()
            if session.get("clerk_user_id") == clerk_user_id
        ]
        sessions.sort(key=lambda item: item.get("last_message_at") or item.get("created_at"), reverse=True)
        return sessions[:limit]

    async def add_chat_message(self, clerk_user_id: str, session_id: str, role: str, content: str) -> dict:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            raise ValueError("Chat session not found")

        message = {
            "id": str(uuid4()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": self._now_iso(),
        }
        self._chat_messages[session_id].append(message)

        session["last_message_at"] = message["created_at"]
        return message

    async def list_chat_messages(self, clerk_user_id: str, session_id: str, limit: int = 100) -> list[dict]:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            return []
        return self._chat_messages.get(session_id, [])[-limit:]

    async def create_quiz_session(self, clerk_user_id: str, payload: dict) -> dict:
        session_id = str(uuid4())
        record = {
            "session_id": session_id,
            "clerk_user_id": clerk_user_id,
            "created_at": self._now_iso(),
            **payload,
        }
        self._quiz_sessions[session_id] = record
        return record

    async def get_quiz_session(self, clerk_user_id: str, session_id: str) -> dict | None:
        record = self._quiz_sessions.get(session_id)
        if not record or record.get("clerk_user_id") != clerk_user_id:
            return None
        return record

    async def store_quiz_submission(self, clerk_user_id: str, session_id: str, payload: dict) -> dict:
        record = {
            "id": str(uuid4()),
            "session_id": session_id,
            "clerk_user_id": clerk_user_id,
            "created_at": self._now_iso(),
            **payload,
        }
        self._quiz_attempts[session_id].append(record)
        return record

    async def list_quiz_history(self, clerk_user_id: str, limit: int = 20) -> list[dict]:
        items = []
        for session in self._quiz_sessions.values():
            if session.get("clerk_user_id") != clerk_user_id:
                continue
            attempts = self._quiz_attempts.get(session["session_id"], [])
            latest_attempt = attempts[-1] if attempts else None
            items.append(
                {
                    "session_id": session["session_id"],
                    "topic": session.get("topic"),
                    "difficulty": session.get("difficulty"),
                    "created_at": session.get("created_at"),
                    "score_percentage": (latest_attempt or {}).get("score_percentage"),
                }
            )

        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items[:limit]

    async def list_articles(self, query: str | None = None, limit: int = 50) -> list[dict]:
        articles = list(self._articles.values())
        if query:
            lowered = query.lower()
            articles = [
                article
                for article in articles
                if lowered in article.get("title", "").lower()
                or lowered in article.get("summary", "").lower()
            ]
        articles.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return articles[:limit]

    async def get_article_by_slug(self, slug: str) -> dict | None:
        return self._articles.get(slug)

    async def seed_articles(self, items: list[dict]) -> int:
        inserted = 0
        for article in items:
            slug = str(article.get("slug", "")).strip()
            if not slug:
                continue
            if slug in self._articles:
                continue
            self._articles[slug] = article
            inserted += 1
        return inserted

    async def upsert_user(self, clerk_user_id: str, payload: dict) -> dict:
        existing = self._users.get(clerk_user_id)
        now = self._now_iso()
        doc = {
            "clerk_user_id": clerk_user_id,
            "created_at": existing.get("created_at") if existing else now,
            **(existing or {}),
            **payload,
        }
        self._users[clerk_user_id] = doc
        return doc

    async def get_subscription(self, clerk_user_id: str) -> dict | None:
        return self._subscriptions.get(clerk_user_id)

    async def upsert_subscription(self, clerk_user_id: str, payload: dict) -> dict:
        existing = self._subscriptions.get(clerk_user_id)
        now = self._now_iso()
        doc = {
            "clerk_user_id": clerk_user_id,
            "created_at": existing.get("created_at") if existing else now,
            "updated_at": now,
            **(existing or {}),
            **payload,
        }
        self._subscriptions[clerk_user_id] = doc
        return doc

    async def add_subscription_event(self, clerk_user_id: str, event_type: str, payload: dict) -> dict:
        item = {
            "id": str(uuid4()),
            "clerk_user_id": clerk_user_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": self._now_iso(),
        }
        self._subscription_events[clerk_user_id].append(item)
        return item

    async def list_subscription_events(self, clerk_user_id: str, limit: int = 50) -> list[dict]:
        rows = self._subscription_events.get(clerk_user_id, [])
        rows_sorted = sorted(rows, key=lambda item: item.get("created_at", ""), reverse=True)
        return rows_sorted[:limit]
