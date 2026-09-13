from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SensorEvent(Base):
    __tablename__ = "sensor_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_event_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    person_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sensor_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sensors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    detected_value: Mapped[str] = mapped_column(String(255), nullable=False)
    sensor_status: Mapped[str] = mapped_column(String(30), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
