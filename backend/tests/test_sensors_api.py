from datetime import datetime

from httpx import AsyncClient


async def test_deleting_sensor_sets_sensor_event_sensor_id_null(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_response = await client.post(
        "/api/v1/people",
        json={"name": "테스트 대상자", "living_space": "집"},
        headers=auth_headers,
    )
    assert person_response.status_code == 201
    person_id = person_response.json()["id"]

    sensor_response = await client.post(
        "/api/v1/sensors",
        json={
            "name": "현관 센서",
            "location": "현관",
            "device_id": "TEST-SENSOR-DELETE-001",
            "person_id": person_id,
            "target_object": "현관문",
            "status": "CONNECTED",
        },
        headers=auth_headers,
    )
    assert sensor_response.status_code == 201
    sensor_id = sensor_response.json()["id"]

    event_response = await client.post(
        "/api/v1/sensor-events",
        json={
            "person_id": person_id,
            "sensor_id": sensor_id,
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
            "sensor_status": "CONNECTED",
        },
        headers=auth_headers,
    )
    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/sensors/{sensor_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    events_response = await client.get(
        "/api/v1/sensor-events",
        params={"person_id": person_id},
        headers=auth_headers,
    )
    assert events_response.status_code == 200
    events = events_response.json()

    assert len(events) == 1
    assert events[0]["id"] == event_id
    assert events[0]["sensor_id"] is None
