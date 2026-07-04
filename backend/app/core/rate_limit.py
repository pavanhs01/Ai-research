"""
Simple sliding-window rate limiter keyed by client identity (Clerk user ID
if authenticated, else IP). Suitable for single-instance deployments; for
multi-instance production scale this should be backed by Redis instead of
an in-process dict (swap the `_buckets` store for a Redis client without
changing the public interface).
"""

import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        identity = self._resolve_identity(request)
        now = time.time()

        timestamps = self._buckets[identity]
        timestamps[:] = [t for t in timestamps if now - t < _WINDOW_SECONDS]

        if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
            logger.warning("Rate limit exceeded for %s", identity)
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limited", "message": "Too many requests, slow down."}},
            )

        timestamps.append(now)
        return await call_next(request)

    @staticmethod
    def _resolve_identity(request: Request) -> str:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return f"token:{hash(auth_header)}"
        client = request.client
        return f"ip:{client.host if client else 'unknown'}"
