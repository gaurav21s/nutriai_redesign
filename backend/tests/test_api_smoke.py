"""End-to-end smoke coverage for all v1 API feature endpoints."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.dependencies import get_in_memory_repository, get_rate_limiter
from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_dependency_caches():
    yield
    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_in_memory_repository.cache_clear()


def test_full_api_smoke(monkeypatch) -> None:
    overrides = {
        "AUTH_DISABLED": "true",
        "ENABLE_CONVEX_PERSISTENCE": "false",
        "ALLOW_MOCK_AI_FALLBACK": "true",
        "FORCE_MOCK_AI_FALLBACK": "true",
        "GOOGLE_API_KEY": "",
        "TOGETHER_API_KEY": "",
        "GROQ_API_KEY": "",
        "RATE_LIMIT_DEFAULT_PER_MINUTE": "200",
        "RATE_LIMIT_AI_PER_MINUTE": "200",
        "RATE_LIMIT_CHAT_PER_MINUTE": "200",
    }
    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    get_settings.cache_clear()
    get_rate_limiter.cache_clear()
    get_in_memory_repository.cache_clear()

    client = TestClient(create_app())

    # Health
    assert client.get("/api/v1/health").status_code == 200

    # Food insights
    food = client.post(
        "/api/v1/food-insights/analyze",
        json={"input_mode": "text", "text": "oats, banana, almonds"},
    )
    assert food.status_code == 200
    food_id = food.json()["id"]
    assert client.get("/api/v1/food-insights/history").status_code == 200
    assert client.get(f"/api/v1/food-insights/history/{food_id}").status_code == 200

    # Ingredient checks
    ingredient = client.post(
        "/api/v1/ingredient-checks/analyze",
        json={"input_mode": "text", "ingredients_text": "oats, spinach, refined sugar"},
    )
    assert ingredient.status_code == 200
    ingredient_id = ingredient.json()["id"]
    assert client.get("/api/v1/ingredient-checks/history").status_code == 200
    assert client.get(f"/api/v1/ingredient-checks/history/{ingredient_id}").status_code == 200

    # Meal plans + PDF export
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
    assert client.get("/api/v1/meal-plans/history").status_code == 200
    assert client.get(f"/api/v1/meal-plans/history/{meal_id}").status_code == 200
    meal_pdf = client.post(
        f"/api/v1/meal-plans/{meal_id}/export/pdf",
        json={"full_name": "Demo User", "age": 31},
    )
    assert meal_pdf.status_code == 200
    assert meal_pdf.headers["content-type"].startswith("application/pdf")

    # Recipes + shopping links
    recipe = client.post(
        "/api/v1/recipes/generate",
        json={"dish_name": "Paneer Bowl", "recipe_type": "healthier"},
    )
    assert recipe.status_code == 200
    recipe_payload = recipe.json()
    recipe_id = recipe_payload["id"]
    assert "shopping_links" in recipe_payload
    assert isinstance(recipe_payload["shopping_links"], dict)
    links = client.post(
        "/api/v1/recipes/shopping-links",
        json={"ingredients": ["paneer", "spinach", "olive oil"]},
    )
    assert links.status_code == 200
    assert client.get("/api/v1/recipes/history").status_code == 200
    assert client.get(f"/api/v1/recipes/history/{recipe_id}").status_code == 200

    # Quizzes
    quiz = client.post(
        "/api/v1/quizzes/generate",
        json={"topic": "protein", "difficulty": "easy", "question_count": 3},
    )
    assert quiz.status_code == 200
    quiz_payload = quiz.json()
    session_id = quiz_payload["session_id"]
    answers = [{"question_index": i, "selected_option": "A"} for i in range(len(quiz_payload["questions"]))]
    submit = client.post(f"/api/v1/quizzes/{session_id}/submit", json={"answers": answers})
    assert submit.status_code == 200
    assert client.get("/api/v1/quizzes/history").status_code == 200
    assert client.get(f"/api/v1/quizzes/history/{session_id}").status_code == 200

    # Subscriptions (upgrade before plan-gated features)
    plans = client.get("/api/v1/subscriptions/plans")
    assert plans.status_code == 200
    assert len(plans.json()["plans"]) == 3

    current = client.get("/api/v1/subscriptions/current")
    assert current.status_code == 200
    assert current.json()["subscription"]["tier"] in {"free", "plus", "pro"}

    selected = client.post("/api/v1/subscriptions/select", json={"tier": "plus", "currency": "INR"})
    assert selected.status_code == 200
    assert selected.json()["subscription"]["tier"] == "plus"
    assert selected.json()["subscription"]["currency"] == "INR"

    assert client.get("/api/v1/subscriptions/history").status_code == 200
    seeded = client.post("/api/v1/subscriptions/demo-users/seed")
    assert seeded.status_code == 200
    assert len(seeded.json()["users"]) == 2

    # Chat (allowed after plus plan selection)
    session = client.post("/api/v1/nutri-chat/sessions", json={"title": "General Nutrition"})
    assert session.status_code == 200
    chat_session_id = session.json()["session_id"]
    assert client.get("/api/v1/nutri-chat/sessions").status_code == 200
    message = client.post(
        f"/api/v1/nutri-chat/sessions/{chat_session_id}/messages",
        json={"content": "How can I improve my breakfast?"},
    )
    assert message.status_code == 200
    assert client.get(f"/api/v1/nutri-chat/sessions/{chat_session_id}/messages").status_code == 200

    # Calculators
    assert client.post("/api/v1/calculators/bmi", json={"weight_kg": 72, "height_cm": 175}).status_code == 200
    assert (
        client.post(
            "/api/v1/calculators/calories",
            json={
                "gender": "Male",
                "weight_kg": 72,
                "height_cm": 175,
                "age": 31,
                "activity_multiplier": 1.55,
            },
        ).status_code
        == 200
    )
    assert client.get("/api/v1/calculators/history").status_code == 200

    # Articles
    article_list = client.get("/api/v1/articles")
    assert article_list.status_code == 200
    articles = article_list.json()["items"]
    assert len(articles) > 0
    assert client.get(f"/api/v1/articles/{articles[0]['slug']}").status_code == 200

    # Recommendations (allowed after plus plan selection)
    recommendation = client.post(
        "/api/v1/recommendations/generate",
        json={"query": "white rice dinner", "recommendation_type": "both"},
    )
    assert recommendation.status_code == 200
    assert client.get("/api/v1/recommendations/history").status_code == 200
