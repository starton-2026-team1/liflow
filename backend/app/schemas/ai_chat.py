from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    person_id: int | None = None
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, min_length=36, max_length=36)


class ChatAnswer(BaseModel):
    conversation_id: str
    answer: str
    model: str
    provider: str
    disclaimer: str


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: str
    person_id: int | None
    role: str
    content: str
    model: str | None
    created_at: datetime
