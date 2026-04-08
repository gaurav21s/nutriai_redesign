from __future__ import annotations

import sys
import types

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.exceptions import AuthorizationException
from app.dependencies import get_in_memory_repository, get_rate_limiter, get_shared_coordinator
from app.main import create_app
from app.repositories.in_memory import InMemoryRepository
from app.schemas.subscriptions import ConfirmCheckoutRequest
from app.services.subscription_service import SubscriptionService


@pytest.fixture(autouse=True)
def _clear_dependency_caches():
    yield
    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_shared_coordinator.cache_clear()
    get_in_memory_repository.cache_clear()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_non_demo_user_cannot_self_assign_paid_tier(monkeypatch: pytest.MonkeyPatch) -> None:
    overrides = {
        "AUTH_DISABLED": "true",
        "ENABLE_CONVEX_PERSISTENCE": "false",
        "ALLOW_MOCK_AI_FALLBACK": "true",
        "FORCE_MOCK_AI_FALLBACK": "true",
        "ENVIRONMENT": "development",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_shared_coordinator.cache_clear()
    get_in_memory_repository.cache_clear()

    client = TestClient(create_app())
    response = client.post(
        "/api/v1/subscriptions/select",
        json={"tier": "plus", "currency": "USD"},
        headers={"x-dev-user-id": "regular_user"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Paid plans must be activated through checkout"


def test_dev_user_gets_demo_pro_subscription_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    overrides = {
        "AUTH_DISABLED": "true",
        "ENABLE_CONVEX_PERSISTENCE": "false",
        "ALLOW_MOCK_AI_FALLBACK": "true",
        "FORCE_MOCK_AI_FALLBACK": "true",
        "ENVIRONMENT": "development",
        "DEV_USER_ID": "dev_user",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_shared_coordinator.cache_clear()
    get_in_memory_repository.cache_clear()

    client = TestClient(create_app())
    response = client.get("/api/v1/subscriptions/current")

    assert response.status_code == 200
    subscription = response.json()["subscription"]
    assert subscription["tier"] == "pro"
    assert subscription["is_demo"] is True
    assert all(subscription["permissions"].values()) is True


@pytest.mark.anyio
async def test_checkout_confirmation_requires_matching_user() -> None:
    class FakeCheckoutSessions:
        @staticmethod
        def retrieve(session_id: str, options: dict) -> object:
            assert session_id == "sess_123"
            assert options == {"expand": ["customer", "subscription"]}
            return types.SimpleNamespace(
                id=session_id,
                customer="cus_123",
                subscription="sub_123",
                payment_status="paid",
                metadata={
                    "clerk_user_id": "someone_else",
                    "tier": "pro",
                    "currency": "USD",
                },
            )

    class FakeStripeClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.checkout = types.SimpleNamespace(sessions=FakeCheckoutSessions())

    monkeypatch_module = types.SimpleNamespace(StripeClient=FakeStripeClient)
    original = sys.modules.get("stripe")
    sys.modules["stripe"] = monkeypatch_module

    try:
        service = SubscriptionService(
            repository=InMemoryRepository(),
            stripe_secret_key="sk_test_123",
            environment="development",
            dev_user_id="dev_user",
        )

        with pytest.raises(AuthorizationException):
            await service.confirm_checkout(
                "dev_user",
                ConfirmCheckoutRequest(session_id="sess_123"),
            )
    finally:
        if original is None:
            sys.modules.pop("stripe", None)
        else:
            sys.modules["stripe"] = original
