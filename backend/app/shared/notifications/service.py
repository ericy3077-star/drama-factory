"""Notification service — push messages via WebSocket and/or database."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.notifications.websocket import ConnectionManager

log = structlog.get_logger()

# Will be injected from main.py at app startup
_ws_manager: ConnectionManager | None = None


def set_ws_manager(manager: ConnectionManager) -> None:
    global _ws_manager
    _ws_manager = manager


async def send_notification(
    session: AsyncSession,
    user_id: str,
    title: str,
    body: str,
    notification_type: str = "info",
    metadata: dict[str, Any] | None = None,
) -> str:
    """
    Persist a notification and push it via WebSocket if the user is online.
    Returns the notification id.
    """
    notification_id = str(uuid4())
    now = datetime.now(timezone.utc)

    # Persist to DB (notifications table — created in migrations)
    await session.execute(
        text("""
            INSERT INTO notifications (id, user_id, title, body, notification_type, metadata, created_at)
            VALUES (:id, :uid, :title, :body, :ntype, :meta::jsonb, :now)
        """),
        {
            "id": notification_id, "uid": user_id,
            "title": title, "body": body, "ntype": notification_type,
            "meta": _json_safe(metadata or {}), "now": now,
        },
    )
    await session.commit()

    # Push via WebSocket if user is online
    if _ws_manager and _ws_manager.is_connected(user_id):
        await _ws_manager.send_personal(user_id, {
            "type": "notification",
            "id": notification_id,
            "title": title,
            "body": body,
            "notification_type": notification_type,
            "created_at": now.isoformat(),
        })

    return notification_id


async def get_notifications(
    session: AsyncSession,
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> list[dict[str, Any]]:
    where = "user_id = :uid"
    if unread_only:
        where += " AND read_at IS NULL"
    result = await session.execute(
        text(f"""
            SELECT id, title, body, notification_type, metadata, read_at, created_at
            FROM notifications WHERE {where}
            ORDER BY created_at DESC LIMIT :limit
        """),
        {"uid": user_id, "limit": limit},
    )
    return [dict(r) for r in result.mappings().all()]


async def mark_read(
    session: AsyncSession,
    user_id: str,
    notification_id: str,
) -> bool:
    result = await session.execute(
        text("""
            UPDATE notifications
            SET read_at = now()
            WHERE id = :id AND user_id = :uid AND read_at IS NULL
            RETURNING id
        """),
        {"id": notification_id, "uid": user_id},
    )
    await session.commit()
    return result.rowcount > 0


def _json_safe(obj: Any) -> str:
    import json
    return json.dumps(obj, default=str)
