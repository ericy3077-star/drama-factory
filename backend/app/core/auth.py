"""JWT token creation and validation."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import settings

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    expire = _now() + (
        expires_delta
        or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": _now(),
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    """Create a signed JWT refresh token with longer expiry."""
    expire = _now() + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": _now(),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT; raise 401 on any error."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise CREDENTIALS_EXCEPTION from exc

    if payload.get("type") != "access":
        raise CREDENTIALS_EXCEPTION
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode and validate a refresh token."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise CREDENTIALS_EXCEPTION from exc

    if payload.get("type") != "refresh":
        raise CREDENTIALS_EXCEPTION
    return payload
