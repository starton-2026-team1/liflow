from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.api.v1.ai_chat import router as ai_chat_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.device_events import router as device_events_router
from app.api.v1.people import router as people_router
from app.api.v1.realtime_events import router as realtime_events_router
from app.api.v1.sensor_events import router as sensor_events_router
from app.api.v1.sensors import router as sensors_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    device_events_router, prefix="/device-events", tags=["Device Events"]
)
api_router.include_router(
    realtime_events_router, prefix="/ws", tags=["Realtime Events"]
)
authentication = [Depends(get_current_user)]
api_router.include_router(
    ai_chat_router,
    prefix="/ai-chat",
    tags=["AI Chat"],
    dependencies=authentication,
)
api_router.include_router(
    alerts_router,
    prefix="/alerts",
    tags=["Alerts"],
    dependencies=authentication,
)
api_router.include_router(
    people_router,
    prefix="/people",
    tags=["People"],
    dependencies=authentication,
)
api_router.include_router(
    sensors_router,
    prefix="/sensors",
    tags=["Sensors"],
    dependencies=authentication,
)
api_router.include_router(
    sensor_events_router,
    prefix="/sensor-events",
    tags=["Sensor Events"],
    dependencies=authentication,
)
