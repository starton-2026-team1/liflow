from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.models.person_status_event import PersonStatusEvent
from app.repositories.person_repository import list_owned_people
from app.repositories.sensor_repository import get_sensor_by_device_id
from app.repositories.status_event_repository import (
    create_status_event,
    get_latest_status_event,
    get_status_event_by_external_id,
    list_status_events_page,
)
from app.schemas.status_event import (
    PersonStatusHistoryItem,
    PersonStatusHistoryPage,
    PersonStatusResponse,
    StatusEventCreate,
)
from app.services.person_service import find_owned_person_or_404

UNKNOWN_STATUS = "UNKNOWN"


def _matches_existing(existing: PersonStatusEvent, sensor_id: int, data: StatusEventCreate) -> bool:
    return (
        existing.sensor_id == sensor_id
        and existing.status == data.status
        and existing.detected_value == data.detected_value
    )


async def record_status_event(
    session: AsyncSession, data: StatusEventCreate
) -> tuple[PersonStatusEvent, bool, str | None]:
    """Returns (event, created, previous_status).

    previous_status is the person's latest status immediately before this
    event, or None if either this is their first-ever status event or the
    event was a duplicate resend (no state actually changed).
    """
    sensor = await get_sensor_by_device_id(session, data.device_id)
    if sensor is None:
        raise AppError(ErrorCode.SENSOR_NOT_FOUND)

    existing = await get_status_event_by_external_id(session, data.event_id)
    if existing is not None:
        if not _matches_existing(existing, sensor.id, data):
            raise AppError(ErrorCode.EVENT_ID_CONFLICT)
        return existing, False, None

    previous_event = await get_latest_status_event(session, sensor.person_id)
    previous_status = previous_event.status if previous_event is not None else None

    try:
        event = await create_status_event(
            session, data, person_id=sensor.person_id, sensor_id=sensor.id
        )
        return event, True, previous_status
    except IntegrityError as exc:
        existing = await get_status_event_by_external_id(session, data.event_id)
        if existing is None:
            raise
        if not _matches_existing(existing, sensor.id, data):
            raise AppError(ErrorCode.EVENT_ID_CONFLICT) from exc
        return existing, False, None


def _to_status_response(person_id: int, event: PersonStatusEvent | None) -> PersonStatusResponse:
    if event is None:
        return PersonStatusResponse(
            person_id=person_id, status=UNKNOWN_STATUS, judged_at=None, sensor_id=None
        )
    return PersonStatusResponse(
        person_id=person_id,
        status=event.status,
        judged_at=event.judged_at,
        sensor_id=event.sensor_id,
    )


async def get_person_latest_status(
    session: AsyncSession, person_id: int, user_id: int
) -> PersonStatusResponse:
    person = await find_owned_person_or_404(session, person_id, user_id)
    event = await get_latest_status_event(session, person.id)
    return _to_status_response(person.id, event)


async def get_person_status_history(
    session: AsyncSession, person_id: int, user_id: int, page: int, page_size: int
) -> PersonStatusHistoryPage:
    person = await find_owned_person_or_404(session, person_id, user_id)
    items, total = await list_status_events_page(session, person.id, page, page_size)
    return PersonStatusHistoryPage(
        items=[PersonStatusHistoryItem.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


async def list_latest_statuses_for_user(
    session: AsyncSession, user_id: int
) -> list[PersonStatusResponse]:
    people = await list_owned_people(session, user_id)
    responses = []
    for person in people:
        event = await get_latest_status_event(session, person.id)
        responses.append(_to_status_response(person.id, event))
    return responses
