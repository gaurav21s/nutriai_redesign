"""Aggregate v1 routers."""

from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    articles,
    calculators,
    food_insights,
    health,
    ingredient_checks,
    meal_plans,
    nutri_chat,
    operations,
    quizzes,
    recipes,
    smart_picks,
    subscriptions,
)
from app.dependencies import require_permission

router = APIRouter()
router.include_router(health.router)
router.include_router(operations.router)
router.include_router(food_insights.router, dependencies=[Depends(require_permission("food_insight"))])
router.include_router(ingredient_checks.router, dependencies=[Depends(require_permission("ingredient_checker"))])
router.include_router(meal_plans.router, dependencies=[Depends(require_permission("meal_planner"))])
router.include_router(recipes.router, dependencies=[Depends(require_permission("recipe_finder"))])
router.include_router(quizzes.router, dependencies=[Depends(require_permission("nutri_quiz"))])
router.include_router(nutri_chat.router, dependencies=[Depends(require_permission("nutri_chat"))])
router.include_router(calculators.router, dependencies=[Depends(require_permission("nutri_calc"))])
router.include_router(articles.router, dependencies=[Depends(require_permission("articles"))])
router.include_router(smart_picks.router, dependencies=[Depends(require_permission("recommendations"))])
router.include_router(subscriptions.router)
