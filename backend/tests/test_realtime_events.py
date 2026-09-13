import asyncio
import json
from typing import Any, cast

from fastapi import WebSocketDisconnect

from app.api.v1 import realtime_events
from app.services.realtime_event_service import RealtimeEventManager


class FakeWebSocket:
    def __init__(self, incoming: list[Any] | None = None) -> None:
        self.incoming = list(incoming or [])
        self.accepted = False
        self.sent: list[dict[str, Any]] = []
        self.closed_code: int | None = None
        self.send_error: Exception | None = None
        self.send_calls = 0
        self.headers: dict[str, str] = {}

    async def accept(self) -> None:
        self.accepted = True

    async def receive(self) -> dict[str, Any]:
        if not self.incoming:
            raise WebSocketDisconnect()
        message = self.incoming.pop(0)
        if isinstance(message, BaseException):
            raise message
        if isinstance(message, str):
            return {"type": "websocket.receive", "text": message}
        return {"type": "websocket.receive", "text": json.dumps(message)}

    async def send_json(self, message: dict[str, Any]) -> None:
        self.send_calls += 1
        if self.send_error is not None:
            raise self.send_error
        self.sent.append(message)

    async def close(self, code: int, reason: str | None = None) -> None:
        self.closed_code = code


class SlowWebSocket(FakeWebSocket):
    async def receive(self) -> dict[str, Any]:
        await asyncio.sleep(1)
        return {"type": "websocket.receive", "text": "{}"}


async def test_realtime_stream_authenticates_and_removes_disconnected_client(
    monkeypatch: Any,
) -> None:
    websocket = FakeWebSocket([{"type": "authenticate", "token": "valid-token"}])

    async def authenticate(_token: str | None) -> int:
        return 7

    monkeypatch.setattr(realtime_events, "authenticate_realtime_token", authenticate)
    monkeypatch.setattr(realtime_events, "access_token_expiry", lambda _token: 9e12)
    await realtime_events.sensor_event_stream(cast(Any, websocket))

    assert websocket.accepted is True
    assert websocket.sent == [{"type": "authenticated", "version": 1, "role": "guardian"}]

    await realtime_events.realtime_event_manager.publish_sensor_event(
        7, {"type": "sensor_event.created"}
    )
    assert websocket.sent == [{"type": "authenticated", "version": 1, "role": "guardian"}]


async def test_realtime_stream_rejects_invalid_authentication(
    monkeypatch: Any,
) -> None:
    websocket = FakeWebSocket([{"type": "authenticate", "token": "expired"}])

    async def reject_authentication(_token: str | None) -> None:
        return None

    monkeypatch.setattr(realtime_events, "authenticate_realtime_token", reject_authentication)
    monkeypatch.setattr(realtime_events, "access_token_expiry", lambda _token: 9e12)
    await realtime_events.sensor_event_stream(cast(Any, websocket))

    assert websocket.closed_code == 4401
    assert websocket.sent[0]["error"] == "connection_rejected"


async def test_realtime_stream_rejects_invalid_json() -> None:
    websocket = FakeWebSocket(["{invalid"])

    await realtime_events.sensor_event_stream(cast(Any, websocket))

    assert websocket.closed_code == 4400
    assert websocket.sent[0]["error"] == "connection_rejected"


async def test_realtime_stream_times_out_during_authentication(
    monkeypatch: Any,
) -> None:
    websocket = SlowWebSocket()
    monkeypatch.setattr(realtime_events, "AUTHENTICATION_TIMEOUT_SECONDS", 0.001)

    await realtime_events.sensor_event_stream(cast(Any, websocket))

    assert websocket.closed_code == 4408
    assert websocket.sent[0]["error"] == "authentication_timeout"


async def test_realtime_stream_closes_when_authentication_service_fails(
    monkeypatch: Any,
) -> None:
    websocket = FakeWebSocket([{"type": "authenticate", "token": "valid-token"}])

    async def fail_authentication(_token: str | None) -> int:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(realtime_events, "authenticate_realtime_token", fail_authentication)
    monkeypatch.setattr(realtime_events, "access_token_expiry", lambda _token: 9e12)
    await realtime_events.sensor_event_stream(cast(Any, websocket))

    assert websocket.closed_code == 1011
    assert websocket.sent[0]["error"] == "realtime_unavailable"


async def test_realtime_stream_reports_unsupported_messages(monkeypatch: Any) -> None:
    websocket = FakeWebSocket(
        [
            {"type": "authenticate", "token": "valid-token"},
            {"type": "unknown"},
        ]
    )

    async def authenticate(_token: str | None) -> int:
        return 7

    monkeypatch.setattr(realtime_events, "authenticate_realtime_token", authenticate)
    monkeypatch.setattr(realtime_events, "access_token_expiry", lambda _token: 9e12)
    await realtime_events.sensor_event_stream(cast(Any, websocket))

    assert websocket.sent[1]["error"] == "unsupported_message"


async def test_realtime_manager_removes_failed_connections() -> None:
    manager = RealtimeEventManager()
    websocket = FakeWebSocket()
    websocket.send_error = RuntimeError("connection closed")
    await manager.connect(1, cast(Any, websocket))

    await manager.publish_sensor_event(1, {"type": "sensor_event.created"})
    websocket.send_error = None
    await manager.publish_sensor_event(1, {"type": "sensor_event.created"})

    assert websocket.send_calls == 1


async def test_realtime_manager_publishes_only_to_matching_user() -> None:
    manager = RealtimeEventManager()
    owner_websocket = FakeWebSocket()
    other_websocket = FakeWebSocket()
    await manager.connect(1, cast(Any, owner_websocket))
    await manager.connect(2, cast(Any, other_websocket))

    event = {"type": "sensor_event.created", "data": {"id": 10}}
    await manager.publish_sensor_event(1, event)

    assert owner_websocket.sent == [event]
    assert other_websocket.sent == []
