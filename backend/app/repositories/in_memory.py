"""In-memory repository for local development and tests."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from app.core.exceptions import AppException
from app.repositories.base import CompositeRepository


class InMemoryRepository(CompositeRepository):
    """Simple process-local persistence."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, dict]] = defaultdict(dict)
        self._quiz_sessions: dict[str, dict] = {}
        self._quiz_attempts: dict[str, list[dict]] = defaultdict(list)
        self._chat_sessions: dict[str, dict] = {}
        self._chat_messages: dict[str, list[dict]] = defaultdict(list)
        self._chat_actions: dict[str, dict[str, dict]] = defaultdict(dict)
        self._articles: dict[str, dict] = {}
        self._users: dict[str, dict] = {}
        self._subscriptions: dict[str, dict] = {}
        self._subscription_events: dict[str, list[dict]] = defaultdict(list)
        self._subscription_usage: dict[tuple[str, str], dict] = {}
        self._operations: dict[str, dict] = {}
        self._operation_by_idempotency: dict[tuple[str, str, str], str] = {}

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
            "next_sequence_no": 0,
        }
        self._chat_sessions[session_id] = session
        return session

    async def get_chat_session(self, clerk_user_id: str, session_id: str) -> dict | None:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            return None
        return session

    async def update_chat_session(self, clerk_user_id: str, session_id: str, payload: dict) -> dict | None:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            return None
        session.update(payload)
        return session

    async def delete_chat_session(self, clerk_user_id: str, session_id: str) -> dict | None:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            return None
        self._chat_sessions.pop(session_id, None)
        self._chat_messages.pop(session_id, None)
        self._chat_actions.pop(session_id, None)
        return {"session_id": session_id, "deleted": True}

    async def reserve_chat_sequence(self, clerk_user_id: str, session_id: str) -> int:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            raise ValueError("Chat session not found")
        next_sequence_no = int(session.get("next_sequence_no") or 0) + 1
        session["next_sequence_no"] = next_sequence_no
        return next_sequence_no

    async def list_chat_sessions(self, clerk_user_id: str, limit: int = 30) -> list[dict]:
        sessions = [
            session
            for session in self._chat_sessions.values()
            if session.get("clerk_user_id") == clerk_user_id
        ]
        sessions.sort(key=lambda item: item.get("last_message_at") or item.get("created_at"), reverse=True)
        return sessions[:limit]

    async def add_chat_message(
        self,
        clerk_user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            raise ValueError("Chat session not found")

        message = {
            "id": str(uuid4()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": self._now_iso(),
            "metadata": metadata,
        }
        self._chat_messages[session_id].append(message)

        session["last_message_at"] = message["created_at"]
        return message

    async def list_chat_messages(self, clerk_user_id: str, session_id: str, limit: int = 100) -> list[dict]:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            return []
        return self._chat_messages.get(session_id, [])[-limit:]

    async def create_chat_action(self, clerk_user_id: str, session_id: str, payload: dict) -> dict:
        session = self._chat_sessions.get(session_id)
        if not session or session.get("clerk_user_id") != clerk_user_id:
            raise ValueError("Chat session not found")

        action_id = str(uuid4())
        doc = {
            "action_id": action_id,
            "session_id": session_id,
            "clerk_user_id": clerk_user_id,
            "created_at": self._now_iso(),
            "resolved_at": None,
            **payload,
        }
        self._chat_actions[session_id][action_id] = doc
        return doc

    async def get_chat_action(self, clerk_user_id: str, session_id: str, action_id: str) -> dict | None:
        action = self._chat_actions.get(session_id, {}).get(action_id)
        if not action or action.get("clerk_user_id") != clerk_user_id:
            return None
        return action

    async def update_chat_action(self, clerk_user_id: str, session_id: str, action_id: str, payload: dict) -> dict | None:
        action = self._chat_actions.get(session_id, {}).get(action_id)
        if not action or action.get("clerk_user_id") != clerk_user_id:
            return None

        updated = {
            **action,
            **payload,
        }
        if payload.get("status") in {"confirmed", "rejected"} and not updated.get("resolved_at"):
            updated["resolved_at"] = self._now_iso()
        self._chat_actions[session_id][action_id] = updated
        return updated

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
            "attempt_id": str(uuid4()),
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

    async def get_subscription_usage(self, clerk_user_id: str, period_key: str) -> dict | None:
        return self._subscription_usage.get((clerk_user_id, period_key))

    async def upsert_subscription_usage(self, clerk_user_id: str, period_key: str, payload: dict) -> dict:
        existing = self._subscription_usage.get((clerk_user_id, period_key))
        now = self._now_iso()
        doc = {
            "clerk_user_id": clerk_user_id,
            "period_key": period_key,
            "created_at": existing.get("created_at") if existing else now,
            "updated_at": now,
            **(existing or {}),
            **payload,
        }
        self._subscription_usage[(clerk_user_id, period_key)] = doc
        return doc

    async def increment_subscription_usage(self, clerk_user_id: str, period_key: str, payload: dict) -> dict:
        existing = self._subscription_usage.get((clerk_user_id, period_key))
        now = self._now_iso()
        bounds = dict(payload.get("bounds") or {})
        deltas = dict(payload.get("deltas") or {})
        limits = dict(payload.get("limits") or {})
        feature_key = str(payload.get("feature_key") or "unknown")

        doc = {
            "clerk_user_id": clerk_user_id,
            "period_key": period_key,
            "period_start": bounds.get("period_start", now),
            "period_end": bounds.get("period_end", now),
            "nutrition_credits_used": int((existing or {}).get("nutrition_credits_used") or 0),
            "chat_messages_used": int((existing or {}).get("chat_messages_used") or 0),
            "pdf_exports_used": int((existing or {}).get("pdf_exports_used") or 0),
            "feature_breakdown": dict((existing or {}).get("feature_breakdown") or {}),
            "created_at": (existing or {}).get("created_at", now),
            "updated_at": now,
        }

        next_nutrition = doc["nutrition_credits_used"] + int(deltas.get("nutrition_credits_used") or 0)
        next_chat = doc["chat_messages_used"] + int(deltas.get("chat_messages_used") or 0)
        next_pdf = doc["pdf_exports_used"] + int(deltas.get("pdf_exports_used") or 0)

        nutrition_limit = limits.get("monthly_nutrition_credits")
        chat_limit = limits.get("monthly_chat_messages")
        pdf_limit = limits.get("pdf_exports_per_month")

        if nutrition_limit is not None and next_nutrition > int(nutrition_limit):
            raise AppException(
                "SUBSCRIPTION_LIMIT_REACHED",
                "Monthly nutrition credits exhausted",
                status_code=403,
                details={"limit_type": "nutrition_credits", "suggested_action": "Upgrade your subscription plan"},
            )
        if chat_limit is not None and next_chat > int(chat_limit):
            raise AppException(
                "SUBSCRIPTION_LIMIT_REACHED",
                "Monthly Nutri Chat message limit reached",
                status_code=403,
                details={"limit_type": "chat_messages", "suggested_action": "Upgrade your subscription plan"},
            )
        if pdf_limit is not None and next_pdf > int(pdf_limit):
            raise AppException(
                "SUBSCRIPTION_LIMIT_REACHED",
                "Monthly PDF export limit reached",
                status_code=403,
                details={"limit_type": "pdf_exports", "suggested_action": "Upgrade your subscription plan"},
            )

        doc["nutrition_credits_used"] = next_nutrition
        doc["chat_messages_used"] = next_chat
        doc["pdf_exports_used"] = next_pdf
        feature_breakdown = dict(doc["feature_breakdown"])
        feature_breakdown[feature_key] = int(feature_breakdown.get(feature_key, 0)) + 1
        doc["feature_breakdown"] = feature_breakdown

        self._subscription_usage[(clerk_user_id, period_key)] = doc
        return doc

    async def create_operation(self, clerk_user_id: str, payload: dict) -> dict:
        operation_id = str(payload.get("operation_id") or uuid4())
        now = self._now_iso()
        doc = {
            "operation_id": operation_id,
            "clerk_user_id": clerk_user_id,
            "feature": str(payload.get("feature") or ""),
            "status": str(payload.get("status") or "queued"),
            "queue_tier": str(payload.get("queue_tier") or "free"),
            "resource_scope": dict(payload.get("resource_scope") or {}),
            "workload_pool": str(payload.get("workload_pool") or "text_generation"),
            "idempotency_key": payload.get("idempotency_key"),
            "request_payload": dict(payload.get("request_payload") or {}),
            "response_payload": dict(payload.get("response_payload") or {}),
            "result_ref": payload.get("result_ref"),
            "sequence_no": payload.get("sequence_no"),
            "request_id": payload.get("request_id"),
            "error_code": payload.get("error_code"),
            "error_message": payload.get("error_message"),
            "enqueued_at": payload.get("enqueued_at", now),
            "started_at": payload.get("started_at"),
            "finished_at": payload.get("finished_at"),
            "created_at": payload.get("created_at", now),
            "updated_at": payload.get("updated_at", now),
        }
        self._operations[operation_id] = doc
        idempotency_key = doc.get("idempotency_key")
        if isinstance(idempotency_key, str) and idempotency_key:
            self._operation_by_idempotency[(clerk_user_id, doc["feature"], idempotency_key)] = operation_id
        return doc

    async def get_operation(self, clerk_user_id: str, operation_id: str) -> dict | None:
        operation = self._operations.get(operation_id)
        if not operation or operation.get("clerk_user_id") != clerk_user_id:
            return None
        return operation

    async def get_operation_by_idempotency(self, clerk_user_id: str, feature: str, idempotency_key: str) -> dict | None:
        operation_id = self._operation_by_idempotency.get((clerk_user_id, feature, idempotency_key))
        if not operation_id:
            return None
        return await self.get_operation(clerk_user_id, operation_id)

    async def update_operation(self, clerk_user_id: str, operation_id: str, payload: dict) -> dict | None:
        operation = self._operations.get(operation_id)
        if not operation or operation.get("clerk_user_id") != clerk_user_id:
            return None
        updated = {
            **operation,
            **payload,
            "updated_at": self._now_iso(),
        }
        self._operations[operation_id] = updated
        return updated
