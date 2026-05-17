"""EduStar adaptive learning engine."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.platform.memory.engine import memory_engine

log = structlog.get_logger()


async def record_event(
    session: AsyncSession,
    user_id: str,
    course_id: UUID,
    lesson_id: UUID | None,
    event_type: str,
    payload: dict[str, Any],
) -> UUID:
    """
    Record a learner event and optionally store it in MemoryOS
    so the agent can recall learning history.
    """
    from uuid import uuid4
    event_id = uuid4()

    await session.execute(
        text("""
            INSERT INTO learner_events (id, user_id, course_id, lesson_id, event_type, payload)
            VALUES (:id, :uid, :cid, :lid, :etype, :payload::jsonb)
        """),
        {
            "id": event_id, "uid": user_id, "cid": course_id,
            "lid": lesson_id, "etype": event_type,
            "payload": _json_safe(payload),
        },
    )
    await session.commit()

    # Store significant events in memory for agent context
    if event_type in ("completed", "quiz_submitted"):
        content = (
            f"User completed lesson '{payload.get('lesson_title', '')}' "
            f"in course '{payload.get('course_title', '')}'. "
            f"Score: {payload.get('score', 'N/A')}."
        )
        await memory_engine.store(
            session=session,
            user_id=user_id,
            content=content,
            content_type="learning_event",
            topic=payload.get("topic"),
            metadata={"course_id": str(course_id), "event_type": event_type},
        )

    return event_id


async def get_learning_progress(
    session: AsyncSession,
    user_id: str,
    course_id: UUID,
) -> dict[str, Any]:
    """
    Compute completion percentage and recent activity for a course.
    """
    total_result = await session.execute(
        text("SELECT COUNT(*) FROM lessons WHERE course_id = :cid"),
        {"cid": course_id},
    )
    total: int = total_result.scalar() or 0

    completed_result = await session.execute(
        text("""
            SELECT COUNT(DISTINCT lesson_id)
            FROM learner_events
            WHERE user_id = :uid AND course_id = :cid AND event_type = 'completed'
        """),
        {"uid": user_id, "cid": course_id},
    )
    completed: int = completed_result.scalar() or 0

    last_activity_result = await session.execute(
        text("""
            SELECT MAX(created_at)
            FROM learner_events
            WHERE user_id = :uid AND course_id = :cid
        """),
        {"uid": user_id, "cid": course_id},
    )
    last_activity = last_activity_result.scalar()

    return {
        "course_id": str(course_id),
        "total_lessons": total,
        "completed_lessons": completed,
        "completion_pct": round(completed / total * 100, 1) if total else 0.0,
        "last_activity": last_activity.isoformat() if last_activity else None,
    }


async def get_recommended_next_lesson(
    session: AsyncSession,
    user_id: str,
    course_id: UUID,
) -> dict[str, Any] | None:
    """Return the next incomplete lesson for the user in a course."""
    result = await session.execute(
        text("""
            SELECT l.id, l.title, l.lesson_type, l.order_index, l.duration_minutes
            FROM lessons l
            WHERE l.course_id = :cid
              AND l.id NOT IN (
                  SELECT DISTINCT lesson_id
                  FROM learner_events
                  WHERE user_id = :uid AND course_id = :cid AND event_type = 'completed'
                    AND lesson_id IS NOT NULL
              )
            ORDER BY l.order_index ASC
            LIMIT 1
        """),
        {"cid": course_id, "uid": user_id},
    )
    row = result.mappings().first()
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "title": row["title"],
        "lesson_type": row["lesson_type"],
        "order_index": row["order_index"],
        "duration_minutes": row["duration_minutes"],
    }


def _json_safe(obj: Any) -> str:
    import json
    return json.dumps(obj, default=str, ensure_ascii=False)
