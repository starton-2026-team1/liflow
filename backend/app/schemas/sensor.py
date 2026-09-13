from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SensorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=50)
    device_id: str = Field(min_length=1, max_length=100)
    person_id: int
    target_object: str = Field(min_length=1, max_length=100)
    status: str = Field(default="DISCONNECTED", max_length=30)


class SensorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = Field(default=None, min_length=1, max_length=50)
    person_id: int | None = None
    target_object: str | None = Field(default=None, min_length=1, max_length=100)
    status: str | None = Field(default=None, max_length=30)


class SensorResponse(SensorCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
