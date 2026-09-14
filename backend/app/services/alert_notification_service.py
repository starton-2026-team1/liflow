import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.realtime_event_service import realtime_event_manager
from app.services.web_push_service import send_alert_web_push

logger = logging.getLogger(__name__)


async def notify_alert(session: AsyncSession, user_id: int, alert_payload: dict) -> None:
    event = {"type": "alert.created", "data": alert_payload}
    try:
        await realtime_event_manager.publish_sensor_event(user_id, event)
    except Exception:
        logger.exception("WebSocket alert delivery failed for user %s", user_id)
    await send_alert_web_push(session, user_id, alert_payload)
