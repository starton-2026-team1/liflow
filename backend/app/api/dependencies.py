from secrets import compare_digest
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.errors import AppError, ErrorCode
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    user_id = (
        decode_access_token(credentials.credentials) if credentials is not None else None
    )
    user = await get_user_by_id(session, user_id) if user_id is not None else None
    if user is None:
        raise AppError(
            ErrorCode.AUTH_INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

device_api_key_header = APIKeyHeader(name="X-Device-Key", auto_error=False)


async def verify_device_api_key(
    api_key: Annotated[str | None, Depends(device_api_key_header)],
) -> None:
    if not settings.device_api_key:
        raise AppError(ErrorCode.DEVICE_API_KEY_NOT_CONFIGURED)
    if api_key is None or not compare_digest(api_key, settings.device_api_key):
        raise AppError(ErrorCode.DEVICE_INVALID_API_KEY)
