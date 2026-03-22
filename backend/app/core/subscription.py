"""Subscription permission model shared across backend layers."""

from __future__ import annotations

from typing import Literal

PlanTier = Literal["free", "plus", "pro"]

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


def get_tier_permissions(tier: str) -> dict[str, bool]:
    if tier == "free":
        enabled = {
            "food_insight",
            "ingredient_checker",
            "meal_planner",
            "recipe_finder",
            "nutri_quiz",
            "nutri_calc",
            "articles",
            "docs",
        }
    elif tier == "plus":
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
            "priority_support",
        }
    else:
        enabled = set(PERMISSION_KEYS)

    return {key: key in enabled for key in PERMISSION_KEYS}


def get_default_subscription_payload() -> dict:
    return {
        "tier": "free",
        "status": "active",
        "currency": "USD",
        "amount": 0,
        "interval": "month",
        "permissions": get_tier_permissions("free"),
        "is_demo": False,
    }
