import re
from collections import Counter
from datetime import datetime, timedelta
from uuid import uuid4

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.chat_repository import list_chat_messages, save_chat_message
from app.repositories.sensor_event_repository import (
    list_person_sensor_events_between,
    list_sensor_events,
)
from app.repositories.sensor_repository import list_sensors
from app.schemas.ai_chat import ChatAnswer, ChatRequest
from app.schemas.sensor_event import WeeklyActivitySummaryResponse
from app.services.local_gemma_service import ask_local_gemma
from app.services.person_service import find_person_or_404

DISCLAIMER = (
    "AI 답변은 의료 진단이나 처방을 대신하지 않습니다. "
    "증상이 지속되면 의료진과 상담하세요."
)
UNCLEAR_QUESTION_RESPONSE = (
    "질문을 정확히 이해하지 못했어요. 내용을 조금 더 구체적으로 입력해 주세요. "
    "긴급한 의료 지원이 필요한 경우 즉시 119에 연락하세요.\n"
    "※ AI 답변은 의료진의 진단이나 처방을 대신하지 않습니다."
)
INSTRUCTIONS = """당신은 독거인 생활 안전 모니터링 서비스의 보호자 지원 AI입니다.
제공된 데이터에서 확인되는 사실과 추정을 구분하고 없는 사실은 만들지 마세요.
한국어로 간결하게 답하고 의료 진단, 처방 변경, 검증되지 않은 치료를 권하지 마세요.
민간요법을 물으면 일반적인 생활 보조 정보로만 설명하고 근거의 한계, 금기·상호작용 가능성,
의료진 상담 필요성을 함께 알리세요. 의식 저하, 호흡 곤란, 흉통, 마비, 심한 출혈 등 응급 징후가
언급되면 민간요법보다 119 신고와 즉시 의료 도움을 우선 안내하세요.
답변 마지막에는 반드시 '※ AI 답변은 의료 진단이나 처방을 대신하지 않습니다.'를 포함하세요."""
NON_MEDICAL_CLAUDE_INSTRUCTIONS = """당신은 생활 안전 서비스의 일반 정보 도우미입니다.
의학, 증상, 질병, 약물, 치료, 진단, 응급상황에 관한 질문에는 답하지 말고
'의료 관련 내용은 로컬 의료 AI와 의료진 상담을 이용해 주세요.'라고만 안내하세요.
그 외 일반적인 제품 사용법, 서비스 이용법, 일상 정보만 간결하게 답하세요."""
WEEKLY_SUMMARY_INSTRUCTIONS = """당신은 독거인 생활 안전 모니터링 서비스의 생활 기록 요약 도우미입니다.
제공된 센서 기록에서 직접 확인되는 사실만 사용해 한국어 존댓말로 두세 문장으로 요약하세요.
기록 수, 자주 감지된 활동, 첫 활동 시간대, 지난주 대비 변화 중 의미 있는 내용만 설명하세요.
대상자의 이름, ID, 전화번호는 쓰지 마세요. 건강 상태를 추측하거나 의료 진단·처방·위험 판단을 하지 마세요.
마크다운 제목이나 목록 없이 요약문만 출력하세요."""
MEDICAL_TERMS = (
    "증상", "질병", "병원", "의사", "약", "복용", "치료", "진단", "통증",
    "열", "기침", "감기", "독감", "혈압", "당뇨", "응급", "119", "출혈",
    "호흡", "흉통", "마비", "의식", "건강", "의학", "수술", "부작용",
)


def _is_medical_question(question: str) -> bool:
    return any(term in question.lower() for term in MEDICAL_TERMS)


def _is_unclear_question(question: str) -> bool:
    normalized = question.strip()
    return len(normalized) < 2 or re.search(r"[A-Za-z0-9가-힣]", normalized) is None


