"""Tests for the NutriChat agent runtime.

Uses a MockAgentModel that returns predictable AIMessage objects so tests
don't require live LLM connections. Covers:
  - Direct answers (no tools)
  - Single tool calls (preview and lookup)
  - Parallel multi-tool calls
  - Pending action persistence
  - Loop guard (max loops)
  - Duplicate tool deduplication
"""

from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage

from app.schemas.nutri_chat import ChatContextSection
from app.services.nutri_chat_agent import NutriChatAgentRuntime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx_section(feature: str = "nutri_calc", summary: str = "2 saved calculations. Latest BMI: 22.9 (healthy).") -> ChatContextSection:
    return ChatContextSection(
        feature=feature,
        label=feature.replace("_", " ").title(),
        item_count=2,
        summary=summary,
        last_updated=None,
    )


class MockAgentModel:
    """Returns a sequence of pre-configured AIMessage objects, one per invoke call."""

    def __init__(self, responses: list[AIMessage]) -> None:
        self._queue = list(responses)
        self.call_count = 0

    async def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        self.call_count += 1
        if self._queue:
            return self._queue.pop(0)
        return AIMessage(content="I can help with that.")


def _bmi_tool_result() -> dict[str, Any]:
    return {
        "tool_name": "preview_bmi",
        "result": {"bmi": 22.9, "category": "healthy"},
        "reasoning_note": "BMI preview is ready.",
        "source_reference": {"source_type": "tool", "feature": "nutri_calc", "label": "BMI preview"},
        "pending_action": {
            "kind": "save_calculation",
            "title": "Save BMI result",
            "summary": "Save this BMI preview.",
            "status": "pending",
            "preview_payload": {"calculator_type": "bmi", "input": {"weight_kg": 70, "height_cm": 175}, "result": {"bmi": 22.9}},
        },
    }


def _recipe_tool_result() -> dict[str, Any]:
    return {
        "tool_name": "preview_recipe",
        "result": {"recipe_name": "High Protein Paneer Bowl", "ingredient_list": ["paneer", "rice"]},
        "reasoning_note": "Recipe preview is ready.",
        "source_reference": {"source_type": "tool", "feature": "recipes", "label": "Recipe preview"},
        "pending_action": {
            "kind": "save_recipe",
            "title": "Save recipe",
            "summary": "Save this recipe.",
            "status": "pending",
            "preview_payload": {"input": {"dish_name": "paneer bowl"}, "result": {"recipe_name": "High Protein Paneer Bowl"}},
        },
    }


