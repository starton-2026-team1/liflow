from typing import Any

import httpx
import pytest

from app.core.config import settings
from app.services.local_gemma_service import ask_local_gemma


async def test_local_gemma_calls_configured_gpu_api(monkeypatch: Any) -> None:
    request_seen: httpx.Request | None = None

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal request_seen
        request_seen = request
        return httpx.Response(200, json={"answer": "로컬 모델 답변"})

    transport = httpx.MockTransport(handle)
    real_async_client = httpx.AsyncClient

    def create_client(**kwargs: Any) -> httpx.AsyncClient:
        return real_async_client(transport=transport, **kwargs)

    monkeypatch.setattr(settings, "local_ai_api_url", "http://gpu.internal:9000")
    monkeypatch.setattr(settings, "local_ai_api_key", "secret-key")
    monkeypatch.setattr(httpx, "AsyncClient", create_client)

    answer = await ask_local_gemma("질문", "센서 기록")

    assert answer == "로컬 모델 답변"
    assert request_seen is not None
    assert request_seen.url == "http://gpu.internal:9000/generate"
    assert request_seen.headers["X-API-Key"] == "secret-key"


async def test_local_gemma_requires_api_configuration(monkeypatch: Any) -> None:
    monkeypatch.setattr(settings, "local_ai_api_url", "")
    monkeypatch.setattr(settings, "local_ai_api_key", "")

    with pytest.raises(RuntimeError, match="설정"):
        await ask_local_gemma("질문", "센서 기록")
