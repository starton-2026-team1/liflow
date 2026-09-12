import asyncio
import json
import logging
from collections import deque
from secrets import compare_digest
from time import monotonic, time

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.security import access_token_expiry, decode_access_token
from app.repositories.user_repository import get_user_by_id
from app.schemas.websocket import SocketAuthentication, SocketRequest
from app.services.realtime_event_service import realtime_event_manager
from app.services.socket_rpc_service import dispatch_socket_request

router = APIRouter()
logger = logging.getLogger(__name__)
AUTHENTICATION_TIMEOUT_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 15
IDLE_TIMEOUT_SECONDS = 70
MAX_MESSAGE_BYTES = 65_536


async def close_with_error(websocket: WebSocket, *, code: int, error: str, message: str) -> None:
    try:
        await realtime_event_manager.send(
            websocket, {"type": "error", "error": error, "message": message}
        )
    except Exception:
        pass
    try:
        async with asyncio.timeout(1):
            await websocket.close(code=code)
    except Exception:
        pass


async def read_message(websocket: WebSocket) -> dict:
    frame = await websocket.receive()
    if frame["type"] == "websocket.disconnect":
        raise WebSocketDisconnect(frame.get("code", 1000))
    text = frame.get("text")
    if text is None:
        raise HTTPException(400, "Only JSON text messages are supported")
    if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise HTTPException(413, "Message exceeds 64 KiB")
    try:
        message = json.loads(text)
    except (ValueError, RecursionError) as exc:
        raise HTTPException(400, "Messages must be valid JSON") from exc
    if not isinstance(message, dict):
        raise HTTPException(400, "Message must be a JSON object")
    return message


async def authenticate_realtime_token(token: str | None) -> int | None:
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        return None
    async with async_session_factory() as session:
        user = await get_user_by_id(session, user_id)
        return user.id if user is not None else None


def verify_device_key(key: str | None) -> None:
    if not settings.device_api_key:
        raise HTTPException(503, "Device API key is not configured")
    if not key or not compare_digest(key, settings.device_api_key):
        raise HTTPException(401, "Invalid device API key")


async def respond_error(
    websocket: WebSocket,
    request_id: str | None,
    status: int,
    detail: str,
    fields: list | None = None,
) -> None:
    await realtime_event_manager.send(
        websocket,
        {
            "type": "response",
            "id": request_id,
            "ok": False,
            "status": status,
            "error": {"message": detail, "fields": fields or []},
        },
    )