def _lookup_calc_result() -> dict[str, Any]:
    return {
        "tool_name": "lookup_calculation_history",
        "result": {"count": 2, "items": [{"type": "bmi", "bmi": 22.9, "category": "healthy", "date": "2026-03-15"}]},
        "reasoning_note": "Found 2 saved calculation records.",
        "source_reference": {"source_type": "tool", "feature": "nutri_calc", "label": "Calculation history"},
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_agent_direct_answer_no_tools() -> None:
    """Agent with no tool calls returns final_response and no pending action."""
    model = MockAgentModel([AIMessage(content="Hi! I'm NutriAI. I can help with nutrition.")])
    calls: list[tuple[str, dict, str]] = []

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:
        calls.append((tool_name, tool_input, clerk_user_id))
        raise AssertionError("Should not call tools for a greeting")

    async def run() -> None:
        runtime = NutriChatAgentRuntime(agent_model=model, tool_executor=tool_executor)  # type: ignore[arg-type]
        result = await runtime.run(
            clerk_user_id="u1",
            session_id="s1",
            user_input="Hello!",
            transcript=[],
            context_sections=[],
        )
        assert "NutriAI" in result["final_response"] or "help" in result["final_response"].lower()
        assert result["pending_action"] is None
        assert len(result["reasoning_steps"]) >= 2  # at least "Reviewing" + "Prepared"

    asyncio.run(run())
    assert calls == []


def test_agent_single_preview_tool_produces_pending_action() -> None:
    """Agent calling preview_bmi should surface a pending_action in the result."""
    tool_call_msg = AIMessage(
        content="",
        tool_calls=[{"id": "tc1", "name": "preview_bmi", "args": {"weight_kg": 70.0, "height_cm": 175.0}, "type": "tool_call"}],
    )
    final_msg = AIMessage(content="Your BMI is 22.9, which is in the healthy range.")
    model = MockAgentModel([tool_call_msg, final_msg])

    received_tool_calls: list[str] = []

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:
        received_tool_calls.append(tool_name)
        return _bmi_tool_result()

    async def run() -> None:
        runtime = NutriChatAgentRuntime(agent_model=model, tool_executor=tool_executor)  # type: ignore[arg-type]
        result = await runtime.run(
            clerk_user_id="u1",
            session_id="s1",
            user_input="Calculate my BMI, I'm 70kg and 175cm",
            transcript=[],
            context_sections=[],
        )
        assert result["pending_action"] is not None
        assert result["pending_action"]["kind"] == "save_calculation"
        assert "22.9" in result["final_response"]
        labels = [s["label"] for s in result["reasoning_steps"]]
        assert any("Bmi" in lbl or "Bmi" in lbl or "preview" in lbl.lower() or "Running" in lbl for lbl in labels)

    asyncio.run(run())
    assert received_tool_calls == ["preview_bmi"]


def test_agent_lookup_tool_no_pending_action() -> None:
    """History lookup tools must NOT produce a pending_action."""
    tool_call_msg = AIMessage(
        content="",
        tool_calls=[{"id": "tc1", "name": "lookup_calculation_history", "args": {"limit": 5}, "type": "tool_call"}],
    )
    final_msg = AIMessage(content="Your most recent BMI was 22.9 (healthy) from March 15th.")
    model = MockAgentModel([tool_call_msg, final_msg])

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:
        assert tool_name == "lookup_calculation_history"
        return _lookup_calc_result()

    async def run() -> None:
        runtime = NutriChatAgentRuntime(agent_model=model, tool_executor=tool_executor)  # type: ignore[arg-type]
        result = await runtime.run(
            clerk_user_id="u1",
            session_id="s1",
            user_input="What was my last BMI?",
            transcript=[],
            context_sections=[],
        )
        assert result["pending_action"] is None
        assert "22.9" in result["final_response"]

    asyncio.run(run())


def test_agent_parallel_multi_tool_calls() -> None:
    """Agent can call two tools in a single turn (parallel execution)."""
    parallel_call_msg = AIMessage(
        content="",
        tool_calls=[
            {"id": "tc1", "name": "lookup_calculation_history", "args": {"limit": 5}, "type": "tool_call"},
            {"id": "tc2", "name": "preview_recipe", "args": {"dish_name": "protein bowl"}, "type": "tool_call"},
        ],
    )
    final_msg = AIMessage(content="Based on your BMI history and the recipe preview, here are my recommendations...")
    model = MockAgentModel([parallel_call_msg, final_msg])

    executed_tools: list[str] = []

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:
        executed_tools.append(tool_name)
        if tool_name == "lookup_calculation_history":
            return _lookup_calc_result()
        return _recipe_tool_result()

    async def run() -> None:
        runtime = NutriChatAgentRuntime(agent_model=model, tool_executor=tool_executor)  # type: ignore[arg-type]
        result = await runtime.run(
            clerk_user_id="u1",
            session_id="s1",
            user_input="Show my BMI history and suggest a protein recipe",
            transcript=[],
            context_sections=[],
        )
        # Both tools should have been called
        assert "lookup_calculation_history" in executed_tools
        assert "preview_recipe" in executed_tools
        # Only last preview tool's pending_action kept
        assert result["pending_action"] is not None
        assert result["pending_action"]["kind"] == "save_recipe"
        # Source references should have both
        features = [r.get("feature") for r in result["source_references"]]
        assert "nutri_calc" in features
        assert "recipes" in features

    asyncio.run(run())
    assert len(executed_tools) == 2


def test_agent_loop_guard_stops_at_max_loops() -> None:
    """Agent should stop calling tools after _MAX_LOOPS iterations."""
    # Return tool calls every time — the guard should force a direct answer
    def _make_tool_call() -> AIMessage:
        return AIMessage(
            content="",
            tool_calls=[{"id": "tc-x", "name": "preview_bmi", "args": {"weight_kg": 70.0, "height_cm": 175.0}, "type": "tool_call"}],
        )

    model = MockAgentModel([_make_tool_call() for _ in range(10)])

    call_count = 0

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:
        nonlocal call_count
        call_count += 1
        return _bmi_tool_result()

    async def run() -> None:
        runtime = NutriChatAgentRuntime(agent_model=model, tool_executor=tool_executor)  # type: ignore[arg-type]
        result = await runtime.run(
            clerk_user_id="u1",
            session_id="s1",
            user_input="Keep calculating my BMI",
            transcript=[],
            context_sections=[],
        )
        # Should complete without infinite loop
        assert result["final_response"]
        # Should not have exceeded max tool calls
        assert call_count <= 6  # _MAX_TOTAL_TOOL_CALLS

    asyncio.run(run())


def test_agent_deduplicates_same_tool_calls() -> None:
    """The same tool called with the same args twice should only execute once."""
    same_call = {"id": "tc1", "name": "lookup_calculation_history", "args": {"limit": 5}, "type": "tool_call"}
    first_response = AIMessage(content="", tool_calls=[same_call])
    second_response = AIMessage(content="", tool_calls=[{**same_call, "id": "tc2"}])  # same args, different id
    final_msg = AIMessage(content="Here is what I found from your history.")
    model = MockAgentModel([first_response, second_response, final_msg])

    call_count = 0

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:
        nonlocal call_count
        call_count += 1
        return _lookup_calc_result()

    async def run() -> None:
        runtime = NutriChatAgentRuntime(agent_model=model, tool_executor=tool_executor)  # type: ignore[arg-type]
        result = await runtime.run(
            clerk_user_id="u1",
            session_id="s1",
            user_input="Show my calculations",
            transcript=[],
            context_sections=[],
        )
        assert result["final_response"]
        # Second call with same args should be deduped
        assert call_count == 1

    asyncio.run(run())


def test_agent_passes_clerk_user_id_to_tool_executor() -> None:
    """clerk_user_id must be forwarded from AgentState to the tool executor."""
    tool_call_msg = AIMessage(
        content="",
        tool_calls=[{"id": "tc1", "name": "lookup_recipe_history", "args": {"limit": 3}, "type": "tool_call"}],
    )
    final_msg = AIMessage(content="You have saved 2 recipes.")
    model = MockAgentModel([tool_call_msg, final_msg])

    received_user_ids: list[str] = []

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:
        received_user_ids.append(clerk_user_id)
        return {
            "tool_name": tool_name,
            "result": {"count": 2, "items": []},
            "reasoning_note": "Found 2 recipes.",
            "source_reference": {"source_type": "tool", "feature": "recipes", "label": "Recipe history"},
        }

    async def run() -> None:
        runtime = NutriChatAgentRuntime(agent_model=model, tool_executor=tool_executor)  # type: ignore[arg-type]
        await runtime.run(
            clerk_user_id="test-user-123",
            session_id="s1",
            user_input="Show my recipes",
            transcript=[],
            context_sections=[],
        )

    asyncio.run(run())
    assert received_user_ids == ["test-user-123"]


def test_agent_emits_reasoning_steps_in_order() -> None:
    """Reasoning steps should be emitted in chronological order with correct statuses."""
    model = MockAgentModel([AIMessage(content="No problem, here's a direct answer.")])
    emitted: list[dict] = []

    async def emitter(event: dict) -> None:
        if event.get("type") == "reasoning_step":
            emitted.append(event["data"])

    async def tool_executor(tool_name: str, tool_input: dict, clerk_user_id: str = "") -> dict:
        raise AssertionError("Should not call tools")

    async def run() -> None:
        runtime = NutriChatAgentRuntime(agent_model=model, tool_executor=tool_executor)  # type: ignore[arg-type]
        await runtime.run(
            clerk_user_id="u1",
            session_id="s1",
            user_input="What is protein?",
            transcript=[],
            context_sections=[],
            emitter=emitter,
        )

    asyncio.run(run())
    assert len(emitted) >= 2
    statuses = {s["status"] for s in emitted}
    assert "completed" in statuses
    # IDs should be sequential strings
    ids = [s["id"] for s in emitted]
    assert ids == [f"step_{i+1}" for i in range(len(ids))]


def test_build_context_sections_empty() -> None:
    """build_context_sections with no data returns empty list."""
    from app.services.nutri_chat_agent import build_context_sections

    result = build_context_sections({})
    assert result == []


def test_build_context_sections_with_bmi() -> None:
    """build_context_sections correctly summarizes BMI calculations."""
    from app.services.nutri_chat_agent import build_context_sections

    result = build_context_sections({
        "calculations": [
            {"calculator_type": "bmi", "result": {"bmi": 22.9, "category": "healthy"}, "created_at": "2026-03-15T10:00:00Z"},
        ],
        "recommendations": [],
        "mealPlans": [],
        "recipes": [],
        "foodInsights": [],
        "ingredientChecks": [],
    })
    assert len(result) == 1
    assert result[0].feature == "nutri_calc"
    assert "22.9" in result[0].summary
