"""MemoryOS unit tests — mocked DB, no network calls."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import pytest

from app.platform.memory.engine import MemoryEngine, Memory


def _make_memory_row(**kwargs) -> dict:
    return {
        "id": kwargs.get("id", uuid4()),
        "user_id": kwargs.get("user_id", "user-1"),
        "content": kwargs.get("content", "Test memory content"),
        "content_type": kwargs.get("content_type", "note"),
        "topic": kwargs.get("topic", None),
        "metadata": kwargs.get("metadata", {}),
        "created_at": kwargs.get("created_at", datetime(2026, 1, 1, tzinfo=timezone.utc)),
        "rrf_score": kwargs.get("rrf_score", 0.5),
    }


@pytest.mark.asyncio
async def test_memory_store_new(mock_session) -> None:
    """store() embeds, inserts, and returns a Memory object."""
    engine = MemoryEngine()
    mock_row = _make_memory_row(content="Apple Inc. Q4 earnings beat estimates")

    # No existing fingerprint
    dedup_result = MagicMock()
    dedup_result.mappings.return_value.first.return_value = None

    insert_result = MagicMock()
    insert_result.mappings.return_value.one.return_value = mock_row

    mock_session.execute = AsyncMock(side_effect=[dedup_result, insert_result])
    mock_session.commit = AsyncMock()

    with patch(
        "app.platform.memory.engine.embed_text",
        new_callable=AsyncMock,
        return_value=[0.1] * 1024,
    ), patch(
        "app.platform.memory.engine.content_fingerprint",
        return_value="abc123",
    ):
        mem = await engine.store(
            mock_session, "user-1", "Apple Inc. Q4 earnings beat estimates", "note"
        )

    assert isinstance(mem, Memory)
    assert mem.content == "Apple Inc. Q4 earnings beat estimates"
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_memory_store_dedup(mock_session) -> None:
    """store() returns existing memory on duplicate fingerprint."""
    engine = MemoryEngine()
    existing_row = _make_memory_row(content="Existing content")

    dedup_result = MagicMock()
    dedup_result.mappings.return_value.first.return_value = existing_row
    mock_session.execute = AsyncMock(return_value=dedup_result)

    with patch("app.platform.memory.engine.embed_text", new_callable=AsyncMock), \
         patch("app.platform.memory.engine.content_fingerprint", return_value="dup"):
        mem = await engine.store(mock_session, "user-1", "Existing content", "note")

    assert mem.content == "Existing content"
    assert mock_session.commit.call_count == 0  # no insert on dedup


@pytest.mark.asyncio
async def test_memory_recall(mock_session) -> None:
    """recall() returns a list of Memory objects via hybrid_search."""
    engine = MemoryEngine()
    rows = [_make_memory_row(content=f"Memory {i}") for i in range(3)]

    with patch(
        "app.platform.memory.engine.hybrid_search",
        new_callable=AsyncMock,
        return_value=rows,
    ):
        results = await engine.recall(mock_session, "user-1", "earnings", top_k=3)

    assert len(results) == 3
    assert all(isinstance(r, Memory) for r in results)


@pytest.mark.asyncio
async def test_memory_delete(mock_session) -> None:
    """delete() soft-deletes and returns True on success."""
    engine = MemoryEngine()
    result = MagicMock()
    result.rowcount = 1
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.commit = AsyncMock()

    deleted = await engine.delete(mock_session, uuid4(), "user-1")
    assert deleted is True
