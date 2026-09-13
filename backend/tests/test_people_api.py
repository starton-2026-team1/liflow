from httpx import AsyncClient


async def test_person_crud(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create_response = await client.post(
        "/api/v1/people",
        json={
            "name": "테스트 대상자",
            "age_group": "70대",
            "phone": None,
            "living_space": "집",
            "health_notes": None,
            "monitoring_status": "PAUSED",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    person_id = create_response.json()["id"]

    list_response = await client.get("/api/v1/people", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = await client.patch(
        f"/api/v1/people/{person_id}",
        json={"monitoring_status": "ACTIVE"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["monitoring_status"] == "ACTIVE"

    sensor_response = await client.post(
        "/api/v1/sensors",
        json={
            "name": "삭제 확인 센서",
            "location": "현관",
            "device_id": "CASCADE-SENSOR-001",
            "person_id": person_id,
            "target_object": "현관문",
            "status": "CONNECTED",
        },
        headers=auth_headers,
    )
    assert sensor_response.status_code == 201

    delete_response = await client.delete(
        f"/api/v1/people/{person_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    sensors_response = await client.get("/api/v1/sensors", headers=auth_headers)
    assert sensors_response.status_code == 200
    assert sensors_response.json() == []

    missing_response = await client.get(
        f"/api/v1/people/{person_id}", headers=auth_headers
    )
    assert missing_response.status_code == 404
