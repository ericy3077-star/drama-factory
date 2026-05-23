"""Shared pytest fixtures."""
from __future__ import annotations

# IMPORTANT: Set env vars before any app imports so pydantic-settings
# can build Settings without requiring real service credentials.
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("APP_ENV", "development")

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session


# In-memory SQLite for unit tests (no pgvector, test logic only)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_session() -> AsyncMock:
    """Return a mock AsyncSession for unit tests that don't need a real DB."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with mocked DB session and no real external connections."""
    from app.main import create_app

    app = create_app()

    mock_sess = AsyncMock(spec=AsyncSession)
    mock_sess.execute = AsyncMock()
    mock_sess.commit = AsyncMock()

    async def override_get_session():
        yield mock_sess

    app.dependency_overrides[get_session] = override_get_session

    # Patch out DB and Redis startup/shutdown so tests don't need real services
    with patch("app.main.startup_database", new_callable=AsyncMock), \
         patch("app.main.shutdown_database", new_callable=AsyncMock), \
         patch("app.main.get_redis", return_value=AsyncMock(aclose=AsyncMock())):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as c:
            yield c
