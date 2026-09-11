import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class RealtimeEventManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._send_locks: dict[WebSocket, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[user_id].add(websocket)
            self._send_locks.setdefault(websocket, asyncio.Lock())

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(user_id)
            if connections is None:
                return
            connections.discard(websocket)
            self._send_locks.pop(websocket, None)
            if not connections:
                self._connections.pop(user_id, None)

    async def _send(self, websocket: WebSocket, event: dict[str, Any]) -> None:
        async with self._lock:
            send_lock = self._send_locks.get(websocket)
        if send_lock is None:
            return
        async with send_lock:
            await websocket.send_json(event)

    async def publish_sensor_event(
        self, user_id: int, event: dict[str, Any]
    ) -> None:
        async with self._lock:
            connections = tuple(self._connections.get(user_id, ()))

        if not connections:
            return

        results = await asyncio.gather(
            *(self._send(websocket, event) for websocket in connections),
            return_exceptions=True,
        )
        failed_connections = [
            websocket
            for websocket, result in zip(connections, results, strict=True)
            if isinstance(result, BaseException)
        ]
        for websocket in failed_connections:
            await self.disconnect(user_id, websocket)


realtime_event_manager = RealtimeEventManager()
