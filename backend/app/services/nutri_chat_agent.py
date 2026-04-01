"""LangGraph runtime for agentic Nutri Chat."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Literal, Protocol, TypedDict, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.core.exceptions import AppException, ExternalServiceException
from app.schemas.calculators import BMIRequest, CaloriesRequest
from app.schemas.nutri_chat import ChatContextSection, ChatSourceReference
from app.schemas.recipes import RecipeGenerateRequest
from app.schemas.recommendations import RecommendationGenerateRequest
from app.services.nutri_chat_tools import ALL_TOOLS, LOOKUP_TOOL_NAMES, PREVIEW_TOOL_NAMES
from app.utils.ai_clients import _response_text
from app.utils.prompt_builders import agent_chat_system_prompt


# ---------------------------------------------------------------------------
# Shared type helpers
# ---------------------------------------------------------------------------


class AgentState(TypedDict, total=False):
    clerk_user_id: str
    session_id: str
    user_input: str
    transcript: list[dict[str, str]]
    context_sections: list[dict[str, Any]]
    context_summary: str
    messages: list[BaseMessage]
    reasoning_steps: list[dict[str, Any]]
    source_references: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    pending_action: dict[str, Any] | None
    final_response: str
    loop_count: int
    total_tool_calls: int
    called_tool_signatures: list[str]  # "tool_name:args_hash" for dedup
    emitter: Callable[[dict[str, Any]], Awaitable[None]] | None


class AgentModel(Protocol):
    async def invoke(self, messages: list[BaseMessage]) -> AIMessage: ...


class ToolExecutor(Protocol):
    async def __call__(self, tool_name: str, tool_input: dict[str, Any], clerk_user_id: str) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _message_text(message: BaseMessage | None) -> str:
    if message is None:
        return ""
    return _response_text(message)


def _tool_call_name(tool_call: dict[str, Any]) -> str:
    return str(tool_call.get("name") or "").strip()


def _tool_call_args(tool_call: dict[str, Any]) -> dict[str, Any]:
    raw_args = tool_call.get("args")
    if isinstance(raw_args, dict):
        return raw_args
    return {}


def _tool_call_id(tool_call: dict[str, Any]) -> str:
    return str(tool_call.get("id") or f"tool-{_now_iso()}")


def _readable_tool_name(tool_name: str) -> str:
    return tool_name.replace("_", " ").replace("preview ", "").replace("lookup ", "").strip().title()


def _tool_signature(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Stable string for deduplication — tool name + sorted args."""
    sorted_args = json.dumps(tool_input, sort_keys=True, ensure_ascii=True)
    return f"{tool_name}:{sorted_args}"


def _context_summary_lines(context_sections: list[dict[str, Any]]) -> str:
    if not context_sections:
        return "- No saved NutriAI context is available for this user yet."
    return "\n".join(
        f"- {str(section.get('label', 'Context'))}: {str(section.get('summary', '')).strip()}"
        for section in context_sections
    )


def _build_agent_system_prompt(context_sections: list[dict[str, Any]]) -> str:
    return f"""{agent_chat_system_prompt()}

Saved NutriAI context available for quick reference (use lookup tools to get full detail):
{_context_summary_lines(context_sections)}""".strip()


def _transcript_to_messages(
    transcript: list[dict[str, str]],
    *,
    user_input: str,
    context_sections: list[dict[str, Any]],
) -> list[BaseMessage]:
    messages: list[BaseMessage] = [SystemMessage(content=_build_agent_system_prompt(context_sections))]

    for item in transcript[-10:]:
        role = str(item.get("role", "user"))
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        if role == "assistant":
            messages.append(AIMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))

    # Append current user input if not already the last message
    if not transcript or str(transcript[-1].get("content", "")).strip() != user_input.strip():
        messages.append(HumanMessage(content=user_input.strip()))

    return messages


