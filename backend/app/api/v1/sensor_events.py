from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.database import get_db_session
from app.repositories.sensor_event_repository import list_sensor_events
from app.schemas.sensor_event import SensorEventCreate, SensorEventResponse
from app.services.person_service import find_person_or_404
from app.services.sensor_event_service import record_sensor_event

router = APIRouter()


@router.post("", response_model=SensorEventResponse, status_code=status.HTTP_201_CREATED)
async def create_sensor_event(
    data: SensorEventCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> SensorEventResponse:
    return await record_sensor_event(session, current_user.id, data)


@router.get("", response_model=list[SensorEventResponse])
async def get_sensor_events(
    current_user: CurrentUser,
    person_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
) -> list[SensorEventResponse]:
    if person_id is not None:
        await find_person_or_404(session, person_id, current_user.id)
    return await list_sensor_events(session, current_user.id, person_id, limit)


@router.get("/people/{person_id}/timeline", response_model=list[SensorEventResponse])
async def get_person_timeline(
    person_id: int,
    current_user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
) -> list[SensorEventResponse]:
    await find_person_or_404(session, person_id, current_user.id)
    return await list_sensor_events(session, current_user.id, person_id, limit)
