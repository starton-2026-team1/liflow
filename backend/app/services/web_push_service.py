import asyncio
import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.push_subscription_repository import (
    delete_push_subscription_by_id,
    list_push_subscriptions,
)

logger = logging.getLogger(__name__)


def web_push_enabled() -> bool:
    return bool(settings.web_push_vapid_public_key and settings.web_push_vapid_private_key)


def _send(subscription_info: dict, payload: str) -> None:
    webpush(
        subscription_info=subscription_info,
        data=payload,
        vapid_private_key=settings.web_push_vapid_private_key,
        vapid_claims={"sub": settings.web_push_vapid_subject},
        ttl=300,
    )


async def send_alert_web_push(session: AsyncSession, user_id: int, alert: dict) -> None:
    if not web_push_enabled():
        return
    payload = json.dumps(
        {
            "title": alert.get("title", "이상 행동이 감지됐어요"),
            "body": alert.get("description", "보호 대상자의 상태를 확인해 주세요."),
            "tag": f"alert-{alert.get('id', '')}",
            "url": "/",
            "data": alert,
        },
        ensure_ascii=False,
    )
    subscriptions = await list_push_subscriptions(session, user_id)
    for subscription in subscriptions:
        info = {
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
        }
        try:
            await asyncio.to_thread(_send, info, payload)
        except WebPushException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in (404, 410):
                await delete_push_subscription_by_id(session, subscription.id)
            else:
                logger.warning(
                    "Web Push delivery failed for subscription %s: %s", subscription.id, exc
                )
        except Exception:
            logger.exception(
                "Unexpected Web Push delivery failure for subscription %s", subscription.id
            )
