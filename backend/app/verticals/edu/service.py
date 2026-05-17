"""EduStar business logic layer."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.platform.agent.orchestrator import agent_orchestrator
from app.platform.agent.tools.edu_tools import generate_quiz
from app.verticals.edu.course_factory import generate_course_from_topic
from app.verticals.edu.learning import (
    get_learning_progress,
    get_recommended_next_lesson,
    record_event,
)
from app.verticals.edu.schemas import (
    AgentTaskResponse,
    CourseCreate,
    CourseFactoryRequest,
    CourseSchema,
    GeneratedCourseOutline,
    LearnerEventCreate,
    LearnerEventSchema,
    LessonCreate,
    LessonSchema,
    QuizRequest,
    QuizResponse,
)

log = structlog.get_logger()


# ── Courses ───────────────────────────────────────────────────────────────────

async def create_course(
    session: AsyncSession,
    user_id: str,
    data: CourseCreate,
) -> CourseSchema:
    course_id = uuid4()
    result = await session.execute(
        text("""
            INSERT INTO courses
                (id, user_id, title, description, topic, difficulty,
                 duration_weeks, tags, is_published)
            VALUES
                (:id, :uid, :title, :desc, :topic, :diff, :weeks, :tags::text[], false)
            RETURNING id, user_id, title, description, topic, difficulty,
                      duration_weeks, tags, is_published, created_at, updated_at
        """),
        {
            "id": course_id, "uid": user_id,
            "title": data.title, "desc": data.description,
            "topic": data.topic, "diff": data.difficulty,
            "weeks": data.duration_weeks,
            "tags": "{" + ",".join(data.tags) + "}",
        },
    )
    await session.commit()
    return CourseSchema.model_validate(dict(result.mappings().one()))


async def list_courses(
    session: AsyncSession,
    user_id: str,
    limit: int = 20,
) -> list[CourseSchema]:
    result = await session.execute(
        text("""
            SELECT id, user_id, title, description, topic, difficulty,
                   duration_weeks, tags, is_published, created_at, updated_at
            FROM courses WHERE user_id = :uid
            ORDER BY created_at DESC LIMIT :limit
        """),
        {"uid": user_id, "limit": limit},
    )
    return [CourseSchema.model_validate(dict(r)) for r in result.mappings().all()]


async def get_course(
    session: AsyncSession,
    user_id: str,
    course_id: UUID,
) -> CourseSchema | None:
    result = await session.execute(
        text("""
            SELECT id, user_id, title, description, topic, difficulty,
                   duration_weeks, tags, is_published, created_at, updated_at
            FROM courses WHERE id = :id AND user_id = :uid
        """),
        {"id": course_id, "uid": user_id},
    )
    row = result.mappings().first()
    return CourseSchema.model_validate(dict(row)) if row else None


# ── Lessons ───────────────────────────────────────────────────────────────────

async def add_lesson(
    session: AsyncSession,
    course_id: UUID,
    data: LessonCreate,
) -> LessonSchema:
    lesson_id = uuid4()
    result = await session.execute(
        text("""
            INSERT INTO lessons (id, course_id, title, lesson_type, content, order_index, duration_minutes)
            VALUES (:id, :cid, :title, :ltype, :content, :order, :dur)
            RETURNING id, course_id, title, lesson_type, content, order_index, duration_minutes, created_at
        """),
        {
            "id": lesson_id, "cid": course_id,
            "title": data.title, "ltype": data.lesson_type,
            "content": data.content, "order": data.order_index,
            "dur": data.duration_minutes,
        },
    )
    await session.commit()
    return LessonSchema.model_validate(dict(result.mappings().one()))


async def list_lessons(
    session: AsyncSession,
    course_id: UUID,
) -> list[LessonSchema]:
    result = await session.execute(
        text("""
            SELECT id, course_id, title, lesson_type, content, order_index, duration_minutes, created_at
            FROM lessons WHERE course_id = :cid ORDER BY order_index ASC
        """),
        {"cid": course_id},
    )
    return [LessonSchema.model_validate(dict(r)) for r in result.mappings().all()]


# ── Course factory ────────────────────────────────────────────────────────────

async def factory_create_course(
    session: AsyncSession,
    user_id: str,
    request: CourseFactoryRequest,
) -> tuple[UUID, GeneratedCourseOutline]:
    return await generate_course_from_topic(session, user_id, request)


# ── Learner events ────────────────────────────────────────────────────────────

async def log_event(
    session: AsyncSession,
    user_id: str,
    data: LearnerEventCreate,
) -> LearnerEventSchema:
    event_id = await record_event(
        session, user_id, data.course_id, data.lesson_id, data.event_type, data.payload
    )
    result = await session.execute(
        text("""
            SELECT id, user_id, course_id, lesson_id, event_type, payload, created_at
            FROM learner_events WHERE id = :id
        """),
        {"id": event_id},
    )
    return LearnerEventSchema.model_validate(dict(result.mappings().one()))


async def get_progress(
    session: AsyncSession,
    user_id: str,
    course_id: UUID,
) -> dict[str, Any]:
    return await get_learning_progress(session, user_id, course_id)


async def next_lesson(
    session: AsyncSession,
    user_id: str,
    course_id: UUID,
) -> dict[str, Any] | None:
    return await get_recommended_next_lesson(session, user_id, course_id)


# ── Quiz ──────────────────────────────────────────────────────────────────────

async def create_quiz(request: QuizRequest) -> QuizResponse:
    questions = await generate_quiz(request.topic, request.num_questions, request.difficulty)
    return QuizResponse(topic=request.topic, questions=questions)


# ── Agent ─────────────────────────────────────────────────────────────────────

async def run_edu_agent(
    user_id: str,
    task: str,
    context: dict[str, Any] | None = None,
) -> AgentTaskResponse:
    result = await agent_orchestrator.run(user_id, task, vertical="edu", context=context)
    return AgentTaskResponse(
        status=result.status,
        answer=result.answer,
        step_results=result.step_results,
        error=result.error or None,
        requires_human=result.requires_human,
    )
