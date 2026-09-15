from datetime import UTC, datetime

from httpx import AsyncClient


async def create_person(client: AsyncClient, headers: dict[str, str], name: str = "어머니") -> int:
    response = await client.post(
        "/api/v1/people",
        headers=headers,
        json={
            "name": name,
            "living_space": "서울 집",
            "monitoring_status": "ACTIVE",
            "inactivity_threshold_minutes": 45,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def alert_payload(person_id: int, external_id: str = "ai-event-1") -> dict:
    return {
        "person_id": person_id,
        "cause": "AI_ANOMALY",
        "severity": "WARNING",
        "title": "평소와 다른 활동",
        "description": "반복 행동이 감지됐어요.",
        "evidence": "10분 동안 현관 센서 7회",
        "source": "AI",
        "occurred_at": datetime.now(UTC).isoformat(),
        "external_id": external_id,
    }


async def test_alert_lifecycle_keeps_read_and_safety_confirmation_separate(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await create_person(client, auth_headers)
    created = await client.post(
        "/api/v1/alerts", headers=auth_headers, json=alert_payload(person_id)
    )

    assert created.status_code == 201
    alert_id = created.json()["id"]
    assert created.json()["read_at"] is None
    assert created.json()["safety_confirmed_at"] is None

    count = await client.get("/api/v1/alerts/unread-count", headers=auth_headers)
    assert count.json() == {"count": 1}

    read = await client.patch(f"/api/v1/alerts/{alert_id}/read", headers=auth_headers)
    assert read.json()["read_at"] is not None
    assert read.json()["safety_confirmed_at"] is None

    confirmed = await client.post(
        f"/api/v1/alerts/{alert_id}/safety-confirmations", headers=auth_headers
    )
    assert confirmed.json()["safety_confirmed_at"] is not None


async def test_duplicate_external_alert_is_suppressed(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await create_person(client, auth_headers)
    payload = alert_payload(person_id)

    first = await client.post("/api/v1/alerts", headers=auth_headers, json=payload)
    duplicate = await client.post("/api/v1/alerts", headers=auth_headers, json=payload)

    assert first.status_code == 201
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == first.json()["id"]


<<<<<<< HEAD
async def test_person_safety_confirmation_confirms_all_active_alerts(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await create_person(client, auth_headers)
    other_person_id = await create_person(client, auth_headers, name="아버지")
    first = await client.post(
        "/api/v1/alerts", headers=auth_headers, json=alert_payload(person_id, "event-1")
    )
    second = await client.post(
        "/api/v1/alerts", headers=auth_headers, json=alert_payload(person_id, "event-2")
    )
    other = await client.post(
        "/api/v1/alerts", headers=auth_headers, json=alert_payload(other_person_id, "event-3")
    )

    confirmed = await client.post(
        "/api/v1/alerts/safety-confirmations",
        params={"person_id": person_id},
        headers=auth_headers,
    )

    assert confirmed.status_code == 200
    assert {item["id"] for item in confirmed.json()} == {first.json()["id"], second.json()["id"]}
    assert all(item["read_at"] is not None for item in confirmed.json())
    assert all(item["safety_confirmed_at"] is not None for item in confirmed.json())

    remaining = await client.get(
        "/api/v1/alerts", params={"person_id": other_person_id}, headers=auth_headers
    )
    assert remaining.json()[0]["id"] == other.json()["id"]
    assert remaining.json()[0]["safety_confirmed_at"] is None
=======
async def test_single_safety_confirmation_also_confirms_all_owned_alerts(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await create_person(client, auth_headers)
    created_ids = []
    for index in range(2):
        response = await client.post(
            "/api/v1/alerts",
            headers=auth_headers,
            json=alert_payload(person_id, f"legacy-bulk-alert-{index}"),
        )
        assert response.status_code == 201
        created_ids.append(response.json()["id"])

    confirmed = await client.post(
        f"/api/v1/alerts/{created_ids[0]}/safety-confirmations",
        headers=auth_headers,
    )
    alerts = await client.get("/api/v1/alerts", headers=auth_headers)

    assert confirmed.status_code == 200
    assert all(alert["read_at"] is not None for alert in alerts.json())
    assert all(alert["safety_confirmed_at"] is not None for alert in alerts.json())


async def test_confirm_all_alert_safety_only_updates_owned_alerts(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await create_person(client, auth_headers)
    for index in range(2):
        response = await client.post(
            "/api/v1/alerts",
            headers=auth_headers,
            json=alert_payload(person_id, f"bulk-alert-{index}"),
        )
        assert response.status_code == 201

    confirmed = await client.post("/api/v1/alerts/safety-confirmations", headers=auth_headers)
    alerts = await client.get("/api/v1/alerts", headers=auth_headers)
    unread = await client.get("/api/v1/alerts/unread-count", headers=auth_headers)

    assert confirmed.status_code == 200
    assert confirmed.json() == {"count": 2}
    assert all(alert["read_at"] is not None for alert in alerts.json())
    assert all(alert["safety_confirmed_at"] is not None for alert in alerts.json())
    assert unread.json() == {"count": 0}
    assert (
        await client.post("/api/v1/alerts/safety-confirmations", headers=auth_headers)
    ).json() == {"count": 0}
>>>>>>> fabae5b951d7884041490ded438c2d534cae99d1


async def test_alert_access_is_limited_to_person_owner(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await create_person(client, auth_headers)
    created = await client.post(
        "/api/v1/alerts", headers=auth_headers, json=alert_payload(person_id)
    )

    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "other@example.com", "password": "password1234"},
    )
    other_headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}
    hidden = await client.get("/api/v1/alerts", headers=other_headers)
    forbidden = await client.patch(
        f"/api/v1/alerts/{created.json()['id']}/read", headers=other_headers
    )

    assert hidden.json() == []
    assert forbidden.status_code == 404


async def test_paused_person_does_not_accept_ai_alert(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await create_person(client, auth_headers)
    await client.patch(
        f"/api/v1/people/{person_id}",
        headers=auth_headers,
        json={"monitoring_status": "PAUSED"},
    )

    response = await client.post(
        "/api/v1/alerts", headers=auth_headers, json=alert_payload(person_id)
    )

    assert response.status_code == 409
