"""EduStar course factory — AI-generated course curricula."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.platform.agent.tools.edu_tools import create_course_outline
from app.verticals.edu.schemas import CourseFactoryRequest, GeneratedCourseOutline

log = structlog.get_logger()


async def generate_course_from_topic(
    session: AsyncSession,
    user_id: str,
    request: CourseFactoryRequest,
) -> tuple[UUID, GeneratedCourseOutline]:
    """
    Use Claude to generate a complete course outline, then persist it to the DB.
    Returns (course_id, outline).
    """
    log.info("course_factory.generate", topic=request.topic, level=request.level)

    # Generate outline via Claude
    raw_outline = await create_course_outline(
        topic=request.topic,
        duration_weeks=request.duration_weeks,
        level=request.level,
    )

    # Enrich with learning goals if provided
    if request.learning_goals and "modules" in raw_outline:
        for i, module in enumerate(raw_outline["modules"]):
            if i < len(request.learning_goals):
                module.setdefault("custom_goal", request.learning_goals[i])

    # Estimate total hours (10h per week on average)
    estimated_hours = request.duration_weeks * 10

    outline = GeneratedCourseOutline(
        title=raw_outline.get("title", f"{request.topic} Course"),
        description=raw_outline.get("description", ""),
        target_audience=raw_outline.get("target_audience", request.level),
        modules=raw_outline.get("modules", []),
        estimated_hours=estimated_hours,
    )

    # Persist course record
    course_id = uuid4()
    tags = [request.topic, request.level]
    await session.execute(
        text("""
            INSERT INTO courses
                (id, user_id, title, description, topic, difficulty,
                 duration_weeks, tags, is_published, outline_json)
            VALUES
                (:id, :uid, :title, :desc, :topic, :diff,
                 :weeks, :tags::text[], false, :outline::jsonb)
        """),
        {
            "id": course_id, "uid": user_id,
            "title": outline.title, "desc": outline.description,
            "topic": request.topic, "diff": request.level,
            "weeks": request.duration_weeks,
            "tags": "{" + ",".join(tags) + "}",
            "outline": _json_safe(outline.modules),
        },
    )

    # Persist individual lessons from modules
    await _persist_lessons(session, course_id, outline.modules)
    await session.commit()

    log.info("course_factory.done", course_id=str(course_id), modules=len(outline.modules))
    return course_id, outline


async def _persist_lessons(
    session: AsyncSession,
    course_id: UUID,
    modules: list[dict[str, Any]],
) -> None:
    """Create lesson rows for each lesson in each module."""
    order = 0
    for module in modules:
        lessons = module.get("lessons", module.get("lesson_titles", []))
        for lesson_title in lessons:
            lesson_id = uuid4()
            title = lesson_title if isinstance(lesson_title, str) else str(lesson_title)
            await session.execute(
                text("""
                    INSERT INTO lessons (id, course_id, title, lesson_type, content, order_index, duration_minutes)
                    VALUES (:id, :cid, :title, 'article', '', :order, 15)
                """),
                {"id": lesson_id, "cid": course_id, "title": title[:200], "order": order},
            )
            order += 1


def _json_safe(obj: Any) -> str:
    import json
    return json.dumps(obj, default=str, ensure_ascii=False)
