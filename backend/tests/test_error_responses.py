from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from app.core.config import settings

DEVICE_HEADERS = {"X-Device-Key": "test-device-api-key"}


async def _create_person(client: AsyncClient, headers: dict[str, str]) -> int:
    response = await client.post(
        "/api/v1/people",
        headers=headers,
        json={"name": "테스트 대상자", "living_space": "집"},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_sensor(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    person_id: int,
    device_id: str,
    status: str = "CONNECTED",
) -> int:
    response = await client.post(
        "/api/v1/sensors",
        headers=headers,
        json={
            "name": "현관 센서",
            "location": "현관",
            "device_id": device_id,
            "person_id": person_id,
            "target_object": "현관문",
            "status": status,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_duplicate_email_returns_auth_email_already_registered(
    client: AsyncClient,
) -> None:
    credentials = {"email": "dup@example.com", "password": "password1234"}
    first = await client.post("/api/v1/auth/signup", json=credentials)
    assert first.status_code == 201

    response = await client.post("/api/v1/auth/signup", json=credentials)

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "AUTH_EMAIL_ALREADY_REGISTERED"
    assert body["message"] == "이미 가입된 이메일입니다."
    assert body["detail"] == "이미 가입된 이메일입니다."
    assert body["fields"] == []


async def test_login_failure_returns_auth_invalid_credentials(
    client: AsyncClient,
) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "login@example.com", "password": "password1234"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "AUTH_INVALID_CREDENTIALS"
    assert body["message"] == "이메일 또는 비밀번호가 올바르지 않습니다."
    assert body["detail"] == "이메일 또는 비밀번호가 올바르지 않습니다."
    assert body["fields"] == []


async def test_missing_token_returns_auth_invalid_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/people")

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "AUTH_INVALID_TOKEN"
    assert body["message"] == "인증 정보가 없거나 만료되었습니다."
    assert body["detail"] == "인증 정보가 없거나 만료되었습니다."
    assert body["fields"] == []


async def test_malformed_token_returns_auth_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/people",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "AUTH_INVALID_TOKEN"
    assert body["detail"] == "인증 정보가 없거나 만료되었습니다."


async def test_expired_token_returns_auth_invalid_token(client: AsyncClient) -> None:
    expired_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(
        "/api/v1/people",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "AUTH_INVALID_TOKEN"
    assert body["detail"] == "인증 정보가 없거나 만료되었습니다."


async def test_person_not_found(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/people/999999", headers=auth_headers)

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "PERSON_NOT_FOUND"
    assert body["message"] == "대상자를 찾을 수 없습니다."
    assert body["detail"] == "대상자를 찾을 수 없습니다."
    assert body["fields"] == []


async def test_sensor_not_found(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/sensors/999999", headers=auth_headers)

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "SENSOR_NOT_FOUND"
    assert body["message"] == "센서를 찾을 수 없습니다."
    assert body["detail"] == "센서를 찾을 수 없습니다."
    assert body["fields"] == []


async def test_sensor_device_id_conflict(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await _create_person(client, auth_headers)
    await _create_sensor(
        client, auth_headers, person_id=person_id, device_id="DUP-DEVICE-001"
    )

    response = await client.post(
        "/api/v1/sensors",
        headers=auth_headers,
        json={
            "name": "중복 센서",
            "location": "거실",
            "device_id": "DUP-DEVICE-001",
            "person_id": person_id,
            "target_object": "거실문",
            "status": "CONNECTED",
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "SENSOR_DEVICE_ID_CONFLICT"
    assert body["message"] == "이미 등록된 센서 고유번호입니다."
    assert body["detail"] == "이미 등록된 센서 고유번호입니다."
    assert body["fields"] == []


async def test_device_event_rejects_disconnected_sensor(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await _create_person(client, auth_headers)
    await _create_sensor(
        client,
        auth_headers,
        person_id=person_id,
        device_id="DISCONNECTED-001",
        status="DISCONNECTED",
    )

    response = await client.post(
        "/api/v1/device-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "evt-disconnected-001",
            "device_id": "DISCONNECTED-001",
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "SENSOR_NOT_CONNECTED"
    assert body["message"] == "센서가 연결되어 있지 않습니다."
    assert body["detail"] == "센서가 연결되어 있지 않습니다."
    assert body["fields"] == []


async def test_device_event_id_conflict(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    person_id = await _create_person(client, auth_headers)
    await _create_sensor(
        client, auth_headers, person_id=person_id, device_id="EVT-CONFLICT-A"
    )
    await _create_sensor(
        client, auth_headers, person_id=person_id, device_id="EVT-CONFLICT-B"
    )

    first = await client.post(
        "/api/v1/device-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "evt-shared-001",
            "device_id": "EVT-CONFLICT-A",
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
        },
    )
    assert first.status_code == 201

    response = await client.post(
        "/api/v1/device-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "evt-shared-001",
            "device_id": "EVT-CONFLICT-B",
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "EVENT_ID_CONFLICT"
    assert body["message"] == "동일한 이벤트 ID가 다른 데이터에 사용되었습니다."
    assert body["detail"] == "동일한 이벤트 ID가 다른 데이터에 사용되었습니다."
    assert body["fields"] == []


async def test_missing_required_field_returns_validation_error(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "novalidation@example.com"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "입력값을 확인해 주세요."
    assert body["detail"] == "입력값을 확인해 주세요."
    assert body["fields"] == [
        {"field": "body.password", "message": "필수 입력값입니다."}
    ]


async def test_unknown_route_returns_route_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "ROUTE_NOT_FOUND"
    assert body["message"] == "요청한 API를 찾을 수 없습니다."
    assert body["detail"] == "요청한 API를 찾을 수 없습니다."
    assert body["fields"] == []


async def test_device_api_key_not_configured(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "device_api_key", "")

    response = await client.post(
        "/api/v1/device-events",
        headers=DEVICE_HEADERS,
        json={
            "event_id": "evt-no-key-001",
            "device_id": "ANY-DEVICE",
            "detected_at": datetime.now().isoformat(),
            "detected_value": "OPEN",
        },
    )

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "DEVICE_API_KEY_NOT_CONFIGURED"
    assert body["message"] == "서버에 장치 인증 키가 설정되지 않았습니다."
    assert body["detail"] == "서버에 장치 인증 키가 설정되지 않았습니다."
    assert body["fields"] == []
