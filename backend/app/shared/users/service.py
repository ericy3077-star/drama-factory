"""User management business logic."""
from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth import create_access_token, create_refresh_token, decode_refresh_token
from app.core.security import hash_password, verify_password
from app.shared.users.schemas import (
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserProfileUpdate,
    UserRegister,
    UserSchema,
)


async def register_user(
    session: AsyncSession,
    data: UserRegister,
) -> tuple[UserSchema, TokenResponse]:
    """Register a new user; raise 409 if email already taken."""
    # Check uniqueness
    existing = await session.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": data.email.lower()},
    )
    if existing.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        )

    user_id = uuid4()
    pw_hash = hash_password(data.password)

    result = await session.execute(
        text("""
            INSERT INTO users (id, email, password_hash, display_name, is_active)
            VALUES (:id, :email, :pw, :name, true)
            RETURNING id, email, display_name, avatar_url, bio, timezone, is_active, created_at
        """),
        {
            "id": user_id,
            "email": data.email.lower(),
            "pw": pw_hash,
            "name": data.display_name,
        },
    )
    await session.commit()
    user = UserSchema.model_validate(dict(result.mappings().one()))
    tokens = _issue_tokens(str(user.id))
    return user, tokens


async def authenticate_user(
    session: AsyncSession,
    data: UserLogin,
) -> tuple[UserSchema, TokenResponse]:
    """Verify credentials and return tokens."""
    result = await session.execute(
        text("""
            SELECT id, email, password_hash, display_name, avatar_url,
                   bio, timezone, is_active, created_at
            FROM users WHERE email = :email AND is_active = true
        """),
        {"email": data.email.lower()},
    )
    row = result.mappings().first()
    if not row or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    user = UserSchema.model_validate({k: v for k, v in row.items() if k != "password_hash"})
    tokens = _issue_tokens(str(user.id))
    return user, tokens


async def refresh_tokens(data: RefreshRequest) -> TokenResponse:
    """Rotate tokens using a valid refresh token."""
    payload = decode_refresh_token(data.refresh_token)
    user_id: str = payload.get("sub", "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return _issue_tokens(user_id)


async def get_user_profile(session: AsyncSession, user_id: str) -> UserSchema:
    result = await session.execute(
        text("""
            SELECT id, email, display_name, avatar_url, bio, timezone, is_active, created_at
            FROM users WHERE id = :id AND is_active = true
        """),
        {"id": UUID(user_id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserSchema.model_validate(dict(row))


async def update_user_profile(
    session: AsyncSession,
    user_id: str,
    data: UserProfileUpdate,
) -> UserSchema:
    updates: list[str] = ["updated_at = now()"]
    params: dict[str, object] = {"id": UUID(user_id)}

    if data.display_name is not None:
        updates.append("display_name = :display_name")
        params["display_name"] = data.display_name
    if data.avatar_url is not None:
        updates.append("avatar_url = :avatar_url")
        params["avatar_url"] = data.avatar_url
    if data.bio is not None:
        updates.append("bio = :bio")
        params["bio"] = data.bio
    if data.timezone is not None:
        updates.append("timezone = :timezone")
        params["timezone"] = data.timezone

    result = await session.execute(
        text(f"""
            UPDATE users SET {", ".join(updates)} WHERE id = :id AND is_active = true
            RETURNING id, email, display_name, avatar_url, bio, timezone, is_active, created_at
        """),
        params,
    )
    await session.commit()
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserSchema.model_validate(dict(row))


async def change_password(
    session: AsyncSession,
    user_id: str,
    data: PasswordChangeRequest,
) -> None:
    result = await session.execute(
        text("SELECT password_hash FROM users WHERE id = :id AND is_active = true"),
        {"id": UUID(user_id)},
    )
    row = result.mappings().first()
    if not row or not verify_password(data.current_password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    new_hash = hash_password(data.new_password)
    await session.execute(
        text("UPDATE users SET password_hash = :pw, updated_at = now() WHERE id = :id"),
        {"pw": new_hash, "id": UUID(user_id)},
    )
    await session.commit()


def _issue_tokens(user_id: str) -> TokenResponse:
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
