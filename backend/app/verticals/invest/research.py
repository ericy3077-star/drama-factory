"""InvestMind research workbench — AI-driven stock analysis."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import anthropic
import structlog

from app.config import settings
from app.platform.agent.tools.invest_tools import (
    fetch_stock_price,
    get_financial_ratios,
    search_news,
)
from app.verticals.invest.schemas import ResearchReport

log = structlog.get_logger()


async def generate_research_report(
    symbol: str,
    depth: str = "standard",
    include_news: bool = True,
    include_ratios: bool = True,
) -> ResearchReport:
    """
    Generate a comprehensive research report for *symbol*.

    Depth modes:
    - quick    → price + 3-sentence summary (Haiku)
    - standard → price + ratios + news + analysis (Haiku)
    - deep     → full fundamental + sentiment analysis (Sonnet)
    """
    log.info("research.start", symbol=symbol, depth=depth)

    # Gather data concurrently
    tasks: list[Any] = [fetch_stock_price(symbol)]
    if include_ratios:
        tasks.append(get_financial_ratios(symbol))
    if include_news:
        tasks.append(search_news(f"{symbol} stock news", max_results=5))

    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    price_data: dict[str, Any] = gathered[0] if not isinstance(gathered[0], Exception) else {}
    ratios_data: dict[str, Any] = {}
    news_data: list[dict[str, str]] = []

    idx = 1
    if include_ratios:
        ratios_data = gathered[idx] if not isinstance(gathered[idx], Exception) else {}
        idx += 1
    if include_news:
        raw_news = gathered[idx] if not isinstance(gathered[idx], Exception) else []
        news_data = [n for n in raw_news if isinstance(n, dict) and "error" not in n]

    # Build context for Claude
    context_parts = [f"Stock: {symbol}"]
    if price_data.get("price"):
        context_parts.append(f"Current price: {price_data['price']} {price_data.get('currency', '')}")
    if ratios_data:
        context_parts.append(f"P/E: {ratios_data.get('pe_ratio')}")
        context_parts.append(f"Market cap: {ratios_data.get('market_cap')}")
        context_parts.append(f"Beta: {ratios_data.get('beta')}")
    if news_data:
        headlines = [n.get("title", "") for n in news_data[:3]]
        context_parts.append("Recent headlines: " + " | ".join(headlines))

    context = "\n".join(context_parts)

    model = "claude-sonnet-4-5" if depth == "deep" else "claude-haiku-4-5"
    max_tokens = 2000 if depth == "deep" else 800

    prompt = (
        f"Based on the following data, write a concise investment research summary for {symbol}.\n\n"
        f"{context}\n\n"
        f"Include:\n"
        f"1. Company overview (1-2 sentences)\n"
        f"2. Key investment thesis (2-3 sentences)\n"
        f"3. Top 3 risks\n"
        f"4. Top 3 opportunities\n"
        f"5. Overall sentiment (bullish/neutral/bearish)\n\n"
        f"Be factual, concise, and professional. "
        f"Respond as JSON: {{summary, company_name, risks (array), opportunities (array), sentiment}}"
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    text = message.content[0].text  # type: ignore[union-attr]
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        parsed = json.loads(text[start:end])
    except Exception:
        parsed = {"summary": text, "company_name": symbol, "risks": [], "opportunities": []}

    return ResearchReport(
        symbol=symbol,
        company_name=parsed.get("company_name"),
        summary=parsed.get("summary", ""),
        current_price=price_data.get("price"),
        key_ratios={k: v for k, v in ratios_data.items() if v is not None and k != "symbol"},
        recent_news=news_data,
        risks=parsed.get("risks", []),
        opportunities=parsed.get("opportunities", []),
        generated_at=datetime.now(timezone.utc),
    )
