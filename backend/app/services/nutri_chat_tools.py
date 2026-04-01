"""LangChain tool definitions for NutriAI agent chat.

Two categories:
  - lookup_*  : Read user history from the repository. No pending action produced.
  - preview_* : Generate new content via AI services. May produce a pending action.
"""

from __future__ import annotations

from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# History lookup tools
# ---------------------------------------------------------------------------


@tool("lookup_calculation_history")
def lookup_calculation_history_tool(limit: int = 5) -> str:
    """Look up the user's saved BMI and calorie calculations.

    Use this when the user asks about their past calculations, BMI history,
    calorie history, or wants to review previously saved numbers.
    Returns a compact summary of their most recent saved calculations.
    """


@tool("lookup_recipe_history")
def lookup_recipe_history_tool(limit: int = 3) -> str:
    """Look up the user's previously generated and saved recipes.

    Use this when the user asks about their past recipes, wants to see what
    recipes they have saved, or needs recipe history for context.
    Returns a compact summary of their most recent saved recipes.
    """


@tool("lookup_recommendation_history")
def lookup_recommendation_history_tool(limit: int = 3) -> str:
    """Look up the user's saved nutrition recommendation sets.

    Use this when the user asks about their past recommendations, wants to
    review previously suggested food alternatives or healthy recipes they saved.
    Returns a compact summary of their most recent saved recommendation sets.
    """


@tool("lookup_meal_plan_history")
def lookup_meal_plan_history_tool(limit: int = 3) -> str:
    """Look up the user's saved meal plans.

    Use this when the user asks about their past meal plans, wants to review
    a previously generated diet plan, or needs meal plan context.
    Returns a compact summary of their most recent saved meal plans.
    """


@tool("lookup_food_insights_history")
def lookup_food_insights_history_tool(limit: int = 3) -> str:
    """Look up the user's saved food analysis results (food insights).

    Use this when the user asks about past food analyses, wants to know
    what foods they previously analyzed, or needs food insight history.
    Returns a compact summary of their most recent food insight records.
    """


@tool("lookup_ingredient_checks_history")
def lookup_ingredient_checks_history_tool(limit: int = 3) -> str:
    """Look up the user's saved ingredient check results.

    Use this when the user asks about ingredient checks they've done,
    packaged food labels they analyzed, or ingredient check history.
    Returns a compact summary of their most recent ingredient check records.
    """


# ---------------------------------------------------------------------------
# Preview tools (generate new content — may produce a pending save action)
# ---------------------------------------------------------------------------


@tool("preview_bmi")
def preview_bmi_tool(weight_kg: float, height_cm: float) -> str:
    """Calculate a BMI preview from weight in kilograms and height in centimeters.

    Use this when the user provides their weight and height and wants to know
    their BMI. The result is a preview — the user can choose to save it afterward.
    weight_kg: body weight in kilograms (e.g. 70.0)
    height_cm: height in centimeters (e.g. 175.0)
    """


@tool("preview_calories")
def preview_calories_tool(
    gender: str,
    weight_kg: float,
    height_cm: float,
    age: int,
    activity_multiplier: float,
) -> str:
    """Estimate daily maintenance calories (BMR × activity multiplier).

    Use this when the user wants to know their calorie needs or TDEE.
    gender: "Male" or "Female"
    weight_kg: body weight in kilograms
    height_cm: height in centimeters
    age: age in years
    activity_multiplier: sedentary=1.2, light=1.375, moderate=1.55, active=1.725, very active=1.9
    The result is a preview — the user can choose to save it afterward.
    """


@tool("preview_recommendations")
def preview_recommendations_tool(query: str, recommendation_type: str = "both") -> str:
    """Generate nutrition recommendations for a food or meal query.

    Use this when the user wants healthier food alternatives, new healthy
    recipe ideas, or nutritional recommendations for a specific food/meal.
    query: the food, meal, or goal the user is asking about
    recommendation_type: "healthier_alternative", "new_healthy_recipe", or "both"
    The result is a preview — the user can choose to save it afterward.
    """


@tool("preview_recipe")
def preview_recipe_tool(dish_name: str, recipe_type: str = "new_healthy") -> str:
    """Generate a recipe preview for a requested dish or nutritional goal.

    Use this when the user asks for a specific recipe, wants to cook something
    healthy, or needs a recipe suggestion aligned with their fitness goals.
    dish_name: name of the dish or a description like "high protein chicken bowl"
    recipe_type: "normal", "healthier", or "new_healthy"
    The result is a preview — the user can choose to save it afterward.
    """


# ---------------------------------------------------------------------------
# Tool registry — all tools in one list for .bind_tools()
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    lookup_calculation_history_tool,
    lookup_recipe_history_tool,
    lookup_recommendation_history_tool,
    lookup_meal_plan_history_tool,
    lookup_food_insights_history_tool,
    lookup_ingredient_checks_history_tool,
    preview_bmi_tool,
    preview_calories_tool,
    preview_recommendations_tool,
    preview_recipe_tool,
]

LOOKUP_TOOL_NAMES = {
    "lookup_calculation_history",
    "lookup_recipe_history",
    "lookup_recommendation_history",
    "lookup_meal_plan_history",
    "lookup_food_insights_history",
    "lookup_ingredient_checks_history",
}

PREVIEW_TOOL_NAMES = {
    "preview_bmi",
    "preview_calories",
    "preview_recommendations",
    "preview_recipe",
}
