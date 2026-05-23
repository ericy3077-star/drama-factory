"""InvestMind — memory-augmented agentic streaming chat."""
from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator
from typing import Any

import anthropic
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.platform.memory.engine import memory_engine
from app.platform.agent.tools.invest_tools import (
    fetch_stock_price,
    get_financial_ratios,
    screen_stocks,
    search_news,
)

log = structlog.get_logger()

# ── Tool definitions (Claude tool_use schema) ─────────────────────────────────

INVEST_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_financial_news",
        "description": (
            "Search for recent financial news, market events, and analyst commentary "
            "about a company, sector, macro theme, or ticker symbol."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query in Chinese or English"},
                "max_results": {"type": "integer", "default": 5, "description": "Number of results"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_stock_data",
        "description": (
            "Fetch real-time stock price and key financial ratios (P/E, P/B, market cap, "
            "52-week range, EPS, beta) for a given ticker symbol."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Ticker symbol, e.g. AAPL, 600519.SS (A-share)",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "recall_memories",
        "description": (
            "Search the user's personal research knowledge base for past insights, notes, "
            "analysis, and conclusions. Always call this first when discussing a stock or sector "
            "the user may have researched before."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for in memory"},
                "top_k": {"type": "integer", "default": 5, "description": "Max results to return"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_insight",
        "description": (
            "Permanently save an important investment insight, research conclusion, or "
            "investment thesis to the user's knowledge base. Use this proactively when "
            "the conversation produces a valuable conclusion."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The insight or conclusion to save"},
                "topic": {
                    "type": "string",
                    "description": "Ticker symbol or theme this relates to, e.g. '600519' or '消费行业'",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "screen_stocks",
        "description": "Filter stocks by financial criteria: P/E range, market cap, or sector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "min_pe": {"type": "number", "description": "Minimum P/E ratio"},
                "max_pe": {"type": "number", "description": "Maximum P/E ratio"},
                "min_market_cap": {"type": "number", "description": "Min market cap in USD"},
                "sector": {"type": "string", "description": "Sector name, e.g. Technology, Financials"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
]

_SYSTEM_TEMPLATE = """\
你是 InvestMind，用户专属的 AI 投资研究助手。

你的核心能力：
- 搜索最新财经新闻（search_financial_news）
- 获取个股实时行情与财务指标（get_stock_data）
- 调取用户历史研究记忆（recall_memories）—— **每次讨论具体股票/板块前必须先调用**
- 将重要结论保存到用户永久知识库（save_insight）—— 有价值的洞察主动保存
- 按条件筛选股票（screen_stocks）

工作原则：
- 数据驱动，不做无依据的价格预测
- 投资建议仅供参考，不构成投资意见，重要分析结尾加免责声明
- 优先利用用户历史记录，避免重复劳动，形成知识复利

{memory_context}\
"""


# ── Tool executor ─────────────────────────────────────────────────────────────

async def _execute_tool(
    name: str,
    tool_input: dict[str, Any],
    session: AsyncSession,
    user_id: str,
) -> Any:
    if name == "search_financial_news":
        return await search_news(tool_input["query"], tool_input.get("max_results", 5))

    if name == "get_stock_data":
        symbol = tool_input["symbol"]
        price, ratios = await _gather_stock(symbol)
        return {**price, **{k: v for k, v in ratios.items() if k != "symbol"}}

    if name == "recall_memories":
        mems = await memory_engine.recall(
            session, user_id, tool_input["query"], top_k=tool_input.get("top_k", 5)
        )
        return [m.to_dict() for m in mems]

    if name == "save_insight":
        await memory_engine.store(
            session,
            user_id,
            tool_input["content"],
            content_type="insight",
            topic=tool_input.get("topic"),
        )
        return {"saved": True, "preview": tool_input["content"][:120]}

    if name == "screen_stocks":
        return await screen_stocks(**tool_input)

    return {"error": f"unknown tool: {name}"}


async def _gather_stock(symbol: str) -> tuple[dict[str, Any], dict[str, Any]]:
    import asyncio
    price, ratios = await asyncio.gather(
        fetch_stock_price(symbol),
        get_financial_ratios(symbol),
        return_exceptions=True,
    )
    return (
        price if isinstance(price, dict) else {"symbol": symbol, "error": str(price)},
        ratios if isinstance(ratios, dict) else {},
    )


# ── SSE helpers ───────────────────────────────────────────────────────────────

def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


# ── Core streaming generator ──────────────────────────────────────────────────

async def chat_stream(
    session: AsyncSession,
    user_id: str,
    message: str,
    history: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """
    Memory-augmented agentic chat loop.

    1. Recall relevant memories → embed in system prompt
    2. Stream Claude response; visualize tool calls in real time
    3. Execute tools, feed results back, continue streaming (full agentic loop)
    4. After completion, auto-save conversation summary to memory
    """
    # Step 1: pre-emptive memory recall
    memories = await memory_engine.recall(session, user_id, message, top_k=5)
    memory_context = ""
    if memories:
        lines = [f"- [{m.topic or '通用'}] {m.content[:300]}" for m in memories]
        memory_context = "【自动召回的历史研究记录，供参考】\n" + "\n".join(lines) + "\n"

    system = _SYSTEM_TEMPLATE.format(memory_context=memory_context)

    # Build conversation history (last 20 turns)
    msgs: list[dict[str, Any]] = [
        {"role": h["role"], "content": h["content"]}
        for h in history[-20:]
    ]
    msgs.append({"role": "user", "content": message})

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    full_response = ""

    # Agentic loop — keep going until stop_reason != "tool_use"
    while True:
        pending_tools: dict[str, dict[str, Any]] = {}
        current_tool_id: str | None = None

        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            tools=INVEST_TOOLS,  # type: ignore[arg-type]
            messages=msgs,
        ) as stream:
            async for event in stream:
                etype = event.type

                if etype == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool_id = block.id
                        pending_tools[block.id] = {
                            "name": block.name,
                            "input_str": "",
                            "input": {},
                            "start_time": time.monotonic(),
                        }
                        yield _sse({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": {},
                            "status": "running",
                        })

                elif etype == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        full_response += delta.text
                        yield _sse({"type": "content_delta", "delta": {"text": delta.text}})
                    elif delta.type == "input_json_delta" and current_tool_id:
                        pending_tools[current_tool_id]["input_str"] += delta.partial_json

                elif etype == "content_block_stop":
                    if current_tool_id and current_tool_id in pending_tools:
                        try:
                            pending_tools[current_tool_id]["input"] = json.loads(
                                pending_tools[current_tool_id]["input_str"]
                            )
                        except Exception:
                            pass
                        current_tool_id = None

            final_msg = await stream.get_final_message()

        if final_msg.stop_reason != "tool_use":
            break

        # Reconstruct assistant content for conversation history
        assistant_content: list[dict[str, Any]] = []
        for block in final_msg.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        msgs.append({"role": "assistant", "content": assistant_content})

        # Execute tools and stream results
        tool_results: list[dict[str, Any]] = []
        for tool_id, info in pending_tools.items():
            try:
                result = await _execute_tool(info["name"], info["input"], session, user_id)
                status = "completed"
            except Exception as exc:
                result = {"error": str(exc)}
                status = "failed"
                log.error("chat.tool_failed", tool=info["name"], error=str(exc))

            duration_ms = int((time.monotonic() - info["start_time"]) * 1000)
            yield _sse({
                "type": "tool_use",
                "id": tool_id,
                "name": info["name"],
                "input": info["input"],
                "status": status,
                "output": result,
                "duration_ms": duration_ms,
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        msgs.append({"role": "user", "content": tool_results})

    # Step 4: auto-save conversation to memory
    if full_response and len(full_response) > 80:
        summary = f"Q: {message[:200]}\nA: {full_response[:600]}"
        await memory_engine.store(
            session, user_id, summary, content_type="conversation"
        )
        log.info("chat.memory_saved", user_id=user_id, length=len(summary))

    yield "data: [DONE]\n\n"
