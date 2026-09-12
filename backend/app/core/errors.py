from dataclasses import dataclass
from enum import StrEnum

from fastapi import status


class ErrorCode(StrEnum):
    BAD_REQUEST = "BAD_REQUEST"
    SENSOR_PERSON_MISMATCH = "SENSOR_PERSON_MISMATCH"
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_CURRENT_PASSWORD_INCORRECT = "AUTH_CURRENT_PASSWORD_INCORRECT"
    DEVICE_INVALID_API_KEY = "DEVICE_INVALID_API_KEY"
    FORBIDDEN = "FORBIDDEN"
    PERSON_NOT_FOUND = "PERSON_NOT_FOUND"
    SENSOR_NOT_FOUND = "SENSOR_NOT_FOUND"
    ROUTE_NOT_FOUND = "ROUTE_NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    AUTH_EMAIL_ALREADY_REGISTERED = "AUTH_EMAIL_ALREADY_REGISTERED"
    SENSOR_DEVICE_ID_CONFLICT = "SENSOR_DEVICE_ID_CONFLICT"
    SENSOR_NOT_CONNECTED = "SENSOR_NOT_CONNECTED"
    EVENT_ID_CONFLICT = "EVENT_ID_CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    DEVICE_API_KEY_NOT_CONFIGURED = "DEVICE_API_KEY_NOT_CONFIGURED"


ERROR_HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.BAD_REQUEST: status.HTTP_400_BAD_REQUEST,
    ErrorCode.SENSOR_PERSON_MISMATCH: status.HTTP_400_BAD_REQUEST,
    ErrorCode.AUTH_INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_CURRENT_PASSWORD_INCORRECT: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.DEVICE_INVALID_API_KEY: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.PERSON_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.SENSOR_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.ROUTE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.METHOD_NOT_ALLOWED: status.HTTP_405_METHOD_NOT_ALLOWED,
    ErrorCode.AUTH_EMAIL_ALREADY_REGISTERED: status.HTTP_409_CONFLICT,
    ErrorCode.SENSOR_DEVICE_ID_CONFLICT: status.HTTP_409_CONFLICT,
    ErrorCode.SENSOR_NOT_CONNECTED: status.HTTP_409_CONFLICT,
    ErrorCode.EVENT_ID_CONFLICT: status.HTTP_409_CONFLICT,
    ErrorCode.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ErrorCode.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.INTERNAL_SERVER_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.DATABASE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.DEVICE_API_KEY_NOT_CONFIGURED: status.HTTP_503_SERVICE_UNAVAILABLE,
}

ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.BAD_REQUEST: "잘못된 요청입니다.",
    ErrorCode.SENSOR_PERSON_MISMATCH: "선택한 센서는 해당 대상자에게 연결되어 있지 않습니다.",
    ErrorCode.AUTH_INVALID_CREDENTIALS: "이메일 또는 비밀번호가 올바르지 않습니다.",
    ErrorCode.AUTH_INVALID_TOKEN: "인증 정보가 없거나 만료되었습니다.",
    ErrorCode.AUTH_CURRENT_PASSWORD_INCORRECT: "현재 비밀번호가 올바르지 않습니다.",
    ErrorCode.DEVICE_INVALID_API_KEY: "장치 인증 키가 올바르지 않습니다.",
    ErrorCode.FORBIDDEN: "해당 작업을 수행할 권한이 없습니다.",
    ErrorCode.PERSON_NOT_FOUND: "대상자를 찾을 수 없습니다.",
    ErrorCode.SENSOR_NOT_FOUND: "센서를 찾을 수 없습니다.",
    ErrorCode.ROUTE_NOT_FOUND: "요청한 API를 찾을 수 없습니다.",
    ErrorCode.METHOD_NOT_ALLOWED: "지원하지 않는 요청 방식입니다.",
    ErrorCode.AUTH_EMAIL_ALREADY_REGISTERED: "이미 가입된 이메일입니다.",
    ErrorCode.SENSOR_DEVICE_ID_CONFLICT: "이미 등록된 센서 고유번호입니다.",
    ErrorCode.SENSOR_NOT_CONNECTED: "센서가 연결되어 있지 않습니다.",
    ErrorCode.EVENT_ID_CONFLICT: "동일한 이벤트 ID가 다른 데이터에 사용되었습니다.",
    ErrorCode.VALIDATION_ERROR: "입력값을 확인해 주세요.",
    ErrorCode.RATE_LIMITED: "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
    ErrorCode.INTERNAL_SERVER_ERROR: "서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    ErrorCode.DATABASE_UNAVAILABLE: "데이터베이스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.",
    ErrorCode.DEVICE_API_KEY_NOT_CONFIGURED: "서버에 장치 인증 키가 설정되지 않았습니다.",
}


@dataclass
class ErrorFieldDetail:
    field: str
    message: str


class AppError(Exception):
    """공통 API 예외. 전역 예외 핸들러가 이 예외를 표준 에러 응답으로 변환한다."""

    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        detail: str | None = None,
        fields: list[ErrorFieldDetail] | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        resolved_message = message or ERROR_MESSAGES[code]
        self.code = code
        self.message = resolved_message
        self.detail = detail or resolved_message
        self.fields = fields or []
        self.http_status = ERROR_HTTP_STATUS[code]
        self.headers = headers
        super().__init__(self.message)
