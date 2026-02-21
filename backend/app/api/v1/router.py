"""Aggregate v1 routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    articles,
    calculators,
    food_insights,
    health,
    ingredient_checks,
    meal_plans,
    nutri_chat,
    quizzes,
    recipes,
    recommendations,
)

router = APIRouter()
router.include_router(health.router)
router.include_router(food_insights.router)
router.include_router(ingredient_checks.router)
router.include_router(meal_plans.router)
router.include_router(recipes.router)
router.include_router(quizzes.router)
router.include_router(nutri_chat.router)
router.include_router(calculators.router)
router.include_router(articles.router)
router.include_router(recommendations.router)
