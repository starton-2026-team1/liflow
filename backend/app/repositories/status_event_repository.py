from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person_status_event import PersonStatusEvent
from app.schemas.status_event import StatusEventCreate


async def create_status_event(
    session: AsyncSession,
    data: StatusEventCreate,
    person_id: int,
    sensor_id: int,
) -> PersonStatusEvent:
    event = PersonStatusEvent(
        external_event_id=data.event_id,
        person_id=person_id,
        sensor_id=sensor_id,
        status=data.status,
        judged_at=data.judged_at,
        detected_value=data.detected_value,
    )
    session.add(event)
    await session.flush()
    await session.refresh(event)
    return event


async def get_status_event_by_external_id(
    session: AsyncSession, external_event_id: str
) -> PersonStatusEvent | None:
    return await session.scalar(
        select(PersonStatusEvent).where(
            PersonStatusEvent.external_event_id == external_event_id
        )
    )


async def get_latest_status_event(
    session: AsyncSession, person_id: int
) -> PersonStatusEvent | None:
    return await session.scalar(
        select(PersonStatusEvent)
        .where(PersonStatusEvent.person_id == person_id)
        .order_by(PersonStatusEvent.judged_at.desc(), PersonStatusEvent.id.desc())
        .limit(1)
    )


async def list_status_events_page(
    session: AsyncSession, person_id: int, page: int, page_size: int
) -> tuple[list[PersonStatusEvent], int]:
    total = await session.scalar(
        select(func.count())
        .select_from(PersonStatusEvent)
        .where(PersonStatusEvent.person_id == person_id)
    )
    result = await session.scalars(
        select(PersonStatusEvent)
        .where(PersonStatusEvent.person_id == person_id)
        .order_by(PersonStatusEvent.judged_at.desc(), PersonStatusEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.all()), total or 0
