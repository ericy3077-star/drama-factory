"""Auth endpoint tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient


# ── register ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """POST /api/v1/auth/register returns 201 with user + tokens."""
    mock_user = MagicMock()
    mock_user.model_dump.return_value = {
        "id": "user-123", "email": "test@example.com",
        "display_name": "Test User", "is_active": True,
    }
    mock_tokens = MagicMock()
    mock_tokens.model_dump.return_value = {
        "access_token": "access.jwt.here",
        "refresh_token": "refresh.jwt.here",
        "token_type": "bearer",
    }

    with patch(
        "app.shared.users.service.register_user",
        new_callable=AsyncMock,
        return_value=(mock_user, mock_tokens),
    ):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "display_name": "Test User",
            },
        )

    assert resp.status_code == 201
    data = resp.json()
    assert "tokens" in data
    assert data["tokens"]["access_token"] == "access.jwt.here"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """POST /api/v1/auth/register returns 409 if email exists."""
    from fastapi import HTTPException, status

    with patch(
        "app.shared.users.service.register_user",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        ),
    ):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "exists@example.com",
                "password": "SecurePass123!",
                "display_name": "Test",
            },
        )

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """POST /api/v1/auth/login returns 200 with tokens."""
    mock_user = MagicMock()
    mock_user.model_dump.return_value = {"id": "u1", "email": "a@b.com"}
    mock_tokens = MagicMock()
    mock_tokens.model_dump.return_value = {
        "access_token": "tok", "refresh_token": "rtok", "token_type": "bearer"
    }

    with patch(
        "app.shared.users.service.authenticate_user",
        new_callable=AsyncMock,
        return_value=(mock_user, mock_tokens),
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "a@b.com", "password": "pass"},
        )

    assert resp.status_code == 200
    assert resp.json()["tokens"]["access_token"] == "tok"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """POST /api/v1/auth/login returns 401 for wrong credentials."""
    from fastapi import HTTPException, status

    with patch(
        "app.shared.users.service.authenticate_user",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials"),
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "a@b.com", "password": "wrong"},
        )

    assert resp.status_code == 401


# ── protected route ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_protected_route_requires_token(client: AsyncClient) -> None:
    """GET /api/v1/users/me returns 401 without auth header."""
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401
