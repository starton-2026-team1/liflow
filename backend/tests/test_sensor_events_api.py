from datetime import datetime, timedelta

from httpx import AsyncClient


async def test_sensor_event_flow(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_response = await client.post(
        "/api/v1/people",
        json={"name": "테스트 대상자", "living_space": "집"},
        headers=auth_headers,
    )
    person_id = person_response.json()["id"]

    sensor_response = await client.post(
        "/api/v1/sensors",
        json={
            "name": "현관 센서",
            "location": "현관",
            "device_id": "TEST-SENSOR-001",
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

    timeline_response = await client.get(
        f"/api/v1/sensor-events/people/{person_id}/timeline",
        headers=auth_headers,
    )
    assert timeline_response.status_code == 200
    assert len(timeline_response.json()) == 1
    assert timeline_response.json()[0]["detected_value"] == "OPEN"


async def test_sensor_event_rejects_missing_relations(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/sensor-events",
        json={
            "person_id": 999,
            "sensor_id": 999,
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
            "sensor_status": "CONNECTED",
        },
        headers=auth_headers,
    )
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "PERSON_NOT_FOUND"
    assert body["detail"] == "대상자를 찾을 수 없습니다."


async def test_weekly_summary_reuses_cache_until_a_new_event_arrives(
    client: AsyncClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    person_response = await client.post(
        "/api/v1/people",
        json={"name": "요약 대상자", "living_space": "집"},
        headers=auth_headers,
    )
    person_id = person_response.json()["id"]
    sensor_response = await client.post(
        "/api/v1/sensors",
        json={
            "name": "복약 센서",
            "location": "거실",
            "device_id": "SUMMARY-SENSOR-001",
            "person_id": person_id,
            "target_object": "약 보관함",
            "status": "CONNECTED",
        },
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/sensor-events",
        json={
            "person_id": person_id,
            "sensor_id": sensor_response.json()["id"],
            "detected_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "detected_value": "저녁 복약함 열림",
            "sensor_status": "CONNECTED",
        },
        headers=auth_headers,
    )

    claude_calls = 0

    async def fake_claude(messages, instructions):
        nonlocal claude_calls
        claude_calls += 1
        assert "저녁 복약함 열림" in messages[0]["content"]
        assert "의료 진단" in instructions
        return f"Claude 호출 {claude_calls}회 요약"

    monkeypatch.setattr(
        "app.services.ai_chat_service._ask_claude_with_instructions",
        fake_claude,
    )
    first_response = await client.get(
        f"/api/v1/sensor-events/people/{person_id}/weekly-summary",
        headers=auth_headers,
    )
    cached_response = await client.get(
        f"/api/v1/sensor-events/people/{person_id}/weekly-summary",
        headers=auth_headers,
    )

    await client.post(
        "/api/v1/sensor-events",
        json={
            "person_id": person_id,
            "sensor_id": sensor_response.json()["id"],
            "detected_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "detected_value": "저녁 복약함 열림",
            "sensor_status": "CONNECTED",
        },
        headers=auth_headers,
    )
    refreshed_response = await client.get(
        f"/api/v1/sensor-events/people/{person_id}/weekly-summary",
        headers=auth_headers,
    )

    assert first_response.status_code == 200
    assert first_response.json()["summary"] == "Claude 호출 1회 요약"
    assert cached_response.json()["summary"] == "Claude 호출 1회 요약"
    assert refreshed_response.json()["summary"] == "Claude 호출 2회 요약"
    assert refreshed_response.json()["event_count"] == 2
    assert refreshed_response.json()["provider"] == "anthropic"
    assert claude_calls == 2
