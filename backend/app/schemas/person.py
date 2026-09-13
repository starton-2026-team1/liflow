from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PersonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age_group: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    living_space: str = Field(min_length=1, max_length=100)
    health_notes: str | None = Field(default=None, max_length=1000)
    monitoring_status: str = Field(default="PAUSED", max_length=30)
    inactivity_threshold_minutes: int = Field(default=30, ge=5, le=1440)


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    age_group: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    living_space: str | None = Field(default=None, min_length=1, max_length=100)
    health_notes: str | None = Field(default=None, max_length=1000)
    monitoring_status: str | None = Field(default=None, max_length=30)
    inactivity_threshold_minutes: int | None = Field(default=None, ge=5, le=1440)


class PersonResponse(PersonCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
