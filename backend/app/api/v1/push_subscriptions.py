from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.core.database import get_db_session
from app.repositories.push_subscription_repository import (
    delete_push_subscription,
    save_push_subscription,
)
from app.schemas.push_subscription import (
    PushSubscriptionCreate,
    PushSubscriptionDelete,
    WebPushConfiguration,
)
from app.services.web_push_service import web_push_enabled

router = APIRouter()


@router.get("/configuration", response_model=WebPushConfiguration)
async def get_web_push_configuration() -> WebPushConfiguration:
    enabled = web_push_enabled()
    return WebPushConfiguration(
        enabled=enabled,
        public_key=settings.web_push_vapid_public_key if enabled else None,
    )


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def subscribe(
    data: PushSubscriptionCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await save_push_subscription(
        session,
        user_id=current_user.id,
        endpoint=str(data.endpoint),
        p256dh=data.keys.p256dh,
        auth=data.keys.auth,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(
    data: PushSubscriptionDelete,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await delete_push_subscription(session, current_user.id, str(data.endpoint))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
