"""HTTP error boundary and safe diagnostics shared by all API routes.

Use AppError subclasses for expected failures. Unexpected exceptions become 500,
with a request ID and type/frame diagnostics, without logging exception messages,
request bodies, credentials, query strings, or third-party response bodies.
"""
import logging
import re
import time
import traceback
from pathlib import Path
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders

from app.models.common import Envelope, ValidationIssue

logger = logging.getLogger("uvicorn.error")


def error_response(request: Request, status: int, code: str, message: str, *,
                   issues: list[ValidationIssue] | None = None,
                   headers: dict[str, str] | None = None) -> JSONResponse:
    request_id = request.state.request_id
    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = request_id
    return JSONResponse(status_code=status, headers=response_headers,
                        content=Envelope.error_response(
                            code, message, request_id=request_id, issues=issues,
                        ).model_dump())


def log_failure(request: Request, exc: Exception, code: str, status: int) -> None:
    # logger.exception/str(exc) can reveal provider keys, SQL parameters and DSNs.
    # Log only exception types and frame locations, including chained causes.
    causes = []
    current = exc
    seen = set()
    while current is not None and id(current) not in seen and len(causes) < 4:
        seen.add(id(current))
        frames = traceback.extract_tb(current.__traceback__)[-6:]
        locations = ",".join(f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in frames)
        causes.append(f"{type(current).__name__}[{locations}]")
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    route = request.scope.get("route")
    logger.log(logging.ERROR if status >= 500 else logging.WARNING,
               "request_id=%s code=%s status=%s route=%s causes=%s",
               request.state.request_id, code, status,
               getattr(route, "path", "<unmatched>"), " <- ".join(causes))


_INPUT_MESSAGES = {
    "missing": "필수 입력값입니다.",
    "json_invalid": "올바른 JSON 형식으로 보내 주세요.",
    "string_type": "문자열로 입력해 주세요.",
    "string_too_short": "입력값이 너무 짧습니다.",
    "string_too_long": "입력값이 너무 깁니다.",
    "int_parsing": "정수로 입력해 주세요.",
    "greater_than_equal": "허용된 최솟값 이상으로 입력해 주세요.",
    "less_than_equal": "허용된 최댓값 이하로 입력해 주세요.",
}


def validation_issues(errors: list[dict]) -> list[ValidationIssue]:
    issues = []
    for error in errors[:10]:
        parts = [str(part) for part in error.get("loc", ())]
        field = ".".join(part if re.fullmatch(r"[\w-]{1,64}", part) else "field" for part in parts)
        code = error.get("type", "invalid")
        issues.append(ValidationIssue(field=field or "body", code=code,
                                      message=_INPUT_MESSAGES.get(code, "입력값을 확인해 주세요.")))
    return issues


class RequestContextMiddleware:
    """ASGI boundary: keep 500 responses inside CORS and attach IDs to all responses."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        scope.setdefault("state", {})["request_id"] = uuid4().hex
        request = Request(scope)
        started = time.monotonic()
        response_started = False
        status = 500

        async def send_with_id(message):
            nonlocal response_started, status
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                MutableHeaders(scope=message)["X-Request-ID"] = request.state.request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception as exc:
            log_failure(request, exc, "InternalServerError", 500)
            if response_started:
                # A streaming/background failure cannot replace headers already sent.
                raise
            response = error_response(request, 500, "InternalServerError",
                                      "서버에서 오류가 발생했습니다. 요청 ID를 담당자에게 전달해 주세요.")
            await response(scope, receive, send_with_id)
        finally:
            route = scope.get("route")
            logger.info("request_id=%s method=%s route=%s status=%s elapsed_ms=%s",
                        request.state.request_id, scope["method"],
                        getattr(route, "path", "<unmatched>"), status,
                        round((time.monotonic() - started) * 1000))
