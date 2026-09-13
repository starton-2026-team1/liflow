from sqlalchemy import Select, or_, select
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
