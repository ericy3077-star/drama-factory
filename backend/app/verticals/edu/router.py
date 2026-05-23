"""EduStar API routes."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.dependencies import CurrentUserId, DBSession
from app.verticals.edu import service
from app.verticals.edu.chat import chat_stream
from app.verticals.edu.schemas import (
    AgentTaskRequest,
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

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[dict[str, str]] = Field(default_factory=list)


# ── Chat (memory-augmented agentic SSE) ──────────────────────────────────────

@router.post("/chat")
async def edu_chat(
    request: ChatRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> StreamingResponse:
    return StreamingResponse(
        chat_stream(session, user_id, request.message, request.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Courses ───────────────────────────────────────────────────────────────────

@router.get("/courses", response_model=list[CourseSchema])
async def list_courses(
    user_id: CurrentUserId,
    session: DBSession,
    limit: int = 20,
) -> list[CourseSchema]:
    return await service.list_courses(session, user_id, limit)


@router.post("/courses", response_model=CourseSchema, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    user_id: CurrentUserId,
    session: DBSession,
) -> CourseSchema:
    return await service.create_course(session, user_id, data)


@router.get("/courses/{course_id}", response_model=CourseSchema)
async def get_course(
    course_id: UUID,
    user_id: CurrentUserId,
    session: DBSession,
) -> CourseSchema:
    course = await service.get_course(session, user_id, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


# ── Lessons ───────────────────────────────────────────────────────────────────

@router.get("/courses/{course_id}/lessons", response_model=list[LessonSchema])
async def list_lessons(
    course_id: UUID,
    user_id: CurrentUserId,
    session: DBSession,
) -> list[LessonSchema]:
    return await service.list_lessons(session, course_id)


@router.post("/courses/{course_id}/lessons", response_model=LessonSchema, status_code=status.HTTP_201_CREATED)
async def add_lesson(
    course_id: UUID,
    data: LessonCreate,
    user_id: CurrentUserId,
    session: DBSession,
) -> LessonSchema:
    return await service.add_lesson(session, course_id, data)


# ── Course factory (AI-generated) ─────────────────────────────────────────────

@router.post("/factory", status_code=status.HTTP_201_CREATED)
async def factory_create(
    request: CourseFactoryRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> dict[str, Any]:
    course_id, outline = await service.factory_create_course(session, user_id, request)
    return {
        "course_id": str(course_id),
        "outline": outline.model_dump(),
    }


# ── Learning progress ─────────────────────────────────────────────────────────

@router.post("/events", response_model=LearnerEventSchema, status_code=status.HTTP_201_CREATED)
async def log_event(
    data: LearnerEventCreate,
    user_id: CurrentUserId,
    session: DBSession,
) -> LearnerEventSchema:
    return await service.log_event(session, user_id, data)


@router.get("/courses/{course_id}/progress")
async def get_progress(
    course_id: UUID,
    user_id: CurrentUserId,
    session: DBSession,
) -> dict[str, Any]:
    return await service.get_progress(session, user_id, course_id)


@router.get("/courses/{course_id}/next-lesson")
async def next_lesson(
    course_id: UUID,
    user_id: CurrentUserId,
    session: DBSession,
) -> dict[str, Any] | None:
    return await service.next_lesson(session, user_id, course_id)


# ── Quiz ──────────────────────────────────────────────────────────────────────

@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz(
    request: QuizRequest,
    user_id: CurrentUserId,
) -> QuizResponse:
    return await service.create_quiz(request)


# ── Agent ─────────────────────────────────────────────────────────────────────

@router.post("/agent", response_model=AgentTaskResponse)
async def run_agent(
    request: AgentTaskRequest,
    user_id: CurrentUserId,
) -> AgentTaskResponse:
    return await service.run_edu_agent(user_id, request.task, request.context)


@router.post("/agent/stream")
async def stream_agent(
    request: AgentTaskRequest,
    user_id: CurrentUserId,
) -> StreamingResponse:
    import json
    from app.platform.agent.orchestrator import agent_orchestrator

    async def event_stream():  # type: ignore[return]
        async for update in agent_orchestrator.stream(user_id, request.task, "edu", request.context):
            yield f"data: {json.dumps(update)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
