from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.database import get_db_session
from app.repositories.person_repository import list_people
from app.schemas.person import PersonCreate, PersonResponse, PersonUpdate
from app.services.person_service import (
    find_person_or_404,
    register_person,
    remove_person,
    update_registered_person,
)

router = APIRouter()


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    data: PersonCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> PersonResponse:
    return await register_person(session, current_user.id, data)


@router.get("", response_model=list[PersonResponse])
async def get_people(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> list[PersonResponse]:
    return await list_people(session, current_user.id)


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> PersonResponse:
    return await find_person_or_404(session, person_id, current_user.id)


@router.patch("/{person_id}", response_model=PersonResponse)
async def patch_person(
    person_id: int,
    data: PersonUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> PersonResponse:
    return await update_registered_person(session, person_id, current_user.id, data)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await remove_person(session, person_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
