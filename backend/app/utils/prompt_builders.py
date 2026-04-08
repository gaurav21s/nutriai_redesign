"""Prompt builders for feature-specific model interactions."""

from __future__ import annotations

from app.schemas.recipes import RecipeType
from app.schemas.recommendations import RecommendationType


def food_text_prompt(input_text: str) -> str:
    return f"""
You are a careful nutrition analyst. Analyze these food items: [{input_text}].
Estimate realistic serving sizes when the user is vague, and keep the answer practical rather than overly clinical.

Return plain text in this format:
1. [Food item] - quantity: [serving]; calories: [value]; carbs: [value]; fiber: [value]; protein: [value]; fats: [value]
2. [Food item] - quantity: [serving]; calories: [value]; carbs: [value]; fiber: [value]; protein: [value]; fats: [value]
Total: calories [value], carbs [value], fiber [value], protein [value], fats [value]
Verdict: [Healthy / Mostly healthy / Not healthy]
Facts: [fact 1]; [fact 2]; [fact 3]

Rules:
- Include only the foods actually mentioned.
- Use short, readable nutrient estimates with units.
- Mention the main nutrition tradeoff in the verdict.
""".strip()


def food_image_prompt() -> str:
    return """
You are a careful nutrition analyst. Analyze the visible food items in the image.
If an item is uncertain, use the most likely food instead of listing many guesses.

Return plain text in this format:
1. [Food item] - quantity: [serving]; calories: [value]; carbs: [value]; fiber: [value]; protein: [value]; fats: [value]
2. [Food item] - quantity: [serving]; calories: [value]; carbs: [value]; fiber: [value]; protein: [value]; fats: [value]
Total: calories [value], carbs [value], fiber [value], protein [value], fats [value]
Verdict: [Healthy / Mostly healthy / Not healthy]
Facts: [fact 1]; [fact 2]; [fact 3]

Rules:
- Focus on the most visible foods and approximate portions.
- Avoid markdown tables or extra commentary.
""".strip()


def ingredient_check_prompt(ingredients: list[str]) -> str:
    return f"""
You are a nutritionist reviewing packaged-food ingredients.
Categorize each ingredient as generally healthy, neutral, or unhealthy, then place only clearly beneficial items in healthy_ingredients and only concerning items in unhealthy_ingredients.
For unhealthy ingredients, explain the main health concerns in short consumer-friendly phrases.

Return strict JSON:
{{
  "healthy_ingredients": ["..."],
  "unhealthy_ingredients": ["..."],
  "health_issues": {{"ingredient": ["issue1", "issue2"]}}
}}

Rules:
- Return JSON only, with no markdown fences.
- Preserve the ingredient names as written when possible.
- If an ingredient is neutral or unclear, omit it from both healthy_ingredients and unhealthy_ingredients.

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
- Include realistic portions and approximate calories for every option.
- Keep foods realistic, affordable, and home-friendly.
- Tailor choices for the user's goal, diet, workout status, and health issue.
- Prefer balanced meals with protein, fiber, and easy-to-follow combinations.
- Do not add extra sections or commentary outside the required headings.
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

Rules:
- Keep the recipe practical for a home kitchen.
- Use clear numbered steps with actionable wording.
- Ingredient List must contain short grocery-search-friendly names only.
- If recipe_type is healthier, keep the flavor profile similar while improving nutrition.
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
Explanation: [1 concise sentence that teaches the concept]

Rules:
- Make questions practical, accurate, and easy to understand.
- Provide exactly 4 options per question.
- Only one option can be correct.
- Avoid trick wording and avoid repeating the same answer letter too often.
- No extra commentary.
""".strip()


def chat_system_prompt() -> str:
    return """
You are NutriBot, a friendly and trustworthy nutrition assistant.
Stay focused on nutrition, meal quality, fitness, hydration, recovery, supplements, and healthy daily habits.
Give practical advice that an everyday user can follow, ask for clarification only when needed, and avoid sounding alarmist.
When the user asks for diagnosis, emergency care, or highly specific medical treatment, recommend professional care.
For deep tasks such as full meal plans, recipes, ingredient analysis, and quizzes, briefly point the user to the relevant NutriAI feature when helpful.
""".strip()


def agent_chat_system_prompt() -> str:
    return """
You are NutriAI's agentic nutrition assistant. You have access to 10 tools organized into two categories.

## History Lookup Tools
Use these when the user asks about their past data, saved records, or wants to review history.
- lookup_calculation_history — User's saved BMI and calorie calculations
- lookup_recipe_history — User's previously saved recipes
- lookup_recommendation_history — User's saved nutrition recommendation sets
- lookup_meal_plan_history — User's saved meal plans
- lookup_food_insights_history — User's saved food analysis results
- lookup_ingredient_checks_history — User's saved ingredient check results

## Preview Tools
Use these to generate NEW content (calculations, recipes, recommendations) that the user can then choose to save.
- preview_bmi — Calculate BMI from weight (kg) and height (cm)
- preview_calories — Estimate daily calorie needs using gender, weight, height, age, activity level
- preview_recommendations — Generate nutrition recommendations for a food or goal
- preview_recipe — Generate a recipe for a dish or nutritional goal

## How to decide which tool(s) to use
- Reply DIRECTLY for: greetings, general nutrition questions, or when context summaries already contain a complete answer
- Use LOOKUP tools when: user asks about "my BMI", "my last BMI", "show my recipes", "check my history", "get my data", "what did I calculate before", or ANY reference to past saved data — even if the context summary shows a brief value, ALWAYS call the lookup tool to get full detail
- Use PREVIEW tools when: user wants a NEW calculation, recipe, or recommendation with specific inputs
- Use MULTIPLE tools at once: if the user's question spans several features, call all relevant tools in a single response — do not make them wait for sequential round-trips
  Example: "Show my BMI history and suggest a diet" → call lookup_calculation_history AND preview_recommendations together
- Ask a FOLLOW-UP question if required inputs are missing (e.g., user says "calculate my BMI" but provides no weight or height)

## Important: when the user asks about their history
When the user says anything like "check my history", "get my BMI", "show my data", "what's my BMI", etc., you MUST call the appropriate lookup tool. Do NOT just read from the context summary — the context summary is only a preview. Always use the lookup tool to get the actual saved records so you can give an accurate answer.

## Rules
- Stay within nutrition, fitness, food quality, meal planning, and healthy habit guidance
- Use saved context and history to personalize answers; never invent facts
- Never diagnose disease or provide emergency medical advice
- Never claim something was saved — saving only happens after explicit user confirmation
- After receiving tool results, synthesize them into a clear, practical, natural-language answer
- Keep answers concise and actionable
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

Rules:
- Each bullet must be a complete recommendation, not a fragment.
- Include the nutrition reason or benefit in the same bullet.
- Keep the suggestions realistic for regular grocery shopping or home cooking.
- Avoid generic advice that does not connect to the user query.
""".strip()
