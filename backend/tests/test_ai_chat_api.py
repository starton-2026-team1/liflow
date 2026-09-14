from typing import Any
from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.core.config import settings
from app.schemas.ai_chat import ChatAnswer
from app.schemas.websocket import SocketRequest
from app.services import socket_rpc_service


class FakeClaude:
    def __init__(self) -> None:
        self.requests: list[list[dict[str, str]]] = []

    async def ask(self, messages: list[dict[str, str]]) -> str:
        self.requests.append(messages)
        return (
            "최근 활동 기록은 평소 범위예요. "
            "※ AI 답변은 의료 진단이나 처방을 대신하지 않습니다."
        )


async def create_person(client: AsyncClient, headers: dict[str, str]) -> int:
    response = await client.post(
        "/api/v1/people",
        headers=headers,
        json={"name": "아버지", "living_space": "부산 집", "monitoring_status": "ACTIVE"},
    )
    return response.json()["id"]


async def test_person_chat_is_disabled_without_sending_data_to_claude(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: Any
) -> None:
    person_id = await create_person(client, auth_headers)
    monkeypatch.setattr(settings, "local_ai_enabled", True)
    local_ai = AsyncMock(side_effect=RuntimeError("GPU unavailable"))
    claude = AsyncMock(side_effect=AssertionError("Claude must not be called"))
    monkeypatch.setattr("app.services.ai_chat_service.ask_local_gemma", local_ai)
    monkeypatch.setattr(
        "app.services.ai_chat_service._ask_claude_with_instructions", claude
    )

    response = await client.post(
        "/api/v1/ai-chat/messages",
        headers=auth_headers,
        json={"person_id": person_id, "question": "최근 건강 상태는 어때?"},
    )

    assert response.status_code == 503
    assert "로컬 AI" in response.json()["detail"]
    claude.assert_not_awaited()


async def test_chat_rejects_other_guardians_person(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: Any
) -> None:
    person_id = await create_person(client, auth_headers)
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "chat-other@example.com", "password": "password1234"},
    )
    other_headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")

    response = await client.post(
        "/api/v1/ai-chat/messages",
        headers=other_headers,
        json={"person_id": person_id, "question": "건강 상태를 알려줘"},
    )

    assert response.status_code == 404


async def test_person_chat_stays_disabled_when_anthropic_key_exists(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: Any
) -> None:
    person_id = await create_person(client, auth_headers)
    monkeypatch.setattr(settings, "local_ai_enabled", True)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.ai_chat_service.ask_local_gemma",
        AsyncMock(side_effect=RuntimeError("GPU unavailable")),
    )

    response = await client.post(
        "/api/v1/ai-chat/messages",
        headers=auth_headers,
        json={"person_id": person_id, "question": "상태를 알려줘"},
    )

    assert response.status_code == 503


async def test_general_question_does_not_require_a_person(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: Any
) -> None:
    fake_claude = FakeClaude()
    monkeypatch.setattr(settings, "local_ai_enabled", False)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.ai_chat_service._ask_claude_with_instructions",
        lambda messages, _instructions: fake_claude.ask(messages),
    )

    response = await client.post(
        "/api/v1/ai-chat/messages",
        headers=auth_headers,
        json={"question": "생강차를 마실 때 주의할 점은?"},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "anthropic"
    assert fake_claude.requests[0][-1]["content"] == "생강차를 마실 때 주의할 점은?"


async def test_local_ai_chat_without_person_saves_nullable_person(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: Any
) -> None:
    monkeypatch.setattr(settings, "local_ai_enabled", True)
    monkeypatch.setattr(
        "app.services.ai_chat_service.ask_local_gemma",
        AsyncMock(return_value="센서 기록을 확인했습니다."),
    )

    response = await client.post(
        "/api/v1/ai-chat/messages",
        headers=auth_headers,
        json={"question": "최근 상태를 알려줘"},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "local"


async def test_non_medical_local_failure_falls_back_to_claude(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: Any
) -> None:
    monkeypatch.setattr(settings, "local_ai_enabled", True)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(
        "app.services.ai_chat_service.ask_local_gemma",
        AsyncMock(side_effect=RuntimeError("GPU unavailable")),
    )
    monkeypatch.setattr(
        "app.services.ai_chat_service._ask_claude_with_instructions",
        AsyncMock(return_value="서비스 사용법 답변"),
    )

    response = await client.post(
        "/api/v1/ai-chat/messages",
        headers=auth_headers,
        json={"question": "알림 설정 방법을 알려줘"},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "anthropic"


async def test_chat_is_available_through_authenticated_websocket_rpc(
    monkeypatch: Any,
) -> None:
    async def fake_ask_ai(_session: Any, user_id: int, data: Any) -> ChatAnswer:
        assert user_id == 7
        assert data.question == "건강관리 방법을 알려줘"
        return ChatAnswer(
            conversation_id="00000000-0000-0000-0000-000000000001",
            answer="충분한 수분을 섭취하세요.",
            model="claude-sonnet-4-6",
            provider="anthropic",
            disclaimer="참고용 답변입니다.",
        )

    monkeypatch.setattr(socket_rpc_service, "ask_ai", fake_ask_ai)
    request = SocketRequest(
        type="request",
        id="ai-test",
        method="POST",
        path="/ai-chat/messages",
        body={"question": "건강관리 방법을 알려줘"},
    )

    result = await socket_rpc_service.dispatch_socket_request(
        object(), request, type("User", (), {"id": 7})()
    )

    assert result.status == 200
    assert result.data["provider"] == "anthropic"
