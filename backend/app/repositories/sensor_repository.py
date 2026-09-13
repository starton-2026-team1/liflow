from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.models.sensor import Sensor
from app.schemas.sensor import SensorCreate, SensorUpdate


async def create_sensor(session: AsyncSession, data: SensorCreate) -> Sensor:
    sensor = Sensor(**data.model_dump())
    session.add(sensor)
    await session.flush()
    await session.refresh(sensor)
    return sensor


async def list_sensors(session: AsyncSession, user_id: int) -> list[Sensor]:
    result = await session.scalars(
        select(Sensor)
        .join(Person, Person.id == Sensor.person_id)
        .where(or_(Person.user_id == user_id, Person.user_id.is_(None)))
        .order_by(Sensor.id)
    )
    return list(result.all())


async def get_sensor(
    session: AsyncSession, sensor_id: int, user_id: int
) -> Sensor | None:
    return await session.scalar(
        select(Sensor)
        .join(Person, Person.id == Sensor.person_id)
        .where(
            Sensor.id == sensor_id,
            or_(Person.user_id == user_id, Person.user_id.is_(None)),
        )
    )


async def get_owned_sensor(
    session: AsyncSession, sensor_id: int, user_id: int
) -> Sensor | None:
    return await session.scalar(
        select(Sensor)
        .join(Person, Person.id == Sensor.person_id)
        .where(Sensor.id == sensor_id, Person.user_id == user_id)
    )


async def get_sensor_by_device_id(
    session: AsyncSession, device_id: str
) -> Sensor | None:
    return await session.scalar(select(Sensor).where(Sensor.device_id == device_id))


async def update_sensor(session: AsyncSession, sensor: Sensor, data: SensorUpdate) -> Sensor:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(sensor, key, value)
    await session.flush()
    await session.refresh(sensor)
    return sensor


async def delete_sensor(session: AsyncSession, sensor: Sensor) -> None:
    await session.delete(sensor)
