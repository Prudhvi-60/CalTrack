from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import get_settings

_AUTH_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
}
_AI_PREFIXES = ("/api/v1/ai/analyze-food", "/api/v1/chat", "/api/v1/import/pdf", "/api/v1/import/meal-plan")


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: float = 60) -> bool:
        if limit <= 0:
            return True
        now = time.monotonic()
        with self._lock:
            bucket = self._hits[key]
            cutoff = now - window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True


limiter = SlidingWindowLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled or request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        limit = 0
        if path in _AUTH_PATHS:
            limit = settings.auth_rate_limit_per_minute
        elif path.startswith(_AI_PREFIXES):
            limit = settings.ai_rate_limit_per_minute
        if limit <= 0:
            return await call_next(request)
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        if not limiter.allow(f"{path}:{ip}", limit):
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "RATE_LIMITED", "message": "Too many requests. Please try again shortly."}},
            )
        return await call_next(request)
