"""Application configuration via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_secret_key: str = "change-me"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(..., description="asyncpg PostgreSQL URL")
    database_pool_size: int = 20
    database_max_overflow: int = 40

    # ── Supabase ─────────────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(..., description="Long random secret for JWT signing")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # ── AI providers ──────────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # ── Avatar & Voice ────────────────────────────────────────────────────────
    heygen_api_key: str = ""
    elevenlabs_api_key: str = ""

    # ── LangSmith ────────────────────────────────────────────────────────────
    langsmith_api_key: str = ""
    langsmith_project: str = "drama-factory"
    langchain_tracing_v2: bool = False

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: Annotated[list[str], Field(default_factory=list)] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # ── Celery ───────────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
