"""Task planner — decomposes a high-level task into executable steps."""
from __future__ import annotations

import json
from typing import Any

import anthropic
import structlog

from app.config import settings
from app.platform.agent.tools.registry import list_tools

log = structlog.get_logger()


class TaskPlan:
    def __init__(self, steps: list[dict[str, Any]], reasoning: str) -> None:
        self.steps = steps          # [{tool, args, description}]
        self.reasoning = reasoning  # why this plan was chosen


async def plan_task(
    task: str,
    vertical: str,
    context: dict[str, Any] | None = None,
) -> TaskPlan:
    """
    Use Claude to decompose *task* into a sequence of tool calls.
    Returns a TaskPlan with ordered steps.
    """
    available_tools = list_tools(vertical)
    tools_desc = ", ".join(available_tools) if available_tools else "none"

    system = (
        "You are a task planner for an AI assistant platform. "
        "Given a user task and available tools, produce a step-by-step plan. "
        "Each step must specify: tool (from available list), args (dict), description. "
        "If no tool is needed, use tool='respond' and put the response in args.content. "
        "Respond ONLY with valid JSON: {reasoning: str, steps: [{tool, args, description}]}"
    )

    user_msg = f"Task: {task}\nVertical: {vertical}\nAvailable tools: {tools_desc}"
    if context:
        user_msg += f"\nContext: {json.dumps(context, default=str)}"

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = message.content[0].text  # type: ignore[union-attr]
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        parsed = json.loads(text[start:end])
        return TaskPlan(
            steps=parsed.get("steps", []),
            reasoning=parsed.get("reasoning", ""),
        )
    except Exception as exc:
        log.warning("plan_task.parse_error", error=str(exc), raw=text[:200])
        # Fallback: single respond step
        return TaskPlan(
            steps=[{"tool": "respond", "args": {"content": text}, "description": "Direct response"}],
            reasoning="Fallback to direct response due to parse error",
        )
