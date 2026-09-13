from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StatusEventCreate(BaseModel):
    event_id: str = Field(min_length=1, max_length=100)
    device_id: str = Field(min_length=1, max_length=100)
    status: Literal["NORMAL", "ABNORMAL"]
    judged_at: datetime
    detected_value: str | None = Field(default=None, max_length=255)


class StatusEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str = Field(validation_alias="external_event_id")
    person_id: int
    sensor_id: int | None
    status: str
    judged_at: datetime
    detected_value: str | None
    received_at: datetime


class PersonStatusResponse(BaseModel):
    person_id: int
    status: str
    judged_at: datetime | None
    sensor_id: int | None


class PersonStatusHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int | None
    status: str
    judged_at: datetime
    detected_value: str | None
    received_at: datetime


class PersonStatusHistoryPage(BaseModel):
    items: list[PersonStatusHistoryItem]
    page: int
    page_size: int
    total: int
