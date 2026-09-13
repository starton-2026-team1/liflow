import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.person import Person
from app.models.sensor import Sensor
from app.models.sensor_event import SensorEvent
from app.repositories.alert_repository import (
    create_alert,
    get_active_alert,
    get_alert_by_dedup_key,
    resolve_active_alerts,
)
from app.repositories.person_repository import get_person_owner_id
from app.schemas.alert import AlertResponse
from app.services.alert_service import utc_now
from app.services.realtime_event_service import realtime_event_manager

logger = logging.getLogger(__name__)


def within_check_window(now: datetime) -> bool:
    start = settings.alert_check_start_hour
    end = settings.alert_check_end_hour
    return start == end or (start < end and start <= now.hour < end) or (
        start > end and (now.hour >= start or now.hour < end)
    )


async def create_once(session: AsyncSession, **values: object):
    dedup_key = str(values["dedup_key"])
    existing = await get_alert_by_dedup_key(session, dedup_key)
    if existing is not None:
        return None
    return await create_alert(session, **values)


async def inspect_alert_conditions(session: AsyncSession, now: datetime | None = None) -> list:
    now = now or utc_now()
    if not within_check_window(now):
        return []

    people = list(
        (
            await session.scalars(
                select(Person).where(
                    Person.user_id.is_not(None), Person.monitoring_status == "ACTIVE"
                )
            )
        ).all()
    )
    created = []
    for person in people:
        sensors = list(
            (await session.scalars(select(Sensor).where(Sensor.person_id == person.id))).all()
        )
        disconnected = [sensor for sensor in sensors if sensor.status.upper() == "DISCONNECTED"]
        for sensor in disconnected:
            if await get_active_alert(
                session,
                person_id=person.id,
                cause="SENSOR_DISCONNECTED",
                sensor_id=sensor.id,
            ):
                continue
            alert = await create_once(
                session,
                person_id=person.id,
                sensor_id=sensor.id,
                cause="SENSOR_DISCONNECTED",
                severity="WARNING",
                title="센서 연결 상태 확인",
                description=f"{sensor.name}의 연결이 끊겼어요.",
                evidence=f"{sensor.location} · {sensor.target_object}",
                source="SYSTEM",
                dedup_key=f"sensor-disconnected:{sensor.id}:{now.isoformat()}",
                occurred_at=now,
            )
            if alert is not None:
                created.append(alert)

        for sensor in sensors:
            if sensor.status.upper() != "DISCONNECTED":
                await resolve_active_alerts(
                    session,
                    person_id=person.id,
                    cause="SENSOR_DISCONNECTED",
                    sensor_id=sensor.id,
                    resolved_at=now,
                )

        latest_at = await session.scalar(
            select(func.max(SensorEvent.detected_at)).where(SensorEvent.person_id == person.id)
        )
        if latest_at is None:
            continue
        if latest_at.tzinfo is not None:
            latest_at = latest_at.replace(tzinfo=None)
        threshold = timedelta(minutes=person.inactivity_threshold_minutes)
        if now - latest_at >= threshold:
            alert = await create_once(
                session,
                person_id=person.id,
                sensor_id=None,
                cause="INACTIVITY",
                severity="WARNING",
                title="장시간 움직임 없음",
                description=f"{person.inactivity_threshold_minutes}분 이상 움직임이 없어요.",
                evidence=f"마지막 감지 {latest_at.isoformat(timespec='minutes')}",
                source="SYSTEM",
                dedup_key=f"inactivity:{person.id}:{latest_at.isoformat()}",
                occurred_at=latest_at + threshold,
            )
            if alert is not None:
                created.append(alert)
        else:
            await resolve_active_alerts(
                session, person_id=person.id, cause="INACTIVITY", resolved_at=now
            )
    return created


async def run_alert_monitor(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            async with async_session_factory() as session:
                async with session.begin():
                    alerts = await inspect_alert_conditions(session)
                notifications = []
                for alert in alerts:
                    owner_id = await get_person_owner_id(session, alert.person_id)
                    if owner_id is not None:
                        notifications.append((owner_id, AlertResponse.model_validate(alert)))
            for owner_id, alert in notifications:
                await realtime_event_manager.publish_sensor_event(
                    owner_id,
                    {"type": "alert.created", "data": alert.model_dump(mode="json")},
                )
        except Exception:
            logger.exception("Alert monitor cycle failed")
        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=max(5, settings.alert_check_interval_seconds)
            )
        except TimeoutError:
            pass
