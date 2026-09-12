import logging

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.database import get_db_session
from app.repositories.alert_repository import count_unread_alerts, list_alerts
from app.schemas.alert import AlertCreate, AlertResponse, UnreadAlertCount
from app.services.alert_service import confirm_alert_safety, create_external_alert, mark_alert_read
from app.services.person_service import find_person_or_404
from app.services.realtime_event_service import realtime_event_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=list[AlertResponse])
async def get_alerts(
    current_user: CurrentUser,
    person_id: int | None = None,
    unread_only: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
) -> list[AlertResponse]:
    if person_id is not None:
        await find_person_or_404(session, person_id, current_user.id)
    return await list_alerts(session, current_user.id, person_id, unread_only, limit)


@router.get("/unread-count", response_model=UnreadAlertCount)
async def get_unread_count(
    current_user: CurrentUser, session: AsyncSession = Depends(get_db_session)
) -> UnreadAlertCount:
    return UnreadAlertCount(count=await count_unread_alerts(session, current_user.id))


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_alert(
    data: AlertCreate,
    response: Response,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> AlertResponse:
    alert, created = await create_external_alert(session, current_user.id, data)
    if not created:
        response.status_code = status.HTTP_200_OK
        return alert
    await session.commit()
    payload = AlertResponse.model_validate(alert).model_dump(mode="json")
    try:
        await realtime_event_manager.publish_sensor_event(
            current_user.id, {"type": "alert.created", "data": payload}
        )
    except Exception:
        logger.exception("Failed to publish alert %s", alert.id)
    return alert


@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def read_alert(
    alert_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> AlertResponse:
    return await mark_alert_read(session, alert_id, current_user.id)


@router.post("/{alert_id}/safety-confirmations", response_model=AlertResponse)
async def confirm_safety(
    alert_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> AlertResponse:
    return await confirm_alert_safety(session, alert_id, current_user.id)
