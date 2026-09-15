from datetime import UTC, datetime
from hashlib import sha256
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.core.database import get_db_session
from app.models.alert import Alert
from app.models.nfc_tag import NfcHelpEvent, NfcTag
from app.models.person import Person
from app.repositories.alert_repository import create_alert
from app.repositories.person_repository import get_owned_person
from app.schemas.alert import AlertResponse
from app.schemas.nfc_tag import (
    NfcContactResponse,
    NfcHelpCreated,
    NfcHelpPage,
    NfcHelpStatus,
    NfcTagCreate,
    NfcTagResponse,
)
from app.services.alert_notification_service import notify_alert

router = APIRouter()
public_router = APIRouter()


def digest(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def find_tag(session: AsyncSession, token: str) -> NfcTag:
    tag = await session.scalar(
        select(NfcTag).where(NfcTag.public_token_hash == digest(token), NfcTag.is_active.is_(True))
    )
    if tag is None:
        raise HTTPException(404, "안심태그를 찾을 수 없습니다.")
    return tag


async def find_event(session: AsyncSession, event_id: int, finder_token: str):
    row = (
        await session.execute(
            select(NfcHelpEvent, Alert, NfcTag)
            .join(Alert, Alert.id == NfcHelpEvent.alert_id)
            .join(NfcTag, NfcTag.id == NfcHelpEvent.nfc_tag_id)
            .where(
                NfcHelpEvent.id == event_id, NfcHelpEvent.finder_token_hash == digest(finder_token)
            )
        )
    ).first()
    if row is None:
        raise HTTPException(404, "발견 기록을 찾을 수 없습니다.")
    return row


@router.post("", response_model=NfcTagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: NfcTagCreate, current_user: CurrentUser, session: AsyncSession = Depends(get_db_session)
):
    if await get_owned_person(session, data.person_id, current_user.id) is None:
        raise HTTPException(404, "Person not found")
    token = token_urlsafe(32)
    tag = NfcTag(
        **data.model_dump(),
        guardian_name="보호자",
        public_token_hash=digest(token),
    )
    session.add(tag)
    await session.flush()
    return NfcTagResponse(
        id=tag.id, public_url=f"{settings.public_frontend_url.rstrip('/')}/nfc/help/{token}"
    )


@public_router.get("/{token}", response_model=NfcHelpPage)
async def help_page(token: str, session: AsyncSession = Depends(get_db_session)):
    tag = await find_tag(session, token)
    return NfcHelpPage(tag_name=tag.name)


@public_router.post("/{token}/alerts", response_model=NfcHelpCreated)
async def send_help(token: str, session: AsyncSession = Depends(get_db_session)):
    tag = await find_tag(session, token)
    person = await session.get(Person, tag.person_id)
    if person is None or person.user_id is None:
        raise HTTPException(404, "대상자를 찾을 수 없습니다.")
    now = utc_now()
    alert = await create_alert(
        session,
        person_id=person.id,
        sensor_id=None,
        cause="NFC_HELP",
        severity="WARNING",
        title="안심태그 발견 알림",
        description="외부에서 안심태그를 확인한 분이 보호자에게 알림을 보냈습니다.",
        evidence="안심태그 알림 버튼이 눌렸습니다.",
        source="NFC",
        occurred_at=now,
        dedup_key=f"nfc:{tag.id}:{token_urlsafe(12)}",
    )
    finder_token = token_urlsafe(32)
    event = NfcHelpEvent(
        nfc_tag_id=tag.id, alert_id=alert.id, finder_token_hash=digest(finder_token)
    )
    session.add(event)
    await session.flush()
    await notify_alert(
        session, person.user_id, AlertResponse.model_validate(alert).model_dump(mode="json")
    )
    return NfcHelpCreated(
        event_id=event.id,
        finder_token=finder_token,
        contact_available_at=now if tag.contact_reveal_enabled else None,
        message="보호자에게 알림을 보냈습니다.",
    )


@public_router.get("/events/{event_id}", response_model=NfcHelpStatus)
async def help_status(
    event_id: int,
    finder_token: str = Query(min_length=20),
    session: AsyncSession = Depends(get_db_session),
):
    event, alert, tag = await find_event(session, event_id, finder_token)
    acknowledged = alert.safety_confirmed_at is not None
    return NfcHelpStatus(
        acknowledged=acknowledged,
        contact_available=tag.contact_reveal_enabled,
        contact_available_at=event.requested_at if tag.contact_reveal_enabled else None,
    )


@public_router.post("/events/{event_id}/contact", response_model=NfcContactResponse)
async def reveal_contact(
    event_id: int,
    finder_token: str = Query(min_length=20),
    session: AsyncSession = Depends(get_db_session),
):
    event, _alert, tag = await find_event(session, event_id, finder_token)
    if not tag.contact_reveal_enabled:
        raise HTTPException(403, "연락처를 확인할 수 없습니다.")
    event.contact_revealed_at = event.contact_revealed_at or utc_now()
    await session.flush()
    return NfcContactResponse(guardian_phone=tag.guardian_phone)
