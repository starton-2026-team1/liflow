from uuid import uuid4

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.chat_repository import list_chat_messages, save_chat_message
from app.schemas.ai_chat import ChatAnswer, ChatRequest
from app.services.person_service import find_person_or_404

DISCLAIMER = (
    "AI 답변은 의료 진단이나 처방을 대신하지 않습니다. "
    "증상이 지속되면 의료진과 상담하세요."
)
INSTRUCTIONS = """당신은 독거인 생활 안전 모니터링 서비스의 보호자 지원 AI입니다.
제공된 데이터에서 확인되는 사실과 추정을 구분하고 없는 사실은 만들지 마세요.
한국어로 간결하게 답하고 의료 진단, 처방 변경, 검증되지 않은 치료를 권하지 마세요.
민간요법을 물으면 일반적인 생활 보조 정보로만 설명하고 근거의 한계, 금기·상호작용 가능성,
의료진 상담 필요성을 함께 알리세요. 의식 저하, 호흡 곤란, 흉통, 마비, 심한 출혈 등 응급 징후가
언급되면 민간요법보다 119 신고와 즉시 의료 도움을 우선 안내하세요.
답변 마지막에는 반드시 '※ AI 답변은 의료 진단이나 처방을 대신하지 않습니다.'를 포함하세요."""


async def _ask_claude(messages: list[dict[str, str]]) -> str:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="Anthropic API key is not configured")

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 800,
        "system": INSTRUCTIONS,
        "messages": messages,
    }
    try:
        async with httpx.AsyncClient(
            base_url=settings.anthropic_base_url, timeout=60.0
        ) as client:
            response = await client.post(
                "/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json=payload,
            )
            response.raise_for_status()
            blocks = response.json().get("content", [])
    except (httpx.HTTPError, ValueError, AttributeError) as exc:
        raise HTTPException(
            status_code=503, detail="Claude service is temporarily unavailable"
        ) from exc
    return "".join(
        block.get("text", "")
        for block in blocks
        if block.get("type") == "text"
    ).strip()


async def ask_ai(session: AsyncSession, user_id: int, data: ChatRequest) -> ChatAnswer:
    person = (
        await find_person_or_404(session, data.person_id, user_id)
        if data.person_id is not None
        else None
    )
    conversation_id = data.conversation_id or str(uuid4())
    history = await list_chat_messages(session, user_id, conversation_id)
    if person is not None:
        raise HTTPException(
            status_code=503,
            detail="대상자 기록 AI 분석은 로컬 모델 준비 후 제공됩니다",
        )
    # 일반 Claude 상담에는 대상자와 연결된 과거 메시지를 포함하지 않는다.
    allowed_history = (
        [message for message in history if message.person_id is None]
        if person is None
        else [
            message
            for message in history
            if message.person_id is None or message.person_id == person.id
        ]
    )
    messages = [
        {"role": message.role, "content": message.content}
        for message in allowed_history
    ]
    messages.append({"role": "user", "content": data.question})

    answer = await _ask_claude(messages)
    model = settings.anthropic_model
    provider = "anthropic"
    if not answer:
        raise HTTPException(status_code=503, detail="AI returned an empty response")

    await save_chat_message(
        session,
        conversation_id=conversation_id,
        user_id=user_id,
        person_id=person.id if person is not None else None,
        role="user",
        content=data.question,
        model=None,
    )
    await save_chat_message(
        session,
        conversation_id=conversation_id,
        user_id=user_id,
        person_id=person.id if person is not None else None,
        role="assistant",
        content=answer,
        model=model,
    )
    return ChatAnswer(
        conversation_id=conversation_id,
        answer=answer,
        model=model,
        provider=provider,
        disclaimer=DISCLAIMER,
    )
