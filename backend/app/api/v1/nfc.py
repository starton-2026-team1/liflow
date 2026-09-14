import logging

import ndef
import nfc
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.errors import AppError, ErrorCode

# 화면 구성 [안심태그 버튼 -> 이름, 전화번호를 입력해주세요 -> 태깅을 해주세요 -> 백엔드 통신 nfc]

router = APIRouter()
logger = logging.getLogger(__name__)

NFC_READER_PATH = "usb"
NFC_TAG_WAIT_TIMEOUT_SEC = 10


class NfcRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=1, max_length=20)


class NfcRegisterResponse(BaseModel):
    name: str
    phone: str


def _write_ndef_records(tag: nfc.tag.Tag, name: str, phone: str) -> None:
    if not tag.ndef or not tag.ndef.is_writeable:
        raise AppError(ErrorCode.NFC_WRITE_FAILED, detail="태그가 쓰기 가능한 상태가 아닙니다.")

    records = [
        ndef.TextRecord(name, language="ko"),
        ndef.TextRecord(phone, language="ko"),
    ]
    try:
        tag.ndef.records = records
    except Exception as exc:  # nfcpy는 태그 종류별로 다양한 예외를 던진다.
        raise AppError(ErrorCode.NFC_WRITE_FAILED) from exc


@router.post("", response_model=NfcRegisterResponse)
def write_nfc(data: NfcRegisterRequest) -> NfcRegisterResponse:
    try:
        clf = nfc.ContactlessFrontend(NFC_READER_PATH)
    except OSError as exc:
        logger.exception("NFC 리더기 연결에 실패했습니다.")
        raise AppError(ErrorCode.NFC_READER_NOT_CONNECTED) from exc

    try:
        tag = clf.connect(rdwr={"on-connect": lambda _tag: False})
        if tag is None:
            raise AppError(ErrorCode.NFC_TAG_NOT_DETECTED)

        _write_ndef_records(tag, data.name, data.phone)
    finally:
        clf.close()

    logger.info("NFC 태그 등록 완료: name=%s", data.name)
    return NfcRegisterResponse(name=data.name, phone=data.phone)
