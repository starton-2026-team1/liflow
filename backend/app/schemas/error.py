from pydantic import BaseModel

from app.core.errors import ErrorCode


class ErrorFieldResponse(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str
    detail: str
    fields: list[ErrorFieldResponse] = []
