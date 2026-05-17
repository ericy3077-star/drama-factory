"""InvestMind business logic layer."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.platform.agent.orchestrator import agent_orchestrator
from app.verticals.invest.feed import fetch_personalised_feed
from app.verticals.invest.research import generate_research_report
from app.verticals.invest.schemas import (
    AgentTaskResponse,
    FeedItemSchema,
    FeedRequest,
    ResearchNote,
    ResearchNoteCreate,
    ResearchNoteUpdate,
    ResearchReport,
    ResearchRequest,
    WatchlistItem,
    WatchlistItemCreate,
)
from app.verticals.invest.tools import normalise_ticker

log = structlog.get_logger()


# ── Watchlist ─────────────────────────────────────────────────────────────────

async def add_to_watchlist(
    session: AsyncSession,
    user_id: str,
    data: WatchlistItemCreate,
) -> WatchlistItem:
    symbol = normalise_ticker(data.symbol)
    result = await session.execute(
        text("""
            INSERT INTO watchlists (id, user_id, symbol, notes, alert_price_above, alert_price_below)
            VALUES (:id, :uid, :sym, :notes, :above, :below)
            ON CONFLICT (user_id, symbol) DO UPDATE
                SET notes = EXCLUDED.notes,
                    alert_price_above = EXCLUDED.alert_price_above,
                    alert_price_below = EXCLUDED.alert_price_below,
                    updated_at = now()
            RETURNING id, user_id, symbol, notes, alert_price_above, alert_price_below, created_at
        """),
        {
            "id": uuid4(), "uid": user_id, "sym": symbol,
            "notes": data.notes, "above": data.alert_price_above,
            "below": data.alert_price_below,
        },
    )
    await session.commit()
    return WatchlistItem.model_validate(dict(result.mappings().one()))


async def get_watchlist(session: AsyncSession, user_id: str) -> list[WatchlistItem]:
    result = await session.execute(
        text("""
            SELECT id, user_id, symbol, notes, alert_price_above, alert_price_below, created_at
            FROM watchlists WHERE user_id = :uid ORDER BY created_at DESC
        """),
        {"uid": user_id},
    )
    return [WatchlistItem.model_validate(dict(r)) for r in result.mappings().all()]


async def remove_from_watchlist(session: AsyncSession, user_id: str, symbol: str) -> bool:
    sym = normalise_ticker(symbol)
    result = await session.execute(
        text("DELETE FROM watchlists WHERE user_id = :uid AND symbol = :sym RETURNING id"),
        {"uid": user_id, "sym": sym},
    )
    await session.commit()
    return result.rowcount > 0


# ── Research notes ────────────────────────────────────────────────────────────

async def create_research_note(
    session: AsyncSession,
    user_id: str,
    data: ResearchNoteCreate,
) -> ResearchNote:
    note_id = uuid4()
    result = await session.execute(
        text("""
            INSERT INTO research_notes (id, user_id, symbol, title, content, tags)
            VALUES (:id, :uid, :sym, :title, :content, :tags::text[])
            RETURNING id, user_id, symbol, title, content, tags, created_at, updated_at
        """),
        {
            "id": note_id, "uid": user_id, "sym": data.symbol,
            "title": data.title, "content": data.content,
            "tags": "{" + ",".join(data.tags) + "}",
        },
    )
    await session.commit()
    return ResearchNote.model_validate(dict(result.mappings().one()))


async def list_research_notes(
    session: AsyncSession,
    user_id: str,
    symbol: str | None = None,
    limit: int = 50,
) -> list[ResearchNote]:
    where = "user_id = :uid"
    params: dict[str, Any] = {"uid": user_id, "limit": limit}
    if symbol:
        where += " AND symbol = :sym"
        params["sym"] = normalise_ticker(symbol)

    result = await session.execute(
        text(f"""
            SELECT id, user_id, symbol, title, content, tags, created_at, updated_at
            FROM research_notes WHERE {where}
            ORDER BY updated_at DESC LIMIT :limit
        """),
        params,
    )
    return [ResearchNote.model_validate(dict(r)) for r in result.mappings().all()]


async def update_research_note(
    session: AsyncSession,
    user_id: str,
    note_id: UUID,
    data: ResearchNoteUpdate,
) -> ResearchNote | None:
    updates: list[str] = ["updated_at = now()"]
    params: dict[str, Any] = {"id": note_id, "uid": user_id}

    if data.title is not None:
        updates.append("title = :title")
        params["title"] = data.title
    if data.content is not None:
        updates.append("content = :content")
        params["content"] = data.content
    if data.tags is not None:
        updates.append("tags = :tags::text[]")
        params["tags"] = "{" + ",".join(data.tags) + "}"

    result = await session.execute(
        text(f"""
            UPDATE research_notes SET {", ".join(updates)}
            WHERE id = :id AND user_id = :uid
            RETURNING id, user_id, symbol, title, content, tags, created_at, updated_at
        """),
        params,
    )
    await session.commit()
    row = result.mappings().first()
    return ResearchNote.model_validate(dict(row)) if row else None


# ── Feed ──────────────────────────────────────────────────────────────────────

async def get_feed(
    session: AsyncSession,
    user_id: str,
    request: FeedRequest,
) -> list[FeedItemSchema]:
    # Augment tickers from watchlist if none provided
    tickers = list(request.tickers)
    if not tickers:
        watchlist = await get_watchlist(session, user_id)
        tickers = [w.symbol for w in watchlist]

    return await fetch_personalised_feed(tickers, request.topics, request.limit)


# ── Research ──────────────────────────────────────────────────────────────────

async def run_research(request: ResearchRequest) -> ResearchReport:
    return await generate_research_report(
        symbol=normalise_ticker(request.symbol),
        depth=request.depth,
        include_news=request.include_news,
        include_ratios=request.include_ratios,
    )


# ── Agent ─────────────────────────────────────────────────────────────────────

async def run_invest_agent(
    user_id: str,
    task: str,
    context: dict[str, Any] | None = None,
) -> AgentTaskResponse:
    result = await agent_orchestrator.run(user_id, task, vertical="invest", context=context)
    return AgentTaskResponse(
        status=result.status,
        answer=result.answer,
        step_results=result.step_results,
        error=result.error or None,
        requires_human=result.requires_human,
    )
