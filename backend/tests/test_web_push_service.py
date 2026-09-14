import logging
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from pywebpush import WebPushException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models import Base
from app.models.push_subscription import PushSubscription
from app.repositories.push_subscription_repository import list_push_subscriptions
from app.services import web_push_service

LOGGER_NAME = "app.services.web_push_service"

FAKE_ENDPOINT = "https://push.example.test/subscriptions/should-never-appear-in-logs"
FAKE_P256DH = "SECRET-P256DH-KEY-SHOULD-NEVER-APPEAR"
FAKE_AUTH = "SECRET-AUTH-SECRET-SHOULD-NEVER-APPEAR"
FAKE_VAPID_PRIVATE_KEY = "SECRET-VAPID-PRIVATE-KEY-SHOULD-NEVER-APPEAR"


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


@pytest.fixture(autouse=True)
def _enable_web_push(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "web_push_vapid_public_key", "test-public-key")
    monkeypatch.setattr(settings, "web_push_vapid_private_key", FAKE_VAPID_PRIVATE_KEY)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def _add_subscription(session: AsyncSession, *, user_id: int) -> PushSubscription:
    subscription = PushSubscription(
        user_id=user_id,
        endpoint_hash=f"digest-{user_id}",
        endpoint=FAKE_ENDPOINT,
        p256dh=FAKE_P256DH,
        auth=FAKE_AUTH,
    )
    session.add(subscription)
    await session.flush()
    await session.refresh(subscription)
    return subscription


def _assert_no_sensitive_data(text: str) -> None:
    assert FAKE_ENDPOINT not in text
    assert FAKE_P256DH not in text
    assert FAKE_AUTH not in text
    assert FAKE_VAPID_PRIVATE_KEY not in text


async def test_successful_delivery_logs_info_with_identifiers(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    subscription = await _add_subscription(db_session, user_id=101)
    monkeypatch.setattr(web_push_service, "webpush", lambda **kwargs: None)

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        await web_push_service.send_alert_web_push(
            db_session, 101, {"id": 1, "title": "안전 확인 필요", "description": "설명"}
        )

    info_records = [r for r in caplog.records if r.levelno == logging.INFO]
    assert len(info_records) == 1
    message = info_records[0].getMessage()
    assert "101" in message
    assert str(subscription.id) in message
    _assert_no_sensitive_data(caplog.text)


async def test_failed_delivery_logs_warning_with_status_code(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    subscription = await _add_subscription(db_session, user_id=202)

    def failing_webpush(**kwargs: object) -> None:
        info = kwargs["subscription_info"]
        raise WebPushException(
            f"Push service rejected request for {info['endpoint']}",
            response=FakeResponse(500),
        )

    monkeypatch.setattr(web_push_service, "webpush", failing_webpush)

    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        await web_push_service.send_alert_web_push(
            db_session, 202, {"id": 2, "title": "안전 확인 필요", "description": "설명"}
        )

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) == 1
    message = warning_records[0].getMessage()
    assert "202" in message
    assert str(subscription.id) in message
    assert "500" in message
    _assert_no_sensitive_data(caplog.text)

    # Not an expiry status code, so the subscription must survive.
    remaining = await list_push_subscriptions(db_session, 202)
    assert len(remaining) == 1


@pytest.mark.parametrize("status_code", [404, 410])
async def test_expired_subscription_is_deleted_and_logged(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    status_code: int,
) -> None:
    subscription = await _add_subscription(db_session, user_id=303)

    def expired_webpush(**kwargs: object) -> None:
        info = kwargs["subscription_info"]
        raise WebPushException(f"Gone: {info['endpoint']}", response=FakeResponse(status_code))

    monkeypatch.setattr(web_push_service, "webpush", expired_webpush)

    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        await web_push_service.send_alert_web_push(
            db_session, 303, {"id": 3, "title": "안전 확인 필요", "description": "설명"}
        )

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) == 1
    message = warning_records[0].getMessage()
    assert "303" in message
    assert str(subscription.id) in message
    assert str(status_code) in message
    _assert_no_sensitive_data(caplog.text)

    remaining = await list_push_subscriptions(db_session, 303)
    assert remaining == []


async def test_unexpected_exception_keeps_using_logger_exception(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    await _add_subscription(db_session, user_id=404)

    def broken_webpush(**kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(web_push_service, "webpush", broken_webpush)

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        await web_push_service.send_alert_web_push(
            db_session, 404, {"id": 4, "title": "안전 확인 필요", "description": "설명"}
        )

    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) == 1
    assert error_records[0].exc_info is not None

    # Unexpected errors are not treated as expiry: nothing should be deleted.
    remaining = await list_push_subscriptions(db_session, 404)
    assert len(remaining) == 1
