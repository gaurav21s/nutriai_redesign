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
    """Look up the user's saved BMI and calorie calculations from their history.

    ALWAYS use this tool when the user:
    - asks about their BMI, past BMI, BMI history, or "my BMI"
    - asks about their calorie calculations, TDEE, or BMR history
    - says "check my history", "get my data", "show my calculations"
    - references any previously saved calculation numbers

    Returns a compact summary of their most recent saved calculations including
    BMI values, categories, calorie estimates, and dates.
    limit: number of records to fetch (1-10, default 5)
    """


@tool("lookup_recipe_history")
def lookup_recipe_history_tool(limit: int = 3) -> str:
    """Look up the user's previously generated and saved recipes.

    Use this when the user asks about their past recipes, wants to see what
    recipes they have saved, or needs recipe history for context.
    Returns a compact summary of their most recent saved recipes.
    """


@tool("lookup_smart_picks_history")
def lookup_smart_picks_history_tool(limit: int = 3) -> str:
    """Look up the user's saved Nutri Smart Picks decision sets.

    Use this when the user asks about their past smart picks, wants to
    review previously ranked food options, or needs saved real-world choice history.
    Nutri Smart Picks is the structured compare/rank/choose feature for
    real-life food situations, not a meal plan, recipe, or open-ended coach.
    Returns a compact summary of their most recent saved Nutri Smart Picks sets.
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
# Tool registry — all tools in one list for .bind_tools()
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    lookup_calculation_history_tool,
    lookup_recipe_history_tool,
    lookup_smart_picks_history_tool,
    lookup_meal_plan_history_tool,
    lookup_food_insights_history_tool,
    lookup_ingredient_checks_history_tool,
]

LOOKUP_TOOL_NAMES = {
    "lookup_calculation_history",
    "lookup_recipe_history",
    "lookup_smart_picks_history",
    "lookup_meal_plan_history",
    "lookup_food_insights_history",
    "lookup_ingredient_checks_history",
}
