"""Deterministic fallback AI clients for local development/testing."""

from __future__ import annotations

import re


class FallbackGeminiClient:
    """Drop-in Gemini replacement that returns parseable deterministic content."""

    async def generate_text(self, prompt: str) -> str:
        if "Return strict JSON" in prompt:
            return """{
  "healthy_ingredients": ["oats", "almonds", "spinach"],
  "unhealthy_ingredients": ["refined sugar"],
  "health_issues": {"refined sugar": ["blood sugar spikes", "empty calories"]}
}"""

        return """1. Oatmeal Bowl - 280 calories, 45g carbs, 7g fiber, 10g protein, 8g fats
2. Greek Yogurt - 120 calories, 6g carbs, 0g fiber, 12g protein, 4g fats
Total: 400 calories, 51g carbs, 7g fiber, 22g protein, 12g fats
Verdict: Healthy
Facts: Rich in fiber; balanced protein; supports satiety."""

    async def generate_with_image(self, prompt: str, image_bytes: bytes, mime_type: str = "image/png") -> str:
        _ = (prompt, image_bytes, mime_type)
        return """1. Mixed Salad - 220 calories, 24g carbs, 6g fiber, 8g protein, 10g fats
Total: 220 calories, 24g carbs, 6g fiber, 8g protein, 10g fats
Verdict: Healthy
Facts: High micronutrient density; moderate energy load."""

    async def identify_ingredients_from_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        _ = (image_bytes, mime_type)
        return "tomato, spinach, olive oil, chickpeas, lemon"


class FallbackTogetherClient:
    """Drop-in Together replacement for meal-plan and chat prompts."""

    async def generate_text(self, prompt: str, temperature: float = 0.2) -> str:
        _ = temperature
        if "Create a practical homemade meal plan." in prompt:
            return """Breakfast:
- Vegetable omelette with whole wheat toast (320 calories)
- Oats with chia and banana (340 calories)

Lunch:
- Brown rice, dal, and sauteed vegetables (520 calories)
- Quinoa bowl with paneer and greens (500 calories)

Pre-Workout:
- Banana with peanut butter (180 calories)
- Greek yogurt with berries (170 calories)

Post-Workout:
- Protein smoothie with milk and oats (260 calories)
- Cottage cheese and fruit (220 calories)

Dinner:
- Grilled tofu with stir-fried vegetables (430 calories)
- Lentil soup with mixed salad (390 calories)
"""

        return (
            "Great question. Prioritize whole foods, keep hydration high, and aim for "
            "a protein source in each meal to support consistent energy."
        )


class FallbackGroqClient:
    """Drop-in Groq replacement for recipe/quiz/recommendation prompts."""

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        _ = (system_prompt, temperature)
        if "Return in this exact structure:" in prompt:
            return """Recipe Name: Balanced Power Bowl
Ingredients:
1. 1 cup cooked quinoa
2. 1/2 cup chickpeas
3. 1 cup mixed vegetables
4. 1 tbsp olive oil
Steps:
1. Cook quinoa until fluffy.
2. Saute vegetables and chickpeas in olive oil.
3. Combine and season to taste.
Ingredient List: quinoa, chickpeas, mixed vegetables, olive oil
Explanation: Higher fiber and protein profile with lower saturated fat."""

        if "multiple-choice questions" in prompt:
            match = re.search(r"Generate\s+(\d+)", prompt, re.IGNORECASE)
            count = int(match.group(1)) if match else 3
            lines: list[str] = []
            for i in range(1, count + 1):
                lines.extend(
                    [
                        f"Q{i}. Which nutrient mainly supports muscle repair?",
                        "A. Protein",
                        "B. Sodium",
                        "C. Fructose",
                        "D. Cholesterol",
                        "Correct Answer: A",
                        "Explanation: Protein provides amino acids used for muscle recovery.",
                    ]
                )
            return "\n".join(lines)

        return """- Swap sugary drinks with water infused with lemon.
- Replace refined snacks with nuts and fruit.
- Build meals around vegetables, lean protein, and whole grains."""


class FallbackOpenRouterClient:
    """Deterministic fallback client for agent planning in local development/testing."""

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        _ = (system_prompt, temperature)
        lowered = prompt.lower()

        if '"next_action"' in prompt:
            if "tool results:" in lowered:
                return """{
  "thinking_title": "Drafting the answer",
  "thinking_detail": "I have the tool output I need, so I can answer directly and offer a save action when relevant.",
  "next_action": "reply",
  "tool_name": "",
  "tool_input": {},
  "reply": "Here is the result I worked out from your NutriAI data and the tool preview. If you want, you can save it to your history from the action card below."
}"""

            if "bmi" in lowered and "weight_kg" in lowered and "height_cm" in lowered:
                return """{
  "thinking_title": "Running a BMI check",
  "thinking_detail": "The user gave enough information for a BMI preview, so I should calculate it before answering.",
  "next_action": "tool",
  "tool_name": "preview_bmi",
  "tool_input": {"weight_kg": 72, "height_cm": 175},
  "reply": ""
}"""

            if "calorie" in lowered and "activity_multiplier" in lowered:
                return """{
  "thinking_title": "Estimating calorie needs",
  "thinking_detail": "The user appears to want calorie guidance and the required profile fields are available.",
  "next_action": "tool",
  "tool_name": "preview_calories",
  "tool_input": {"gender": "Male", "weight_kg": 72, "height_cm": 175, "age": 30, "activity_multiplier": 1.55},
  "reply": ""
}"""

            if "recommend" in lowered or "alternative" in lowered:
                return """{
  "thinking_title": "Generating recommendations",
  "thinking_detail": "A recommendation preview will make the reply more concrete for the user.",
  "next_action": "tool",
  "tool_name": "preview_recommendations",
  "tool_input": {"query": "healthy dinner ideas", "recommendation_type": "both"},
  "reply": ""
}"""

            return """{
  "thinking_title": "Using saved NutriAI context",
  "thinking_detail": "I can answer directly from the user's message and the recent history summary without running a tool.",
  "next_action": "reply",
  "tool_name": "",
  "tool_input": {},
  "reply": "Based on your recent NutriAI activity, focus on consistent protein, more fiber-rich foods, and a breakfast you can repeat on busy days. If you want a more specific calculation or recommendation, I can work one out here."
}"""

        return (
            "Based on your recent NutriAI data, I would keep the plan practical: anchor meals around "
            "protein, use your latest calculator results as a baseline, and adjust one habit at a time."
        )
