from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    sensor_id: int | None
    cause: str
    severity: str
    title: str
    description: str
    evidence: str | None
    source: str
    occurred_at: datetime
    read_at: datetime | None
    safety_confirmed_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime


class AlertCreate(BaseModel):
    person_id: int
    sensor_id: int | None = None
    cause: str = Field(min_length=1, max_length=50)
    severity: str = Field(default="WARNING", max_length=20)
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)
    evidence: str | None = Field(default=None, max_length=2000)
    source: str = Field(default="AI", max_length=30)
    occurred_at: datetime
    external_id: str = Field(min_length=1, max_length=100)


class UnreadAlertCount(BaseModel):
    count: int
