from datetime import datetime, timedelta
from typing import Any, cast

from httpx import AsyncClient

from app.services.realtime_event_service import realtime_event_manager
from tests.test_realtime_events import FakeWebSocket

DEVICE_HEADERS = {"X-Device-Key": "test-device-api-key"}
WRONG_DEVICE_HEADERS = {"X-Device-Key": "wrong-key"}


async def _create_person_and_sensor(
    client: AsyncClient, headers: dict[str, str], *, device_id: str
) -> tuple[int, int]:
    person = await client.post(
        "/api/v1/people",
        headers=headers,
        json={"name": "테스트 대상자", "living_space": "집"},
    )
    person_id = person.json()["id"]
    sensor = await client.post(
        "/api/v1/sensors",
        headers=headers,
        json={
            "name": "테스트 센서",
            "location": "거실",
            "device_id": device_id,
            "person_id": person_id,
            "target_object": "거실문",
            "status": "CONNECTED",
        },
    )
    return person_id, sensor.json()["id"]


async def test_create_status_event_success(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id, _ = await _create_person_and_sensor(
        client, auth_headers, device_id="STATUS-API-001"
    )

    response = await client.post(
        "/api/v1/status-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "status-api-evt-1",
            "device_id": "STATUS-API-001",
            "status": "NORMAL",
            "judged_at": datetime.now().isoformat(),
            "detected_value": "20.1",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["person_id"] == person_id
    assert body["status"] == "NORMAL"
    assert body["event_id"] == "status-api-evt-1"
    assert body["detected_value"] == "20.1"


async def test_duplicate_event_id_same_content_is_idempotent(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _create_person_and_sensor(client, auth_headers, device_id="STATUS-API-002")
    payload = {
        "event_id": "status-api-evt-2",
        "device_id": "STATUS-API-002",
        "status": "ABNORMAL",
        "judged_at": datetime.now().isoformat(),
        "detected_value": "45.0",
    }

    first = await client.post("/api/v1/status-events", headers=DEVICE_HEADERS, json=payload)
    second = await client.post("/api/v1/status-events", headers=DEVICE_HEADERS, json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


async def test_duplicate_event_id_different_content_returns_conflict(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await _create_person_and_sensor(client, auth_headers, device_id="STATUS-API-003")
    await client.post(
        "/api/v1/status-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "status-api-evt-3",
            "device_id": "STATUS-API-003",
            "status": "NORMAL",
            "judged_at": datetime.now().isoformat(),
        },
    )

    response = await client.post(
        "/api/v1/status-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "status-api-evt-3",
            "device_id": "STATUS-API-003",
            "status": "ABNORMAL",
            "judged_at": datetime.now().isoformat(),
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "EVENT_ID_CONFLICT"


async def test_unknown_device_id_returns_sensor_not_found(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/status-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "status-api-evt-4",
            "device_id": "NO-SUCH-DEVICE",
            "status": "NORMAL",
            "judged_at": datetime.now().isoformat(),
        },
    )

    assert response.status_code == 404
    assert response.json()["code"] == "SENSOR_NOT_FOUND"


async def test_wrong_device_key_returns_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/status-events",
        headers=WRONG_DEVICE_HEADERS,
        json={
            "event_id": "status-api-evt-5",
            "device_id": "ANY-DEVICE",
            "status": "NORMAL",
            "judged_at": datetime.now().isoformat(),
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == "DEVICE_INVALID_API_KEY"


async def test_get_person_latest_status_with_data(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id, _ = await _create_person_and_sensor(
        client, auth_headers, device_id="STATUS-API-006"
    )
    await client.post(
        "/api/v1/status-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "status-api-evt-6",
            "device_id": "STATUS-API-006",
            "status": "ABNORMAL",
            "judged_at": datetime.now().isoformat(),
        },
    )

    response = await client.get(f"/api/v1/people/{person_id}/status", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["person_id"] == person_id
    assert body["status"] == "ABNORMAL"
    assert body["sensor_id"] is not None
    assert body["judged_at"] is not None


async def test_get_person_latest_status_without_data_returns_unknown(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person = await client.post(
        "/api/v1/people",
        headers=auth_headers,
        json={"name": "미판단 대상자", "living_space": "집"},
    )
    person_id = person.json()["id"]

    response = await client.get(f"/api/v1/people/{person_id}/status", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "person_id": person_id,
        "status": "UNKNOWN",
        "judged_at": None,
        "sensor_id": None,
    }


async def test_status_history_pagination(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id, _ = await _create_person_and_sensor(
        client, auth_headers, device_id="STATUS-API-008"
    )
    base_time = datetime.now()
    for i in range(3):
        await client.post(
            "/api/v1/status-events",
            headers=DEVICE_HEADERS,
            json={
                "event_id": f"status-api-hist-{i}",
                "device_id": "STATUS-API-008",
                "status": "ABNORMAL" if i == 2 else "NORMAL",
                "judged_at": (base_time + timedelta(minutes=i)).isoformat(),
            },
        )

    page1 = await client.get(
        f"/api/v1/people/{person_id}/status/history",
        params={"page": 1, "page_size": 2},
        headers=auth_headers,
    )
    page2 = await client.get(
        f"/api/v1/people/{person_id}/status/history",
        params={"page": 2, "page_size": 2},
        headers=auth_headers,
    )

    assert page1.status_code == 200
    body1 = page1.json()
    assert body1["page"] == 1
    assert body1["page_size"] == 2
    assert body1["total"] == 3
    assert len(body1["items"]) == 2
    assert body1["items"][0]["status"] == "ABNORMAL"  # most recent first

    assert page2.status_code == 200
    body2 = page2.json()
    assert len(body2["items"]) == 1


async def test_all_people_status_returns_latest_per_person(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id, _ = await _create_person_and_sensor(
        client, auth_headers, device_id="STATUS-API-009"
    )
    await client.post(
        "/api/v1/status-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "status-api-evt-9",
            "device_id": "STATUS-API-009",
            "status": "ABNORMAL",
            "judged_at": datetime.now().isoformat(),
        },
    )

    response = await client.get("/api/v1/people/status", headers=auth_headers)

    assert response.status_code == 200
    items = response.json()
    assert any(
        item["person_id"] == person_id and item["status"] == "ABNORMAL" for item in items
    )


async def test_other_user_cannot_access_person_status(client: AsyncClient) -> None:
    owner = await client.post(
        "/api/v1/auth/signup",
        json={"email": "status-owner@example.com", "password": "password1234"},
    )
    owner_headers = {"Authorization": f"Bearer {owner.json()['access_token']}"}
    other = await client.post(
        "/api/v1/auth/signup",
        json={"email": "status-other@example.com", "password": "password1234"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    person = await client.post(
        "/api/v1/people",
        headers=owner_headers,
        json={"name": "타인 대상자", "living_space": "집"},
    )
    person_id = person.json()["id"]

    status_response = await client.get(
        f"/api/v1/people/{person_id}/status", headers=other_headers
    )
    history_response = await client.get(
        f"/api/v1/people/{person_id}/status/history", headers=other_headers
    )

    assert status_response.status_code == 404
    assert status_response.json()["code"] == "PERSON_NOT_FOUND"
    assert history_response.status_code == 404
    assert history_response.json()["code"] == "PERSON_NOT_FOUND"


async def test_status_change_publishes_websocket_event_and_repeat_does_not(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["id"]
    websocket = FakeWebSocket()
    await realtime_event_manager.connect(user_id, cast(Any, websocket))

    try:
        person_id, _ = await _create_person_and_sensor(
            client, auth_headers, device_id="STATUS-API-WS-001"
        )
        base_time = datetime.now()

        # First-ever judgement: previous_status is None but still notifies.
        first = await client.post(
            "/api/v1/status-events",
            headers=DEVICE_HEADERS,
            json={
                "event_id": "status-api-ws-1",
                "device_id": "STATUS-API-WS-001",
                "status": "NORMAL",
                "judged_at": base_time.isoformat(),
            },
        )
        assert first.status_code == 201

        # Same status again: should NOT publish a second time.
        repeat = await client.post(
            "/api/v1/status-events",
            headers=DEVICE_HEADERS,
            json={
                "event_id": "status-api-ws-2",
                "device_id": "STATUS-API-WS-001",
                "status": "NORMAL",
                "judged_at": (base_time + timedelta(minutes=1)).isoformat(),
            },
        )
        assert repeat.status_code == 201

        # Status changes: publish again.
        changed = await client.post(
            "/api/v1/status-events",
            headers=DEVICE_HEADERS,
            json={
                "event_id": "status-api-ws-3",
                "device_id": "STATUS-API-WS-001",
                "status": "ABNORMAL",
                "judged_at": (base_time + timedelta(minutes=2)).isoformat(),
            },
        )
        assert changed.status_code == 201

        assert len(websocket.sent) == 2
        assert websocket.sent[0] == {
            "type": "person_status_changed",
            "payload": {
                "person_id": person_id,
                "previous_status": None,
                "status": "NORMAL",
                "judged_at": base_time.isoformat(),
            },
        }
        assert websocket.sent[1]["payload"]["previous_status"] == "NORMAL"
        assert websocket.sent[1]["payload"]["status"] == "ABNORMAL"
    finally:
        await realtime_event_manager.disconnect(user_id, cast(Any, websocket))


async def test_status_change_does_not_notify_other_users(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    owner_id = me.json()["id"]
    other_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "status-ws-other@example.com", "password": "password1234"},
    )
    other_user_id = other_signup.json()["user"]["id"]

    owner_ws = FakeWebSocket()
    other_ws = FakeWebSocket()
    await realtime_event_manager.connect(owner_id, cast(Any, owner_ws))
    await realtime_event_manager.connect(other_user_id, cast(Any, other_ws))

    try:
        await _create_person_and_sensor(client, auth_headers, device_id="STATUS-API-WS-002")
        await client.post(
            "/api/v1/status-events",
            headers=DEVICE_HEADERS,
            json={
                "event_id": "status-api-ws-4",
                "device_id": "STATUS-API-WS-002",
                "status": "ABNORMAL",
                "judged_at": datetime.now().isoformat(),
            },
        )

        assert len(owner_ws.sent) == 1
        assert other_ws.sent == []
    finally:
        await realtime_event_manager.disconnect(owner_id, cast(Any, owner_ws))
        await realtime_event_manager.disconnect(other_user_id, cast(Any, other_ws))