async def _ask_claude_with_instructions(
    messages: list[dict[str, str]], instructions: str
) -> str:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="Anthropic API key is not configured")

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": settings.anthropic_max_tokens,
        "system": instructions,
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
    if _is_unclear_question(data.question):
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
            content=UNCLEAR_QUESTION_RESPONSE,
            model="input-validation",
        )
        return ChatAnswer(
            conversation_id=conversation_id,
            answer=UNCLEAR_QUESTION_RESPONSE,
            model="input-validation",
            provider="local",
            disclaimer=DISCLAIMER,
        )
    if settings.local_ai_enabled:
        events = await list_sensor_events(
            session, user_id, person.id if person is not None else None, limit=50
        )
        sensor_context = (
            "대상자: " + (person.name or "알 수 없음")
            if person is not None
            else "대상자가 선택되지 않았습니다."
        )
        if events:
            sensor_context += "\n최근 센서 기록:\n" + "\n".join(
                f"- {event.detected_at.isoformat()} | 값={event.detected_value} | "
                f"상태={event.sensor_status} | AI={event.ai_label or '미분석'} "
                f"({event.ai_score if event.ai_score is not None else '-'})"
                for event in reversed(events)
            )
        else:
            sensor_context += "\n최근 센서 기록이 없습니다."
        try:
            answer = await ask_local_gemma(
                data.question,
                sensor_context,
                include_medical_knowledge=_is_medical_question(data.question),
            )
            model = "gemma-4-E2B-it-medical"
            provider = "local"
        except RuntimeError as exc:
            if _is_medical_question(data.question):
                raise HTTPException(
                    status_code=503,
                    detail="의료 질문에 답할 로컬 AI를 사용할 수 없습니다",
                ) from exc
            answer = await _ask_claude_with_instructions(
                [{"role": "user", "content": data.question}],
                NON_MEDICAL_CLAUDE_INSTRUCTIONS,
            )
            model = settings.anthropic_model
            provider = "anthropic"
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

    if _is_medical_question(data.question):
        answer = "의료 관련 내용은 로컬 의료 AI와 의료진 상담을 이용해 주세요."
    else:
        answer = await _ask_claude_with_instructions(messages, NON_MEDICAL_CLAUDE_INSTRUCTIONS)
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


async def summarize_weekly_activity(
    session: AsyncSession,
    user_id: int,
    person_id: int,
    now: datetime | None = None,
) -> WeeklyActivitySummaryResponse:
    await find_person_or_404(session, person_id, user_id)
    today = (now or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    period_start = today - timedelta(days=7)
    previous_start = period_start - timedelta(days=7)
    events = await list_person_sensor_events_between(
        session, person_id, previous_start, today
    )
    current_events = [event for event in events if event.detected_at >= period_start]
    previous_events = [event for event in events if event.detected_at < period_start]

    if not current_events:
        return WeeklyActivitySummaryResponse(
            summary="최근 7일에는 분석할 센서 기록이 없어요. 기록이 쌓이면 생활 패턴을 요약해드릴게요.",
            period_start=period_start.date(),
            period_end=(today - timedelta(days=1)).date(),
            event_count=0,
            provider="local",
            model="deterministic",
        )

    sensors = {
        sensor.id: sensor
        for sensor in await list_sensors(session, user_id)
        if sensor.person_id == person_id
    }
    daily_lines = []
    for offset in range(7):
        day = period_start + timedelta(days=offset)
        day_end = day + timedelta(days=1)
        day_events = [
            event for event in current_events if day <= event.detected_at < day_end
        ]
        if not day_events:
            daily_lines.append(f"- {day.date().isoformat()}: 기록 없음")
            continue
        daily_lines.append(
            f"- {day.date().isoformat()}: {len(day_events)}건, "
            f"첫 활동 {day_events[0].detected_at.strftime('%H:%M')}, "
            f"마지막 활동 {day_events[-1].detected_at.strftime('%H:%M')}"
        )

    activity_counts = Counter()
    for event in current_events:
        sensor = sensors.get(event.sensor_id)
        sensor_label = sensor.name if sensor is not None else "기타 센서"
        value = event.detected_value.strip()
        activity = (
            value
            if value and not re.fullmatch(r"[-+]?\d+(\.\d+)?", value)
            else sensor_label
        )
        activity_counts[activity] += 1
    top_activities = ", ".join(
        f"{name} {count}건" for name, count in activity_counts.most_common(8)
    )
    anomaly_count = sum(event.ai_is_anomaly is True for event in current_events)
    comparison = (
        "지난주 기록 없음"
        if not previous_events
        else f"지난주 {len(previous_events)}건 대비 이번 주 {len(current_events)}건"
    )
    prompt = "\n".join(
        [
            f"분석 기간: {period_start.date().isoformat()} ~ {(today - timedelta(days=1)).date().isoformat()}",
            f"이번 주 전체 기록: {len(current_events)}건",
            f"비교: {comparison}",
            f"AI 이상 감지: {anomaly_count}건",
            f"주요 활동: {top_activities or '분류 가능한 활동 없음'}",
            "일별 기록:",
            *daily_lines,
        ]
    )
    answer = await _ask_claude_with_instructions(
        [{"role": "user", "content": prompt}], WEEKLY_SUMMARY_INSTRUCTIONS
    )
    if not answer:
        raise HTTPException(status_code=503, detail="AI returned an empty summary")
    return WeeklyActivitySummaryResponse(
        summary=answer,
        period_start=period_start.date(),
        period_end=(today - timedelta(days=1)).date(),
        event_count=len(current_events),
        provider="anthropic",
        model=settings.anthropic_model,
    )
