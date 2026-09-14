import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

async def ask_local_gemma(
    question: str, sensor_context: str, include_medical_knowledge: bool = False
) -> str:
    if not settings.local_ai_api_url or not settings.local_ai_api_key:
        raise RuntimeError("로컬 AI API 설정이 없습니다")

    try:
        async with httpx.AsyncClient(
            timeout=settings.local_ai_timeout_seconds
        ) as client:
            response = await client.post(
                f"{settings.local_ai_api_url.rstrip('/')}/generate",
                headers={"X-API-Key": settings.local_ai_api_key},
                json={
                    "question": question,
                    "sensor_context": sensor_context,
                    "include_medical_knowledge": include_medical_knowledge,
                },
            )
            response.raise_for_status()
            answer = response.json().get("answer", "").strip()
    except (httpx.HTTPError, ValueError, AttributeError) as exc:
        logger.exception("Remote Gemma inference failed")
        raise RuntimeError("로컬 AI 추론에 실패했습니다") from exc
    if not answer:
        raise RuntimeError("로컬 AI가 빈 답변을 반환했습니다")
    return answer
