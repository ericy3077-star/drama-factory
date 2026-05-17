"""Avatar generation worker — processes video generation tasks from the queue."""
from __future__ import annotations

import asyncio
import signal
import sys
from typing import Any
from uuid import UUID

import structlog

from app.database import get_sessionmaker, startup_database
from app.platform.avatar.pipeline import run_generation_pipeline
from app.workers.queue import TaskQueue, get_task_queue

log = structlog.get_logger()

_running = True


def _handle_shutdown(sig: int, frame: Any) -> None:
    global _running
    log.info("avatar_worker.shutdown_signal", signal=sig)
    _running = False


async def process_task(queue: TaskQueue, raw_task: Any) -> None:
    """Process a single avatar generation task."""
    task = raw_task
    payload = task.payload

    try:
        task_id = UUID(payload["task_id"])
        avatar_id = payload["avatar_id"]
        script = payload["script"]
        language = payload.get("language", "zh")
        voice_id = payload.get("voice_id")

        log.info(
            "avatar_worker.processing",
            task_id=str(task_id),
            avatar_id=avatar_id,
        )

        session_factory = get_sessionmaker()
        async with session_factory() as session:
            await run_generation_pipeline(
                session=session,
                task_id=task_id,
                avatar_id=avatar_id,
                script=script,
                language=language,
                voice_id=voice_id,
            )

        await queue.complete(task.task_id, result={"task_id": str(task_id), "status": "completed"})

    except Exception as exc:
        log.error("avatar_worker.task_error", task_id=task.task_id, error=str(exc))
        await queue.fail(task, error=str(exc))


async def run_worker(concurrency: int = 2) -> None:
    """
    Main worker loop.
    Processes avatar generation tasks from the queue with *concurrency* parallel slots.
    """
    log.info("avatar_worker.starting", concurrency=concurrency)
    await startup_database()
    queue = get_task_queue()

    semaphore = asyncio.Semaphore(concurrency)
    active_tasks: set[asyncio.Task[None]] = set()

    while _running:
        task = await queue.dequeue(timeout=5)
        if task is None:
            continue

        if task.task_type != "avatar_generate":
            # Not our task type — re-enqueue for other workers
            import json
            await queue._r.lpush(task.priority, task.to_json())
            continue

        async def _run_with_semaphore(t: Any) -> None:
            async with semaphore:
                await process_task(queue, t)

        t = asyncio.create_task(_run_with_semaphore(task))
        active_tasks.add(t)
        t.add_done_callback(active_tasks.discard)

    # Graceful shutdown: wait for active tasks
    if active_tasks:
        log.info("avatar_worker.draining", active=len(active_tasks))
        await asyncio.gather(*active_tasks, return_exceptions=True)

    log.info("avatar_worker.stopped")


def main() -> None:
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
