import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import verify_device_api_key
from app.core.database import get_db_session
from app.repositories.person_repository import get_person_owner_id
from app.schemas.alert import AlertResponse
from app.schemas.status_event import StatusEventCreate, StatusEventResponse
from app.services.alert_notification_service import notify_alert
from app.services.alert_service import create_ai_abnormal_alert
from app.services.realtime_event_service import realtime_event_manager
from app.services.status_event_service import record_status_event

router = APIRouter(dependencies=[Depends(verify_device_api_key)])
logger = logging.getLogger(__name__)


@router.post("", response_model=StatusEventResponse, status_code=status.HTTP_201_CREATED)
async def create_status_event(
    data: StatusEventCreate,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> StatusEventResponse:
    event, created, previous_status = await record_status_event(session, data)
    if not created:
        response.status_code = status.HTTP_200_OK
        return event

    owner_id = await get_person_owner_id(session, event.person_id)
    alert = None
    if event.status.upper() == "ABNORMAL" and previous_status != "ABNORMAL":
        alert = await create_ai_abnormal_alert(
            session,
            person_id=event.person_id,
            sensor_id=event.sensor_id,
            external_event_id=data.event_id,
            occurred_at=data.judged_at,
            detected_value=data.detected_value,
        )
    await session.commit()
    if owner_id is not None and previous_status != event.status:
        try:
            await realtime_event_manager.publish_sensor_event(
                owner_id,
                {
                    "type": "person_status_changed",
                    "payload": {
                        "person_id": event.person_id,
                        "previous_status": previous_status,
                        "status": event.status,
                        "judged_at": event.judged_at.isoformat(),
                    },
                },
            )
        except Exception:
            logger.exception(
                "Failed to publish person status change for person %s to user %s",
                event.person_id,
                owner_id,
            )
        if alert is not None:
            payload = AlertResponse.model_validate(alert).model_dump(mode="json")
            await notify_alert(session, owner_id, payload)
    return event
