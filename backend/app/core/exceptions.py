"""Custom exception hierarchy and FastAPI exception handlers."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.utils.posthog_client import capture_posthog_event


class AppException(Exception):
    """Base domain exception with structured metadata."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = HTTPStatus.BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = int(status_code)
        self.details = details or {}


class AuthenticationException(AppException):
    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None) -> None:
        super().__init__("AUTHENTICATION_FAILED", message, status_code=HTTPStatus.UNAUTHORIZED, details=details)


class AuthorizationException(AppException):
    def __init__(self, message: str = "Permission denied", details: dict[str, Any] | None = None) -> None:
        super().__init__("PERMISSION_DENIED", message, status_code=HTTPStatus.FORBIDDEN, details=details)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None) -> None:
        super().__init__("NOT_FOUND", message, status_code=HTTPStatus.NOT_FOUND, details=details)


class ConfigurationException(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__("MISCONFIGURATION", message, status_code=HTTPStatus.INTERNAL_SERVER_ERROR, details=details)


class ExternalServiceException(AppException):
    def __init__(self, message: str = "Upstream service unavailable", details: dict[str, Any] | None = None) -> None:
        super().__init__("UPSTREAM_ERROR", message, status_code=HTTPStatus.BAD_GATEWAY, details=details)


class RateLimitException(AppException):
    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None) -> None:
        super().__init__("RATE_LIMITED", message, status_code=HTTPStatus.TOO_MANY_REQUESTS, details=details)


def _error_payload(
    code: str,
    message: str,
    *,
    request_id: str | None,
    details: dict[str, Any] | list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for all API responses."""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message, request_id=request_id, details=exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content=_error_payload(
                "VALIDATION_ERROR",
                "Request validation failed",
                request_id=request_id,
                details=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        settings = get_settings()
        distinct_id = getattr(request.state, "posthog_distinct_id", None) or request_id or "anonymous_backend"

        capture_posthog_event(
            "backend_exception",
            distinct_id=distinct_id,
            properties={
                "path": request.url.path,
                "method": request.method,
                "request_id": request_id,
                "environment": settings.environment,
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
            },
        )

        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=_error_payload(
                "INTERNAL_ERROR",
                "An unexpected error occurred",
                request_id=request_id,
                details={"exception": str(exc)},
            ),
        )