async def process_request(
    websocket: WebSocket, request: SocketRequest, auth: SocketAuthentication, *, device: bool
) -> bool:
    """Commit one request before acknowledging or broadcasting; never hold a session while idle."""
    try:
        async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
            async with async_session_factory() as session:
                async with session.begin():
                    user = None
                    if device:
                        verify_device_key(auth.api_key)
                    elif auth.token:
                        user_id = decode_access_token(auth.token)
                        user = await get_user_by_id(session, user_id) if user_id else None
                        if user is None:
                            raise HTTPException(401, "Invalid or expired token")
                    result = await dispatch_socket_request(session, request, user, device=device)
    except HTTPException as exc:
        await respond_error(websocket, request.id, exc.status_code, str(exc.detail))
        # Wrong passwords on public login/profile requests don't invalidate the connection.
        return not (
            exc.status_code == 401
            and str(exc.detail)
            in (
                "Invalid or expired token",
                "Invalid device API key",
            )
        )
    except ValidationError as exc:
        fields = [
            {"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
            for e in exc.errors(include_input=False, include_url=False)
        ]
        await respond_error(websocket, request.id, 422, "Invalid request data", fields)
        return True
    except IntegrityError:
        await respond_error(websocket, request.id, 409, "Data conflicts with existing records")
        return True
    except TimeoutError:
        await respond_error(websocket, request.id, 504, "Request timed out; reload before retrying")
        return True
    except SQLAlchemyError:
        logger.warning("WebSocket database operation failed", exc_info=False)
        await respond_error(websocket, request.id, 503, "Database temporarily unavailable")
        return True
    except Exception:
        logger.error("WebSocket operation failed", exc_info=False)
        await respond_error(websocket, request.id, 500, "Request could not be completed")
        return True

    if result.owner_id is not None and result.event is not None:
        try:
            await realtime_event_manager.publish_sensor_event(result.owner_id, result.event)
        except Exception:
            logger.warning("Post-commit WebSocket notification failed", exc_info=False)
    await realtime_event_manager.send(
        websocket,
        {
            "type": "response",
            "id": request.id,
            "ok": True,
            "status": result.status,
            "data": result.data,
        },
    )
    return request.path != "/auth/logout"


async def serve_socket(websocket: WebSocket, *, device: bool = False, stream: bool = False) -> None:
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in settings.allowed_cors_origins:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    user_id = None
    expires_at = None
    try:
        async with asyncio.timeout(AUTHENTICATION_TIMEOUT_SECONDS):
            auth = SocketAuthentication.model_validate(await read_message(websocket))
            if device:
                if auth.token is not None:
                    raise HTTPException(403, "Use device API key authentication")
                verify_device_key(auth.api_key)
            else:
                if auth.api_key is not None:
                    raise HTTPException(403, "Use guardian token authentication")
                if auth.token:
                    expires_at = access_token_expiry(auth.token)
                    user_id = await authenticate_realtime_token(auth.token)
                    if user_id is None or expires_at is None:
                        raise HTTPException(401, "Invalid or expired token")
                elif stream:
                    raise HTTPException(401, "Authentication required")

        if user_id is not None:
            await realtime_event_manager.connect(user_id, websocket, expires_at=expires_at)
        await realtime_event_manager.send(
            websocket,
            {
                "type": "authenticated",
                "version": 1,
                "role": "device" if device else "guardian" if user_id is not None else "anonymous",
            },
        )
        recent_ids: deque[str] = deque(maxlen=256)
        message_times: deque[float] = deque()
        while True:
            remaining = expires_at - time() if expires_at else IDLE_TIMEOUT_SECONDS
            if remaining <= 0:
                raise HTTPException(401, "Token expired")
            try:
                async with asyncio.timeout(min(IDLE_TIMEOUT_SECONDS, remaining)):
                    message = await read_message(websocket)
            except TimeoutError:
                if expires_at and expires_at <= time():
                    raise HTTPException(401, "Token expired") from None
                await close_with_error(
                    websocket, code=4408, error="idle_timeout", message="Heartbeat not received"
                )
                return

            now = monotonic()
            while message_times and message_times[0] < now - 10:
                message_times.popleft()
            message_times.append(now)
            if len(message_times) > 100:
                await close_with_error(
                    websocket, code=4429, error="rate_limited", message="Too many messages"
                )
                return
            if message.get("type") == "ping":
                if device:
                    verify_device_key(auth.api_key)
                await realtime_event_manager.send(websocket, {"type": "pong"})
                continue
            if stream:
                await realtime_event_manager.send(
                    websocket,
                    {
                        "type": "error",
                        "error": "unsupported_message",
                        "message": "Use /ws/rpc for requests",
                    },
                )
                continue
            try:
                request = SocketRequest.model_validate(message)
            except ValidationError:
                request_id = message.get("id")
                await respond_error(
                    websocket,
                    request_id if isinstance(request_id, str) and len(request_id) <= 64 else None,
                    422,
                    "Invalid request envelope",
                )
                continue
            if request.id in recent_ids:
                await respond_error(
                    websocket, request.id, 409, "Request id already used on this connection"
                )
                continue
            recent_ids.append(request.id)
            if not await process_request(websocket, request, auth, device=device):
                await websocket.close(code=1000 if request.path == "/auth/logout" else 4401)
                return
    except TimeoutError:
        await close_with_error(
            websocket, code=4408, error="authentication_timeout", message="Authentication timed out"
        )
    except ValidationError:
        await close_with_error(
            websocket, code=4400, error="invalid_message", message="Invalid authentication envelope"
        )
    except HTTPException as exc:
        code = {401: 4401, 403: 4403, 413: 1009, 503: 1013}.get(exc.status_code, 4400)
        await close_with_error(
            websocket, code=code, error="connection_rejected", message=str(exc.detail)
        )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.warning("WebSocket connection failed", exc_info=False)
        await close_with_error(
            websocket,
            code=1011,
            error="realtime_unavailable",
            message="Realtime service temporarily unavailable",
        )
    finally:
        if user_id is not None:
            await realtime_event_manager.disconnect(user_id, websocket)
        realtime_event_manager.forget(websocket)


@router.websocket("/rpc")
async def application_socket(websocket: WebSocket) -> None:
    await serve_socket(websocket)


@router.websocket("/device-events")
async def device_socket(websocket: WebSocket) -> None:
    await serve_socket(websocket, device=True)


@router.websocket("/sensor-events")
async def sensor_event_stream(websocket: WebSocket) -> None:
    await serve_socket(websocket, stream=True)
