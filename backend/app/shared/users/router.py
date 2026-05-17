"""User management API routes."""
from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies import CurrentUserId, DBSession
from app.shared.users import service
from app.shared.users.schemas import (
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserProfileUpdate,
    UserRegister,
    UserSchema,
)

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    session: DBSession,
) -> dict[str, object]:
    user, tokens = await service.register_user(session, data)
    return {"user": user.model_dump(), "tokens": tokens.model_dump()}


@router.post("/login")
async def login(
    data: UserLogin,
    session: DBSession,
) -> dict[str, object]:
    user, tokens = await service.authenticate_user(session, data)
    return {"user": user.model_dump(), "tokens": tokens.model_dump()}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest) -> TokenResponse:
    return await service.refresh_tokens(data)


@router.get("/me", response_model=UserSchema)
async def get_profile(
    user_id: CurrentUserId,
    session: DBSession,
) -> UserSchema:
    return await service.get_user_profile(session, user_id)


@router.patch("/me", response_model=UserSchema)
async def update_profile(
    data: UserProfileUpdate,
    user_id: CurrentUserId,
    session: DBSession,
) -> UserSchema:
    return await service.update_user_profile(session, user_id, data)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChangeRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> None:
    await service.change_password(session, user_id, data)
