from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.database import get_db_session
from app.repositories.fcm_device_token_repository import (
    delete_fcm_device_token,
    save_fcm_device_token,
)
from app.schemas.fcm_device_token import FcmDeviceTokenCreate, FcmDeviceTokenDelete

router = APIRouter()


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def subscribe(
    data: FcmDeviceTokenCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await save_fcm_device_token(
        session, user_id=current_user.id, token=data.token, platform=data.platform
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(
    data: FcmDeviceTokenDelete,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await delete_fcm_device_token(session, user_id=current_user.id, token=data.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
