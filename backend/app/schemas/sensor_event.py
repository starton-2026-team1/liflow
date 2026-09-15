from datetime import date, datetime

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
    is_anomaly: bool | None = None
    label: str | None = Field(default=None, max_length=50)
    score: float | None = None


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

class WeeklyActivitySummaryResponse(BaseModel):
    summary: str
    period_start: date
    period_end: date
    event_count: int
    provider: str
    model: str


class ActivityChangeResponse(BaseModel):
    date: str
    activity_count: int
    change_count: int | None


class AverageFirstActivityResponse(BaseModel):
    average_first_activity: str
