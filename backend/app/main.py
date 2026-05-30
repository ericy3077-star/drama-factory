"""FastAPI application entry point."""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.database import shutdown_database, startup_database
from app.dependencies import get_redis
from app.shared.notifications.websocket import ConnectionManager

# Vertical routers
from app.verticals.invest.router import router as invest_router
from app.verticals.edu.router import router as edu_router

# Shared routers
from app.shared.users.router import router as users_router
from app.shared.billing.router import router as billing_router
from app.shared.tasks.router import router as tasks_router

log = structlog.get_logger()

# Configure LangSmith tracing before anything imports langchain
if settings.langchain_tracing_v2 and settings.langsmith_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown lifecycle."""
    log.info("startup.begin", env=settings.app_env)
    await startup_database()
    log.info("startup.database_ready")
    yield
    log.info("shutdown.begin")
    await shutdown_database()
    redis = get_redis()
    await redis.aclose()
    log.info("shutdown.complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Drama Factory API",
        version="0.1.0",
        description="AI-native platform: MemoryOS · AgentOS · AvatarOS · PerceptOS",
        default_response_class=ORJSONResponse,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── API routers ───────────────────────────────────────────────────────────
    api_prefix = "/api/v1"
    app.include_router(users_router, prefix=f"{api_prefix}/users", tags=["users"])
    app.include_router(users_router, prefix=f"{api_prefix}/auth", tags=["auth"])
    app.include_router(billing_router, prefix=f"{api_prefix}/billing", tags=["billing"])
    app.include_router(invest_router, prefix=f"{api_prefix}/invest", tags=["invest"])
    app.include_router(edu_router, prefix=f"{api_prefix}/edu", tags=["edu"])
    app.include_router(tasks_router, prefix=f"{api_prefix}/tasks", tags=["tasks"])

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    # ── WebSocket endpoint ────────────────────────────────────────────────────
    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str) -> None:
        await ws_manager.connect(user_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Echo back and broadcast — real logic lives in services
                await ws_manager.send_personal(user_id, {"type": "echo", "data": data})
        except WebSocketDisconnect:
            ws_manager.disconnect(user_id, websocket)

    return app


app = create_app()
