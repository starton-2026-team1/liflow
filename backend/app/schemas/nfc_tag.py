from datetime import datetime

from pydantic import BaseModel, Field


class NfcTagCreate(BaseModel):
    person_id: int
    name: str = Field(min_length=1, max_length=100)
    guardian_name: str = Field(min_length=1, max_length=100)
    guardian_phone: str = Field(pattern=r"^[0-9-]{8,30}$")
    contact_reveal_enabled: bool = True


class NfcTagResponse(BaseModel):
    id: int
    public_url: str


class NfcHelpPage(BaseModel):
    tag_name: str
    message: str = "개인정보 보호를 위해 대상자 정보는 공개하지 않습니다."


class NfcHelpCreated(BaseModel):
    event_id: int
    finder_token: str
    contact_available_at: datetime | None
    message: str


class NfcHelpStatus(BaseModel):
    acknowledged: bool
    contact_available: bool
    contact_available_at: datetime | None


class NfcContactResponse(BaseModel):
    guardian_name: str
    guardian_phone: str
