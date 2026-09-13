from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.database import get_db_session
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    SignUpRequest,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import log_in, sign_up, update_account

router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def create_account(data: SignUpRequest, session: DbSession) -> AuthResponse:
    return await sign_up(session, data)


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, session: DbSession) -> AuthResponse:
    return await log_in(session, data)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return current_user


@router.patch("/me", response_model=UserResponse)
async def patch_me(
    data: UserUpdate, current_user: CurrentUser, session: DbSession
) -> UserResponse:
    return await update_account(session, current_user, data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_current_user: CurrentUser) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
