"""Subscription and quota model shared across backend layers."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

PlanTier = Literal["free", "plus", "pro"]
CurrencyCode = Literal["USD", "INR"]
LOCAL_DEMO_USER_IDS = {"demo_user_1", "demo_user_2"}

PERMISSION_KEYS = [
    "food_insight",
    "ingredient_checker",
    "meal_planner",
    "recipe_finder",
    "nutri_chat",
    "nutri_quiz",
    "nutri_calc",
    "recommendations",
    "articles",
    "docs",
    "priority_support",
]

FEATURE_CREDIT_COSTS = {
    "food_insight_text": 1,
    "food_insight_image": 2,
    "ingredient_checker": 1,
    "nutri_quiz": 1,
    "recipe_finder": 2,
    "recommendations": 2,
    "meal_planner": 3,
}

PLAN_PRICES: dict[PlanTier, dict[CurrencyCode, float]] = {
    "free": {"USD": 0, "INR": 0},
    "plus": {"USD": 7.99, "INR": 499},
    "pro": {"USD": 12.99, "INR": 999},
}

PLAN_LIMITS: dict[PlanTier, dict[str, Any]] = {
    "free": {
        "monthly_nutrition_credits": 12,
        "monthly_chat_messages": 15,
        "history_days": 30,
        "pdf_exports_per_month": 0,
        "max_chat_context_items": 8,
        "priority_processing": False,
    },
    "plus": {
        "monthly_nutrition_credits": 120,
        "monthly_chat_messages": 250,
        "history_days": 365,
        "pdf_exports_per_month": 10,
        "max_chat_context_items": 50,
        "priority_processing": True,
    },
    "pro": {
        "monthly_nutrition_credits": 400,
        "monthly_chat_messages": 800,
        "history_days": None,
        "pdf_exports_per_month": 50,
        "max_chat_context_items": 200,
        "priority_processing": True,
    },
}


def get_tier_permissions(tier: str) -> dict[str, bool]:
    enabled = {
        "food_insight",
        "ingredient_checker",
        "meal_planner",
        "recipe_finder",
        "nutri_chat",
        "nutri_quiz",
        "nutri_calc",
        "recommendations",
        "articles",
        "docs",
    }
    if tier in {"plus", "pro"}:
        enabled.add("priority_support")

    return {key: key in enabled for key in PERMISSION_KEYS}


def get_tier_limits(tier: str) -> dict[str, Any]:
    selected_tier: PlanTier = tier if tier in PLAN_LIMITS else "free"  # type: ignore[assignment]
    return deepcopy(PLAN_LIMITS[selected_tier])


def get_plan_amount(tier: str, currency: str) -> float:
    selected_tier: PlanTier = tier if tier in PLAN_PRICES else "free"  # type: ignore[assignment]
    selected_currency: CurrencyCode = currency if currency in {"USD", "INR"} else "USD"  # type: ignore[assignment]
    return float(PLAN_PRICES[selected_tier][selected_currency])


def get_default_subscription_payload() -> dict[str, Any]:
    return {
        "tier": "free",
        "status": "active",
        "currency": "USD",
        "amount": 0,
        "interval": "month",
        "permissions": get_tier_permissions("free"),
        "limits": get_tier_limits("free"),
        "is_demo": False,
    }


def get_demo_subscription_payload(tier: PlanTier = "pro") -> dict[str, Any]:
    return {
        "tier": tier,
        "status": "active",
        "currency": "USD",
        "amount": 0,
        "interval": "month",
        "permissions": get_tier_permissions(tier),
        "limits": get_tier_limits(tier),
        "is_demo": True,
    }


def current_usage_period(now: datetime | None = None) -> dict[str, str]:
    current = now.astimezone(timezone.utc) if now else datetime.now(tz=timezone.utc)
    period_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period_start.month == 12:
        next_period_start = period_start.replace(year=period_start.year + 1, month=1)
    else:
        next_period_start = period_start.replace(month=period_start.month + 1)
    period_end = next_period_start - timedelta(microseconds=1)
    return {
        "period_key": period_start.strftime("%Y-%m"),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "next_reset_at": next_period_start.isoformat(),
    }


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_within_history_window(value: str | None, history_days: int | None, now: datetime | None = None) -> bool:
    if history_days is None:
        return True
    parsed = parse_iso_datetime(value)
    if parsed is None:
        return False
    current = now.astimezone(timezone.utc) if now else datetime.now(tz=timezone.utc)
    cutoff = current - timedelta(days=history_days)
    return parsed >= cutoff


def is_local_demo_user(environment: str, clerk_user_id: str, dev_user_id: str = "dev_user") -> bool:
    if environment not in {"local", "development"}:
        return False
    return clerk_user_id in {dev_user_id, *LOCAL_DEMO_USER_IDS}
