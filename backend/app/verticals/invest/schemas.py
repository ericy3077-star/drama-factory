"""Pydantic v2 schemas for InvestMind."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


# ── Watchlist ─────────────────────────────────────────────────────────────────

class WatchlistItemCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock ticker symbol")
    notes: str | None = Field(None, max_length=1000)
    alert_price_above: float | None = None
    alert_price_below: float | None = None


class WatchlistItem(BaseModel):
    id: UUID
    user_id: str
    symbol: str
    notes: str | None
    alert_price_above: float | None
    alert_price_below: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Research notes ────────────────────────────────────────────────────────────

class ResearchNoteCreate(BaseModel):
    symbol: str | None = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class ResearchNoteUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = None
    tags: list[str] | None = None


class ResearchNote(BaseModel):
    id: UUID
    user_id: str
    symbol: str | None
    title: str
    content: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Feed ──────────────────────────────────────────────────────────────────────

class FeedItemSchema(BaseModel):
    id: str
    title: str
    url: str
    source: str
    summary: str | None = None
    sentiment: str | None = None  # positive / negative / neutral
    related_tickers: list[str] = Field(default_factory=list)
    published_at: datetime | None = None


class FeedRequest(BaseModel):
    tickers: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    limit: int = Field(20, ge=1, le=100)


# ── Research ──────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    symbol: str
    depth: str = Field("standard", pattern="^(quick|standard|deep)$")
    include_news: bool = True
    include_ratios: bool = True


class ResearchReport(BaseModel):
    symbol: str
    company_name: str | None = None
    summary: str
    current_price: float | None = None
    key_ratios: dict[str, Any] = Field(default_factory=dict)
    recent_news: list[dict[str, str]] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Agent task ────────────────────────────────────────────────────────────────

class AgentTaskRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)


class AgentTaskResponse(BaseModel):
    status: str
    answer: str
    step_results: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    requires_human: bool = False
