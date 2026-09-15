from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fcm_device_token import FcmDeviceToken


async def save_fcm_device_token(
    session: AsyncSession, *, user_id: int, token: str, platform: str
) -> FcmDeviceToken:
    device_token = await session.scalar(
        select(FcmDeviceToken).where(FcmDeviceToken.token == token)
    )
    if device_token is None:
        device_token = FcmDeviceToken(user_id=user_id, token=token, platform=platform)
        session.add(device_token)
    else:
        device_token.user_id = user_id
        device_token.platform = platform
    await session.flush()
    await session.refresh(device_token)
    return device_token


async def list_fcm_device_tokens(
    session: AsyncSession, user_id: int
) -> list[FcmDeviceToken]:
    result = await session.scalars(
        select(FcmDeviceToken).where(FcmDeviceToken.user_id == user_id)
    )
    return list(result.all())


async def delete_fcm_device_token(
    session: AsyncSession, *, user_id: int | None = None, token: str
) -> None:
    query = delete(FcmDeviceToken).where(FcmDeviceToken.token == token)
    if user_id is not None:
        query = query.where(FcmDeviceToken.user_id == user_id)
    await session.execute(query)
