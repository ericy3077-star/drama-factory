"""AvatarOS — digital human engine facade."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.platform.avatar import heygen

log = structlog.get_logger()


class Avatar:
    def __init__(self, row: dict[str, Any]) -> None:
        self.id: UUID = row["id"]
        self.user_id: str = row["user_id"]
        self.name: str = row["name"]
        self.heygen_avatar_id: str = row.get("heygen_avatar_id", "")
        self.photo_url: str | None = row.get("photo_url")
        self.status: str = row.get("status", "pending")
        self.created_at = row.get("created_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "name": self.name,
            "heygen_avatar_id": self.heygen_avatar_id,
            "photo_url": self.photo_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GenerationTask:
    def __init__(self, row: dict[str, Any]) -> None:
        self.id: UUID = row["id"]
        self.avatar_id: UUID = row["avatar_id"]
        self.stage: str = row.get("stage", "pending")
        self.heygen_video_id: str | None = row.get("heygen_video_id")
        self.video_url: str | None = row.get("video_url")
        self.error_message: str | None = row.get("error_message")
        self.created_at = row.get("created_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "avatar_id": str(self.avatar_id),
            "stage": self.stage,
            "heygen_video_id": self.heygen_video_id,
            "video_url": self.video_url,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TaskStatus:
    def __init__(self, task: GenerationTask) -> None:
        self.task_id = task.id
        self.stage = task.stage
        self.video_url = task.video_url
        self.error = task.error_message

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "stage": self.stage,
            "video_url": self.video_url,
            "error": self.error,
        }


class AvatarEngine:
    """
    Facade for all digital-human operations.
    Persists avatar + task metadata in Postgres and delegates rendering to HeyGen.
    """

    async def create_avatar(
        self,
        session: AsyncSession,
        user_id: str,
        materials: dict[str, Any],
    ) -> Avatar:
        """
        Register a new avatar.
        *materials* must contain at least 'photo_url' and 'name'.
        Calls HeyGen to create a talking-photo avatar.
        """
        photo_url: str = materials["photo_url"]
        name: str = materials.get("name", "My Avatar")
        gender: str = materials.get("gender", "neutral")

        heygen_result = await heygen.create_avatar_from_photo(photo_url, name, gender)
        heygen_avatar_id = (
            heygen_result.get("data", {}).get("avatar_id")
            or heygen_result.get("avatar_id", "")
        )

        avatar_id = uuid4()
        result = await session.execute(
            text("""
                INSERT INTO avatars (id, user_id, name, photo_url, heygen_avatar_id, status)
                VALUES (:id, :uid, :name, :photo, :hid, 'active')
                RETURNING id, user_id, name, photo_url, heygen_avatar_id, status, created_at
            """),
            {"id": avatar_id, "uid": user_id, "name": name,
             "photo": photo_url, "hid": heygen_avatar_id},
        )
        await session.commit()
        return Avatar(dict(result.mappings().one()))

    async def generate_video(
        self,
        session: AsyncSession,
        avatar_id: UUID,
        script: str,
        language: str = "zh",
        voice_id: str | None = None,
    ) -> GenerationTask:
        """
        Queue a video generation task.
        Returns a GenerationTask immediately; the actual rendering runs in a worker.
        """
        # Look up the HeyGen avatar ID from our database
        row = await session.execute(
            text("SELECT heygen_avatar_id FROM avatars WHERE id = :id"),
            {"id": avatar_id},
        )
        avatar = row.mappings().first()
        if not avatar:
            raise ValueError(f"Avatar {avatar_id} not found")

        task_id = uuid4()
        result = await session.execute(
            text("""
                INSERT INTO generation_tasks
                    (id, avatar_id, script, language, voice_id, stage)
                VALUES (:id, :aid, :script, :lang, :vid, 'pending')
                RETURNING id, avatar_id, stage, heygen_video_id, video_url, error_message, created_at
            """),
            {"id": task_id, "aid": avatar_id, "script": script,
             "lang": language, "vid": voice_id},
        )
        await session.commit()
        task = GenerationTask(dict(result.mappings().one()))

        log.info("avatar.task_queued", task_id=str(task_id), avatar_id=str(avatar_id))
        return task

    async def get_task_status(
        self,
        session: AsyncSession,
        task_id: UUID,
    ) -> TaskStatus:
        """Fetch current status of a generation task."""
        result = await session.execute(
            text("""
                SELECT id, avatar_id, stage, heygen_video_id, video_url, error_message, created_at
                FROM generation_tasks WHERE id = :id
            """),
            {"id": task_id},
        )
        row = result.mappings().first()
        if not row:
            raise ValueError(f"Task {task_id} not found")
        return TaskStatus(GenerationTask(dict(row)))

    async def list_avatars(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[Avatar]:
        """List all active avatars for *user_id*."""
        result = await session.execute(
            text("""
                SELECT id, user_id, name, photo_url, heygen_avatar_id, status, created_at
                FROM avatars
                WHERE user_id = :uid AND status != 'deleted'
                ORDER BY created_at DESC
            """),
            {"uid": user_id},
        )
        return [Avatar(dict(r)) for r in result.mappings().all()]

    async def delete_avatar(
        self,
        session: AsyncSession,
        avatar_id: UUID,
        user_id: str,
    ) -> bool:
        """Soft-delete an avatar."""
        result = await session.execute(
            text("""
                UPDATE avatars SET status = 'deleted', updated_at = now()
                WHERE id = :id AND user_id = :uid AND status != 'deleted'
                RETURNING id
            """),
            {"id": avatar_id, "uid": user_id},
        )
        await session.commit()
        return result.rowcount > 0


# Module-level singleton
avatar_engine = AvatarEngine()
