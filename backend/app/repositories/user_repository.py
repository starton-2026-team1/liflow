from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def create_user(session: AsyncSession, email: str, password_hash: str) -> User:
    user = User(email=email.lower(), password_hash=password_hash)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email.lower()))


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def update_user(
    session: AsyncSession,
    user: User,
    email: str | None = None,
    password_hash: str | None = None,
) -> User:
    if email is not None:
        user.email = email.lower()
    if password_hash is not None:
        user.password_hash = password_hash
    await session.flush()
    await session.refresh(user)
    return user
