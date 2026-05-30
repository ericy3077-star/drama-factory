"""EduStar API routes."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.dependencies import CurrentUserId, DBSession
from app.verticals.edu import service
from app.verticals.edu.chat import chat_stream
from app.verticals.edu.schemas import (
    AgentTaskRequest,
    AgentTaskResponse,
    AvatarCreate,
    AvatarStatus,
    CourseCreate,
    CourseFactoryRequest,
    CourseSchema,
    DigitalAvatar,
    GeneratedCourseOutline,
    LearnerEventCreate,
    LearnerEventSchema,
    LessonCreate,
    LessonSchema,
    QuizRequest,
    QuizResponse,
    VideoGenerateRequest,
    VideoJob,
    VideoJobStatus,
)

log = structlog.get_logger()

# ── In-memory stores (demo / pre-DB) ─────────────────────────────────────────

_AVATARS: dict[str, DigitalAvatar] = {
    "avatar-001": DigitalAvatar(
        id="avatar-001",
        name="李明博士",
        description="专业金融分析讲师，擅长用通俗易懂的方式讲解复杂概念",
        status=AvatarStatus.READY,
        thumbnail_url="https://api.dicebear.com/7.x/avataaars/svg?seed=liming",
        created_at=datetime.now(timezone.utc) - timedelta(days=14),
    ),
    "avatar-002": DigitalAvatar(
        id="avatar-002",
        name="陈教授",
        description="资深编程教育专家，拥有15年高校教学经验",
        status=AvatarStatus.READY,
        thumbnail_url="https://api.dicebear.com/7.x/avataaars/svg?seed=chenprofessor",
        created_at=datetime.now(timezone.utc) - timedelta(days=7),
    ),
    "avatar-003": DigitalAvatar(
        id="avatar-003",
        name="王晓雪",
        description="新生代科技创业导师，专注 AI 应用与产品思维",
        status=AvatarStatus.TRAINING,
        thumbnail_url="https://api.dicebear.com/7.x/avataaars/svg?seed=wangxiaoxue",
        created_at=datetime.now(timezone.utc) - timedelta(hours=6),
    ),
}

_VIDEO_JOBS: dict[str, VideoJob] = {
    "job-001": VideoJob(
        id="job-001",
        avatar_id="avatar-001",
        script="同学们好，今天我们来深入讲解量化投资策略中的动量因子模型……",
        status=VideoJobStatus.COMPLETED,
        progress=100,
        video_url="https://storage.example.com/videos/job-001.mp4",
        duration_seconds=183.5,
        created_at=datetime.now(timezone.utc) - timedelta(days=3),
    ),
    "job-002": VideoJob(
        id="job-002",
        avatar_id="avatar-002",
        script="本节课我们来实战演练 Python 异步编程，从 asyncio 基础到高并发服务……",
        status=VideoJobStatus.PROCESSING,
        progress=62,
        video_url=None,
        duration_seconds=None,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=25),
    ),
}

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


# ── Digital Avatars ───────────────────────────────────────────────────────────

@router.get("/avatars", response_model=list[DigitalAvatar])
async def list_avatars(
    user_id: CurrentUserId,
) -> list[DigitalAvatar]:
    """Return all avatars (in-memory store, demo-ready)."""
    return list(_AVATARS.values())


@router.post("/avatars", response_model=DigitalAvatar, status_code=status.HTTP_201_CREATED)
async def create_avatar(
    data: AvatarCreate,
    user_id: CurrentUserId,
) -> DigitalAvatar:
    """Create a new digital avatar and start training pipeline."""
    avatar_id = f"avatar-{uuid.uuid4().hex[:8]}"
    avatar = DigitalAvatar(
        id=avatar_id,
        name=data.name,
        description=data.description,
        status=AvatarStatus.CREATING,
        thumbnail_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={avatar_id}",
        created_at=datetime.now(timezone.utc),
    )
    _AVATARS[avatar_id] = avatar
    log.info("edu.avatar.created", avatar_id=avatar_id, name=data.name, user_id=user_id)
    return avatar


@router.post("/avatars/{avatar_id}/generate", response_model=VideoJob, status_code=status.HTTP_202_ACCEPTED)
async def generate_avatar_video(
    avatar_id: str,
    request: VideoGenerateRequest,
    user_id: CurrentUserId,
) -> VideoJob:
    """Enqueue a video generation job for the given avatar."""
    if avatar_id not in _AVATARS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar not found")
    avatar = _AVATARS[avatar_id]
    if avatar.status != AvatarStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Avatar is not ready for generation (current status: {avatar.status})",
        )
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    job = VideoJob(
        id=job_id,
        avatar_id=avatar_id,
        script=request.script,
        status=VideoJobStatus.QUEUED,
        progress=0,
        video_url=None,
        duration_seconds=None,
        created_at=datetime.now(timezone.utc),
    )
    _VIDEO_JOBS[job_id] = job
    log.info("edu.video_job.enqueued", job_id=job_id, avatar_id=avatar_id, user_id=user_id)
    return job


# ── Video Jobs ────────────────────────────────────────────────────────────────

@router.get("/videos", response_model=list[VideoJob])
async def list_video_jobs(
    user_id: CurrentUserId,
) -> list[VideoJob]:
    """List all video generation jobs (most recent first)."""
    jobs = sorted(_VIDEO_JOBS.values(), key=lambda j: j.created_at, reverse=True)
    return jobs
