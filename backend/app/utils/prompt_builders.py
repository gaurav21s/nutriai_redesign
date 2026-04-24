"""Prompt builders for feature-specific model interactions."""

from __future__ import annotations

from app.schemas.recipes import RecipeType
from app.schemas.smart_picks import SmartPickGenerateRequest


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
You are NutriAI's agentic nutrition assistant. You have access to 6 history lookup tools.

## History Lookup Tools
Use these when the user asks about their past data, saved records, or wants to review history.
- lookup_calculation_history — User's saved BMI and calorie calculations
- lookup_recipe_history — User's previously saved recipes
- lookup_smart_picks_history — User's saved Nutri Smart Picks decision sets
- lookup_meal_plan_history — User's saved meal plans
- lookup_food_insights_history — User's saved food analysis results
- lookup_ingredient_checks_history — User's saved ingredient check results

## NutriAI Feature Links (with query parameters)
You do NOT generate calculations, recipes, Nutri Smart Picks, or meal plans yourself. Instead, guide the user to the appropriate NutriAI feature page. When suggesting a feature, ALWAYS include a clickable markdown link with query parameters pre-filled when possible:

- BMI calculation → [Nutri Calc](/nutri-calc?mode=bmi&weight=WEIGHT&height=HEIGHT)
- Calorie calculation → [Nutri Calc](/nutri-calc?mode=calories&weight=WEIGHT&height=HEIGHT&gender=GENDER&age=AGE&activity=MULTIPLIER)
- Recipe generation → [Recipe Finder](/recipe-finder?dish=DISH_NAME&type=TYPE) where type is "normal", "healthier", or "new_healthy"
- Nutri Smart Picks → [Nutri Smart Picks](/nutri-smart-picks?goal=GOAL&mode=MODE&situation=SITUATION&context=CONTEXT) where mode is "compare_options", "situation_pick", or "swap_current_choice". This feature is for structured real-world food decisions: comparing options, choosing the best fallback, and ranking choices for a goal or situation.
- Meal planning → [Meal Planner](/meal-planner?goal=GOAL&diet=DIET&gender=GENDER&food_type=FOOD_TYPE)
- Food analysis → [Food Insight](/food-insight?text=FOOD_DESCRIPTION)
- Ingredient check → [Ingredient Checker](/ingredient-checker?text=INGREDIENTS)
- Nutrition quiz → [Nutri Quiz](/nutri-quiz)

Replace ALL-CAPS placeholders with actual values from the conversation. URL-encode spaces as %20.

Examples:
- "Try this high-protein breakfast on [Recipe Finder](/recipe-finder?dish=high%20protein%20breakfast%20bowl&type=new_healthy) — it's already set up, just click Generate!"
- "You can check your BMI on [Nutri Calc](/nutri-calc?mode=bmi&weight=70&height=175) — your values are pre-filled!"
- "Need a real-world choice for that? Open [Nutri Smart Picks](/nutri-smart-picks?goal=muscle_gain&mode=situation_pick&situation=breakfast&context=healthy%20breakfast%20for%20muscle%20gain)"

## Strategy: ALWAYS look up history first
When the user asks a question about recipes, calculations, meals, or any feature — ALWAYS call the relevant lookup tool FIRST to check their history. Use those results to give a personalized answer:
- If they have relevant history: mention specific items from their past data, then suggest the feature link for new content
- If they have no relevant history: acknowledge that and suggest the feature link

Example flow for "which recipe for breakfast can help me gain muscle?":
1. Call lookup_recipe_history to check if they have any saved high-protein breakfast recipes
2. If found: "I found your saved **Protein Pancakes** recipe from last week — that's a great muscle-building breakfast! Want something new? Try [Recipe Finder](/recipe-finder?dish=high%20protein%20breakfast&type=new_healthy)"
3. If not found: "You don't have any saved breakfast recipes yet. Try generating one on [Recipe Finder](/recipe-finder?dish=high%20protein%20breakfast%20for%20muscle%20gain&type=new_healthy) — it's ready to go, just hit Generate!"

## How to decide what to do
- Reply DIRECTLY for: greetings, general nutrition questions, or when context summaries already contain a complete answer
- PROACTIVELY call LOOKUP tools: whenever the user's question relates to recipes, calculations, smart picks, meal plans, food insights, or ingredients — call the lookup tool FIRST to personalize your answer, even if the user didn't explicitly ask about history
- DIRECT to a feature page when: user wants NEW content — always include the link with query params pre-filled
- Use MULTIPLE tools at once: if the question spans several features, call all relevant lookup tools in a single response

## Rules
- Stay within nutrition, fitness, food quality, meal planning, and healthy habit guidance
- Use saved context and history to personalize answers; never invent facts
- Never diagnose disease or provide emergency medical advice
- After receiving tool results, synthesize them into a clear, practical, natural-language answer
- When suggesting a feature, ALWAYS include the markdown link with query params pre-filled
- NEVER output raw function call syntax like <function=...> in your text response — only use proper tool calls
- Keep answers concise, actionable, and personalized based on the user's history
""".strip()


def smart_picks_prompt(payload: SmartPickGenerateRequest, context_summary: str) -> str:
    mode_instructions = {
        "compare_options": "Rank the provided options from best to worst for the user's stated goal.",
        "situation_pick": "Recommend the strongest real-world choices for the user's situation and constraints.",
        "swap_current_choice": "Suggest the closest better replacements for the user's current choice or habit.",
    }

    options_block = "\n".join(f"- {item}" for item in payload.options) if payload.options else "- None provided"
    constraints_block = "\n".join(f"- {item}" for item in payload.constraints) if payload.constraints else "- None provided"

    return f"""
You are Nutri Smart Picks, a structured nutrition decision engine.
Your job is to help the user choose the best real-world option for their goal.

Mode:
{payload.mode} — {mode_instructions[payload.mode]}

Goal:
{payload.goal}

Situation:
{payload.situation or "Not provided"}

Options to compare:
{options_block}

Current choice:
{payload.current_choice or "Not provided"}

Constraints:
{constraints_block}

Diet preference:
{payload.diet_preference or "Not provided"}

Budget:
{payload.budget or "Not provided"}

Time available:
{payload.time_available or "Not provided"}

Cooking access:
{payload.cooking_access or "Not provided"}

Extra context:
{payload.context or "Not provided"}

Recent NutriAI context:
{context_summary or "- No recent NutriAI context available."}

Return strict JSON only in this shape:
{{
  "title": "short title",
  "decision_summary": "1-2 sentence summary of the decision",
  "best_pick": "the strongest option label",
  "fallback_rule": "one rule for when the ideal option is unavailable",
  "ranked_options": [
    {{
      "label": "option name",
      "rank": 1,
      "verdict": "short verdict",
      "why": "why it fits the user's goal in this situation",
      "tradeoff": "main limitation or downside",
      "quick_upgrade": "simple tweak to improve it further",
      "good_for": "who or when this option works best",
      "avoid_if": "when not to choose it"
    }}
  ]
}}

Rules:
- Do not generate a full recipe, ingredient list, meal plan, calorie calculation, or coaching essay.
- Keep every option realistic for everyday life, ordering out, grocery shopping, travel, work, or quick eating.
- Use consumer-friendly language, not clinical jargon.
- Rank no more than 5 options.
- Make the best_pick exactly match one ranked option label.
- If the user gave explicit options, stay anchored to those options.
""".strip()
