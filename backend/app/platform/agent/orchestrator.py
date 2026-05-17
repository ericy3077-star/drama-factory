"""AgentOS — LangGraph state-machine orchestrator."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from enum import StrEnum
from typing import Any, TypedDict

import anthropic
import structlog
from langgraph.graph import END, StateGraph

from app.config import settings
from app.platform.agent.executor import execute_plan
from app.platform.agent.planner import plan_task

log = structlog.get_logger()


# ── State definition ──────────────────────────────────────────────────────────

class AgentStatus(StrEnum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING_HUMAN = "WAITING_HUMAN"
    DONE = "DONE"
    FAILED = "FAILED"


class AgentState(TypedDict):
    user_id: str
    task: str
    vertical: str
    context: dict[str, Any]
    status: str
    plan: list[dict[str, Any]]
    step_results: list[dict[str, Any]]
    final_answer: str
    error: str
    human_input: str | None
    requires_human: bool


class AgentResult:
    def __init__(self, state: AgentState) -> None:
        self.status = state["status"]
        self.answer = state.get("final_answer", "")
        self.step_results = state.get("step_results", [])
        self.error = state.get("error", "")
        self.requires_human = state.get("requires_human", False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "answer": self.answer,
            "step_results": self.step_results,
            "error": self.error,
            "requires_human": self.requires_human,
        }


# ── Node functions ────────────────────────────────────────────────────────────

async def planning_node(state: AgentState) -> AgentState:
    """Decompose the task into a structured plan."""
    log.info("agent.planning", user_id=state["user_id"], task=state["task"][:80])
    try:
        plan = await plan_task(state["task"], state["vertical"], state.get("context"))
        return {
            **state,
            "status": AgentStatus.EXECUTING,
            "plan": plan.steps,
        }
    except Exception as exc:
        log.error("agent.planning_failed", error=str(exc))
        return {**state, "status": AgentStatus.FAILED, "error": str(exc)}


async def executing_node(state: AgentState) -> AgentState:
    """Run the planned steps sequentially."""
    log.info("agent.executing", steps=len(state["plan"]))
    try:
        results = await execute_plan(state["plan"])
        step_dicts = [r.to_dict() for r in results]

        # Check if any step needs human confirmation
        needs_human = any(
            r.tool in ("confirm_trade", "approve_payment") for r in results
        )
        if needs_human:
            return {
                **state,
                "status": AgentStatus.WAITING_HUMAN,
                "step_results": step_dicts,
                "requires_human": True,
            }

        # Synthesise final answer from step outputs
        outputs = [r.output for r in results if r.success and r.output]
        final = await _synthesise(state["task"], outputs, state["vertical"])

        return {
            **state,
            "status": AgentStatus.DONE,
            "step_results": step_dicts,
            "final_answer": final,
            "requires_human": False,
        }
    except Exception as exc:
        log.error("agent.executing_failed", error=str(exc))
        return {**state, "status": AgentStatus.FAILED, "error": str(exc)}


async def human_review_node(state: AgentState) -> AgentState:
    """Handle human approval (called externally by injecting human_input)."""
    human_input = state.get("human_input") or ""
    if human_input.strip().lower() in ("yes", "approve", "ok", "confirmed"):
        # Resume execution with approved action
        return {**state, "status": AgentStatus.DONE, "requires_human": False,
                "final_answer": "Action approved and executed successfully."}
    return {**state, "status": AgentStatus.FAILED, "error": "Action rejected by user.",
            "requires_human": False}


async def _synthesise(task: str, outputs: list[Any], vertical: str) -> str:
    """Use Claude to synthesise step outputs into a coherent final answer."""
    if not outputs:
        return "Task completed with no data outputs."

    import json
    outputs_text = json.dumps(outputs, default=str)[:6000]

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": (
                f"Based on the following data gathered for the task '{task}', "
                f"write a clear, helpful response for the user in the {vertical} domain.\n\n"
                f"Data: {outputs_text}"
            ),
        }],
    )
    return message.content[0].text  # type: ignore[union-attr]


# ── Graph construction ────────────────────────────────────────────────────────

def _route_after_planning(state: AgentState) -> str:
    if state["status"] == AgentStatus.FAILED:
        return "failed"
    return "executing"


def _route_after_executing(state: AgentState) -> str:
    if state["status"] == AgentStatus.WAITING_HUMAN:
        return "human_review"
    if state["status"] == AgentStatus.FAILED:
        return "failed"
    return "done"


def _route_after_human(state: AgentState) -> str:
    return "done" if state["status"] == AgentStatus.DONE else "failed"


def _build_graph() -> Any:
    """Construct and compile the LangGraph state machine."""
    builder: StateGraph = StateGraph(AgentState)

    builder.add_node("planning", planning_node)
    builder.add_node("executing", executing_node)
    builder.add_node("human_review", human_review_node)

    builder.set_entry_point("planning")

    builder.add_conditional_edges(
        "planning",
        _route_after_planning,
        {"executing": "executing", "failed": END},
    )
    builder.add_conditional_edges(
        "executing",
        _route_after_executing,
        {"human_review": "human_review", "done": END, "failed": END},
    )
    builder.add_conditional_edges(
        "human_review",
        _route_after_human,
        {"done": END, "failed": END},
    )

    return builder.compile()


_graph = _build_graph()


# ── Public API ────────────────────────────────────────────────────────────────

class AgentOrchestrator:
    """Entry-point for running agent tasks."""

    async def run(
        self,
        user_id: str,
        task: str,
        vertical: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Execute *task* end-to-end and return the final result."""
        initial_state: AgentState = {
            "user_id": user_id,
            "task": task,
            "vertical": vertical,
            "context": context or {},
            "status": AgentStatus.PLANNING,
            "plan": [],
            "step_results": [],
            "final_answer": "",
            "error": "",
            "human_input": None,
            "requires_human": False,
        }
        final_state: AgentState = await _graph.ainvoke(initial_state)
        return AgentResult(final_state)

    async def stream(
        self,
        user_id: str,
        task: str,
        vertical: str,
        context: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream state updates as the agent progresses through nodes.
        Yields dicts with {node, status, data} for each transition.
        """
        initial_state: AgentState = {
            "user_id": user_id,
            "task": task,
            "vertical": vertical,
            "context": context or {},
            "status": AgentStatus.PLANNING,
            "plan": [],
            "step_results": [],
            "final_answer": "",
            "error": "",
            "human_input": None,
            "requires_human": False,
        }
        async for node_name, state in _graph.astream(initial_state):
            yield {
                "node": node_name,
                "status": state.get("status"),
                "plan_steps": len(state.get("plan", [])),
                "completed_steps": len(state.get("step_results", [])),
                "final_answer": state.get("final_answer"),
                "error": state.get("error"),
                "requires_human": state.get("requires_human", False),
            }


# Module-level singleton
agent_orchestrator = AgentOrchestrator()
