"""Avatar generation pipeline — orchestrates script → TTS → HeyGen video."""
from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.avatar import heygen

log = structlog.get_logger()


class PipelineStage(StrEnum):
    SCRIPT_READY = "script_ready"
    VIDEO_SUBMITTED = "video_submitted"
    VIDEO_PROCESSING = "video_processing"
    COMPLETED = "completed"
    FAILED = "failed"


async def run_generation_pipeline(
    session: AsyncSession,
    task_id: UUID,
    avatar_id: str,
    script: str,
    language: str = "zh",
    voice_id: str | None = None,
) -> None:
    """
    Long-running pipeline that:
    1. Submits video to HeyGen
    2. Polls until complete or failed
    3. Updates the generation_tasks table

    Designed to be run in a background worker (e.g., Celery task).
    """
    log.info("pipeline.start", task_id=str(task_id), avatar_id=avatar_id)

    async def _update_task(stage: str, heygen_video_id: str | None = None,
                           video_url: str | None = None, error: str | None = None) -> None:
        await session.execute(
            text("""
                UPDATE generation_tasks
                SET stage = :stage,
                    heygen_video_id = COALESCE(:vid, heygen_video_id),
                    video_url = COALESCE(:url, video_url),
                    error_message = :err,
                    updated_at = now()
                WHERE id = :task_id
            """),
            {"stage": stage, "vid": heygen_video_id, "url": video_url,
             "err": error, "task_id": task_id},
        )
        await session.commit()

    try:
        # Step 1: Submit to HeyGen
        result = await heygen.generate_video(avatar_id, script, voice_id, language)
        video_id = result.get("data", {}).get("video_id") or result.get("video_id")
        if not video_id:
            raise ValueError(f"HeyGen did not return a video_id: {result}")

        await _update_task(PipelineStage.VIDEO_SUBMITTED, heygen_video_id=video_id)

        # Step 2: Poll until done (max 10 minutes)
        max_polls = 60
        for _ in range(max_polls):
            await asyncio.sleep(10)
            status_data = await heygen.get_video_status(video_id)
            status = (
                status_data.get("data", {}).get("status")
                or status_data.get("status", "")
            ).lower()

            if status == "completed":
                video_url = (
                    status_data.get("data", {}).get("video_url")
                    or status_data.get("video_url", "")
                )
                await _update_task(PipelineStage.COMPLETED, video_url=video_url)
                log.info("pipeline.completed", task_id=str(task_id), video_url=video_url)
                return

            if status == "failed":
                raise RuntimeError(f"HeyGen reported failure: {status_data}")

            await _update_task(PipelineStage.VIDEO_PROCESSING)

        raise TimeoutError("Video generation did not complete within 10 minutes")

    except Exception as exc:
        log.error("pipeline.failed", task_id=str(task_id), error=str(exc))
        await _update_task(PipelineStage.FAILED, error=str(exc))
