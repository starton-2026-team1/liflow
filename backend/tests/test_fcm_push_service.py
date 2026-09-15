from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.repositories.fcm_device_token_repository import (
    list_fcm_device_tokens,
    save_fcm_device_token,
)
from app.services import fcm_push_service


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def test_fcm_notification_is_sent(db_session, monkeypatch):
    await save_fcm_device_token(
        db_session,
        user_id=101,
        token="valid-fcm-device-token-that-is-long-enough",
        platform="android",
    )
    sent = []
    monkeypatch.setattr(fcm_push_service, "_firebase_app", lambda: object())
    monkeypatch.setattr(
        fcm_push_service.messaging, "send", lambda message, app: sent.append(message)
    )

    await fcm_push_service.send_alert_fcm(
        db_session,
        101,
        {
            "id": 10,
            "person_id": 3,
            "cause": "INACTIVITY",
            "severity": "WARNING",
            "title": "장시간 움직임 없음",
            "description": "평소보다 오랫동안 움직임이 없어요.",
        },
    )

    assert len(sent) == 1
    assert sent[0].android.priority == "high"
    assert sent[0].android.notification.channel_id == "liflow_alerts"


async def test_unregistered_fcm_token_is_removed(db_session, monkeypatch):
    token = "expired-fcm-device-token-that-is-long-enough"
    await save_fcm_device_token(
        db_session, user_id=202, token=token, platform="android"
    )
    monkeypatch.setattr(fcm_push_service, "_firebase_app", lambda: object())

    def fail_send(message, app):
        raise fcm_push_service.messaging.UnregisteredError("expired")

    monkeypatch.setattr(fcm_push_service.messaging, "send", fail_send)
    await fcm_push_service.send_alert_fcm(db_session, 202, {"title": "test"})

    assert await list_fcm_device_tokens(db_session, 202) == []
