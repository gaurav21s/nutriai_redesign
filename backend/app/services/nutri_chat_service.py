"""Service layer for agentic Nutri Chat."""

from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from collections.abc import AsyncIterator
from typing import Any, Awaitable, Callable

from app.core.exceptions import AppException, NotFoundException
from app.repositories.base import CompositeRepository
from app.schemas.nutri_chat import (
    ChatActionResponse,
    ChatContextResponse,
    ChatMessage,
    ChatMessageMetadata,
    ChatPendingAction,
    ChatSessionResponse,
)
from app.services.calculator_service import CalculatorService
from app.services.nutri_chat_agent import (
    NutriChatAgentRuntime,
    build_context_sections,
    build_pending_action,
    build_tool_reference,
    validate_bmi_input,
    validate_calorie_input,
    validate_recipe_input,
    validate_recommendation_input,
)
from app.services.nutri_chat_tools import LOOKUP_TOOL_NAMES
from app.services.recipe_service import RecipeService
from app.services.recommendation_service import RecommendationService


class NutriChatService:
    def __init__(
        self,
        repository: CompositeRepository,
        agent_runtime: NutriChatAgentRuntime,
        calculator_service: CalculatorService,
        recipe_service: RecipeService,
        recommendation_service: RecommendationService,
    ) -> None:
        self.repository = repository
        self.agent_runtime = agent_runtime
        self.calculator_service = calculator_service
        self.recipe_service = recipe_service
        self.recommendation_service = recommendation_service

    async def create_session(self, clerk_user_id: str, title: str | None = None) -> ChatSessionResponse:
        payload = await self.repository.create_chat_session(
            clerk_user_id,
            title or "Nutri Agent",
        )
        return ChatSessionResponse.model_validate(payload)

    async def list_sessions(self, clerk_user_id: str, limit: int = 30) -> list[ChatSessionResponse]:
        rows = await self.repository.list_chat_sessions(clerk_user_id, limit)
        return [ChatSessionResponse.model_validate(item) for item in rows]

    async def list_messages(self, clerk_user_id: str, session_id: str, limit: int = 100) -> list[ChatMessage]:
        rows = await self.repository.list_chat_messages(clerk_user_id, session_id, limit)
        hydrated: list[ChatMessage] = []
        for row in rows:
            metadata = row.get("metadata")
            if isinstance(metadata, dict) and isinstance(metadata.get("pending_action"), dict):
                action_id = str(metadata["pending_action"].get("action_id", "")).strip()
                if action_id:
                    latest_action = await self.repository.get_chat_action(clerk_user_id, session_id, action_id)
                    if latest_action:
                        metadata = {**metadata, "pending_action": latest_action}
            hydrated.append(ChatMessage.model_validate({**row, "metadata": metadata}))
        return hydrated

    async def get_context(self, clerk_user_id: str, session_id: str | None = None) -> ChatContextResponse:
        _ = session_id
        payloads = await self._load_context_payloads(clerk_user_id)
        return ChatContextResponse(items=build_context_sections(payloads))

    async def send_message(self, clerk_user_id: str, session_id: str, content: str) -> ChatMessage:
        message = await self._run_turn(clerk_user_id, session_id, content)
        return ChatMessage.model_validate(message)

    async def stream_turn(self, clerk_user_id: str, session_id: str, content: str) -> AsyncIterator[str]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def emit(event: dict[str, Any]) -> None:
            await queue.put(event)

        async def runner() -> None:
            try:
                await self._run_turn(clerk_user_id, session_id, content, emitter=emit)
            except Exception as exc:
                await emit({"type": "error", "data": {"message": str(exc)}})
            finally:
                await emit({"type": "done", "data": {}})

        task = asyncio.create_task(runner())
        try:
            while True:
                event = await queue.get()
                yield f"{json.dumps(event, ensure_ascii=True)}\n"
                if event["type"] == "done":
                    break
        finally:
            await task

    async def confirm_action(self, clerk_user_id: str, session_id: str, action_id: str) -> ChatActionResponse:
        action = await self.repository.get_chat_action(clerk_user_id, session_id, action_id)
        if not action:
            raise NotFoundException("Pending action not found")
        if action.get("status") != "pending":
            raise AppException("INVALID_ACTION_STATE", "Only pending actions can be confirmed")

        kind = str(action.get("kind", ""))
        preview_payload = action.get("preview_payload", {})
        saved_record_id: str | None = None

        if kind == "save_calculation":
            calculator_type = str(preview_payload.get("calculator_type", ""))
            input_payload = preview_payload.get("input", {})
            result_payload = preview_payload.get("result", {})
            _ = result_payload
            if calculator_type == "bmi":
                request = validate_bmi_input(input_payload)
                response = await self.calculator_service.preview_bmi(request)
                record = await self.calculator_service.save_bmi_preview(clerk_user_id, request, response)
                saved_record_id = str(record.get("id", ""))
            elif calculator_type == "calories":
                request = validate_calorie_input(input_payload)
                response = await self.calculator_service.preview_calories(request)
                record = await self.calculator_service.save_calories_preview(clerk_user_id, request, response)
                saved_record_id = str(record.get("id", ""))
            else:
                raise AppException("INVALID_ACTION", "Unsupported calculator action payload")
        elif kind == "save_recommendations":
            request = validate_recommendation_input(preview_payload.get("input", {}))
            response = await self.recommendation_service.preview(request)
            record = await self.recommendation_service.save_preview(clerk_user_id, request, response)
            saved_record_id = str(record.get("id", ""))
        elif kind == "save_recipe":
            request = validate_recipe_input(preview_payload.get("input", {}))
            response = await self.recipe_service.preview(request)
            record = await self.recipe_service.save_preview(clerk_user_id, request, response)
            saved_record_id = str(record.get("id", ""))
        else:
            raise AppException("INVALID_ACTION", "Unsupported pending action type")

        updated = await self.repository.update_chat_action(
            clerk_user_id, session_id, action_id,
            {"status": "confirmed", "saved_record_id": saved_record_id},
        )
        if not updated:
            raise NotFoundException("Pending action not found")

        await self.repository.add_chat_message(
            clerk_user_id, session_id, "assistant",
            "Saved! You can find it in your history now.",
        )
        return ChatActionResponse(action=ChatPendingAction.model_validate(updated))

    async def reject_action(self, clerk_user_id: str, session_id: str, action_id: str) -> ChatActionResponse:
        action = await self.repository.get_chat_action(clerk_user_id, session_id, action_id)
        if not action:
            raise NotFoundException("Pending action not found")
        if action.get("status") != "pending":
            raise AppException("INVALID_ACTION_STATE", "Only pending actions can be rejected")

        updated = await self.repository.update_chat_action(
            clerk_user_id, session_id, action_id, {"status": "rejected"},
        )
        if not updated:
            raise NotFoundException("Pending action not found")
        return ChatActionResponse(action=ChatPendingAction.model_validate(updated))

    async def _run_turn(
        self,
        clerk_user_id: str,
        session_id: str,
        content: str,
        emitter: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> dict[str, Any]:
        # Validate session exists
        sessions = await self.repository.list_chat_sessions(clerk_user_id, limit=100)
        if not any(s.get("session_id") == session_id for s in sessions):
            raise NotFoundException("Chat session not found")

        # Store user message and build transcript
        await self.repository.add_chat_message(clerk_user_id, session_id, "user", content)
        recent = await self.repository.list_chat_messages(clerk_user_id, session_id, limit=12)
        transcript = [
            {"role": str(item.get("role", "user")), "content": str(item.get("content", ""))}
            for item in recent
            if str(item.get("content", "")).strip()
        ]

        # Load and emit context
        context_payloads = await self._load_context_payloads(clerk_user_id)
        context_sections = build_context_sections(context_payloads)

        if emitter:
            await emitter({
                "type": "context",
                "data": ChatContextResponse(items=context_sections).model_dump(mode="json"),
            })

        # Run agent
        agent_result = await self.agent_runtime.run(
            clerk_user_id=clerk_user_id,
            session_id=session_id,
            user_input=content,
            transcript=transcript,
            context_sections=context_sections,
            emitter=emitter,
        )

        # ── Persist pending action BEFORE saving the message ────────
        pending_action_data: dict[str, Any] | None = agent_result.get("pending_action")
        persisted_action: dict[str, Any] | None = None
        if pending_action_data and isinstance(pending_action_data, dict):
            persisted_action = await self.repository.create_chat_action(
                clerk_user_id, session_id, pending_action_data
            )

        # Build metadata
        metadata = ChatMessageMetadata(
            reasoning_steps=agent_result.get("reasoning_steps", []),
            source_references=self._dedupe_source_references(agent_result.get("source_references", [])),
            pending_action=ChatPendingAction.model_validate(persisted_action) if persisted_action else None,
        )

        # Save assistant message
        saved = await self.repository.add_chat_message(
            clerk_user_id,
            session_id,
            "assistant",
            str(agent_result.get("final_response", "")).strip(),
            metadata=metadata.model_dump(mode="json"),
        )

        # Auto-title session from first user message if still default
        await self._maybe_update_session_title(clerk_user_id, session_id, content, recent)

        message = ChatMessage.model_validate(saved)

        if emitter:
            # Stream text chunks
            for chunk in self._chunk_text(message.content):
                await emitter({"type": "assistant_delta", "data": {"delta": chunk}})
                await asyncio.sleep(0.015)

            # Emit pending action card if present
            if message.metadata and message.metadata.pending_action:
                await emitter({
                    "type": "pending_action",
                    "data": message.metadata.pending_action.model_dump(mode="json"),
                })

            await emitter({"type": "message", "data": message.model_dump(mode="json")})

        return message.model_dump(mode="json")

    async def _maybe_update_session_title(
        self,
        clerk_user_id: str,
        session_id: str,
        first_user_content: str,
        recent_messages: list[dict[str, Any]],
    ) -> None:
        """Auto-title the session from the first user message if it's still the default."""
        user_messages = [m for m in recent_messages if m.get("role") == "user"]
        if len(user_messages) != 1:
            return  # Only title on the very first message

        sessions = await self.repository.list_chat_sessions(clerk_user_id, limit=100)
        current = next((s for s in sessions if s.get("session_id") == session_id), None)
        if not current or current.get("title", "").strip() not in ("Nutri Agent", ""):
            return  # Already has a real title

        title = first_user_content.strip()[:60]
        if len(first_user_content.strip()) > 60:
            title = title.rstrip() + "…"

        try:
            await self.repository.update_chat_session(clerk_user_id, session_id, {"title": title})
        except Exception:
            pass  # Non-critical — don't fail the turn

    async def execute_tool(self, tool_name: str, tool_input: dict[str, Any], clerk_user_id: str = "") -> dict[str, Any]:
        # ── History lookup tools ─────────────────────────────────────
        if tool_name in LOOKUP_TOOL_NAMES:
            return await self._execute_lookup_tool(tool_name, tool_input, clerk_user_id)

        # ── Preview tools ────────────────────────────────────────────
        if tool_name == "preview_bmi":
            request = validate_bmi_input(tool_input)
            result = await self.calculator_service.preview_bmi(request)
            return {
                "tool_name": tool_name,
                "result": result.model_dump(mode="json"),
                "reasoning_note": "The BMI preview is ready and can be translated into plain-language guidance.",
                "source_reference": build_tool_reference("nutri_calc", "BMI preview"),
                "pending_action": build_pending_action(
                    kind="save_calculation",
                    title="Save BMI result",
                    summary="Save this BMI preview to your Nutri Calc history.",
                    preview_payload={
                        "calculator_type": "bmi",
                        "input": request.model_dump(),
                        "result": result.model_dump(mode="json"),
                    },
                ),
            }

        if tool_name == "preview_calories":
            request = validate_calorie_input(tool_input)
            result = await self.calculator_service.preview_calories(request)
            return {
                "tool_name": tool_name,
                "result": result.model_dump(mode="json"),
                "reasoning_note": "The calorie estimate is ready and can now be explained in a practical way.",
                "source_reference": build_tool_reference("nutri_calc", "Calorie preview"),
                "pending_action": build_pending_action(
                    kind="save_calculation",
                    title="Save calorie estimate",
                    summary="Save this calorie preview to your Nutri Calc history.",
                    preview_payload={
                        "calculator_type": "calories",
                        "input": request.model_dump(),
                        "result": result.model_dump(mode="json"),
                    },
                ),
            }

        if tool_name == "preview_recommendations":
            request = validate_recommendation_input(tool_input)
            result = await self.recommendation_service.preview(request)
            return {
                "tool_name": tool_name,
                "result": result.model_dump(mode="json"),
                "reasoning_note": "The recommendation preview is ready and can now be summarized for the user.",
                "source_reference": build_tool_reference("recommendations", "Recommendation preview"),
                "pending_action": build_pending_action(
                    kind="save_recommendations",
                    title="Save recommendations",
                    summary="Save this recommendation set to your history.",
                    preview_payload={
                        "input": request.model_dump(),
                        "result": result.model_dump(mode="json"),
                    },
                ),
            }

        if tool_name == "preview_recipe":
            request = validate_recipe_input(tool_input)
            result = await self.recipe_service.preview(request)
            return {
                "tool_name": tool_name,
                "result": result.model_dump(mode="json"),
                "reasoning_note": "The recipe preview is ready and can now be matched to the user's goal.",
                "source_reference": build_tool_reference("recipes", "Recipe preview"),
                "pending_action": build_pending_action(
                    kind="save_recipe",
                    title="Save recipe",
                    summary="Save this recipe to your recipe history.",
                    preview_payload={
                        "input": request.model_dump(),
                        "result": result.model_dump(mode="json"),
                    },
                ),
            }

        raise AppException("UNSUPPORTED_TOOL", f"Unsupported chat tool: {tool_name}")

    async def _execute_lookup_tool(
        self, tool_name: str, tool_input: dict[str, Any], clerk_user_id: str
    ) -> dict[str, Any]:
        limit = int(tool_input.get("limit", 5))
        limit = max(1, min(limit, 10))  # clamp to 1-10

        feature_map = {
            "lookup_calculation_history": ("calculations", "nutri_calc", "Calculation history"),
            "lookup_recipe_history": ("recipes", "recipes", "Recipe history"),
            "lookup_recommendation_history": ("recommendations", "recommendations", "Recommendation history"),
            "lookup_meal_plan_history": ("mealPlans", "mealPlans", "Meal plan history"),
            "lookup_food_insights_history": ("foodInsights", "foodInsights", "Food insight history"),
            "lookup_ingredient_checks_history": ("ingredientChecks", "ingredientChecks", "Ingredient check history"),
        }

        if tool_name not in feature_map:
            raise AppException("UNSUPPORTED_TOOL", f"Unknown lookup tool: {tool_name}")

        feature, source_feature, source_label = feature_map[tool_name]
        records = await self.repository.list_records(feature, clerk_user_id, limit)
        summary = self._summarize_records(feature, records)

        return {
            "tool_name": tool_name,
            "result": summary,
            "reasoning_note": f"Found {len(records)} saved {source_label.lower()} records for the user.",
            "source_reference": build_tool_reference(source_feature, source_label),
            # No pending_action for lookups — they are read-only
        }

    @staticmethod
    def _summarize_records(feature: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Produce a compact summary of history records suitable for the agent."""
        if not records:
            return {"count": 0, "items": [], "note": "No saved records found for this feature."}

        items: list[dict[str, Any]] = []

        if feature == "calculations":
            for r in records:
                calc_type = str(r.get("calculator_type", ""))
                result = r.get("result", {})
                date = str(r.get("created_at", ""))[:10]
                if calc_type == "bmi":
                    items.append({"type": "bmi", "bmi": result.get("bmi"), "category": result.get("category"), "date": date})
                elif calc_type == "calories":
                    items.append({"type": "calories", "bmr": result.get("bmr"), "maintenance": result.get("maintenance_calories"), "date": date})

        elif feature == "recipes":
            for r in records:
                items.append({
                    "recipe_name": r.get("recipe_name", ""),
                    "ingredients_count": len(r.get("ingredient_list", [])),
                    "date": str(r.get("created_at", ""))[:10],
                })

        elif feature == "recommendations":
            for r in records:
                recs = r.get("recommendations", [])
                items.append({
                    "title": r.get("title", ""),
                    "recommendation_count": len(recs),
                    "preview": recs[:2] if recs else [],
                    "date": str(r.get("created_at", ""))[:10],
                })

        elif feature == "mealPlans":
            for r in records:
                sections = r.get("sections", [])
                items.append({
                    "sections": [s.get("name", "") for s in sections],
                    "date": str(r.get("created_at", ""))[:10],
                })

        elif feature == "foodInsights":
            for r in records:
                items.append({
                    "verdict": r.get("verdict", ""),
                    "item_count": len(r.get("items", [])),
                    "date": str(r.get("created_at", ""))[:10],
                })

        elif feature == "ingredientChecks":
            for r in records:
                items.append({
                    "healthy_count": len(r.get("healthy_ingredients", [])),
                    "unhealthy_count": len(r.get("unhealthy_ingredients", [])),
                    "date": str(r.get("created_at", ""))[:10],
                })

        else:
            for r in records:
                items.append({"date": str(r.get("created_at", ""))[:10]})

        return {"count": len(records), "items": items}

    async def _load_context_payloads(self, clerk_user_id: str) -> dict[str, list[dict[str, Any]]]:
        (
            calculations, recommendations, meal_plans,
            recipes, food_insights, ingredient_checks,
        ) = await asyncio.gather(
            self.repository.list_records("calculations", clerk_user_id, 5),
            self.repository.list_records("recommendations", clerk_user_id, 5),
            self.repository.list_records("mealPlans", clerk_user_id, 3),
            self.repository.list_records("recipes", clerk_user_id, 3),
            self.repository.list_records("foodInsights", clerk_user_id, 3),
            self.repository.list_records("ingredientChecks", clerk_user_id, 3),
        )
        return {
            "calculations": calculations,
            "recommendations": recommendations,
            "mealPlans": meal_plans,
            "recipes": recipes,
            "foodInsights": food_insights,
            "ingredientChecks": ingredient_checks,
        }

    @staticmethod
    def _chunk_text(content: str) -> list[str]:
        words = content.split()
        if not words:
            return [content]
        chunks: list[str] = []
        current: list[str] = []
        for word in words:
            current.append(word)
            if len(" ".join(current)) >= 24 or word.endswith((".", ",", "!", "?")):
                chunks.append(" ".join(current) + " ")
                current = []
        if current:
            chunks.append(" ".join(current))
        return chunks

    @staticmethod
    def _dedupe_source_references(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique: OrderedDict[tuple[str, str, str, str | None], dict[str, Any]] = OrderedDict()
        for item in items:
            key = (
                str(item.get("source_type", "")),
                str(item.get("feature", "")),
                str(item.get("label", "")),
                str(item.get("record_id")) if item.get("record_id") else None,
            )
            unique[key] = item
        return list(unique.values())
