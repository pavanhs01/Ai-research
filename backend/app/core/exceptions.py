from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base class for all application-raised, user-facing errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, code: str = "app_error"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "unauthorized")


class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have access to this resource"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "forbidden")


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "not_found")


class RateLimitException(AppException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited")


class ExternalServiceException(AppException):
    """Raised when OpenAI / Pinecone / S3 / Stripe calls fail after retries."""

    def __init__(self, message: str = "An upstream service failed"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY, "external_service_error")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("AppException: %s | path=%s", exc.message, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on path=%s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred"}},
    )
