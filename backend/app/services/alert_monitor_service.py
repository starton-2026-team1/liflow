import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
from app.services.alert_notification_service import notify_alert
from app.services.inactivity_baseline_service import (
    DAYTIME_END_HOUR,
    DAYTIME_START_HOUR,
    MIN_INTERVAL_COUNT,
    format_duration,
    get_inactivity_baseline,
)

logger = logging.getLogger(__name__)


def monitoring_now() -> datetime:
    try:
        timezone = ZoneInfo(settings.monitoring_timezone)
    except ZoneInfoNotFoundError:
        logger.error(
            "Unknown monitoring timezone %s; falling back to UTC",
            settings.monitoring_timezone,
        )
        timezone = ZoneInfo("UTC")
    return datetime.now(timezone).replace(tzinfo=None)


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
    now = now or monitoring_now()
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
        if not DAYTIME_START_HOUR <= now.hour < DAYTIME_END_HOUR:
            continue

        baseline = await get_inactivity_baseline(
            session, person.id, person.inactivity_threshold_minutes, now
        )
        threshold = timedelta(minutes=baseline.threshold_minutes)
        daytime_start = now.replace(
            hour=DAYTIME_START_HOUR, minute=0, second=0, microsecond=0
        )
        inactivity_started_at = max(latest_at, daytime_start)
        inactivity_minutes = max(0, int((now - inactivity_started_at).total_seconds() // 60))
        if inactivity_minutes >= baseline.threshold_minutes:
            if baseline.is_personalized:
                description = (
                    "최근 2주 동안 낮 시간에는 평균 "
                    f"{format_duration(baseline.average_interval_minutes or 0)}마다 "
                    "활동이 감지됐어요. "
                    f"현재 {format_duration(inactivity_minutes)} 동안 활동이 없어 평소보다 긴 "
                    "미활동 상태입니다. 대상자의 상태를 확인해 주세요."
                )
                evidence = (
                    f"최근 2주 활동 간격 {baseline.interval_count}개 · "
                    f"95백분위 {format_duration(baseline.percentile_95_minutes or 0)} · "
                    f"개인화 기준 {format_duration(baseline.threshold_minutes)}"
                )
            else:
                description = (
                    f"현재 {format_duration(inactivity_minutes)} 동안 활동이 없어요. "
                    "생활 기록이 더 쌓일 때까지 안전 기본 기준을 적용합니다. "
                    "대상자의 상태를 확인해 주세요."
                )
                evidence = (
                    f"표본 {baseline.interval_count}/{MIN_INTERVAL_COUNT}개 · "
                    f"임시 기준 {format_duration(baseline.threshold_minutes)}"
                )
            alert = await create_once(
                session,
                person_id=person.id,
                sensor_id=None,
                cause="INACTIVITY",
                severity="WARNING",
                title="장시간 움직임 없음",
                description=description,
                evidence=evidence,
                source="SYSTEM",
                dedup_key=f"inactivity:{person.id}:{latest_at.isoformat()}",
                occurred_at=inactivity_started_at + threshold,
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
                for alert in alerts:
                    owner_id = await get_person_owner_id(session, alert.person_id)
                    if owner_id is not None:
                        payload = AlertResponse.model_validate(alert).model_dump(mode="json")
                        await notify_alert(session, owner_id, payload)
                await session.commit()
        except Exception:
            logger.exception("Alert monitor cycle failed")
        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=max(5, settings.alert_check_interval_seconds)
            )
        except TimeoutError:
            pass
