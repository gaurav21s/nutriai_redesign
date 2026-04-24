from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.core.config import get_settings
from app.dependencies import get_in_memory_repository, get_rate_limiter, get_shared_coordinator
from app.main import create_app
from app.services.nutri_chat_agent import GroqAgentModel, OpenRouterAgentModel


@pytest.fixture(autouse=True)
def _clear_dependency_caches():
    yield
    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_shared_coordinator.cache_clear()
    get_in_memory_repository.cache_clear()


def _build_client(monkeypatch: pytest.MonkeyPatch, *, default_limit: int = 200, chat_limit: int = 200) -> TestClient:
    overrides = {
        "AUTH_DISABLED": "true",
        "ENABLE_CONVEX_PERSISTENCE": "false",
        "ALLOW_MOCK_AI_FALLBACK": "false",
        "FORCE_MOCK_AI_FALLBACK": "false",
        "AGENT_CHAT_PROVIDER": "openrouter",
        "RATE_LIMIT_DEFAULT_PER_MINUTE": str(default_limit),
        "RATE_LIMIT_CHAT_PER_MINUTE": str(chat_limit),
        "RATE_LIMIT_AI_PER_MINUTE": "200",
        "GROQ_API_KEY": "test-groq-key",
        "OPENROUTER_API_KEY": "test-openrouter-key",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_shared_coordinator.cache_clear()
    get_in_memory_repository.cache_clear()

    async def fake_invoke(self, messages):  # type: ignore[no-untyped-def]
        _ = (self, messages)
        return AIMessage(content="Stubbed assistant response.")

    monkeypatch.setattr(GroqAgentModel, "invoke", fake_invoke)
    monkeypatch.setattr(OpenRouterAgentModel, "invoke", fake_invoke)

    return TestClient(create_app())


def test_chat_messages_accept_sessions_older_than_first_page(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch, default_limit=300, chat_limit=300)

    oldest_session_id = ""
    for index in range(105):
        response = client.post("/api/v1/nutri-chat/sessions", json={"title": f"Session {index}"})
        assert response.status_code == 200
        if index == 0:
            oldest_session_id = response.json()["session_id"]

    message = client.post(
        f"/api/v1/nutri-chat/sessions/{oldest_session_id}/messages",
        json={"content": "Please help me improve breakfast."},
    )

    assert message.status_code == 200
    payload = message.json()
    assert payload["role"] == "assistant"
    assert payload["content"] == "Stubbed assistant response."


def test_chat_rate_limit_applies_across_session_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch, default_limit=200, chat_limit=2)

    session_ids: list[str] = []
    for index in range(3):
        response = client.post("/api/v1/nutri-chat/sessions", json={"title": f"Rate Limit {index}"})
        assert response.status_code == 200
        session_ids.append(response.json()["session_id"])

    for session_id in session_ids[:2]:
        response = client.post(
            f"/api/v1/nutri-chat/sessions/{session_id}/messages",
            json={"content": "hello"},
        )
        assert response.status_code == 200

    third = client.post(
        f"/api/v1/nutri-chat/sessions/{session_ids[2]}/messages",
        json={"content": "hello again"},
    )

    assert third.status_code == 429
    payload = third.json()
    assert payload["error"]["code"] == "RATE_LIMITED"


def test_chat_sessions_can_be_renamed_and_deleted(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch, default_limit=200, chat_limit=200)

    created = client.post("/api/v1/nutri-chat/sessions", json={"title": "Original"})
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    renamed = client.patch(f"/api/v1/nutri-chat/sessions/{session_id}", json={"title": "Renamed Session"})
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Renamed Session"

    deleted = client.delete(f"/api/v1/nutri-chat/sessions/{session_id}")
    assert deleted.status_code == 200
    assert deleted.json() == {"session_id": session_id, "deleted": True}

    message = client.post(
        f"/api/v1/nutri-chat/sessions/{session_id}/messages",
        json={"content": "hello"},
    )
    assert message.status_code == 404
