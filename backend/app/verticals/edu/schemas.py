"""Pydantic v2 schemas for EduStar."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DifficultyLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LessonType(StrEnum):
    VIDEO = "video"
    ARTICLE = "article"
    QUIZ = "quiz"
    EXERCISE = "exercise"
    PROJECT = "project"


# ── Course ────────────────────────────────────────────────────────────────────

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    topic: str = Field(..., min_length=1, max_length=100)
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    duration_weeks: int = Field(4, ge=1, le=52)
    tags: list[str] = Field(default_factory=list)


class CourseSchema(BaseModel):
    id: UUID
    user_id: str
    title: str
    description: str
    topic: str
    difficulty: str
    duration_weeks: int
    tags: list[str]
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Lesson ────────────────────────────────────────────────────────────────────

class LessonCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    lesson_type: LessonType = LessonType.ARTICLE
    content: str = Field("", max_length=50000)
    order_index: int = Field(0, ge=0)
    duration_minutes: int = Field(10, ge=1, le=480)


class LessonSchema(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    lesson_type: str
    content: str
    order_index: int
    duration_minutes: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Learner events ────────────────────────────────────────────────────────────

class LearnerEventCreate(BaseModel):
    course_id: UUID
    lesson_id: UUID | None = None
    event_type: str = Field(..., description="started|completed|paused|quiz_submitted")
    payload: dict[str, Any] = Field(default_factory=dict)


class LearnerEventSchema(BaseModel):
    id: UUID
    user_id: str
    course_id: UUID
    lesson_id: UUID | None
    event_type: str
    payload: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Course factory ────────────────────────────────────────────────────────────

class CourseFactoryRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    level: DifficultyLevel = DifficultyLevel.BEGINNER
    duration_weeks: int = Field(4, ge=1, le=12)
    learning_goals: list[str] = Field(default_factory=list)


class GeneratedCourseOutline(BaseModel):
    title: str
    description: str
    target_audience: str
    modules: list[dict[str, Any]]
    estimated_hours: int


# ── Quiz ──────────────────────────────────────────────────────────────────────

class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    num_questions: int = Field(5, ge=1, le=20)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")


class QuizResponse(BaseModel):
    topic: str
    questions: list[dict[str, Any]]


# ── Agent ─────────────────────────────────────────────────────────────────────

class AgentTaskRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)


class AgentTaskResponse(BaseModel):
    status: str
    answer: str
    step_results: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    requires_human: bool = False
