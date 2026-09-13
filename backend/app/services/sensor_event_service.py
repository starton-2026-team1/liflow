from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.models.sensor_event import SensorEvent
from app.repositories.person_repository import get_owned_person
from app.repositories.sensor_event_repository import create_sensor_event
from app.repositories.sensor_repository import get_owned_sensor
from app.schemas.sensor_event import SensorEventCreate


async def record_sensor_event(
    session: AsyncSession, user_id: int, data: SensorEventCreate
) -> SensorEvent:
    if await get_owned_person(session, data.person_id, user_id) is None:
        raise AppError(ErrorCode.PERSON_NOT_FOUND)
    if data.sensor_id is None:
        raise AppError(ErrorCode.SENSOR_NOT_FOUND)
    sensor = await get_owned_sensor(session, data.sensor_id, user_id)
    if sensor is None:
        raise AppError(ErrorCode.SENSOR_NOT_FOUND)
    if sensor.person_id != data.person_id:
        raise AppError(ErrorCode.SENSOR_PERSON_MISMATCH)
    return await create_sensor_event(session, data)
