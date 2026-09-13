from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.person import Person


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
    await session.execute(query.values(resolved_at=resolved_at))
