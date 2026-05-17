"""Step executor — runs individual tool calls and handles errors/retries."""
from __future__ import annotations

import asyncio
from typing import Any

import structlog
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.platform.agent.tools.registry import get_tool

log = structlog.get_logger()


class StepResult:
    def __init__(
        self,
        step_index: int,
        tool: str,
        output: Any,
        error: str | None = None,
        retries: int = 0,
    ) -> None:
        self.step_index = step_index
        self.tool = tool
        self.output = output
        self.error = error
        self.retries = retries
        self.success = error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "tool": self.tool,
            "output": self.output,
            "error": self.error,
            "retries": self.retries,
            "success": self.success,
        }


async def execute_step(
    step: dict[str, Any],
    step_index: int,
    max_retries: int = 2,
) -> StepResult:
    """
    Execute a single plan step.
    Retries transient errors up to *max_retries* times with exponential backoff.
    """
    tool_name: str = step.get("tool", "")
    args: dict[str, Any] = step.get("args", {})

    # Virtual "respond" tool — no actual function call
    if tool_name == "respond":
        return StepResult(step_index, tool_name, args.get("content", ""))

    try:
        fn = get_tool(tool_name)
    except KeyError:
        return StepResult(step_index, tool_name, None, error=f"Unknown tool: {tool_name}")

    last_error: str = ""
    retries = 0
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_retries + 1),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        retry=retry_if_exception_type((httpx_exception_types())),
        reraise=False,
    ):
        with attempt:
            try:
                output = await fn(**args)
                return StepResult(step_index, tool_name, output, retries=retries)
            except Exception as exc:
                last_error = str(exc)
                retries += 1
                log.warning(
                    "executor.step_error",
                    tool=tool_name,
                    attempt=retries,
                    error=last_error,
                )
                raise

    return StepResult(step_index, tool_name, None, error=last_error, retries=retries)


def httpx_exception_types() -> tuple[type[Exception], ...]:
    """Return retryable exception types — imported lazily to avoid circular deps."""
    try:
        import httpx
        return (httpx.TransportError, httpx.TimeoutException)
    except ImportError:
        return (OSError, TimeoutError)


async def execute_plan(
    steps: list[dict[str, Any]],
    stop_on_failure: bool = False,
) -> list[StepResult]:
    """
    Execute a full plan sequentially.
    If *stop_on_failure* is True, abort after first failed step.
    """
    results: list[StepResult] = []
    for idx, step in enumerate(steps):
        result = await execute_step(step, idx)
        results.append(result)
        if not result.success and stop_on_failure:
            log.info("executor.stopping_on_failure", step=idx, tool=step.get("tool"))
            break
    return results
