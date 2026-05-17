"""FastAPI dependency injection providers."""
from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth import decode_access_token
from app.database import get_session

# ── Database ──────────────────────────────────────────────────────────────────

DBSession = Annotated[AsyncSession, Depends(get_session)]

# ── Redis ─────────────────────────────────────────────────────────────────────

_redis_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
    return _redis_pool


RedisClient = Annotated[aioredis.Redis, Depends(get_redis)]

# ── Auth ──────────────────────────────────────────────────────────────────────


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Extract and validate JWT, return user_id."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject",
        )
    return user_id


CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_optional_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str | None:
    """Same as get_current_user_id but returns None instead of raising."""
    if authorization is None or not authorization.startswith("Bearer "):
        return None
    try:
        return await get_current_user_id(authorization)
    except HTTPException:
        return None


OptionalUserId = Annotated[str | None, Depends(get_optional_user_id)]
