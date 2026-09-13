from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.models.sensor import Sensor
from app.repositories.person_repository import get_owned_person
from app.repositories.sensor_repository import (
    create_sensor,
    delete_sensor,
    get_owned_sensor,
    get_sensor,
    update_sensor,
)
from app.schemas.sensor import SensorCreate, SensorUpdate


async def find_sensor_or_404(
    session: AsyncSession, sensor_id: int, user_id: int
) -> Sensor:
    sensor = await get_sensor(session, sensor_id, user_id)
    if sensor is None:
        raise AppError(ErrorCode.SENSOR_NOT_FOUND)
    return sensor


async def find_owned_sensor_or_404(
    session: AsyncSession, sensor_id: int, user_id: int
) -> Sensor:
    sensor = await get_owned_sensor(session, sensor_id, user_id)
    if sensor is None:
        raise AppError(ErrorCode.SENSOR_NOT_FOUND)
    return sensor


async def register_sensor(
    session: AsyncSession, user_id: int, data: SensorCreate
) -> Sensor:
    if await get_owned_person(session, data.person_id, user_id) is None:
        raise AppError(ErrorCode.PERSON_NOT_FOUND)
    try:
        return await create_sensor(session, data)

    except IntegrityError as exc:
        raise AppError(ErrorCode.SENSOR_DEVICE_ID_CONFLICT) from exc


async def update_registered_sensor(
    session: AsyncSession, sensor_id: int, user_id: int, data: SensorUpdate
) -> Sensor:
    sensor = await find_owned_sensor_or_404(session, sensor_id, user_id)
    if data.person_id is not None:
        if await get_owned_person(session, data.person_id, user_id) is None:
            raise AppError(ErrorCode.PERSON_NOT_FOUND)
    try:
        return await update_sensor(session, sensor, data)

    except IntegrityError as exc:
        raise AppError(ErrorCode.SENSOR_DEVICE_ID_CONFLICT) from exc


async def remove_sensor(session: AsyncSession, sensor_id: int, user_id: int) -> None:
    sensor = await find_owned_sensor_or_404(session, sensor_id, user_id)
    await delete_sensor(session, sensor)
