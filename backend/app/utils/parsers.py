"""Robust parsers for model-generated text output."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def parse_food_insight(raw: str) -> dict:
    items: list[dict] = []
    facts: list[str] = []
    verdict = "Unknown"
    totals = {
        "calories": None,
        "carbs": None,
        "fiber": None,
        "protein": None,
        "fats": None,
    }

    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    item_pattern = re.compile(r"^\d+[.)]\s*(.+?)\s*-\s*(.+)$")

    for line in lines:
        if line.lower().startswith("total:"):
            summary = line.split(":", 1)[1]
            for metric, target in [
                ("calories", "calories"),
                ("carbs", "carbs"),
                ("fiber", "fiber"),
                ("protein", "protein"),
                ("fats", "fats"),
            ]:
                metric_match = re.search(rf"([^,;]*{target}[^,;]*)", summary, re.IGNORECASE)
                if metric_match:
                    totals[metric] = metric_match.group(1).strip()
        elif line.lower().startswith("verdict:"):
            verdict = line.split(":", 1)[1].strip()
        elif line.lower().startswith("facts:"):
            fact_content = line.split(":", 1)[1].strip()
            facts.extend([f.strip(" -") for f in re.split(r"[;•]", fact_content) if f.strip()])
        elif line.startswith("-") and facts:
            facts.append(line.strip("- "))
        else:
            match = item_pattern.match(line)
            if match:
                name = match.group(1).strip()
                details = match.group(2).strip()
                items.append(
                    {
                        "name": name,
                        "quantity": _find_labeled_value(details, "quantity"),
                        "calories_range": _find_metric(details, "calories"),
                        "carbs_range": _find_metric(details, "carbs"),
                        "fiber_range": _find_metric(details, "fiber"),
                        "protein_range": _find_metric(details, "protein"),
                        "fats_range": _find_metric(details, "fats"),
                        "details": details,
                    }
                )

    if not facts:
        facts = ["No additional nutrition facts were returned."]

    return {
        "created_at": _now_iso(),
        "items": items,
        "totals": totals,
        "verdict": verdict,
        "facts": facts,
        "raw_response": raw,
    }


def _find_metric(text: str, metric: str) -> str | None:
    match = re.search(rf"([^,;]*{metric}[^,;]*)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _find_labeled_value(text: str, label: str) -> str | None:
    match = re.search(rf"{label}\s*:\s*([^,;]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_ingredient_json(raw: str) -> dict:
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("JSON object not found")
        payload = json.loads(raw[start : end + 1])
        return {
            "healthy_ingredients": payload.get("healthy_ingredients", []),
            "unhealthy_ingredients": payload.get("unhealthy_ingredients", []),
            "health_issues": payload.get("health_issues", {}),
            "raw_response": raw,
            "created_at": _now_iso(),
        }
    except Exception:
        return {
            "healthy_ingredients": [],
            "unhealthy_ingredients": [],
            "health_issues": {},
            "raw_response": raw,
            "created_at": _now_iso(),
        }


def parse_meal_plan(raw: str) -> dict:
    section_pattern = re.compile(r"^(Breakfast|Lunch|Pre-Workout|Post-Workout|Dinner):$", re.IGNORECASE)

    sections: dict[str, list[str]] = {
        "Breakfast": [],
        "Lunch": [],
        "Pre-Workout": [],
        "Post-Workout": [],
        "Dinner": [],
    }

    current_section: str | None = None
    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        match = section_pattern.match(text)
        if match:
            current_section = match.group(1)
            continue
        if current_section:
            sections[current_section].append(text.strip("- "))

    return {
        "created_at": _now_iso(),
        "sections": [{"name": key, "options": value} for key, value in sections.items() if value],
        "raw_response": raw,
    }


def parse_recipe(raw: str) -> dict:
    recipe_name = "Generated Recipe"
    ingredients: list[dict] = []
    steps: list[str] = []
    ingredient_list: list[str] = []
    explanation: str | None = None

    section = None

    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue

        lower = text.lower()
        if lower.startswith("recipe name:"):
            recipe_name = text.split(":", 1)[1].strip() or recipe_name
            section = None
            continue
        if lower.startswith("ingredients:"):
            section = "ingredients"
            continue
        if lower.startswith("steps:"):
            section = "steps"
            continue
        if lower.startswith("ingredient list:"):
            list_text = text.split(":", 1)[1]
            ingredient_list = [item.strip() for item in list_text.split(",") if item.strip()]
            section = None
            continue
        if lower.startswith("explanation:"):
            explanation = text.split(":", 1)[1].strip() or None
            section = None
            continue

        if section == "ingredients":
            cleaned = re.sub(r"^\d+[.)]\s*", "", text)
            ingredients.append({"raw": cleaned})
        elif section == "steps":
            cleaned = re.sub(r"^\d+[.)]\s*", "", text)
            steps.append(cleaned)

    if not ingredient_list and ingredients:
        ingredient_list = [item["raw"].split(",")[0].strip() for item in ingredients]

    return {
        "created_at": _now_iso(),
        "recipe_name": recipe_name,
        "ingredients": ingredients,
        "steps": steps,
        "ingredient_list": ingredient_list,
        "explanation": explanation,
        "raw_response": raw,
    }


def parse_quiz(raw: str) -> list[dict]:
    question_pattern = re.compile(r"^Q(\d+)\.\s*(.+)$")
    option_pattern = re.compile(r"^([A-D])\.\s*(.+)$")
    answer_pattern = re.compile(r"^Correct Answer:\s*([A-D])$", re.IGNORECASE)
    explanation_pattern = re.compile(r"^Explanation:\s*(.+)$", re.IGNORECASE)

    questions: list[dict] = []
    current: dict | None = None

    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue

        q_match = question_pattern.match(text)
        if q_match:
            if current:
                questions.append(current)
            current = {
                "question": q_match.group(2),
                "options": [],
                "correct_answer": "",
                "explanation": "",
            }
            continue

        if current is None:
            continue

        o_match = option_pattern.match(text)
        if o_match:
            current["options"].append(o_match.group(2))
            continue

        a_match = answer_pattern.match(text)
        if a_match:
            current["correct_answer"] = a_match.group(1).upper()
            continue

        e_match = explanation_pattern.match(text)
        if e_match:
            current["explanation"] = e_match.group(1)

    if current:
        questions.append(current)

    validated = [
        q
        for q in questions
        if q.get("question")
        and q.get("correct_answer") in {"A", "B", "C", "D"}
        and len(q.get("options", [])) >= 2
    ]

    return validated


def parse_bullet_recommendations(raw: str) -> list[str]:
    items: list[str] = []
    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith("-") or text.startswith("*"):
            items.append(text[1:].strip())
        elif re.match(r"^\d+[.)]", text):
            items.append(re.sub(r"^\d+[.)]\s*", "", text))
    if not items:
        items = [chunk.strip() for chunk in raw.split("\n") if chunk.strip()]
    return items
