import asyncio
import logging
from json import JSONDecodeError
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import async_session_factory
from app.core.security import decode_access_token
from app.repositories.user_repository import get_user_by_id
from app.services.realtime_event_service import realtime_event_manager

router = APIRouter()
logger = logging.getLogger(__name__)

AUTHENTICATION_TIMEOUT_SECONDS = 5


async def close_with_error(
    websocket: WebSocket, *, code: int, error: str, message: str
) -> None:
    try:
        await websocket.send_json(
            {"type": "error", "error": error, "message": message}
        )
    except (RuntimeError, WebSocketDisconnect):
        pass
    try:
        await websocket.close(code=code)
    except RuntimeError:
        pass


def get_authentication_token(message: Any) -> str | None:
    if not isinstance(message, dict) or message.get("type") != "authenticate":
        return None
    token = message.get("token")
    return token if isinstance(token, str) and token.strip() else None


async def authenticate_realtime_token(token: str | None) -> int | None:
    user_id = decode_access_token(token) if token is not None else None
    if user_id is None:
        return None
    async with async_session_factory() as session:
        user = await get_user_by_id(session, user_id)
        return user.id if user is not None else None


@router.websocket("/sensor-events")
async def sensor_event_stream(
    websocket: WebSocket,
) -> None:
    await websocket.accept()
    user_id: int | None = None

    try:
        async with asyncio.timeout(AUTHENTICATION_TIMEOUT_SECONDS):
            auth_message = await websocket.receive_json()
        token = get_authentication_token(auth_message)
        user_id = await authenticate_realtime_token(token)
        if user_id is None:
            await close_with_error(
                websocket,
                code=4401,
                error="authentication_failed",
                message="Invalid or expired token",
            )
            return

        await realtime_event_manager.connect(user_id, websocket)
        await websocket.send_json({"type": "authenticated"})

        while True:
            message = await websocket.receive_json()
            if isinstance(message, dict) and message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            await websocket.send_json(
                {
                    "type": "error",
                    "error": "unsupported_message",
                    "message": "Only ping messages are supported after authentication",
                }
            )
    except TimeoutError:
        await close_with_error(
            websocket,
            code=4408,
            error="authentication_timeout",
            message="Authentication message was not received in time",
        )
    except JSONDecodeError:
        await close_with_error(
            websocket,
            code=4400,
            error="invalid_message",
            message="Messages must be valid JSON",
        )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Unexpected realtime WebSocket error")
        await close_with_error(
            websocket,
            code=1011,
            error="realtime_unavailable",
            message="Realtime service is temporarily unavailable",
        )
    finally:
        if user_id is not None:
            await realtime_event_manager.disconnect(user_id, websocket)
