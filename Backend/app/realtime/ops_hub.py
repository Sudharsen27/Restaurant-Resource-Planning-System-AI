"""In-memory WebSocket hub for live POS / kitchen / floor updates."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket


class OpsHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, event: str, payload: dict[str, Any] | None = None) -> None:
        message = json.dumps({"event": event, "data": payload or {}})
        async with self._lock:
            clients = list(self._clients)
        dead: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)


ops_hub = OpsHub()


def publish_ops_event(event: str, payload: dict[str, Any] | None = None) -> None:
    """Fire-and-forget broadcast from sync FastAPI route handlers."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(ops_hub.broadcast(event, payload))
