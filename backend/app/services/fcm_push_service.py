import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, exceptions, messaging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.fcm_device_token_repository import (
    delete_fcm_device_token,
    list_fcm_device_tokens,
)

logger = logging.getLogger(__name__)


def _firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    credentials_path = settings.firebase_credentials_path.strip()
    if not credentials_path or not Path(credentials_path).is_file():
        return None
    return firebase_admin.initialize_app(credentials.Certificate(credentials_path))


def fcm_enabled() -> bool:
    return _firebase_app() is not None


async def send_alert_fcm(session: AsyncSession, user_id: int, alert: dict) -> None:
    app = _firebase_app()
    if app is None:
        return

    device_tokens = await list_fcm_device_tokens(session, user_id)
    for device_token in device_tokens:
        try:
            message = messaging.Message(
                token=device_token.token,
                notification=messaging.Notification(
                    title=str(alert.get("title") or "liflow 알림"),
                    body=str(alert.get("description") or "새로운 알림이 도착했습니다."),
                ),
                data={
                    "type": "alert.created",
                    "alert_id": str(alert.get("id") or ""),
                    "person_id": str(alert.get("person_id") or ""),
                    "cause": str(alert.get("cause") or ""),
                    "severity": str(alert.get("severity") or ""),
                },
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id="liflow_alerts",
                        sound="default",
                        default_vibrate_timings=True,
                    ),
                ),
            )
            messaging.send(message, app=app)
        except (messaging.UnregisteredError, messaging.SenderIdMismatchError):
            await delete_fcm_device_token(session, token=device_token.token)
        except exceptions.FirebaseError:
            logger.exception("FCM alert delivery failed for user %s", user_id)
