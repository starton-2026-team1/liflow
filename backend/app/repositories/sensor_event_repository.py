from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.models.sensor_event import SensorEvent
from app.schemas.sensor_event import DeviceEventCreate, SensorEventCreate


async def create_sensor_event(
    session: AsyncSession, data: SensorEventCreate
) -> SensorEvent:
    event = SensorEvent(**data.model_dump())
    session.add(event)
    await session.flush()
    await session.refresh(event)
    return event


async def create_device_sensor_event(
    session: AsyncSession,
    data: DeviceEventCreate,
    person_id: int,
    sensor_id: int,
    sensor_status: str,
    ai_label: str | None = None,
    ai_score: float | None = None,
    ai_is_anomaly: bool | None = None,
) -> SensorEvent:
    event = SensorEvent(
        external_event_id=data.event_id,
        person_id=person_id,
        sensor_id=sensor_id,
        detected_at=data.detected_at,
        detected_value=data.detected_value,
        sensor_status=sensor_status,
        ai_label=ai_label,
        ai_score=ai_score,
        ai_is_anomaly=ai_is_anomaly,
    )
    session.add(event)
    await session.flush()
    await session.refresh(event)
    return event


async def get_sensor_event_by_external_id(
    session: AsyncSession, external_event_id: str
) -> SensorEvent | None:
    return await session.scalar(
        select(SensorEvent).where(
            SensorEvent.external_event_id == external_event_id
        )
    )


async def list_sensor_events(
    session: AsyncSession,
    user_id: int,
    person_id: int | None = None,
    limit: int = 100,
) -> list[SensorEvent]:
    query: Select[tuple[SensorEvent]] = (
        select(SensorEvent)
        .join(Person, Person.id == SensorEvent.person_id)
        .where(or_(Person.user_id == user_id, Person.user_id.is_(None)))
    )
    if person_id is not None:
        query = query.where(SensorEvent.person_id == person_id)
    query = query.order_by(SensorEvent.detected_at.desc()).limit(limit)
    result = await session.scalars(query)
    return list(result.all())



async def get_activity_change(
    session: AsyncSession,
    person_id: int,
):
    daily_count = (
        select(
            func.date(SensorEvent.detected_at).label("date"),
            func.count(SensorEvent.id).label("activity_count"),
        )
        .where(SensorEvent.person_id == person_id)
        .group_by(func.date(SensorEvent.detected_at))
        .order_by(func.date(SensorEvent.detected_at))
    )

    result = await session.execute(daily_count)
    rows = result.all()

    response = []
    previous_count = None

    for row in rows:
        change_count = (
            None
            if previous_count is None
            else row.activity_count - previous_count
        )

        response.append(
            {
                "date": str(row.date),
                "activity_count": row.activity_count,
                "change_count": change_count,
            }
        )

        previous_count = row.activity_count

    return response


async def get_average_first_activity(
    session: AsyncSession,
    person_id: int,
):
    query = (
        select(
            func.date(SensorEvent.detected_at).label("date"),
            func.min(SensorEvent.detected_at).label("first_activity"),
        )
        .where(SensorEvent.person_id == person_id)
        .group_by(func.date(SensorEvent.detected_at))
    )

    result = await session.execute(query)
    rows = result.all()

    if not rows:
        return {"average_first_activity": "00:00"}

    total_seconds = 0

    for row in rows:
        first_time = row.first_activity.time()
        total_seconds += (
            first_time.hour * 3600
            + first_time.minute * 60
            + first_time.second
        )

    average_seconds = total_seconds // len(rows)

    hour = average_seconds // 3600
    minute = (average_seconds % 3600) // 60

    return {
        "average_first_activity": f"{hour:02d}:{minute:02d}"
}
