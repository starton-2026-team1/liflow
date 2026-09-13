from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


async def list_chat_messages(
    session: AsyncSession, user_id: int, conversation_id: str, limit: int = 20
) -> list[ChatMessage]:
    rows = await session.scalars(
        select(ChatMessage)
        .where(
            ChatMessage.user_id == user_id,
            ChatMessage.conversation_id == conversation_id,
        )
        .order_by(ChatMessage.id.desc())
        .limit(limit)
    )
    return list(reversed(rows.all()))


async def save_chat_message(session: AsyncSession, **values: object) -> ChatMessage:
    message = ChatMessage(**values)
    session.add(message)
    await session.flush()
    await session.refresh(message)
    return message
