"""Central tool registry — maps tool names to callables for AgentOS."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from app.platform.agent.tools.invest_tools import (
    fetch_stock_price,
    search_news,
    get_financial_ratios,
    screen_stocks,
)
from app.platform.agent.tools.edu_tools import (
    search_learning_resources,
    generate_quiz,
    summarize_document,
    create_course_outline,
)

ToolFn = Callable[..., Coroutine[Any, Any, Any]]

_REGISTRY: dict[str, ToolFn] = {
    # Investment tools
    "fetch_stock_price": fetch_stock_price,
    "search_news": search_news,
    "get_financial_ratios": get_financial_ratios,
    "screen_stocks": screen_stocks,
    # Education tools
    "search_learning_resources": search_learning_resources,
    "generate_quiz": generate_quiz,
    "summarize_document": summarize_document,
    "create_course_outline": create_course_outline,
}

# Per-vertical tool subsets
VERTICAL_TOOLS: dict[str, list[str]] = {
    "invest": ["fetch_stock_price", "search_news", "get_financial_ratios", "screen_stocks"],
    "edu": ["search_learning_resources", "generate_quiz", "summarize_document", "create_course_outline"],
}


def get_tool(name: str) -> ToolFn:
    if name not in _REGISTRY:
        raise KeyError(f"Tool '{name}' is not registered")
    return _REGISTRY[name]


def get_tools_for_vertical(vertical: str) -> dict[str, ToolFn]:
    names = VERTICAL_TOOLS.get(vertical, [])
    return {n: _REGISTRY[n] for n in names if n in _REGISTRY}


def list_tools(vertical: str | None = None) -> list[str]:
    if vertical:
        return VERTICAL_TOOLS.get(vertical, [])
    return list(_REGISTRY.keys())
