from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SocketAuthentication(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["authenticate"]
    token: str | None = Field(default=None, max_length=4096)
    api_key: str | None = Field(default=None, max_length=4096)


class SocketRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["request"]
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    method: Literal["GET", "POST", "PATCH", "DELETE"]
    path: str = Field(min_length=1, max_length=512)
    body: dict[str, Any] = Field(default_factory=dict)


class EventQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person_id: int | None = Field(default=None, gt=0)
    limit: int = Field(default=100, ge=1, le=500)
