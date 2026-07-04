"""Unit tests for custom exceptions."""
import pytest
from app.core.exceptions import (
    AppException, UnauthorizedException, ForbiddenException,
    NotFoundException, RateLimitException, ExternalServiceException,
)


def test_app_exception_defaults():
    exc = AppException("Something went wrong")
    assert exc.status_code == 400
    assert exc.code == "app_error"
    assert str(exc) == "Something went wrong"


def test_unauthorized_exception():
    exc = UnauthorizedException()
    assert exc.status_code == 401
    assert exc.code == "unauthorized"


def test_forbidden_exception():
    exc = ForbiddenException()
    assert exc.status_code == 403
    assert exc.code == "forbidden"


def test_not_found_exception():
    exc = NotFoundException("Project not found.")
    assert exc.status_code == 404
    assert exc.message == "Project not found."


def test_rate_limit_exception():
    exc = RateLimitException()
    assert exc.status_code == 429
    assert exc.code == "rate_limited"


def test_external_service_exception():
    exc = ExternalServiceException("OpenAI timed out")
    assert exc.status_code == 502
    assert exc.code == "external_service_error"
    assert exc.message == "OpenAI timed out"
