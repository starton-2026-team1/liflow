import asyncio
import logging
import random
from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.person import Person

logger = logging.getLogger(__name__)

DEADLOCK_ERROR_CODE = 1213
RESOLVE_ALERTS_MAX_ATTEMPTS = 3


def _is_deadlock(exc: OperationalError) -> bool:
    orig_args = getattr(exc.orig, "args", ())
    return bool(orig_args) and orig_args[0] == DEADLOCK_ERROR_CODE


def owned_alerts_query(user_id: int) -> Select[tuple[Alert]]:
    return select(Alert).join(Person, Person.id == Alert.person_id).where(Person.user_id == user_id)


async def list_alerts(
    session: AsyncSession, user_id: int, person_id: int | None, unread_only: bool, limit: int
) -> list[Alert]:
    query = owned_alerts_query(user_id)
    if person_id is not None:
        query = query.where(Alert.person_id == person_id)
    if unread_only:
        query = query.where(Alert.read_at.is_(None))
    result = await session.scalars(query.order_by(Alert.occurred_at.desc()).limit(limit))
    return list(result.all())


async def count_unread_alerts(session: AsyncSession, user_id: int) -> int:
    query = (
        select(func.count(Alert.id))
        .join(Person, Person.id == Alert.person_id)
        .where(Person.user_id == user_id, Alert.read_at.is_(None))
    )
    return int(await session.scalar(query) or 0)


async def confirm_all_owned_alerts(
    session: AsyncSession, user_id: int, confirmed_at: datetime
) -> int:
    owned_person_ids = select(Person.id).where(Person.user_id == user_id)
    result = await session.execute(
        update(Alert)
        .where(
            Alert.person_id.in_(owned_person_ids),
            Alert.safety_confirmed_at.is_(None),
        )
        .values(
            read_at=func.coalesce(Alert.read_at, confirmed_at),
            safety_confirmed_at=confirmed_at,
        )
    )
    await session.commit()
    return result.rowcount or 0


async def get_owned_alert(session: AsyncSession, alert_id: int, user_id: int) -> Alert | None:
    return await session.scalar(owned_alerts_query(user_id).where(Alert.id == alert_id))


async def get_alert_by_dedup_key(session: AsyncSession, dedup_key: str) -> Alert | None:
    return await session.scalar(select(Alert).where(Alert.dedup_key == dedup_key))


async def get_active_alert(
    session: AsyncSession, *, person_id: int, cause: str, sensor_id: int | None = None
) -> Alert | None:
    query = select(Alert).where(
        Alert.person_id == person_id, Alert.cause == cause, Alert.resolved_at.is_(None)
    )
    if sensor_id is not None:
        query = query.where(Alert.sensor_id == sensor_id)
    return await session.scalar(query.order_by(Alert.occurred_at.desc()).limit(1))


async def create_alert(session: AsyncSession, **values: object) -> Alert:
    alert = Alert(**values)
    session.add(alert)
    await session.flush()
    await session.refresh(alert)
    return alert


async def resolve_active_alerts(
    session: AsyncSession,
    *,
    person_id: int,
    cause: str,
    resolved_at: datetime,
    sensor_id: int | None = None,
) -> None:
    query = update(Alert).where(
        Alert.person_id == person_id, Alert.cause == cause, Alert.resolved_at.is_(None)
    )
    if sensor_id is not None:
        query = query.where(Alert.sensor_id == sensor_id)
    query = query.values(resolved_at=resolved_at)

    for attempt in range(1, RESOLVE_ALERTS_MAX_ATTEMPTS + 1):
        try:
            async with session.begin_nested():
                await session.execute(query)
            return
        except OperationalError as exc:
            if not _is_deadlock(exc):
                raise
            if attempt == RESOLVE_ALERTS_MAX_ATTEMPTS:
                logger.error(
                    "resolve_active_alerts deadlocked %d times for person_id=%s cause=%s; giving up",
                    attempt,
                    person_id,
                    cause,
                )
                return
            logger.warning(
                "resolve_active_alerts deadlock on attempt %d/%d for person_id=%s cause=%s; retrying",
                attempt,
                RESOLVE_ALERTS_MAX_ATTEMPTS,
                person_id,
                cause,
            )
            await asyncio.sleep(random.uniform(0.1, 0.5))
