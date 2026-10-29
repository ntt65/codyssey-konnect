from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ValidationIssue(BaseModel):
    """Invalid field location and safe guidance; never includes the submitted value."""
    field: str
    code: str
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    issues: list[ValidationIssue] = Field(default_factory=list)


class Envelope(BaseModel, Generic[T]):
    """모든 API 응답의 공통 포맷."""
    ok: bool
    data: T | None = None
    error: ErrorDetail | None = None
    trace: list[dict] | None = None  # 개발 환경에서만 포함
    request_id: str | None = None  # 오류 응답과 X-Request-ID로 서버 로그를 연결

    @classmethod
    def ok_response(cls, data: T, trace: list[dict] | None = None) -> "Envelope[T]":
        return cls(ok=True, data=data, trace=trace)

    @classmethod
    def error_response(
        cls, code: str, message: str, *, request_id: str | None = None,
        issues: list[ValidationIssue] | None = None,
    ) -> "Envelope[None]":
        return cls(ok=False, error=ErrorDetail(code=code, message=message, issues=issues or []),
                   request_id=request_id)