def _infer_direct_context_references(
    user_input: str,
    context_sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lowered = user_input.lower()
    references: list[dict[str, Any]] = []

    feature_keywords = {
        "nutri_calc": ("bmi", "calorie", "maintenance", "bmr", "weight", "height"),
        "recommendations": ("recommend", "alternative", "swap", "better option"),
        "recipes": ("recipe", "meal", "dish", "cook", "muscle"),
        "mealPlans": ("meal plan", "diet plan"),
        "foodInsights": ("food", "healthy", "nutrition"),
        "ingredientChecks": ("ingredient", "label", "packaged"),
    }

    for section in context_sections:
        feature = str(section.get("feature", ""))
        keywords = feature_keywords.get(feature, ())
        if keywords and any(keyword in lowered for keyword in keywords):
            references.append(
                ChatSourceReference(
                    source_type="context",
                    feature=feature,
                    label=str(section.get("label", "Context")),
                ).model_dump()
            )

    return references


# ---------------------------------------------------------------------------
# Agent model implementations
# ---------------------------------------------------------------------------


class GroqAgentModel:
    """Primary agent model using Groq (Llama 3.3 70B) with tool calling."""

    def __init__(self, groq_client: Any) -> None:
        self.tool_model = ChatGroq(  # type: ignore[call-arg]
            api_key=groq_client.api_key,
            model=groq_client.model_name,
            temperature=0.1,
        ).bind_tools(ALL_TOOLS)

    async def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        try:
            response = await self.tool_model.ainvoke(messages)  # type: ignore[arg-type]
        except Exception as exc:
            raise ExternalServiceException(
                "Nutri Agent could not reach Groq",
                details={"reason": str(exc)},
            ) from exc

        if isinstance(response, AIMessage):
            if response.tool_calls or _message_text(response):
                return response

        # Try to extract text from any response type
        content = _response_text(response)
        if content:
            return AIMessage(content=content)

        raise ExternalServiceException(
            "Nutri Agent returned an empty response",
            details={"reason": "Groq returned no answer and no tool call"},
        )


class OpenRouterAgentModel:
    """Fallback agent model using OpenRouter (kept for compatibility)."""

    def __init__(self, model_client: Any) -> None:
        headers: dict[str, str] = {}
        if getattr(model_client, "site_url", ""):
            headers["HTTP-Referer"] = model_client.site_url
        if getattr(model_client, "app_name", ""):
            headers["X-Title"] = model_client.app_name

        self.tool_model = ChatOpenAI(  # type: ignore[call-arg]
            api_key=model_client.api_key,
            base_url=model_client.base_url,
            model=model_client.model_name,
            temperature=0.1,
            default_headers=headers or None,
        ).bind_tools(ALL_TOOLS)

    async def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        try:
            response = await self.tool_model.ainvoke(messages)  # type: ignore[arg-type]
        except Exception as exc:
            raise ExternalServiceException(
                "Nutri Agent could not reach OpenRouter",
                details={"reason": str(exc)},
            ) from exc

        if isinstance(response, AIMessage):
            if response.tool_calls or _message_text(response):
                return response

        content = _response_text(response)
        if content:
            return AIMessage(content=content)

        raise ExternalServiceException(
            "Nutri Agent returned an empty response",
            details={"reason": "OpenRouter returned no answer and no tool call"},
        )


# ---------------------------------------------------------------------------
# Agent runtime (LangGraph)
# ---------------------------------------------------------------------------

_MAX_LOOPS = 4
_MAX_TOTAL_TOOL_CALLS = 6


class NutriChatAgentRuntime:
    def __init__(self, agent_model: AgentModel, tool_executor: ToolExecutor) -> None:
        self.agent_model = agent_model
        self.tool_executor = tool_executor
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("agent", self._agent_node)
        graph.add_node("run_tools", self._tool_node)
        graph.add_node("finish", self._finish_node)

        graph.add_edge(START, "agent")
        graph.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {
                "run_tools": "run_tools",
                "finish": "finish",
            },
        )
        graph.add_edge("run_tools", "agent")
        graph.add_edge("finish", END)
        return graph.compile()

    async def run(
        self,
        *,
        clerk_user_id: str,
        session_id: str,
        user_input: str,
        transcript: list[dict[str, str]],
        context_sections: list[ChatContextSection],
        emitter: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> dict[str, Any]:
        context_section_payloads = [item.model_dump(mode="json") for item in context_sections]
        result = await self.graph.ainvoke(
            {
                "clerk_user_id": clerk_user_id,
                "session_id": session_id,
                "user_input": user_input,
                "transcript": transcript,
                "context_sections": context_section_payloads,
                "context_summary": _context_summary_lines(context_section_payloads),
                "messages": _transcript_to_messages(
                    transcript,
                    user_input=user_input,
                    context_sections=context_section_payloads,
                ),
                "reasoning_steps": [],
                "source_references": [],
                "tool_results": [],
                "pending_action": None,
                "final_response": "",
                "loop_count": 0,
                "total_tool_calls": 0,
                "called_tool_signatures": [],
                "emitter": emitter,
            }
        )
        return dict(result)

    # ------------------------------------------------------------------
    # Emit helper
    # ------------------------------------------------------------------

    async def _emit(
        self,
        steps: list[dict[str, Any]],
        emitter: Callable[[dict[str, Any]], Awaitable[None]] | None,
        label: str,
        detail: str,
        status: Literal["running", "completed", "info"],
    ) -> dict[str, Any]:
        step = {
            "id": f"step_{len(steps) + 1}",
            "label": label,
            "detail": detail,
            "status": status,
            "created_at": _now_iso(),
        }
        if emitter:
            await emitter({"type": "reasoning_step", "data": step})
        return step

    # ------------------------------------------------------------------
    # Agent node
    # ------------------------------------------------------------------

    async def _agent_node(self, state: AgentState) -> AgentState:
        loop_count = int(state.get("loop_count", 0))
        total_tool_calls = int(state.get("total_tool_calls", 0))
        emitter = state.get("emitter")

        stage_label = "Reviewing your request" if loop_count == 0 else "Checking tool results"
        stage_detail = (
            "Reading your message, recent conversation, and saved NutriAI context."
            if loop_count == 0
            else "The agent received tool results and is now deciding how to answer."
        )
        reasoning_steps: list[dict[str, Any]] = list(state.get("reasoning_steps", []))
        start_step = await self._emit(reasoning_steps, emitter, stage_label, stage_detail, "running")
        reasoning_steps.append(start_step)

        # ── Invoke LLM ──────────────────────────────────────────────
        try:
            model_response = await self.agent_model.invoke(state.get("messages", []))
        except ExternalServiceException:
            # One retry with a shorter message list
            try:
                short_messages: list[BaseMessage] = list(state.get("messages", []))[-4:]
                model_response = await self.agent_model.invoke(short_messages)
            except Exception:
                fallback_step = await self._emit(
                    reasoning_steps,
                    emitter,
                    "Agent error",
                    "The model could not be reached. Returning a safe default response.",
                    "completed",
                )
                reasoning_steps.append(fallback_step)
                return {
                    **state,
                    "messages": state.get("messages", []),
                    "reasoning_steps": reasoning_steps,
                    "final_response": "I'm having trouble connecting right now. Please try again in a moment.",
                }

        messages = [*state.get("messages", []), model_response]
        tool_calls: list[dict[str, Any]] = list(getattr(model_response, "tool_calls", []) or [])

        # ── Loop guards ──────────────────────────────────────────────
        if tool_calls and (loop_count >= _MAX_LOOPS or total_tool_calls >= _MAX_TOTAL_TOOL_CALLS):
            guard_step = await self._emit(
                reasoning_steps,
                emitter,
                "Stopping tool loop",
                "The agent has gathered enough signal and will answer directly.",
                "completed",
            )
            reasoning_steps.append(guard_step)
            response_text = _message_text(model_response) or "I have gathered enough information to answer you directly."
            return {
                **state,
                "messages": messages,
                "reasoning_steps": reasoning_steps,
                "final_response": response_text,
            }

        # ── Filter duplicate tool calls ──────────────────────────────
        called_signatures: list[str] = list(state.get("called_tool_signatures", []))
        if tool_calls:
            unique_tool_calls: list[dict[str, Any]] = []
            for tc in tool_calls:
                sig = _tool_signature(_tool_call_name(tc), _tool_call_args(tc))
                if sig not in called_signatures:
                    unique_tool_calls.append(tc)
                else:
                    dedup_step = await self._emit(
                        reasoning_steps,
                        emitter,
                        f"Skipping duplicate {_readable_tool_name(_tool_call_name(tc))}",
                        "This tool was already called with the same parameters.",
                        "info",
                    )
                    reasoning_steps.append(dedup_step)
            tool_calls = unique_tool_calls

        # ── Tool call selected ───────────────────────────────────────
        if tool_calls:
            names = [_readable_tool_name(_tool_call_name(tc)) for tc in tool_calls]
            if len(names) == 1:
                label = f"Selected {names[0]}"
                detail = f"The agent will use {names[0].lower()} to gather information before answering."
            else:
                label = f"Selected {len(names)} tools in parallel"
                detail = f"The agent will run {', '.join(names)} at the same time for a faster, richer answer."

            selected_step = await self._emit(reasoning_steps, emitter, label, detail, "completed")
            reasoning_steps.append(selected_step)

            # Attach only the filtered tool_calls to a patched AIMessage so
            # the tool node processes exactly what we decided to keep.
            if len(tool_calls) != len(list(getattr(model_response, "tool_calls", []) or [])):
                model_response = AIMessage(
                    content=_message_text(model_response),
                    tool_calls=tool_calls,
                )
                messages[-1] = model_response

            return {
                **state,
                "messages": messages,
                "reasoning_steps": reasoning_steps,
            }

        # ── No tool call → direct answer ─────────────────────────────
        ready_step = await self._emit(
            reasoning_steps,
            emitter,
            "Ready to answer",
            "The agent has enough context to reply directly without calling a tool.",
            "completed",
        )
        reasoning_steps.append(ready_step)

        source_references = [*state.get("source_references", [])]
        for ref in _infer_direct_context_references(state.get("user_input", ""), state.get("context_sections", [])):
            if ref not in source_references:
                source_references.append(ref)

        return {
            **state,
            "messages": messages,
            "reasoning_steps": reasoning_steps,
            "source_references": source_references,
            "final_response": _message_text(model_response)
            or "I can help with that. Let me know if you'd like a calculation, recipe, or recommendation.",
        }

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _route_after_agent(self, state: AgentState) -> str:
        if str(state.get("final_response", "")).strip():
            return "finish"

        messages = state.get("messages", [])
        if not messages:
            return "finish"

        latest = messages[-1]
        if isinstance(latest, AIMessage) and (latest.tool_calls or []):
            return "run_tools"
        return "finish"

    # ------------------------------------------------------------------
    # Tool node — parallel execution
    # ------------------------------------------------------------------

    async def _tool_node(self, state: AgentState) -> AgentState:
        messages = state.get("messages", [])
        latest = messages[-1] if messages else None
        if not isinstance(latest, AIMessage) or not (latest.tool_calls or []):
            return state

        tool_calls: list[dict[str, Any]] = list(latest.tool_calls or [])
        clerk_user_id = str(state.get("clerk_user_id", ""))

        emitter = state.get("emitter")
        reasoning_steps = list(state.get("reasoning_steps", []))
        source_references = list(state.get("source_references", []))
        tool_results = list(state.get("tool_results", []))
        called_signatures = list(state.get("called_tool_signatures", []))

        # ── Emit "running" steps for all tools before gathering ──────
        for tc in tool_calls:
            tool_name = _tool_call_name(tc)
            readable = _readable_tool_name(tool_name)
            step = await self._emit(
                reasoning_steps,
                emitter,
                f"Running {readable}",
                f"Fetching {'history from' if tool_name in LOOKUP_TOOL_NAMES else 'a preview via'} {readable.lower()}.",
                "running",
            )
            reasoning_steps.append(step)

        # ── Execute all tool calls concurrently ──────────────────────
        async def _execute_one(tc: dict[str, Any]) -> dict[str, Any]:
            tool_name = _tool_call_name(tc)
            tool_input = _tool_call_args(tc)
            result = await self.tool_executor(tool_name, tool_input, clerk_user_id)
            return {"tool_call": tc, "result": result}

        execution_results = await asyncio.gather(
            *[_execute_one(tc) for tc in tool_calls],
            return_exceptions=True,
        )

        # ── Process results, build ToolMessages ─────────────────────
        new_tool_messages: list[ToolMessage] = []
        last_pending_action: dict[str, Any] | None = state.get("pending_action")

        for item in execution_results:
            if isinstance(item, BaseException):
                # Surface error gracefully as a tool message
                error_msg = ToolMessage(
                    content=json.dumps({"error": str(item)}, ensure_ascii=True),
                    tool_call_id=f"error-{_now_iso()}",
                    name="error",
                )
                new_tool_messages.append(error_msg)
                continue

            tc = item["tool_call"]
            result = item["result"]
            tool_name = _tool_call_name(tc)
            readable = _readable_tool_name(tool_name)

            tool_message = ToolMessage(
                content=json.dumps(
                    {
                        "tool_name": result.get("tool_name"),
                        "result": result.get("result"),
                        "reasoning_note": result.get("reasoning_note"),
                    },
                    ensure_ascii=True,
                ),
                tool_call_id=_tool_call_id(tc),
                name=tool_name,
            )
            new_tool_messages.append(tool_message)

            completed_step = await self._emit(
                reasoning_steps,
                emitter,
                f"Reviewed {readable}",
                str(result.get("reasoning_note", "Result is ready and will be used in the answer.")),
                "completed",
            )
            reasoning_steps.append(completed_step)

            # Accumulate source references
            source_ref = result.get("source_reference")
            if isinstance(source_ref, dict) and source_ref not in source_references:
                source_references.append(source_ref)

            # Track pending action (last preview tool wins)
            if tool_name in PREVIEW_TOOL_NAMES and result.get("pending_action"):
                last_pending_action = result.get("pending_action")

            tool_results.append(result)
            called_signatures.append(_tool_signature(tool_name, _tool_call_args(tc)))

        return {
            **state,
            "messages": [*messages, *new_tool_messages],
            "reasoning_steps": reasoning_steps,
            "source_references": source_references,
            "tool_results": tool_results,
            "pending_action": last_pending_action,
            "loop_count": int(state.get("loop_count", 0)) + 1,
            "total_tool_calls": int(state.get("total_tool_calls", 0)) + len(tool_calls),
            "called_tool_signatures": called_signatures,
        }

    # ------------------------------------------------------------------
    # Finish node
    # ------------------------------------------------------------------

    async def _finish_node(self, state: AgentState) -> AgentState:
        final_message = str(state.get("final_response", "")).strip()
        if not final_message:
            latest_ai = next(
                (m for m in reversed(state.get("messages", [])) if isinstance(m, AIMessage)),
                None,
            )
            final_message = _message_text(cast(BaseMessage | None, latest_ai))

        reasoning_steps: list[dict[str, Any]] = list(state.get("reasoning_steps", []))
        final_step = await self._emit(
            reasoning_steps,
            state.get("emitter"),
            "Prepared final reply",
            "The assistant has packaged the answer for you.",
            "completed",
        )
        reasoning_steps.append(final_step)

        return {
            **state,
            "reasoning_steps": reasoning_steps,
            "final_response": final_message or "I'm ready to help. Could you give me a bit more detail?",
        }


# ---------------------------------------------------------------------------
# Context section builders (used by service layer)
# ---------------------------------------------------------------------------


def build_context_sections(payloads: dict[str, list[dict[str, Any]]]) -> list[ChatContextSection]:
    sections: list[ChatContextSection] = []

    calculations = payloads.get("calculations", [])
    if calculations:
        latest = calculations[0]
        latest_bmi = next((c for c in calculations if c.get("calculator_type") == "bmi"), None)
        latest_calories = next((c for c in calculations if c.get("calculator_type") == "calories"), None)
        summary_parts = [f"{len(calculations)} saved calculations."]
        if latest_bmi:
            r = latest_bmi.get("result", {})
            summary_parts.append(f"Latest BMI: {r.get('bmi', 'n/a')} ({r.get('category', 'unknown')}).")
        if latest_calories:
            r = latest_calories.get("result", {})
            summary_parts.append(
                f"Latest calories: maintenance {r.get('maintenance_calories', 'n/a')}, BMR {r.get('bmr', 'n/a')}."
            )
        sections.append(
            ChatContextSection(
                feature="nutri_calc",
                label="Nutri Calc",
                item_count=len(calculations),
                summary=" ".join(summary_parts),
                last_updated=latest.get("created_at"),
            )
        )

    recommendations = payloads.get("recommendations", [])
    if recommendations:
        latest = recommendations[0]
        sections.append(
            ChatContextSection(
                feature="recommendations",
                label="Recommendations",
                item_count=len(recommendations),
                summary=f"{len(recommendations)} saved recommendation sets. Latest: {latest.get('title', 'recommendations')}.",
                last_updated=latest.get("created_at"),
            )
        )

    for feature_key, label in (
        ("mealPlans", "Meal Planner"),
        ("recipes", "Recipe Finder"),
        ("foodInsights", "Food Insight"),
        ("ingredientChecks", "Ingredient Checker"),
    ):
        items = payloads.get(feature_key, [])
        if not items:
            continue
        latest = items[0]
        sections.append(
            ChatContextSection(
                feature=feature_key,
                label=label,
                item_count=len(items),
                summary=f"{len(items)} saved records. Latest activity on {str(latest.get('created_at', ''))[:10]}.",
                last_updated=latest.get("created_at"),
            )
        )

    return sections


def build_tool_reference(feature: str, label: str) -> dict[str, Any]:
    return ChatSourceReference(source_type="tool", feature=feature, label=label).model_dump()


def build_pending_action(
    *,
    kind: str,
    title: str,
    summary: str,
    preview_payload: dict[str, Any],
) -> dict[str, Any]:
    if kind not in {"save_calculation", "save_recommendations", "save_recipe"}:
        raise AppException("INVALID_ACTION", "Unsupported pending action type")
    return {
        "kind": kind,
        "title": title,
        "summary": summary,
        "status": "pending",
        "preview_payload": preview_payload,
    }


def validate_bmi_input(tool_input: dict[str, Any]) -> BMIRequest:
    return BMIRequest.model_validate(tool_input)


def validate_calorie_input(tool_input: dict[str, Any]) -> CaloriesRequest:
    return CaloriesRequest.model_validate(tool_input)


def validate_recommendation_input(tool_input: dict[str, Any]) -> RecommendationGenerateRequest:
    return RecommendationGenerateRequest.model_validate(tool_input)


def validate_recipe_input(tool_input: dict[str, Any]) -> RecipeGenerateRequest:
    return RecipeGenerateRequest.model_validate(tool_input)
