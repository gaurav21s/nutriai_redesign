"""Service layer for agentic Nutri Chat."""

from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from collections.abc import AsyncIterator
from typing import Any, Awaitable, Callable

from app.core.exceptions import AppException, NotFoundException
from app.core.logging import get_logger

logger = get_logger("app.services.nutri_chat")

_MAX_MESSAGE_LENGTH = 4000

# Simple greetings that can be answered instantly without agent/LLM
_GREETING_TOKENS: set[str] = {
    "hi", "hii", "hiii", "hey", "hello", "hola", "yo", "sup",
    "howdy", "hiya", "heya", "namaste",
    "good morning", "good afternoon", "good evening", "good night",
    "how are you", "how are you doing", "whats up", "what's up",
    "thanks", "thank you", "thank you so much", "thx",
    "bye", "goodbye", "see you", "see ya", "cya",
    "ok", "okay", "cool", "nice", "great", "awesome",
}
_GREETING_RESPONSE = (
    "Hey there! I'm your NutriAI assistant. How can I help you today? "
    "I can calculate your BMI, find recipes, check ingredients, "
    "create meal plans, or answer any nutrition questions you have."
)
_THANKS_RESPONSE = (
    "You're welcome! Let me know if there's anything else I can help you with — "
    "whether it's a calculation, recipe, or any nutrition question."
)
_BYE_RESPONSE = (
    "Goodbye! Feel free to come back anytime you need nutrition help. Take care!"
)


def _is_simple_greeting(content: str) -> str | None:
    """Return a fast response if content is a simple greeting, else None."""
    normalized = content.strip().lower().rstrip("!.,?;:")
    if normalized in _GREETING_TOKENS or len(normalized) <= 3:
        if normalized in ("thanks", "thank you", "thank you so much", "thx"):
            return _THANKS_RESPONSE
        if normalized in ("bye", "goodbye", "see you", "see ya", "cya"):
            return _BYE_RESPONSE
        return _GREETING_RESPONSE
    return None


from app.repositories.base import CompositeRepository
from app.schemas.nutri_chat import (
    ChatContextResponse,
    ChatMessage,
    ChatMessageMetadata,
    ChatSessionDeleteResponse,
    ChatSessionResponse,
)
from app.services.nutri_chat_agent import (
    NutriChatAgentRuntime,
    build_context_sections,
    build_tool_reference,
)
from app.services.nutri_chat_tools import LOOKUP_TOOL_NAMES
from app.services.subscription_service import SubscriptionService


