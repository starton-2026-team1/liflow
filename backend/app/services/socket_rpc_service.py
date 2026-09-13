import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.person_repository import get_person_owner_id, list_people
from app.repositories.sensor_event_repository import list_sensor_events
from app.repositories.sensor_repository import list_sensors
from app.schemas.ai_chat import ChatAnswer, ChatRequest
from app.schemas.auth import LoginRequest, SignUpRequest, UserResponse, UserUpdate
from app.schemas.person import PersonCreate, PersonResponse, PersonUpdate
from app.schemas.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.schemas.sensor_event import (
    DeviceEventCreate,
    DeviceEventResponse,
    SensorEventCreate,
    SensorEventResponse,
)
from app.schemas.websocket import EventQuery, SocketRequest
from app.services.ai_chat_service import ask_ai
from app.services.auth_service import log_in, sign_up, update_account
from app.services.device_event_service import record_device_event
from app.services.person_service import (
    find_person_or_404,
    register_person,
    remove_person,
    update_registered_person,
)
from app.services.sensor_event_service import record_sensor_event
from app.services.sensor_service import (
    find_sensor_or_404,
    register_sensor,
    remove_sensor,
    update_registered_sensor,
)


@dataclass
class SocketResult:
    data: Any = None
    status: int = 200
    owner_id: int | None = None
    event: dict[str, Any] | None = None


def changed(data: Any, owner_id: int, resource: str, status: int = 200) -> SocketResult:
    return SocketResult(data, status, owner_id, {"type": "data.changed", "resource": resource})


async def dispatch_socket_request(
    session: AsyncSession, request: SocketRequest, user: User | None, *, device: bool = False
) -> SocketResult:
    url = urlsplit(request.path)
    if url.scheme or url.netloc or url.fragment or not request.path.startswith("/"):
        raise HTTPException(400, "Invalid request path")
    path, method = url.path, request.method

    if device:
        if (method, path) != ("POST", "/device-events") or url.query:
            raise HTTPException(403, "Device connections can only submit device events")
        event, created = await record_device_event(
            session, DeviceEventCreate.model_validate(request.body)
        )
        data = DeviceEventResponse.model_validate(event).model_dump(mode="json")
        return SocketResult(
            data,
            201 if created else 200,
            await get_person_owner_id(session, event.person_id) if created else None,
            {"type": "sensor_event.created", "data": data} if created else None,
        )

    if (method, path) == ("GET", "/health"):
        return SocketResult({"status": "ok"})
    if path.startswith("/auth/") and url.query:
        raise HTTPException(400, "Query parameters are not supported")
    if (method, path) == ("POST", "/auth/signup"):
        auth = await sign_up(session, SignUpRequest.model_validate(request.body))
        return SocketResult(auth.model_dump(mode="json"), 201)
    if (method, path) == ("POST", "/auth/login"):
        auth = await log_in(session, LoginRequest.model_validate(request.body))
        return SocketResult(auth.model_dump(mode="json"))
    if user is None:
        raise HTTPException(401, "Authentication required")

    if (method, path) == ("POST", "/auth/logout"):
        return SocketResult(status=204)
    if (method, path) == ("GET", "/auth/me"):
        return SocketResult(UserResponse.model_validate(user).model_dump(mode="json"))
    if (method, path) == ("PATCH", "/auth/me"):
        updated = await update_account(session, user, UserUpdate.model_validate(request.body))
        return changed(
            UserResponse.model_validate(updated).model_dump(mode="json"), user.id, "user"
        )

    if (method, path) == ("POST", "/ai-chat/messages") and not url.query:
        answer = await ask_ai(session, user.id, ChatRequest.model_validate(request.body))
        return SocketResult(ChatAnswer.model_validate(answer).model_dump(mode="json"))

    if (method, path) == ("GET", "/snapshot"):
        people = await list_people(session, user.id)
        sensors = await list_sensors(session, user.id)
        events = await list_sensor_events(session, user.id, limit=500)
        return SocketResult(
            {
                "people": [
                    PersonResponse.model_validate(p).model_dump(mode="json") for p in people
                ],
                "sensors": [
                    SensorResponse.model_validate(s).model_dump(mode="json") for s in sensors
                ],
                "events": [
                    SensorEventResponse.model_validate(e).model_dump(mode="json") for e in events
                ],
            }
        )

    match = re.fullmatch(r"/(people|sensors)(?:/([1-9][0-9]*))?", path)
    if match:
        if url.query:
            raise HTTPException(400, "Query parameters are not supported")
        resource, raw_id = match.groups()
        entity_id = int(raw_id) if raw_id else None
        is_person = resource == "people"
        schema = PersonResponse if is_person else SensorResponse
        if method == "GET":
            if entity_id is None:
                records = await (list_people if is_person else list_sensors)(session, user.id)
                return SocketResult(
                    [schema.model_validate(r).model_dump(mode="json") for r in records]
                )
            record = await (find_person_or_404 if is_person else find_sensor_or_404)(
                session, entity_id, user.id
            )
            return SocketResult(schema.model_validate(record).model_dump(mode="json"))
        if method == "POST" and entity_id is None:
            if is_person:
                record = await register_person(
                    session, user.id, PersonCreate.model_validate(request.body)
                )
            else:
                record = await register_sensor(
                    session, user.id, SensorCreate.model_validate(request.body)
                )
            return changed(
                schema.model_validate(record).model_dump(mode="json"), user.id, resource, 201
            )
        if method == "PATCH" and entity_id is not None:
            if is_person:
                record = await update_registered_person(
                    session, entity_id, user.id, PersonUpdate.model_validate(request.body)
                )
            else:
                record = await update_registered_sensor(
                    session, entity_id, user.id, SensorUpdate.model_validate(request.body)
                )
            return changed(schema.model_validate(record).model_dump(mode="json"), user.id, resource)
        if method == "DELETE" and entity_id is not None:
            await (remove_person if is_person else remove_sensor)(session, entity_id, user.id)
            return changed(None, user.id, resource, 204)
        raise HTTPException(405, "Method not allowed")

    timeline = re.fullmatch(r"/sensor-events/people/([1-9][0-9]*)/timeline", path)
    if method == "GET" and (path == "/sensor-events" or timeline):
        query = EventQuery.model_validate(dict(parse_qsl(url.query, keep_blank_values=True)))
        person_id = int(timeline.group(1)) if timeline else query.person_id
        if person_id is not None:
            await find_person_or_404(session, person_id, user.id)
        records = await list_sensor_events(session, user.id, person_id, query.limit)
        return SocketResult(
            [SensorEventResponse.model_validate(r).model_dump(mode="json") for r in records]
        )
    if (method, path) == ("POST", "/sensor-events") and not url.query:
        event = await record_sensor_event(
            session, user.id, SensorEventCreate.model_validate(request.body)
        )
        data = SensorEventResponse.model_validate(event).model_dump(mode="json")
        return SocketResult(data, 201, user.id, {"type": "sensor_event.created", "data": data})
    raise HTTPException(404, "Unknown operation")
