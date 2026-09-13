from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.models.person import Person
from app.repositories.person_repository import (
    create_person,
    delete_person,
    get_owned_person,
    get_person,
    update_person,
)
from app.schemas.person import PersonCreate, PersonUpdate


async def register_person(
    session: AsyncSession, user_id: int, data: PersonCreate
) -> Person:
    return await create_person(session, user_id, data)


async def find_person_or_404(
    session: AsyncSession, person_id: int, user_id: int
) -> Person:
    person = await get_person(session, person_id, user_id)
    if person is None:
        raise AppError(ErrorCode.PERSON_NOT_FOUND)
    return person


async def find_owned_person_or_404(
    session: AsyncSession, person_id: int, user_id: int
) -> Person:
    person = await get_owned_person(session, person_id, user_id)
    if person is None:
        raise AppError(ErrorCode.PERSON_NOT_FOUND)
    return person


async def update_registered_person(
    session: AsyncSession, person_id: int, user_id: int, data: PersonUpdate
) -> Person:
    person = await find_owned_person_or_404(session, person_id, user_id)
    return await update_person(session, person, data)


async def remove_person(session: AsyncSession, person_id: int, user_id: int) -> None:
    person = await find_owned_person_or_404(session, person_id, user_id)
    await delete_person(session, person)
