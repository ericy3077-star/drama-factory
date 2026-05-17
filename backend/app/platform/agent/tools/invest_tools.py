"""Investment-domain tools for AgentOS."""
from __future__ import annotations

import httpx
import structlog

log = structlog.get_logger()

_ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"


async def fetch_stock_price(symbol: str) -> dict[str, object]:
    """
    Fetch the latest quote for *symbol* from a public data source.
    Falls back to a structured error dict rather than raising so the
    agent can decide how to proceed.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Alpha Vantage GLOBAL_QUOTE (free tier, no key required for demo)
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                headers={"User-Agent": "drama-factory/0.1"},
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            return {
                "symbol": symbol,
                "price": meta.get("regularMarketPrice"),
                "currency": meta.get("currency"),
                "exchange": meta.get("exchangeName"),
                "market_state": meta.get("marketState"),
            }
    except Exception as exc:
        log.warning("fetch_stock_price.error", symbol=symbol, error=str(exc))
        return {"symbol": symbol, "error": str(exc)}


async def search_news(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """
    Search financial news via DuckDuckGo instant-answer API.
    Returns a list of {title, url, snippet} dicts.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                headers={"User-Agent": "drama-factory/0.1"},
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("RelatedTopics", [])[:max_results]:
                if "Text" in item:
                    results.append({
                        "title": item.get("Text", "")[:120],
                        "url": item.get("FirstURL", ""),
                        "snippet": item.get("Text", ""),
                    })
            return results
    except Exception as exc:
        log.warning("search_news.error", query=query, error=str(exc))
        return [{"error": str(exc)}]


async def get_financial_ratios(symbol: str) -> dict[str, object]:
    """
    Return key financial ratios for *symbol* scraped from Yahoo Finance summary.
    """
    try:
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
        params = {"modules": "summaryDetail,defaultKeyStatistics"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                url,
                params=params,
                headers={"User-Agent": "drama-factory/0.1"},
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("quoteSummary", {}).get("result", [{}])[0]
            summary = result.get("summaryDetail", {})
            stats = result.get("defaultKeyStatistics", {})
            return {
                "symbol": symbol,
                "pe_ratio": summary.get("trailingPE", {}).get("raw"),
                "forward_pe": summary.get("forwardPE", {}).get("raw"),
                "market_cap": summary.get("marketCap", {}).get("raw"),
                "dividend_yield": summary.get("dividendYield", {}).get("raw"),
                "52w_high": summary.get("fiftyTwoWeekHigh", {}).get("raw"),
                "52w_low": summary.get("fiftyTwoWeekLow", {}).get("raw"),
                "beta": summary.get("beta", {}).get("raw"),
                "eps_ttm": stats.get("trailingEps", {}).get("raw"),
                "profit_margin": stats.get("profitMargins", {}).get("raw"),
            }
    except Exception as exc:
        log.warning("get_financial_ratios.error", symbol=symbol, error=str(exc))
        return {"symbol": symbol, "error": str(exc)}


async def screen_stocks(
    min_pe: float | None = None,
    max_pe: float | None = None,
    min_market_cap: float | None = None,
    sector: str | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    """
    Placeholder stock screener — integrates with a real data vendor in production.
    Returns demo data so the agent pipeline remains functional during development.
    """
    # In production this would call a financial data API (e.g. Finviz, Polygon)
    demo_results: list[dict[str, object]] = [
        {"symbol": "AAPL", "name": "Apple Inc.", "pe": 28.5, "market_cap": 2.8e12, "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "pe": 32.1, "market_cap": 2.9e12, "sector": "Technology"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "pe": 24.7, "market_cap": 1.8e12, "sector": "Technology"},
        {"symbol": "JPM", "name": "JPMorgan Chase", "pe": 11.2, "market_cap": 5.5e11, "sector": "Financials"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "pe": 15.8, "market_cap": 3.9e11, "sector": "Healthcare"},
    ]

    filtered = demo_results
    if min_pe is not None:
        filtered = [s for s in filtered if isinstance(s["pe"], float) and s["pe"] >= min_pe]
    if max_pe is not None:
        filtered = [s for s in filtered if isinstance(s["pe"], float) and s["pe"] <= max_pe]
    if min_market_cap is not None:
        filtered = [s for s in filtered if isinstance(s["market_cap"], float) and s["market_cap"] >= min_market_cap]
    if sector:
        filtered = [s for s in filtered if s.get("sector", "").lower() == sector.lower()]

    return filtered[:limit]
