from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.repositories.alert_repository import create_alert, get_alert_by_dedup_key, get_owned_alert
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
    if alert.read_at is None:
        alert.read_at = now
    if alert.safety_confirmed_at is None:
        alert.safety_confirmed_at = now
    await session.flush()
    await session.refresh(alert)
    return alert


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