class NutriChatService:
    def __init__(
        self,
        repository: CompositeRepository,
        agent_runtime: NutriChatAgentRuntime,
        subscription_service: SubscriptionService,
    ) -> None:
        self.repository = repository
        self.agent_runtime = agent_runtime
        self.subscription_service = subscription_service

    async def create_session(self, clerk_user_id: str, title: str | None = None) -> ChatSessionResponse:
        payload = await self.repository.create_chat_session(
            clerk_user_id,
            self._normalize_session_title(title),
        )
        return ChatSessionResponse.model_validate(payload)

    async def rename_session(self, clerk_user_id: str, session_id: str, title: str) -> ChatSessionResponse:
        normalized_title = self._normalize_session_title(title)
        current = await self.repository.get_chat_session(clerk_user_id, session_id)
        if not current:
            raise NotFoundException("Chat session not found")

        payload = await self.repository.update_chat_session(
            clerk_user_id,
            session_id,
            {"title": normalized_title},
        )
        if not payload:
            raise NotFoundException("Chat session not found")
        logger.info(
            "chat_session_renamed",
            extra={
                "session_id": session_id,
                "old_title": current.get("title"),
                "new_title": normalized_title,
                "feature": "nutri_chat",
                "clerk_user_id": clerk_user_id,
            },
        )
        return ChatSessionResponse.model_validate(payload)

    async def delete_session(self, clerk_user_id: str, session_id: str) -> ChatSessionDeleteResponse:
        current = await self.repository.get_chat_session(clerk_user_id, session_id)
        if not current:
            raise NotFoundException("Chat session not found")
        payload = await self.repository.delete_chat_session(clerk_user_id, session_id)
        if not payload:
            raise NotFoundException("Chat session not found")
        logger.info(
            "chat_session_deleted",
            extra={
                "session_id": session_id,
                "title": current.get("title"),
                "feature": "nutri_chat",
                "clerk_user_id": clerk_user_id,
            },
        )
        return ChatSessionDeleteResponse.model_validate(payload)

    async def list_sessions(self, clerk_user_id: str, limit: int = 30) -> list[ChatSessionResponse]:
        rows = await self.repository.list_chat_sessions(clerk_user_id, limit)
        rows = await self.subscription_service.filter_history_rows(
            clerk_user_id,
            rows,
            timestamp_keys=("last_message_at", "created_at"),
        )
        return [ChatSessionResponse.model_validate(item) for item in rows]

    async def list_messages(self, clerk_user_id: str, session_id: str, limit: int = 100) -> list[ChatMessage]:
        rows = await self.repository.list_chat_messages(clerk_user_id, session_id, limit)
        rows = await self.subscription_service.filter_history_rows(clerk_user_id, rows)
        return [ChatMessage.model_validate(row) for row in rows]

    async def get_context(self, clerk_user_id: str, session_id: str | None = None) -> ChatContextResponse:
        _ = session_id
        payloads = await self._load_context_payloads(clerk_user_id)
        return ChatContextResponse(items=build_context_sections(payloads))

    async def send_message(self, clerk_user_id: str, session_id: str, content: str) -> ChatMessage:
        message = await self._run_turn(clerk_user_id, session_id, content)
        return ChatMessage.model_validate(message)

    async def send_message_with_operation(
        self,
        clerk_user_id: str,
        session_id: str,
        content: str,
        *,
        operation_id: str | None = None,
        sequence_no: int | None = None,
    ) -> ChatMessage:
        message = await self._run_turn(
            clerk_user_id,
            session_id,
            content,
            operation_metadata={"operation_id": operation_id, "sequence_no": sequence_no},
        )
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
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=90.0)
                except asyncio.TimeoutError:
                    yield f'{json.dumps({"type": "error", "data": {"message": "Response timed out"}}, ensure_ascii=True)}\n'
                    yield f'{json.dumps({"type": "done", "data": {}}, ensure_ascii=True)}\n'
                    break
                yield f"{json.dumps(event, ensure_ascii=True)}\n"
                if event["type"] == "done":
                    break
        finally:
            if not task.done():
                task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    async def stream_turn_with_operation(
        self,
        clerk_user_id: str,
        session_id: str,
        content: str,
        *,
        operation_id: str | None = None,
        sequence_no: int | None = None,
    ) -> AsyncIterator[str]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def emit(event: dict[str, Any]) -> None:
            await queue.put(event)

        async def runner() -> None:
            try:
                await self._run_turn(
                    clerk_user_id,
                    session_id,
                    content,
                    emitter=emit,
                    operation_metadata={"operation_id": operation_id, "sequence_no": sequence_no},
                )
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
            if not task.done():
                task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    async def _run_turn(
        self,
        clerk_user_id: str,
        session_id: str,
        content: str,
        emitter: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
        operation_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if len(content) > _MAX_MESSAGE_LENGTH:
            raise AppException("MESSAGE_TOO_LONG", f"Message exceeds {_MAX_MESSAGE_LENGTH} character limit")

        # Validate session exists directly so older sessions are still reachable.
        session = await self.repository.get_chat_session(clerk_user_id, session_id)
        if not session:
            raise NotFoundException("Chat session not found")
        if not await self.subscription_service.can_access_history_row(
            clerk_user_id,
            session,
            timestamp_keys=("last_message_at", "created_at"),
        ):
            raise NotFoundException("Chat session not found")

        await self.subscription_service.consume_chat_message(clerk_user_id)

        # Store user message and build transcript
        user_message_metadata = {
            key: value
            for key, value in {
                "operation_id": (operation_metadata or {}).get("operation_id"),
                "sequence_no": (operation_metadata or {}).get("sequence_no"),
            }.items()
            if value is not None
        }
        await self.repository.add_chat_message(
            clerk_user_id,
            session_id,
            "user",
            content,
            metadata=user_message_metadata or None,
        )

        # ── Fast-path for simple greetings ─────────────────────────
        greeting_reply = _is_simple_greeting(content)
        if greeting_reply:
            recent = await self.repository.list_chat_messages(clerk_user_id, session_id, limit=12)
            fast_metadata = ChatMessageMetadata(
                reasoning_steps=[],
                source_references=[],
                pending_action=None,
                operation_id=(operation_metadata or {}).get("operation_id"),
                sequence_no=(operation_metadata or {}).get("sequence_no"),
            )
            saved = await self.repository.add_chat_message(
                clerk_user_id, session_id, "assistant", greeting_reply,
                metadata=fast_metadata.model_dump(mode="json"),
            )
            await self._maybe_update_session_title(clerk_user_id, session_id, content, recent)
            message = ChatMessage.model_validate(saved)
            if emitter:
                for chunk in self._chunk_text(message.content):
                    await emitter({"type": "assistant_delta", "data": {"delta": chunk}})
                    await asyncio.sleep(0.010)
                await emitter({"type": "message", "data": message.model_dump(mode="json")})
            return message.model_dump(mode="json")

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

        # Build metadata
        metadata = ChatMessageMetadata(
            reasoning_steps=agent_result.get("reasoning_steps", []),
            source_references=self._dedupe_source_references(agent_result.get("source_references", [])),
            pending_action=None,
            operation_id=(operation_metadata or {}).get("operation_id"),
            sequence_no=(operation_metadata or {}).get("sequence_no"),
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

        current = await self.repository.get_chat_session(clerk_user_id, session_id)
        if not current or current.get("title", "").strip() not in ("Nutri Agent", ""):
            return  # Already has a real title

        title = first_user_content.strip()[:60]
        if len(first_user_content.strip()) > 60:
            title = title.rstrip() + "…"

        try:
            await self.repository.update_chat_session(clerk_user_id, session_id, {"title": title})
        except Exception:
            logger.debug("session_title_update_failed", extra={"session_id": session_id})

    @staticmethod
    def _normalize_session_title(title: str | None) -> str:
        cleaned = (title or "").strip()
        if not cleaned:
            return "Nutri Agent"
        if len(cleaned) > 120:
            raise AppException("INVALID_SESSION_TITLE", "Session title must be 120 characters or fewer")
        return cleaned

    async def execute_tool(self, tool_name: str, tool_input: dict[str, Any], clerk_user_id: str = "") -> dict[str, Any]:
        if tool_name in LOOKUP_TOOL_NAMES:
            return await self._execute_lookup_tool(tool_name, tool_input, clerk_user_id)

        raise AppException("UNSUPPORTED_TOOL", f"Unsupported chat tool: {tool_name}")

    async def _execute_lookup_tool(
        self, tool_name: str, tool_input: dict[str, Any], clerk_user_id: str
    ) -> dict[str, Any]:
        limit = int(tool_input.get("limit", 5))
        limit = max(1, min(limit, 10))  # clamp to 1-10

        feature_map = {
            "lookup_calculation_history": ("calculations", "nutri_calc", "Calculation history"),
            "lookup_recipe_history": ("recipes", "recipes", "Recipe history"),
            "lookup_smart_picks_history": ("recommendations", "recommendations", "Nutri Smart Picks history"),
            "lookup_meal_plan_history": ("mealPlans", "mealPlans", "Meal plan history"),
            "lookup_food_insights_history": ("foodInsights", "foodInsights", "Food insight history"),
            "lookup_ingredient_checks_history": ("ingredientChecks", "ingredientChecks", "Ingredient check history"),
        }

        if tool_name not in feature_map:
            raise AppException("UNSUPPORTED_TOOL", f"Unknown lookup tool: {tool_name}")

        feature, source_feature, source_label = feature_map[tool_name]
        records = await self.repository.list_records(feature, clerk_user_id, limit)
        records = await self.subscription_service.filter_history_rows(clerk_user_id, records)
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
        max_items = await self.subscription_service.get_max_chat_context_items(clerk_user_id)
        per_feature_limit = max(3, min(max_items, 40))
        (
            calculations, recommendations, meal_plans,
            recipes, food_insights, ingredient_checks,
        ) = await asyncio.gather(
            self.repository.list_records("calculations", clerk_user_id, per_feature_limit),
            self.repository.list_records("recommendations", clerk_user_id, per_feature_limit),
            self.repository.list_records("mealPlans", clerk_user_id, per_feature_limit),
            self.repository.list_records("recipes", clerk_user_id, per_feature_limit),
            self.repository.list_records("foodInsights", clerk_user_id, per_feature_limit),
            self.repository.list_records("ingredientChecks", clerk_user_id, per_feature_limit),
        )
        payloads = {
            "calculations": calculations,
            "recommendations": recommendations,
            "mealPlans": meal_plans,
            "recipes": recipes,
            "foodInsights": food_insights,
            "ingredientChecks": ingredient_checks,
        }
        filtered = {
            key: await self.subscription_service.filter_history_rows(clerk_user_id, value)
            for key, value in payloads.items()
        }
        return self.subscription_service.trim_context_payloads(filtered, max_items)

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
