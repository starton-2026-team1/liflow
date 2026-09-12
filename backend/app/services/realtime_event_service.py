import asyncio
from collections import defaultdict
from time import time
from typing import Any

from fastapi import WebSocket


class RealtimeEventManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._send_locks: dict[WebSocket, asyncio.Lock] = {}
        self._expires: dict[WebSocket, float] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self, user_id: int, websocket: WebSocket, *, expires_at: float | None = None
    ) -> None:
        async with self._lock:
            self._connections[user_id].add(websocket)
            self._send_locks.setdefault(websocket, asyncio.Lock())
            if expires_at is not None:
                self._expires[websocket] = expires_at

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(user_id)
            if connections is None:
                return
            connections.discard(websocket)
            self._send_locks.pop(websocket, None)
            self._expires.pop(websocket, None)
            if not connections:
                self._connections.pop(user_id, None)

    def forget(self, websocket: WebSocket) -> None:
        self._send_locks.pop(websocket, None)
        self._expires.pop(websocket, None)

    async def send(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        # Replies, heartbeat and broadcasts share one bounded writer per connection.
        send_lock = self._send_locks.setdefault(websocket, asyncio.Lock())
        async with asyncio.timeout(2):
            async with send_lock:
                if self._expires.get(websocket, float("inf")) <= time():
                    raise RuntimeError("Connection token expired")
                await websocket.send_json(message)

    async def publish_sensor_event(self, user_id: int, event: dict[str, Any]) -> None:
        async with self._lock:
            connections = tuple(self._connections.get(user_id, ()))

        if not connections:
            return

        results = await asyncio.gather(
            *(self.send(websocket, event) for websocket in connections),
            return_exceptions=True,
        )
        failed_connections = [
            websocket
            for websocket, result in zip(connections, results, strict=True)
            if isinstance(result, BaseException)
        ]
        for websocket in failed_connections:
            await self.disconnect(user_id, websocket)
            try:
                async with asyncio.timeout(1):
                    await websocket.close(code=1013)
            except Exception:
                pass


realtime_event_manager = RealtimeEventManager()
