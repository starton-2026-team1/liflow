from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate


async def create_person(
    session: AsyncSession, user_id: int, data: PersonCreate
) -> Person:
    person = Person(user_id=user_id, **data.model_dump())
    session.add(person)
    await session.flush()
    await session.refresh(person)
    return person


async def list_people(session: AsyncSession, user_id: int) -> list[Person]:
    result = await session.scalars(
        select(Person)
        .where(or_(Person.user_id == user_id, Person.user_id.is_(None)))
        .order_by(Person.id)
    )
    return list(result.all())


async def get_person(
    session: AsyncSession, person_id: int, user_id: int
) -> Person | None:
    return await session.scalar(
        select(Person).where(
            Person.id == person_id,
            or_(Person.user_id == user_id, Person.user_id.is_(None)),
        )
    )


async def get_owned_person(
    session: AsyncSession, person_id: int, user_id: int
) -> Person | None:
    return await session.scalar(
        select(Person).where(Person.id == person_id, Person.user_id == user_id)
    )


async def get_person_owner_id(
    session: AsyncSession, person_id: int
) -> int | None:
    return await session.scalar(
        select(Person.user_id).where(Person.id == person_id)
    )


async def update_person(session: AsyncSession, person: Person, data: PersonUpdate) -> Person:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(person, key, value)
    await session.flush()
    await session.refresh(person)
    return person


async def delete_person(session: AsyncSession, person: Person) -> None:
    await session.delete(person)
