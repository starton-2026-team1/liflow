from datetime import datetime
from typing import Any

from httpx import AsyncClient


async def register_sensor(
    client: AsyncClient,
    auth_headers: dict[str, str],
    *,
    device_id: str,
    sensor_status: str = "CONNECTED",
) -> tuple[int, int]:
    person_response = await client.post(
        "/api/v1/people",
        headers=auth_headers,
        json={"name": "장치 테스트 대상자", "living_space": "집"},
    )
    person_id = person_response.json()["id"]
    sensor_response = await client.post(
        "/api/v1/sensors",
        headers=auth_headers,
        json={
            "name": "현관 센서",
            "location": "현관",
            "device_id": device_id,
            "person_id": person_id,
            "target_object": "현관문",
            "status": sensor_status,
        },
    )
    return person_id, sensor_response.json()["id"]


async def test_device_event_requires_valid_api_key(client: AsyncClient) -> None:
    data = {
        "event_id": "event-auth-001",
        "device_id": "UNKNOWN",
        "detected_at": datetime.now().isoformat(),
        "detected_value": "OPEN",
    }

    missing = await client.post("/api/v1/device-events", json=data)
    invalid = await client.post(
        "/api/v1/device-events",
        headers={"X-Device-Key": "wrong-key"},
        json=data,
    )
    assert missing.status_code == 401
    assert invalid.status_code == 401


async def test_device_event_is_saved_and_duplicate_is_idempotent(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: Any
) -> None:
    published_events: list[tuple[int, dict[str, Any]]] = []

    async def capture_event(user_id: int, event: dict[str, Any]) -> None:
        published_events.append((user_id, event))

    monkeypatch.setattr(
        "app.api.v1.device_events.realtime_event_manager.publish_sensor_event",
        capture_event,
    )
    person_id, sensor_id = await register_sensor(
        client, auth_headers, device_id="DEVICE-001"
    )
    data = {
        "event_id": "event-001",
        "device_id": "DEVICE-001",
        "detected_at": datetime.now().isoformat(),
        "detected_value": "OPEN",
    }
    device_headers = {"X-Device-Key": "test-device-api-key"}

    created = await client.post(
        "/api/v1/device-events", headers=device_headers, json=data
    )
    duplicate = await client.post(
        "/api/v1/device-events", headers=device_headers, json=data
    )
    assert created.status_code == 201
    assert created.json()["person_id"] == person_id
    assert created.json()["sensor_id"] == sensor_id
    assert created.json()["sensor_status"] == "CONNECTED"
    assert created.json()["event_id"] == data["event_id"]
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == created.json()["id"]
    assert len(published_events) == 1
    assert published_events[0][1]["type"] == "sensor_event.created"
    assert published_events[0][1]["data"]["id"] == created.json()["id"]

    events = await client.get("/api/v1/sensor-events", headers=auth_headers)
    assert len(events.json()) == 1


async def test_device_event_is_saved_when_realtime_publish_fails(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: Any
) -> None:
    await register_sensor(client, auth_headers, device_id="DEVICE-PUBLISH-FAIL")

    async def fail_to_publish(_user_id: int, _event: dict[str, Any]) -> None:
        raise RuntimeError("realtime service unavailable")

    monkeypatch.setattr(
        "app.api.v1.device_events.realtime_event_manager.publish_sensor_event",
        fail_to_publish,
    )
    response = await client.post(
        "/api/v1/device-events",
        headers={"X-Device-Key": "test-device-api-key"},
        json={
            "event_id": "event-publish-fail",
            "device_id": "DEVICE-PUBLISH-FAIL",
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
        },
    )

    assert response.status_code == 201
    events = await client.get("/api/v1/sensor-events", headers=auth_headers)
    assert len(events.json()) == 1


async def test_device_event_rejects_unknown_or_disconnected_sensor(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await register_sensor(
        client,
        auth_headers,
        device_id="DEVICE-DISCONNECTED",
        sensor_status="DISCONNECTED",
    )
    headers = {"X-Device-Key": "test-device-api-key"}

    unknown = await client.post(
        "/api/v1/device-events",
        headers=headers,
        json={
            "event_id": "event-unknown",
            "device_id": "UNKNOWN",
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
        },
    )
    disconnected = await client.post(
        "/api/v1/device-events",
        headers=headers,
        json={
            "event_id": "event-disconnected",
            "device_id": "DEVICE-DISCONNECTED",
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
        },
    )
    assert unknown.status_code == 404
    assert disconnected.status_code == 409


async def test_device_event_rejects_reused_event_id_with_different_data(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await register_sensor(client, auth_headers, device_id="DEVICE-CONFLICT")
    headers = {"X-Device-Key": "test-device-api-key"}
    original = {
        "event_id": "event-conflict",
        "device_id": "DEVICE-CONFLICT",
        "detected_at": datetime.now().isoformat(),
        "detected_value": "OPEN",
    }
    assert (
        await client.post("/api/v1/device-events", headers=headers, json=original)
    ).status_code == 201

    conflicting = {**original, "detected_value": "CLOSED"}
    response = await client.post(
        "/api/v1/device-events", headers=headers, json=conflicting
    )
    assert response.status_code == 409
