from datetime import datetime

from httpx import AsyncClient


async def create_auth_headers(
    client: AsyncClient, email: str
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password1234"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_people_are_isolated_by_user(client: AsyncClient) -> None:
    owner_headers = await create_auth_headers(client, "owner@example.com")
    other_headers = await create_auth_headers(client, "other@example.com")

    create_response = await client.post(
        "/api/v1/people",
        headers=owner_headers,
        json={"name": "소유자 대상자", "living_space": "집"},
    )
    person_id = create_response.json()["id"]

    other_list = await client.get("/api/v1/people", headers=other_headers)
    assert other_list.status_code == 200
    assert other_list.json() == []

    assert (
        await client.get(f"/api/v1/people/{person_id}", headers=other_headers)
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/people/{person_id}",
            headers=other_headers,
            json={"name": "변경 시도"},
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/people/{person_id}", headers=other_headers)
    ).status_code == 404

    owner_response = await client.get(
        f"/api/v1/people/{person_id}", headers=owner_headers
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["name"] == "소유자 대상자"


async def test_sensors_and_events_are_isolated_by_user(client: AsyncClient) -> None:
    owner_headers = await create_auth_headers(client, "owner@example.com")
    other_headers = await create_auth_headers(client, "other@example.com")

    person_response = await client.post(
        "/api/v1/people",
        headers=owner_headers,
        json={"name": "소유자 대상자", "living_space": "집"},
    )
    person_id = person_response.json()["id"]
    sensor_data = {
        "name": "현관 센서",
        "location": "현관",
        "device_id": "OWNER-SENSOR-001",
        "person_id": person_id,
        "target_object": "현관문",
        "status": "CONNECTED",
    }

    foreign_create = await client.post(
        "/api/v1/sensors", headers=other_headers, json=sensor_data
    )
    assert foreign_create.status_code == 404

    sensor_response = await client.post(
        "/api/v1/sensors", headers=owner_headers, json=sensor_data
    )
    assert sensor_response.status_code == 201
    sensor_id = sensor_response.json()["id"]

    assert (await client.get("/api/v1/sensors", headers=other_headers)).json() == []
    assert (
        await client.get(f"/api/v1/sensors/{sensor_id}", headers=other_headers)
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/sensors/{sensor_id}",
            headers=other_headers,
            json={"name": "변경 시도"},
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/sensors/{sensor_id}", headers=other_headers)
    ).status_code == 404

    event_data = {
        "person_id": person_id,
        "sensor_id": sensor_id,
        "detected_at": datetime.now().isoformat(),
        "detected_value": "OPEN",
        "sensor_status": "CONNECTED",
    }
    foreign_event = await client.post(
        "/api/v1/sensor-events", headers=other_headers, json=event_data
    )
    assert foreign_event.status_code == 404

    owner_event = await client.post(
        "/api/v1/sensor-events", headers=owner_headers, json=event_data
    )
    assert owner_event.status_code == 201
    assert (
        await client.get("/api/v1/sensor-events", headers=other_headers)
    ).json() == []
    assert (
        await client.get(
            f"/api/v1/sensor-events/people/{person_id}/timeline",
            headers=other_headers,
        )
    ).status_code == 404


async def test_sensor_event_requires_matching_person(client: AsyncClient) -> None:
    headers = await create_auth_headers(client, "owner@example.com")
    first_person = await client.post(
        "/api/v1/people",
        headers=headers,
        json={"name": "첫 번째 대상자", "living_space": "집"},
    )
    second_person = await client.post(
        "/api/v1/people",
        headers=headers,
        json={"name": "두 번째 대상자", "living_space": "집"},
    )
    sensor = await client.post(
        "/api/v1/sensors",
        headers=headers,
        json={
            "name": "현관 센서",
            "location": "현관",
            "device_id": "MATCH-SENSOR-001",
            "person_id": first_person.json()["id"],
            "target_object": "현관문",
            "status": "CONNECTED",
        },
    )

    response = await client.post(
        "/api/v1/sensor-events",
        headers=headers,
        json={
            "person_id": second_person.json()["id"],
            "sensor_id": sensor.json()["id"],
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
            "sensor_status": "CONNECTED",
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "SENSOR_PERSON_MISMATCH"
    assert body["detail"] == "선택한 센서는 해당 대상자에게 연결되어 있지 않습니다."
