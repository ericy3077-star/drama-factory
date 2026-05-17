"""Redis-backed task queue with priority support, status tracking, and retry logic."""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.config import settings

log = structlog.get_logger()

# Queue name constants
QUEUE_HIGH = "tasks:high"     # paid users
QUEUE_NORMAL = "tasks:normal" # free users
QUEUE_LOW = "tasks:low"       # background jobs

# Status key prefix:  task:{task_id}:status
STATUS_PREFIX = "task"

# Max retry attempts before marking as dead
MAX_RETRIES = 3

# Exponential backoff base (seconds)
BACKOFF_BASE = 2.0


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD = "dead"


class Task:
    def __init__(
        self,
        task_type: str,
        payload: dict[str, Any],
        user_id: str,
        priority: str = QUEUE_NORMAL,
        task_id: str | None = None,
        retry_count: int = 0,
    ) -> None:
        self.task_id = task_id or str(uuid.uuid4())
        self.task_type = task_type
        self.payload = payload
        self.user_id = user_id
        self.priority = priority
        self.retry_count = retry_count
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_json(self) -> str:
        return json.dumps({
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "user_id": self.user_id,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
        })

    @classmethod
    def from_json(cls, data: str | bytes) -> "Task":
        d = json.loads(data)
        return cls(
            task_type=d["task_type"],
            payload=d["payload"],
            user_id=d["user_id"],
            priority=d.get("priority", QUEUE_NORMAL),
            task_id=d["task_id"],
            retry_count=d.get("retry_count", 0),
        )


class TaskQueue:
    """
    Redis-backed priority task queue.

    Priority queues (highest to lowest):
      tasks:high   → paid/enterprise users
      tasks:normal → free users
      tasks:low    → background/maintenance jobs

    Each task's state is stored in a Redis hash at task:{task_id}.
    TTL for completed/failed task metadata: 24 hours.
    """

    def __init__(self, redis: aioredis.Redis) -> None:
        self._r = redis

    async def enqueue(
        self,
        task_type: str,
        payload: dict[str, Any],
        user_id: str,
        is_premium: bool = False,
        priority_override: str | None = None,
    ) -> str:
        """
        Add a task to the appropriate priority queue.
        Returns the task_id.
        """
        queue = priority_override or (QUEUE_HIGH if is_premium else QUEUE_NORMAL)
        task = Task(task_type=task_type, payload=payload, user_id=user_id, priority=queue)

        pipe = self._r.pipeline()
        pipe.lpush(queue, task.to_json())
        pipe.hset(
            f"{STATUS_PREFIX}:{task.task_id}",
            mapping={
                "status": TaskStatus.QUEUED,
                "task_type": task_type,
                "user_id": user_id,
                "retry_count": 0,
                "created_at": task.created_at,
                "updated_at": task.created_at,
            },
        )
        pipe.expire(f"{STATUS_PREFIX}:{task.task_id}", 86400)  # 24h TTL
        await pipe.execute()

        log.info("queue.enqueued", task_id=task.task_id, task_type=task_type, queue=queue)
        return task.task_id

    async def dequeue(self, timeout: int = 5) -> Task | None:
        """
        Block-pop from queues in priority order.
        Returns None on timeout.
        """
        result = await self._r.blpop(
            [QUEUE_HIGH, QUEUE_NORMAL, QUEUE_LOW],
            timeout=timeout,
        )
        if result is None:
            return None
        _queue_name, raw = result
        task = Task.from_json(raw)
        await self._set_status(task.task_id, TaskStatus.RUNNING)
        log.info("queue.dequeued", task_id=task.task_id, task_type=task.task_type)
        return task

    async def complete(self, task_id: str, result: Any = None) -> None:
        """Mark a task as successfully completed."""
        pipe = self._r.pipeline()
        pipe.hset(
            f"{STATUS_PREFIX}:{task_id}",
            mapping={
                "status": TaskStatus.DONE,
                "result": json.dumps(result, default=str) if result is not None else "",
                "updated_at": _now_iso(),
            },
        )
        pipe.expire(f"{STATUS_PREFIX}:{task_id}", 86400)
        await pipe.execute()
        log.info("queue.completed", task_id=task_id)

    async def fail(self, task: Task, error: str) -> None:
        """
        Handle a failed task.
        If under MAX_RETRIES, re-enqueue with exponential backoff delay.
        Otherwise mark as DEAD.
        """
        if task.retry_count < MAX_RETRIES:
            delay = BACKOFF_BASE ** task.retry_count
            log.warning(
                "queue.retrying",
                task_id=task.task_id,
                retry=task.retry_count + 1,
                delay=delay,
            )
            await self._set_status(task.task_id, TaskStatus.RETRYING, error=error)
            await asyncio.sleep(delay)

            # Re-enqueue with incremented retry count
            task.retry_count += 1
            pipe = self._r.pipeline()
            pipe.lpush(task.priority, task.to_json())
            pipe.hset(
                f"{STATUS_PREFIX}:{task.task_id}",
                mapping={"retry_count": task.retry_count, "updated_at": _now_iso()},
            )
            await pipe.execute()
        else:
            log.error("queue.dead", task_id=task.task_id, error=error)
            await self._set_status(task.task_id, TaskStatus.DEAD, error=error)

    async def get_status(self, task_id: str) -> dict[str, Any] | None:
        """Fetch the full status dict for a task."""
        data = await self._r.hgetall(f"{STATUS_PREFIX}:{task_id}")
        return dict(data) if data else None

    async def queue_lengths(self) -> dict[str, int]:
        """Return current length of each priority queue."""
        high, normal, low = await asyncio.gather(
            self._r.llen(QUEUE_HIGH),
            self._r.llen(QUEUE_NORMAL),
            self._r.llen(QUEUE_LOW),
        )
        return {"high": high, "normal": normal, "low": low}

    async def _set_status(
        self,
        task_id: str,
        status: TaskStatus,
        error: str | None = None,
    ) -> None:
        fields: dict[str, str] = {"status": status, "updated_at": _now_iso()}
        if error:
            fields["error"] = error
        await self._r.hset(f"{STATUS_PREFIX}:{task_id}", mapping=fields)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Singleton factory ──────────────────────────────────────────────────────────

_queue_instance: TaskQueue | None = None


def get_task_queue() -> TaskQueue:
    global _queue_instance
    if _queue_instance is None:
        redis_client = aioredis.from_url(
            settings.redis_url,
            max_connections=20,
            decode_responses=True,
        )
        _queue_instance = TaskQueue(redis_client)
    return _queue_instance
