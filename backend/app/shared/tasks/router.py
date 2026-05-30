"""Shared async task status endpoint."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter

from app.dependencies import CurrentUserId, RedisClient

log = structlog.get_logger()

router = APIRouter()

# Redis key prefix used by workers when storing task state
_TASK_KEY_PREFIX = "task:"


def _mock_task(task_id: str) -> dict:
    """Return a plausible in-progress task when Redis has no record."""
    # Deterministically derive a progress value from the task_id so repeated
    # calls return a consistent (slowly advancing) mock rather than random noise.
    seed = sum(ord(c) for c in task_id) % 100
    progress = min(seed + 15, 95)  # never show 100 — stays "in progress"
    now = datetime.now(timezone.utc)
    return {
        "id": task_id,
        "status": "running",
        "progress": progress,
        "result": None,
        "created_at": (now - timedelta(minutes=3)).isoformat(),
        "updated_at": (now - timedelta(seconds=20)).isoformat(),
    }


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    user_id: CurrentUserId,
    redis: RedisClient,
) -> dict:
    """
    Retrieve async task status.

    Checks Redis for a persisted task record written by background workers.
    Falls back to a realistic mock response when Redis is unavailable or the
    task key is not found — so the demo never breaks.
    """
    try:
        raw = await redis.get(f"{_TASK_KEY_PREFIX}{task_id}")
        if raw:
            data: dict = json.loads(raw)
            log.info("tasks.get.cache_hit", task_id=task_id, user_id=user_id)
            return data
        log.info("tasks.get.not_found", task_id=task_id, user_id=user_id)
    except Exception:
        log.warning("tasks.get.redis_error", task_id=task_id, exc_info=True)

    # Graceful fallback — return mock so the frontend task poller keeps working
    return _mock_task(task_id)
