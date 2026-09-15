from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NfcTag(Base):
    __tablename__ = "nfc_tags"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("people.id", ondelete="CASCADE"), index=True
    )
    public_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    guardian_name: Mapped[str] = mapped_column(String(100))
    guardian_phone: Mapped[str] = mapped_column(String(30))
    contact_reveal_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class NfcHelpEvent(Base):
    __tablename__ = "nfc_help_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nfc_tag_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("nfc_tags.id", ondelete="CASCADE"), index=True
    )
    alert_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("alerts.id", ondelete="CASCADE"), index=True
    )
    finder_token_hash: Mapped[str] = mapped_column(String(64))
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    contact_revealed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
