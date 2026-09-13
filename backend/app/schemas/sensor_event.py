from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SensorEventCreate(BaseModel):
    person_id: int
    sensor_id: int | None = None
    detected_at: datetime
    detected_value: str = Field(min_length=1, max_length=255)
    sensor_status: str = Field(max_length=30)


class SensorEventResponse(SensorEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ai_label: str | None = None
    ai_score: float | None = None
    ai_is_anomaly: bool | None = None
    received_at: datetime


class DeviceEventCreate(BaseModel):
    event_id: str = Field(min_length=1, max_length=100)
    device_id: str = Field(min_length=1, max_length=100)
    detected_at: datetime
    detected_value: str = Field(min_length=1, max_length=255)


class DeviceEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str = Field(validation_alias="external_event_id")
    person_id: int
    sensor_id: int
    detected_at: datetime
    detected_value: str
    sensor_status: str
    ai_label: str | None = None
    ai_score: float | None = None
    ai_is_anomaly: bool | None = None
    received_at: datetime
