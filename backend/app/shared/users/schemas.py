"""Pydantic v2 schemas for user management."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    avatar_url: str | None = None
    bio: str | None = Field(None, max_length=500)
    timezone: str | None = None


class UserSchema(BaseModel):
    id: UUID
    email: str
    display_name: str
    avatar_url: str | None
    bio: str | None
    timezone: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
