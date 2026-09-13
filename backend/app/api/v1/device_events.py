import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import verify_device_api_key
from app.core.database import get_db_session
from app.repositories.person_repository import get_person_owner_id
from app.schemas.sensor_event import DeviceEventCreate, DeviceEventResponse
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
    event, created = await record_device_event(session, data)
    if not created:
        response.status_code = status.HTTP_200_OK
        return event

    owner_id = await get_person_owner_id(session, event.person_id)
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
    return event
