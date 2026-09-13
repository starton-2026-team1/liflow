from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser
from app.core.database import get_db_session
from app.repositories.chat_repository import list_chat_messages
from app.schemas.ai_chat import ChatAnswer, ChatMessageResponse, ChatRequest
from app.services.ai_chat_service import ask_ai

router = APIRouter()


@router.post("/messages", response_model=ChatAnswer)
async def create_chat_message(
    data: ChatRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db_session),
) -> ChatAnswer:
    return await ask_ai(session, current_user.id, data)


@router.get("/conversations/{conversation_id}", response_model=list[ChatMessageResponse])
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> list[ChatMessageResponse]:
    return await list_chat_messages(session, current_user.id, conversation_id, limit)
