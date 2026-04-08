"""FastAPI application entrypoint."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.coordination import validate_shared_coordination
from app.core.exceptions import AppException, register_exception_handlers
from app.core.logging import (
    begin_request_context,
    classify_feature,
    classify_outcome,
    clear_request_context,
    configure_logging,
    emit_request_summary,
    get_logger,
    update_request_context,
)
from app.core.security import bearer_scheme, get_optional_auth_context
from app.core.telemetry import flush_telemetry, initialize_telemetry
from app.dependencies import get_shared_coordinator
from app.utils.posthog_client import capture_posthog_event, shutdown_posthog_client


def _parse_content_length(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    validate_shared_coordination(settings)

    logger = get_logger("app.main")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            flush_telemetry()
            await get_shared_coordinator().close()
            shutdown_posthog_client()

    _expose_docs = settings.environment != "production"
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
        docs_url="/docs" if _expose_docs else None,
        redoc_url="/redoc" if _expose_docs else None,
        openapi_url="/openapi.json" if _expose_docs else None,
        description="NutriAI backend API with modular feature routers and typed contracts.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))
        request.state.request_id = request_id
        request.state.response_status_code = None
        request.state.error_code = None
        request.state.error_message = None

        auth_context = await get_optional_auth_context(
            request=request,
            credentials=await bearer_scheme(request),
            settings=settings,
        )
        request.state.auth_context = auth_context
        request.state.posthog_distinct_id = auth_context.clerk_user_id if auth_context else None

        begin_request_context(
            request_id=request_id,
            environment=settings.environment,
            service_namespace=settings.otel_service_namespace,
            path=request.url.path,
            method=request.method,
            feature=classify_feature(request.url.path),
            user_agent=request.headers.get("user-agent", ""),
            request_size_bytes=_parse_content_length(request.headers.get("content-length")),
            query_param_count=len(request.query_params),
            clerk_user_id=auth_context.clerk_user_id if auth_context else None,
            user_email=auth_context.email if auth_context else (request.headers.get("x-user-email") or None),
            client_session_id=request.headers.get("x-client-session-id"),
            client_event_id=request.headers.get("x-client-event-id"),
            client_route=request.headers.get("x-client-route"),
        )

        started = time.perf_counter()
        response = None

        try:
            response = await call_next(request)
            request.state.response_status_code = response.status_code
            response.headers["x-request-id"] = request_id
            return response
        except Exception as exc:
            request.state.response_status_code = getattr(exc, "status_code", 500)
            request.state.error_code = getattr(exc, "code", "INTERNAL_ERROR")
            request.state.error_message = str(exc)
            if isinstance(exc, AppException):
                update_request_context(
                    status_code=exc.status_code,
                    error_code=exc.code,
                    error_message=exc.message,
                    outcome="error",
                )
            else:
                update_request_context(
                    status_code=500,
                    error_code="INTERNAL_ERROR",
                    error_message=str(exc),
                    outcome="error",
                )
            raise
        finally:
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            route = request.scope.get("route")
            status_code = getattr(request.state, "response_status_code", None)
            error_code = getattr(request.state, "error_code", None)
            error_message = getattr(request.state, "error_message", None)

            if response is not None:
                status_code = response.status_code

            update_request_context(
                route=getattr(route, "path", request.url.path),
                status_code=status_code or 500,
                response_size_bytes=_parse_content_length(response.headers.get("content-length")) if response else None,
                latency_ms=latency_ms,
                outcome=classify_outcome(status_code or 500, error_code),
                error_code=error_code,
                error_message=error_message,
            )

            emit_request_summary(logger, settings)

            final_status = status_code or 500
            if request.method != "GET" or final_status >= 400:
                capture_posthog_event(
                    "backend_api_request",
                    distinct_id=request.state.posthog_distinct_id or request_id,
                    properties={
                        "path": request.url.path,
                        "method": request.method,
                        "status_code": final_status,
                        "latency_ms": latency_ms,
                        "request_id": request_id,
                        "environment": settings.environment,
                        "feature": classify_feature(request.url.path),
                        "error_code": error_code,
                    },
                )

            clear_request_context()

    app.include_router(v1_router, prefix=settings.api_v1_prefix)
    initialize_telemetry(app, settings)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"message": "NutriAI API is running", "docs": "/docs"}

    return app


app = create_app()
