"""Feed worker — periodically crawls financial news and caches results in Redis."""
from __future__ import annotations

import asyncio
import json
import signal
from typing import Any

import structlog

from app.config import settings
from app.database import get_sessionmaker, startup_database
from app.workers.queue import get_task_queue

log = structlog.get_logger()

_running = True

# Feed refresh interval in seconds
REFRESH_INTERVAL = 300  # 5 minutes

# Redis cache key prefix
FEED_CACHE_PREFIX = "feed:cache"
FEED_CACHE_TTL = 600  # 10 minutes


def _handle_shutdown(sig: int, frame: Any) -> None:
    global _running
    log.info("feed_worker.shutdown_signal", signal=sig)
    _running = False


async def refresh_feed_for_user(user_id: str, tickers: list[str], topics: list[str]) -> None:
    """Fetch fresh feed items and cache them in Redis."""
    from app.verticals.invest.feed import fetch_personalised_feed
    import redis.asyncio as aioredis

    try:
        items = await fetch_personalised_feed(tickers, topics, limit=50)
        serialised = json.dumps([item.model_dump(mode="json") for item in items], default=str)

        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        cache_key = f"{FEED_CACHE_PREFIX}:{user_id}"
        await redis_client.setex(cache_key, FEED_CACHE_TTL, serialised)
        await redis_client.aclose()

        log.info("feed_worker.refreshed", user_id=user_id, item_count=len(items))
    except Exception as exc:
        log.error("feed_worker.refresh_error", user_id=user_id, error=str(exc))


async def process_feed_task(payload: dict[str, Any]) -> None:
    """Handle a feed refresh task from the queue."""
    user_id = payload["user_id"]
    tickers = payload.get("tickers", [])
    topics = payload.get("topics", [])
    await refresh_feed_for_user(user_id, tickers, topics)


async def scheduled_bulk_refresh() -> None:
    """
    Periodically refresh feeds for active users.
    Fetches users with watchlists from the DB and enqueues feed refresh tasks.
    """
    session_factory = get_sessionmaker()
    from sqlalchemy import text

    async with session_factory() as session:
        result = await session.execute(
            text("""
                SELECT w.user_id, array_agg(w.symbol) AS tickers
                FROM watchlists w
                JOIN users u ON u.id = w.user_id AND u.is_active = true
                GROUP BY w.user_id
                LIMIT 500
            """)
        )
        rows = result.mappings().all()

    queue = get_task_queue()
    for row in rows:
        await queue.enqueue(
            task_type="feed_refresh",
            payload={
                "user_id": str(row["user_id"]),
                "tickers": list(row["tickers"] or []),
                "topics": [],
            },
            user_id=str(row["user_id"]),
            priority_override="tasks:low",
        )

    log.info("feed_worker.bulk_refresh_enqueued", users=len(rows))


async def run_worker() -> None:
    """
    Main feed worker loop.
    Handles on-demand feed refresh tasks AND periodic bulk refresh.
    """
    log.info("feed_worker.starting")
    await startup_database()
    queue = get_task_queue()

    # Schedule periodic bulk refresh
    async def _periodic_refresh() -> None:
        while _running:
            await asyncio.sleep(REFRESH_INTERVAL)
            if _running:
                await scheduled_bulk_refresh()

    refresh_task = asyncio.create_task(_periodic_refresh())

    # Main task processing loop
    while _running:
        task = await queue.dequeue(timeout=5)
        if task is None:
            continue

        if task.task_type != "feed_refresh":
            # Not our task — put it back
            await queue._r.lpush(task.priority, task.to_json())
            continue

        try:
            await process_feed_task(task.payload)
            await queue.complete(task.task_id)
        except Exception as exc:
            await queue.fail(task, error=str(exc))

    refresh_task.cancel()
    log.info("feed_worker.stopped")


def main() -> None:
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
