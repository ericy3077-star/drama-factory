"""InvestMind chat endpoint smoke tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.core.auth import create_access_token


def _make_token(user_id: str = "user-test-123") -> str:
    return create_access_token(user_id)


@pytest.mark.asyncio
async def test_chat_requires_auth(client: AsyncClient) -> None:
    """POST /api/v1/invest/chat returns 401 without token."""
    resp = await client.post(
        "/api/v1/invest/chat",
        json={"message": "What's happening with AAPL?"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_streams_sse(client: AsyncClient) -> None:
    """POST /api/v1/invest/chat with valid token returns text/event-stream."""
    token = _make_token()

    async def fake_stream(*args, **kwargs):
        yield 'data: {"type": "content_delta", "delta": {"text": "Apple"}}\n\n'
        yield 'data: {"type": "content_delta", "delta": {"text": " looks strong"}}\n\n'
        yield "data: [DONE]\n\n"

    with patch(
        "app.verticals.invest.router.chat_stream",
        side_effect=lambda *a, **kw: fake_stream(),
    ):
        resp = await client.post(
            "/api/v1/invest/chat",
            json={"message": "Analyse AAPL", "history": []},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "Apple" in body
    assert "[DONE]" in body
