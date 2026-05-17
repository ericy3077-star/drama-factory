"""InvestMind information feed engine — aggregates and ranks financial news."""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup

from app.verticals.invest.schemas import FeedItemSchema

log = structlog.get_logger()

# RSS sources for financial news
_FEEDS: list[dict[str, str]] = [
    {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss"},
    {"name": "CNBC Top News", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"name": "Yahoo Finance", "url": "https://feeds.finance.yahoo.com/rss/2.0/headline"},
    {"name": "Seeking Alpha", "url": "https://seekingalpha.com/market_currents.xml"},
]


def _item_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


async def _fetch_rss(session: httpx.AsyncClient, source: dict[str, str]) -> list[FeedItemSchema]:
    """Fetch and parse a single RSS feed."""
    try:
        resp = await session.get(source["url"], timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml-xml")
        items = []
        for item in soup.find_all("item")[:20]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            desc = item.find("description")

            if not title or not link:
                continue

            url_str = link.get_text(strip=True)
            published: datetime | None = None
            if pub_date:
                try:
                    from email.utils import parsedate_to_datetime
                    published = parsedate_to_datetime(pub_date.get_text(strip=True))
                except Exception:
                    pass

            items.append(FeedItemSchema(
                id=_item_id(url_str),
                title=title.get_text(strip=True),
                url=url_str,
                source=source["name"],
                summary=desc.get_text(strip=True)[:300] if desc else None,
                published_at=published,
            ))
        return items
    except Exception as exc:
        log.warning("feed.fetch_error", source=source["name"], error=str(exc))
        return []


def _score_item(item: FeedItemSchema, tickers: list[str], topics: list[str]) -> float:
    """Score a feed item by relevance to user's watchlist."""
    text = f"{item.title} {item.summary or ''}".lower()
    score = 0.0

    for ticker in tickers:
        if ticker.lower() in text:
            score += 10.0

    for topic in topics:
        if topic.lower() in text:
            score += 3.0

    # Recency bonus (items from last 6 hours get +5)
    if item.published_at:
        age_hours = (datetime.now(timezone.utc) - item.published_at).total_seconds() / 3600
        if age_hours < 6:
            score += 5.0
        elif age_hours < 24:
            score += 2.0

    return score


async def fetch_personalised_feed(
    tickers: list[str],
    topics: list[str],
    limit: int = 20,
) -> list[FeedItemSchema]:
    """
    Fetch news from multiple RSS sources and rank by relevance to watchlist.
    Returns at most *limit* items sorted by relevance score.
    """
    async with httpx.AsyncClient(
        headers={"User-Agent": "drama-factory/0.1"},
        follow_redirects=True,
    ) as client:
        tasks = [_fetch_rss(client, source) for source in _FEEDS]
        results = await asyncio.gather(*tasks)

    all_items: list[FeedItemSchema] = []
    seen_ids: set[str] = set()
    for batch in results:
        for item in batch:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                all_items.append(item)

    # Sort by relevance
    scored = sorted(all_items, key=lambda i: _score_item(i, tickers, topics), reverse=True)
    return scored[:limit]
