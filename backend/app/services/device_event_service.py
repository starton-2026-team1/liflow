from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.models.sensor_event import SensorEvent
from app.repositories.sensor_event_repository import (
    create_device_sensor_event,
    get_sensor_event_by_external_id,
)
from app.repositories.sensor_repository import get_sensor_by_device_id
from app.schemas.sensor_event import DeviceEventCreate


async def record_device_event(
    session: AsyncSession, data: DeviceEventCreate
) -> tuple[SensorEvent, bool]:
    sensor = await get_sensor_by_device_id(session, data.device_id)
    if sensor is None:
        raise AppError(ErrorCode.SENSOR_NOT_FOUND)

    existing = await get_sensor_event_by_external_id(session, data.event_id)
    if existing is not None:
        if (
            existing.sensor_id != sensor.id
            or existing.detected_value != data.detected_value
        ):
            raise AppError(ErrorCode.EVENT_ID_CONFLICT)
        return existing, False

    if sensor.status.upper() != "CONNECTED":
        raise AppError(ErrorCode.SENSOR_NOT_CONNECTED)

    try:
        async with session.begin_nested():
            event = await create_device_sensor_event(
                session,
                data,
                person_id=sensor.person_id,
                sensor_id=sensor.id,
                sensor_status=sensor.status,
            )
        return event, True
    except IntegrityError as exc:
        existing = await get_sensor_event_by_external_id(session, data.event_id)
        if existing is None:
            raise
        if (
            existing.sensor_id != sensor.id
            or existing.detected_value != data.detected_value
        ):
            raise AppError(ErrorCode.EVENT_ID_CONFLICT) from exc
        return existing, False
