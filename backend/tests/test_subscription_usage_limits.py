from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.dependencies import get_in_memory_repository, get_rate_limiter, get_shared_coordinator
from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_dependency_caches():
    yield
    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_shared_coordinator.cache_clear()
    get_in_memory_repository.cache_clear()


def _build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    overrides = {
        "AUTH_DISABLED": "true",
        "ENABLE_CONVEX_PERSISTENCE": "false",
        "ALLOW_MOCK_AI_FALLBACK": "true",
        "FORCE_MOCK_AI_FALLBACK": "true",
        "RATE_LIMIT_DEFAULT_PER_MINUTE": "200",
        "RATE_LIMIT_AI_PER_MINUTE": "200",
        "RATE_LIMIT_CHAT_PER_MINUTE": "200",
        "ENVIRONMENT": "development",
        "DEV_USER_ID": "dev_user",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_shared_coordinator.cache_clear()
    get_in_memory_repository.cache_clear()
    return TestClient(create_app())


def test_free_user_hits_monthly_credit_cap_and_usage_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)
    headers = {"x-dev-user-id": "regular_user"}

    for _ in range(12):
        response = client.post(
            "/api/v1/ingredient-checks/analyze",
            json={"input_mode": "text", "ingredients_text": "oats, spinach, salt"},
            headers=headers,
        )
        assert response.status_code == 200

    blocked = client.post(
        "/api/v1/ingredient-checks/analyze",
        json={"input_mode": "text", "ingredients_text": "oats, spinach, salt"},
        headers=headers,
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["message"] == "Monthly nutrition credits exhausted"

    usage = client.get("/api/v1/subscriptions/usage", headers=headers)
    assert usage.status_code == 200
    payload = usage.json()["usage"]
    assert payload["nutrition_credits"]["used"] == 12
    assert payload["nutrition_credits"]["limit"] == 12
    assert payload["nutrition_credits"]["remaining"] == 0


def test_free_user_pdf_export_is_blocked_and_history_window_is_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)
    headers = {"x-dev-user-id": "regular_user"}

    meal = client.post(
        "/api/v1/meal-plans/generate",
        json={
            "gender": "Male",
            "goal": "Loss fat",
            "diet_choice": "Vegetarian",
            "issue": "No issue",
            "gym": "do gym/workout",
            "height": "175 cm",
            "weight": "72 kg",
            "food_type": "Indian type",
        },
        headers=headers,
    )
    assert meal.status_code == 200

    export = client.post(
        f"/api/v1/meal-plans/{meal.json()['id']}/export/pdf",
        json={"full_name": "Free User", "age": 28},
        headers=headers,
    )
    assert export.status_code == 403
    assert export.json()["error"]["message"] == "Monthly PDF export limit reached"

    repo = get_in_memory_repository()
    old_timestamp = (datetime.now(tz=timezone.utc) - timedelta(days=45)).isoformat()

    import asyncio

    asyncio.run(
        repo.create_record(
            "calculations",
            "regular_user",
            {
                "created_at": old_timestamp,
                "calculator_type": "bmi",
                "payload": {"weight_kg": 60, "height_cm": 170},
                "result": {"bmi": 20.8, "category": "healthy"},
            },
        )
    )

    fresh = client.post(
        "/api/v1/calculators/bmi",
        json={"weight_kg": 72, "height_cm": 175},
        headers=headers,
    )
    assert fresh.status_code == 200

    history = client.get("/api/v1/calculators/history", headers=headers)
    assert history.status_code == 200
    items = history.json()["items"]
    assert len(items) == 1
    assert items[0]["result"]["bmi"] == pytest.approx(23.5)


def test_saved_pdf_can_be_redownloaded_without_consuming_extra_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch)

    meal = client.post(
        "/api/v1/meal-plans/generate",
        json={
            "gender": "Male",
            "goal": "Loss fat",
            "diet_choice": "Vegetarian",
            "issue": "No issue",
            "gym": "do gym/workout",
            "height": "175 cm",
            "weight": "72 kg",
            "food_type": "Indian type",
        },
    )
    assert meal.status_code == 200
    meal_id = meal.json()["id"]

    export = client.post(
        f"/api/v1/meal-plans/{meal_id}/export/pdf",
        json={"full_name": "Pro User", "age": 28},
    )
    assert export.status_code == 200

    usage_after_export = client.get("/api/v1/subscriptions/usage")
    assert usage_after_export.status_code == 200
    assert usage_after_export.json()["usage"]["pdf_exports"]["used"] == 1

    exports = client.get(f"/api/v1/meal-plans/{meal_id}/exports")
    assert exports.status_code == 200
    export_id = exports.json()["items"][0]["id"]

    redownload = client.get(f"/api/v1/meal-plans/exports/{export_id}/download")
    assert redownload.status_code == 200
    assert redownload.headers["content-type"].startswith("application/pdf")

    usage_after_redownload = client.get("/api/v1/subscriptions/usage")
    assert usage_after_redownload.status_code == 200
    assert usage_after_redownload.json()["usage"]["pdf_exports"]["used"] == 1
