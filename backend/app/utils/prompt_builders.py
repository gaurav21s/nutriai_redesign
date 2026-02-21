"""Prompt builders for feature-specific model interactions."""

from __future__ import annotations

from app.schemas.recipes import RecipeType
from app.schemas.recommendations import RecommendationType


def food_text_prompt(input_text: str) -> str:
    return f"""
You are a nutritionist. Analyze these food items: [{input_text}].
Return structured output with:
1) line-by-line item breakdown with quantity and nutrient ranges,
2) Total: calories, carbs, fiber, protein, fats,
3) Verdict: Healthy or Not Healthy,
4) Facts: 2-3 concise nutrition facts.
""".strip()


def food_image_prompt() -> str:
    return """
You are a nutritionist. Analyze food items visible in the image.
Return:
1) itemized breakdown with quantity and nutrient ranges,
2) Total: calories, carbs, fiber, protein, fats,
3) Verdict,
4) Facts (2-3 concise lines).
""".strip()


def ingredient_check_prompt(ingredients: list[str]) -> str:
    return f"""
You are a nutritionist.
Categorize these ingredients as healthy or unhealthy and list health issues for unhealthy ones.
Return strict JSON:
{{
  "healthy_ingredients": ["..."],
  "unhealthy_ingredients": ["..."],
  "health_issues": {{"ingredient": ["issue1", "issue2"]}}
}}
Ingredients: {", ".join(ingredients)}
""".strip()


def ingredient_from_image_prompt() -> str:
    return (
        "Identify ingredients from the image and return a comma-separated list of ingredient names only."
    )


def meal_plan_prompt(
    gender: str,
    goal: str,
    diet_choice: str,
    issue: str,
    gym: str,
    height: str,
    weight: str,
    food_type: str,
) -> str:
    workout_options = (
        """
Pre-Workout:
- [Option 1 with quantity and calories]
- [Option 2 with quantity and calories]

Post-Workout:
- [Option 1 with quantity and calories]
- [Option 2 with quantity and calories]
""".strip()
        if "do gym" in gym.lower()
        else """
Pre-Workout:
- Not needed

Post-Workout:
- Not needed
""".strip()
    )

    return f"""
Create a practical homemade meal plan.
User: {gender}, goal={goal}, diet={diet_choice}, issue={issue}, workout={gym}, height={height}, weight={weight}, cuisine={food_type}

Strict format:
Breakfast:
- ...
- ...

Lunch:
- ...
- ...

{workout_options}

Dinner:
- ...
- ...

Rules:
- Include portions and calories.
- Keep foods realistic and home-friendly.
- Tailor for user goal and constraints.
""".strip()


def recipe_prompt(dish_name: str, recipe_type: RecipeType) -> str:
    type_instructions = {
        "normal": f"Create a recipe for {dish_name}.",
        "healthier": f"Create a healthier version of {dish_name}.",
        "new_healthy": f"Create a new healthy and trendy recipe inspired by {dish_name}.",
    }

    explanation_line = "Explanation: [why this version is healthier]" if recipe_type == "healthier" else ""

    return f"""
{type_instructions[recipe_type]}
Return in this exact structure:
Recipe Name: ...
Ingredients:
1. ...
2. ...
Steps:
1. ...
2. ...
Ingredient List: ingredient1, ingredient2, ingredient3
{explanation_line}
""".strip()


def quiz_prompt(topic: str, difficulty: str, question_count: int) -> str:
    return f"""
Generate {question_count} {difficulty} multiple-choice questions on {topic}.
Each question must include:
Q1. [question]
A. [option]
B. [option]
C. [optional]
D. [optional]
Correct Answer: [A/B/C/D]
Explanation: [2-3 lines]
No extra commentary.
""".strip()


def chat_system_prompt() -> str:
    return """
You are NutriBot, a concise and friendly nutrition assistant.
Stay focused on nutrition, fitness, meal quality, vitamins, and healthy habits.
For deep tasks (meal plans, recipes, full analysis, quizzes), recommend the appropriate NutriAI feature.
""".strip()


def recommendation_prompt(query: str, recommendation_type: RecommendationType) -> str:
    type_map = {
        "healthier_alternative": "Provide healthier alternatives for the query.",
        "new_healthy_recipe": "Provide a new healthy recipe inspired by the query.",
        "both": "Provide healthier alternatives and one new healthy recipe inspired by the query.",
    }
    return f"""
{type_map[recommendation_type]}
User query: {query}
Return concise bullet points only.
""".strip()
