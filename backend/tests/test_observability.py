from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.logging import RequestLogContext, should_sample_request
from app.dependencies import get_in_memory_repository, get_rate_limiter, get_shared_coordinator
from app.main import create_app


def _clear_caches() -> None:
    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_shared_coordinator.cache_clear()
    get_in_memory_repository.cache_clear()


def _request_summary_records(caplog) -> list[logging.LogRecord]:
    return [record for record in caplog.records if getattr(record, "event_name", None) == "request_summary"]


def test_request_summary_emits_single_wide_event(monkeypatch, caplog) -> None:
    monkeypatch.setenv("AUTH_DISABLED", "true")
    monkeypatch.setenv("ENABLE_CONVEX_PERSISTENCE", "false")
    monkeypatch.setenv("LOG_SUCCESS_SAMPLE_RATE", "1.0")
    _clear_caches()

    client = TestClient(create_app())
    caplog.set_level(logging.INFO)

    response = client.get(
        "/api/v1/health",
        headers={
            "x-dev-user-id": "dev_user_123",
            "x-user-email": "dev@example.com",
            "x-client-session-id": "session-1",
            "x-client-event-id": "event-1",
            "x-client-route": "/dashboard",
        },
    )

    assert response.status_code == 200

    summaries = _request_summary_records(caplog)
    assert len(summaries) == 1
    event = summaries[0].wide_event
    assert event["status_code"] == 200
    assert event["clerk_user_id"] == "dev_user_123"
    assert event["user_email"] == "dev@example.com"
    assert event["client_session_id"] == "session-1"
    assert event["client_event_id"] == "event-1"
    assert event["client_route"] == "/dashboard"
    assert event["feature"] == "health"
    assert event["request_id"] == response.headers["x-request-id"]


def test_request_summary_captures_handled_auth_failure(monkeypatch, caplog) -> None:
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("ENABLE_CONVEX_PERSISTENCE", "false")
    _clear_caches()

    client = TestClient(create_app())
    caplog.set_level(logging.INFO)

    response = client.get("/api/v1/subscriptions/current")

    assert response.status_code == 401

    summaries = _request_summary_records(caplog)
    assert len(summaries) == 1
    event = summaries[0].wide_event
    assert event["status_code"] == 401
    assert event["error_code"] == "AUTHENTICATION_FAILED"
    assert event["outcome"] == "error"


def test_request_summary_captures_unexpected_exception(monkeypatch, caplog) -> None:
    monkeypatch.setenv("AUTH_DISABLED", "true")
    monkeypatch.setenv("ENABLE_CONVEX_PERSISTENCE", "false")
    _clear_caches()

    app = create_app()

    @app.get("/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("boom")

    caplog.set_level(logging.INFO)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom", headers={"x-dev-user-id": "dev_user_123"})

    assert response.status_code == 500

    summaries = _request_summary_records(caplog)
    assert len(summaries) == 1
    event = summaries[0].wide_event
    assert event["status_code"] == 500
    assert event["error_code"] == "INTERNAL_ERROR"
    assert event["outcome"] == "error"


def test_request_sampling_rules() -> None:
    production_settings = Settings(
        _env_file=None,
        environment="production",
        log_success_sample_rate=0.0,
        log_slow_request_ms=1500.0,
        log_vip_user_ids="vip_user",
    )

    successful_request = RequestLogContext(request_id="req-1", environment="production", status_code=200)
    assert should_sample_request(successful_request, production_settings) is False

    vip_request = RequestLogContext(
        request_id="req-2",
        environment="production",
        status_code=200,
        clerk_user_id="vip_user",
    )
    assert should_sample_request(vip_request, production_settings) is True

    slow_request = RequestLogContext(
        request_id="req-3",
        environment="production",
        status_code=200,
        latency_ms=2000.0,
    )
    assert should_sample_request(slow_request, production_settings) is True

    failed_request = RequestLogContext(
        request_id="req-4",
        environment="production",
        status_code=500,
        error_code="INTERNAL_ERROR",
    )
    assert should_sample_request(failed_request, production_settings) is True
