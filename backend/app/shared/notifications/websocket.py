"""WebSocket connection manager for real-time notifications."""
from __future__ import annotations

import asyncio
from typing import Any

import structlog
from fastapi import WebSocket

log = structlog.get_logger()


class ConnectionManager:
    """
    Manages a mapping of user_id → set of active WebSocket connections.
    One user can have multiple concurrent connections (e.g., multiple tabs).
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)
        log.info("ws.connected", user_id=user_id, total=len(self._connections[user_id]))

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id, set())
        conns.discard(websocket)
        if not conns:
            self._connections.pop(user_id, None)
        log.info("ws.disconnected", user_id=user_id)

    async def send_personal(self, user_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to all connections for *user_id*."""
        conns = self._connections.get(user_id, set())
        dead: set[WebSocket] = set()
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception as exc:
                log.warning("ws.send_failed", user_id=user_id, error=str(exc))
                dead.add(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected users."""
        tasks = [self.send_personal(uid, message) for uid in list(self._connections)]
        await asyncio.gather(*tasks, return_exceptions=True)

    def is_connected(self, user_id: str) -> bool:
        return bool(self._connections.get(user_id))

    @property
    def connected_user_count(self) -> int:
        return len(self._connections)
