import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import verify_device_api_key
from app.core.database import get_db_session
from app.repositories.person_repository import get_person_owner_id
from app.schemas.alert import AlertResponse
from app.schemas.sensor_event import DeviceEventCreate, DeviceEventResponse
from app.services.alert_notification_service import notify_alert
from app.services.alert_service import create_ai_abnormal_alert
from app.services.device_event_service import record_device_event
from app.services.realtime_event_service import realtime_event_manager

router = APIRouter(dependencies=[Depends(verify_device_api_key)])
logger = logging.getLogger(__name__)


@router.post("", response_model=DeviceEventResponse, status_code=status.HTTP_201_CREATED)
async def create_device_event(
    data: DeviceEventCreate,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> DeviceEventResponse:
    event, created, became_abnormal = await record_device_event(session, data)

    if not created:
        response.status_code = status.HTTP_200_OK
        return event

    owner_id = await get_person_owner_id(session, event.person_id)
    alert = None
    if became_abnormal:
        alert = await create_ai_abnormal_alert(
            session,
            person_id=event.person_id,
            sensor_id=event.sensor_id,
            external_event_id=data.event_id,
            occurred_at=data.detected_at,
            detected_value=data.detected_value,
        )
    await session.commit()
    if owner_id is not None:
        event_response = DeviceEventResponse.model_validate(event)
        try:
            await realtime_event_manager.publish_sensor_event(
                owner_id,
                {
                    "type": "sensor_event.created",
                    "data": event_response.model_dump(mode="json"),
                },
            )
        except Exception:
            logger.exception(
                "Failed to publish sensor event %s to user %s",
                event.id,
                owner_id,
            )
        if alert is not None:
            payload = AlertResponse.model_validate(alert).model_dump(mode="json")
            await notify_alert(session, owner_id, payload)
    return event
