import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import (
    check_database_connection,
    close_database_connection,
)
from app.core.errors import ERROR_MESSAGES, AppError, ErrorCode
from app.schemas.error import ErrorFieldResponse, ErrorResponse

logger = logging.getLogger(__name__)

_VALIDATION_FIELD_MESSAGES: dict[str, str] = {
    "missing": "필수 입력값입니다.",
    "string_too_short": "최소 길이 이상 입력해 주세요.",
    "too_short": "최소 길이 이상 입력해 주세요.",
    "string_too_long": "허용된 최대 길이를 초과했습니다.",
    "too_long": "허용된 최대 길이를 초과했습니다.",
    "int_parsing": "숫자로 입력해 주세요.",
    "float_parsing": "숫자로 입력해 주세요.",
    "int_type": "숫자로 입력해 주세요.",
    "float_type": "숫자로 입력해 주세요.",
    "decimal_parsing": "숫자로 입력해 주세요.",
    "enum": "허용되지 않은 값입니다.",
    "literal_error": "허용되지 않은 값입니다.",
    "less_than_equal": "허용된 범위의 값을 입력해 주세요.",
    "greater_than_equal": "허용된 범위의 값을 입력해 주세요.",
    "less_than": "허용된 범위의 값을 입력해 주세요.",
    "greater_than": "허용된 범위의 값을 입력해 주세요.",
}


def _validation_field_message(error: dict) -> str:
    error_type = error.get("type", "")
    if error_type == "value_error" and any(
        "email" in str(part).lower() for part in error.get("loc", ())
    ):
        return "올바른 이메일 형식이 아닙니다."
    return _VALIDATION_FIELD_MESSAGES.get(error_type, "입력값이 올바르지 않습니다.")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await check_database_connection()
    yield
    await close_database_connection()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    body = ErrorResponse(
        code=exc.code,
        message=exc.message,
        detail=exc.detail,
        fields=[
            ErrorFieldResponse(field=f.field, message=f.message) for f in exc.fields
        ],
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=body.model_dump(mode="json"),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = [
        ErrorFieldResponse(
            field=".".join(str(part) for part in error["loc"]),
            message=_validation_field_message(error),
        )
        for error in exc.errors()
    ]
    message = ERROR_MESSAGES[ErrorCode.VALIDATION_ERROR]
    body = ErrorResponse(
        code=ErrorCode.VALIDATION_ERROR,
        message=message,
        detail=message,
        fields=fields,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=body.model_dump(mode="json"),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if exc.status_code == status.HTTP_404_NOT_FOUND and exc.detail in (
        None,
        "Not Found",
    ):
        code = ErrorCode.ROUTE_NOT_FOUND
        message = ERROR_MESSAGES[code]
    elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        code = ErrorCode.METHOD_NOT_ALLOWED
        message = ERROR_MESSAGES[code]
    else:
        # 아직 AppError로 전환되지 않은 레거시 HTTPException.
        # 기존 detail 문구를 그대로 보존해 하위 호환을 유지한다.
        code = ErrorCode.BAD_REQUEST
        message = str(exc.detail) if exc.detail else ERROR_MESSAGES[code]
    body = ErrorResponse(code=code, message=message, detail=message, fields=[])
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(mode="json"),
        headers=exc.headers,
    )


@app.exception_handler(DBAPIError)
async def database_error_handler(_: Request, exc: DBAPIError) -> JSONResponse:
    logger.exception("Database error", exc_info=exc)
    message = ERROR_MESSAGES[ErrorCode.DATABASE_UNAVAILABLE]
    body = ErrorResponse(
        code=ErrorCode.DATABASE_UNAVAILABLE,
        message=message,
        detail=message,
        fields=[],
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=body.model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", exc_info=exc)
    message = ERROR_MESSAGES[ErrorCode.INTERNAL_SERVER_ERROR]
    body = ErrorResponse(
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message=message,
        detail=message,
        fields=[],
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=body.model_dump(mode="json"),
    )