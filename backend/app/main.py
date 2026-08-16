from contextlib import asynccontextmanager
import logging
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.ai import router as ai_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.goals import router as goals_router
from app.api.routes.health import router as health_router
from app.api.routes.meals import router as meals_router
from app.api.routes.nutrition import router as nutrition_router
from app.api.routes.pdf import router as pdf_router
from app.core.config import get_settings, validate_production_settings
from app.core.exceptions import AppError
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.schemas.common import ErrorBody, ErrorResponse


def _database_label(raw_url: str) -> str:
    host = (urlsplit(raw_url).hostname or "").lower()
    if "supabase" in host:
        return "supabase"
    if host in {"localhost", "127.0.0.1", "::1"}:
        return "local"
    return "remote"

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("caltrack")
validate_production_settings(settings)
if not settings.uses_gemini:
    logger.warning("AI_PROVIDER is ignored; CalTrack only calls Gemini")
if settings.jwt_secret_key == "change-me-to-a-long-random-secret":
    logger.warning("JWT_SECRET_KEY is the development default. Set a unique secret before production.")
logger.info("AI provider: %s", settings.ai_provider_name)
logger.info("AI model: %s", settings.ai_model or "missing")
logger.info("AI API key: %s", "configured" if settings.ai_configured else "not configured")
logger.info("Database URL: %s", "configured" if bool(settings.database_url.strip()) else "missing")
logger.info("Database: %s", _database_label(settings.database_url))
if not settings.ai_configured:
    logger.warning("GEMINI_API_KEY is missing. Food analysis and chat will return AI_NOT_CONFIGURED until it is set.")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from app.services.ai.gemini_client import close_gemini_client, init_gemini_client

    init_gemini_client(settings)
    try:
        yield
    finally:
        close_gemini_client()


app = FastAPI(
    title="CalTrack API",
    description=(
        "Personal calorie tracker REST API. "
        "The frontend communicates exclusively through this API. "
        "AI providers and PostgreSQL are never accessed from the client."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)
# Added last so it runs first and answers OPTIONS preflight before other middleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(goals_router, prefix="/api/v1")
app.include_router(meals_router, prefix="/api/v1")
app.include_router(nutrition_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(pdf_router, prefix="/api/v1")


def _error_payload(code: str, message: str, details: list[str] | None = None) -> dict:
    return ErrorResponse(error=ErrorBody(code=code, message=message, details=details)).model_dump(
        exclude_none=True
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    path = request.url.path
    expected_refresh_miss = (
        exc.status_code == 401
        and request.method == "POST"
        and path.rstrip("/").endswith("/auth/refresh")
    )
    if not settings.is_production and not expected_refresh_miss:
        logger.warning(
            "AppError %s %s code=%s status=%s rid=%s",
            request.method,
            path,
            exc.code,
            exc.status_code,
            getattr(request.state, "request_id", "-"),
        )
    return JSONResponse(status_code=exc.status_code, content=_error_payload(exc.code, exc.message))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    safe_log = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        message = str(error.get("msg") or "invalid")
        details.append(f"{location}: {message}" if location else message)
        safe_log.append({"loc": location or "-", "type": error.get("type"), "msg": message})
    if not settings.is_production:
        logger.warning(
            "Validation error %s %s status=422 fields=%s rid=%s",
            request.method,
            request.url.path,
            safe_log,
            getattr(request.state, "request_id", "-"),
        )
    return JSONResponse(
        status_code=422,
        content=_error_payload("VALIDATION_ERROR", "Request validation failed", details),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if not settings.is_production:
        logger.warning(
            "HTTPException %s %s status=%s rid=%s",
            request.method,
            request.url.path,
            exc.status_code,
            getattr(request.state, "request_id", "-"),
        )
    code = "UNAUTHORIZED" if exc.status_code == 401 else "HTTP_ERROR"
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(status_code=exc.status_code, content=_error_payload(code, message))


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error rid=%s", getattr(_request.state, "request_id", "-"))
    return JSONResponse(
        status_code=500,
        content=_error_payload("INTERNAL_ERROR", "An unexpected error occurred"),
    )


@app.get("/", tags=["meta"], summary="API root")
def root() -> dict[str, str]:
    return {
        "name": "CalTrack API",
        "docs": "/docs",
        "health": "/health",
    }
