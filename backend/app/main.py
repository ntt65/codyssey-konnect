from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException

from app.config import settings
from app.core.exceptions import AppError
from app.core.errors import RequestContextMiddleware, error_response, log_failure, validation_issues
from app.api import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    report = settings.configuration_report()
    logging.getLogger("uvicorn.error").log(
        logging.INFO if report["ready"] else logging.WARNING,
        "startup profile=%s config_ready=%s missing=%s invalid=%s rag=%s",
        report["profile"], report["ready"], report["missing"], report["invalid"], settings.rag_enabled,
    )
    yield


app = FastAPI(title="AI Hackathon Framework - 팀명: YourTeamName", lifespan=lifespan)

# 정적 파일 제공 (frontend 디렉터리의 index.html 등을 루트 경로에 매핑)
from fastapi.staticfiles import StaticFiles

app.add_middleware(RequestContextMiddleware)
# Added last so CORS also covers error responses produced by the error boundary.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    log_failure(request, exc, type(exc).__name__, exc.status_code)
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return error_response(request, exc.status_code, type(exc).__name__, exc.message, headers=headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    log_failure(request, exc, "ValidationError", 422)
    return error_response(request, 422, "ValidationError", "입력값을 확인해 주세요.",
                          issues=validation_issues(exc.errors()))


@app.exception_handler(ValidationError)
async def internal_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    # Invalid server-generated data is a developer error, not bad user input.
    log_failure(request, exc, "InternalServerError", 500)
    return error_response(request, 500, "InternalServerError", "서버 데이터 처리 중 오류가 발생했습니다.")


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    messages = {
        400: "요청을 처리할 수 없습니다.", 401: "로그인이 필요합니다.",
        403: "이 요청을 수행할 권한이 없습니다.", 404: "요청한 경로를 찾을 수 없습니다.",
        405: "허용되지 않은 요청 방식입니다.", 429: "요청이 많습니다. 잠시 후 다시 시도해 주세요.",
    }
    log_failure(request, exc, f"HTTP{exc.status_code}", exc.status_code)
    return error_response(request, exc.status_code, f"HTTP{exc.status_code}",
                          messages.get(exc.status_code, "요청 처리 중 오류가 발생했습니다."),
                          headers=exc.headers)


# ── 라우터 등록 ────────────────────────────────────
app.include_router(health.router)
from app.api import topic
app.include_router(topic.router)
from app.api import ask
app.include_router(ask.router)

# A root catch-all mount hides API method errors (405) behind static 404s.
# Serve pages explicitly and mount assets only at their own prefixes.
_frontend = Path(__file__).resolve().parents[2] / "frontend"


@app.get("/", include_in_schema=False)
async def homepage():
    return FileResponse(_frontend / "index.html")


@app.get("/topic_demo.html", include_in_schema=False)
async def topic_demo():
    return FileResponse(_frontend / "topic_demo.html")


app.mount("/css", StaticFiles(directory=_frontend / "css"), name="css")
app.mount("/js", StaticFiles(directory=_frontend / "js"), name="js")
