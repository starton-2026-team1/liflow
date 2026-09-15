from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.repositories.alert_repository import (
    confirm_all_owned_alerts,
    create_alert,
    get_active_alert,
    get_alert_by_dedup_key,
    get_owned_alert,
    list_unconfirmed_alerts_for_person,
)
from app.repositories.person_repository import get_owned_person
from app.repositories.sensor_repository import get_owned_sensor
from app.schemas.alert import AlertCreate


def utc_now() -> datetime:
    # MySQL DateTime is stored as timezone-naive UTC throughout this project.
    return datetime.now(UTC).replace(tzinfo=None)


async def find_alert_or_404(session: AsyncSession, alert_id: int, user_id: int) -> Alert:
    alert = await get_owned_alert(session, alert_id, user_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


async def mark_alert_read(session: AsyncSession, alert_id: int, user_id: int) -> Alert:
    alert = await find_alert_or_404(session, alert_id, user_id)
    if alert.read_at is None:
        alert.read_at = utc_now()
        await session.flush()
        await session.refresh(alert)
    return alert


async def confirm_alert_safety(session: AsyncSession, alert_id: int, user_id: int) -> Alert:
    alert = await find_alert_or_404(session, alert_id, user_id)
    now = utc_now()
    await confirm_all_owned_alerts(session, user_id, now)
    await session.refresh(alert)
    return alert


async def confirm_person_safety(session: AsyncSession, person_id: int, user_id: int) -> list[Alert]:
    person = await get_owned_person(session, person_id, user_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    alerts = await list_unconfirmed_alerts_for_person(session, person_id=person_id, user_id=user_id)
    now = utc_now()
    for alert in alerts:
        if alert.read_at is None:
            alert.read_at = now
        alert.safety_confirmed_at = now
    await session.flush()
    for alert in alerts:
        await session.refresh(alert)
    return alerts


async def confirm_all_alert_safety(session: AsyncSession, user_id: int) -> int:
    return await confirm_all_owned_alerts(session, user_id, utc_now())


async def create_external_alert(
    session: AsyncSession, user_id: int, data: AlertCreate
) -> tuple[Alert, bool]:
    person = await get_owned_person(session, data.person_id, user_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    if person.monitoring_status.upper() != "ACTIVE":
        raise HTTPException(status_code=409, detail="Person monitoring is paused")
    if data.sensor_id is not None:
        sensor = await get_owned_sensor(session, data.sensor_id, user_id)
        if sensor is None or sensor.person_id != person.id:
            raise HTTPException(status_code=404, detail="Sensor not found")
    dedup_key = f"external:{data.source}:{data.external_id}"
    existing = await get_alert_by_dedup_key(session, dedup_key)
    if existing is not None:
        return existing, False
    try:
        async with session.begin_nested():
            alert = await create_alert(
                session,
                **data.model_dump(exclude={"external_id"}),
                dedup_key=dedup_key,
            )
        return alert, True
    except IntegrityError:
        existing = await get_alert_by_dedup_key(session, dedup_key)
        if existing is None:
            raise
        return existing, False


async def create_ai_abnormal_alert(
    session: AsyncSession,
    *,
    person_id: int,
    sensor_id: int,
    external_event_id: str,
    occurred_at: datetime,
    detected_value: str | None,
) -> tuple[Alert, bool]:
    existing = await get_active_alert(
        session,
        person_id=person_id,
        sensor_id=sensor_id,
        cause="ABNORMAL_BEHAVIOR",
    )
    if existing is not None:
        return existing, False
    alert = await create_alert(
        session,
        person_id=person_id,
        sensor_id=sensor_id,
        cause="ABNORMAL_BEHAVIOR",
        severity="WARNING",
        title="이상행동 감지",
        description="센서 AI가 평소와 다른 행동을 감지했어요. 대상자의 상태를 확인해 주세요.",
        evidence=(
            f"AI 판정 센서값: {detected_value}"
            if detected_value is not None
            else "AI 이상행동 판정"
        ),
        source="AI",
        dedup_key=f"ai-abnormal:{external_event_id}",
        occurred_at=occurred_at,
    )
    return alert, True
