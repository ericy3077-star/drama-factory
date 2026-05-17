"""InvestMind API routes."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.dependencies import CurrentUserId, DBSession
from app.verticals.invest import service
from app.verticals.invest.schemas import (
    AgentTaskRequest,
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

router = APIRouter()


# ── Watchlist ─────────────────────────────────────────────────────────────────

@router.get("/watchlist", response_model=list[WatchlistItem])
async def list_watchlist(user_id: CurrentUserId, session: DBSession) -> list[WatchlistItem]:
    return await service.get_watchlist(session, user_id)


@router.post("/watchlist", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
async def add_watchlist_item(
    data: WatchlistItemCreate,
    user_id: CurrentUserId,
    session: DBSession,
) -> WatchlistItem:
    return await service.add_to_watchlist(session, user_id, data)


@router.delete("/watchlist/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watchlist_item(
    symbol: str,
    user_id: CurrentUserId,
    session: DBSession,
) -> None:
    removed = await service.remove_from_watchlist(session, user_id, symbol)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol not in watchlist")


# ── Research notes ────────────────────────────────────────────────────────────

@router.get("/notes", response_model=list[ResearchNote])
async def list_notes(
    user_id: CurrentUserId,
    session: DBSession,
    symbol: str | None = None,
    limit: int = 50,
) -> list[ResearchNote]:
    return await service.list_research_notes(session, user_id, symbol, limit)


@router.post("/notes", response_model=ResearchNote, status_code=status.HTTP_201_CREATED)
async def create_note(
    data: ResearchNoteCreate,
    user_id: CurrentUserId,
    session: DBSession,
) -> ResearchNote:
    return await service.create_research_note(session, user_id, data)


@router.patch("/notes/{note_id}", response_model=ResearchNote)
async def update_note(
    note_id: UUID,
    data: ResearchNoteUpdate,
    user_id: CurrentUserId,
    session: DBSession,
) -> ResearchNote:
    note = await service.update_research_note(session, user_id, note_id, data)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


# ── Feed ──────────────────────────────────────────────────────────────────────

@router.post("/feed", response_model=list[FeedItemSchema])
async def get_feed(
    request: FeedRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> list[FeedItemSchema]:
    return await service.get_feed(session, user_id, request)


# ── Research ──────────────────────────────────────────────────────────────────

@router.post("/research", response_model=ResearchReport)
async def research_stock(
    request: ResearchRequest,
    user_id: CurrentUserId,
) -> ResearchReport:
    return await service.run_research(request)


# ── Agent ─────────────────────────────────────────────────────────────────────

@router.post("/agent", response_model=AgentTaskResponse)
async def run_agent(
    request: AgentTaskRequest,
    user_id: CurrentUserId,
) -> AgentTaskResponse:
    return await service.run_invest_agent(user_id, request.task, request.context)


@router.post("/agent/stream")
async def stream_agent(
    request: AgentTaskRequest,
    user_id: CurrentUserId,
) -> StreamingResponse:
    import json
    from app.platform.agent.orchestrator import agent_orchestrator

    async def event_stream():  # type: ignore[return]
        async for update in agent_orchestrator.stream(user_id, request.task, "invest", request.context):
            yield f"data: {json.dumps(update)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
