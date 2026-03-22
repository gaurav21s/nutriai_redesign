"""FastAPI application entrypoint."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.utils.posthog_client import capture_posthog_event, resolve_posthog_distinct_id, shutdown_posthog_client


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    logger = get_logger("app.main")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            shutdown_posthog_client()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
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
        request.state.posthog_distinct_id = await resolve_posthog_distinct_id(request, settings)

        started = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)

        response.headers["x-request-id"] = request_id

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            },
        )

        if request.method != "GET" or response.status_code >= 400:
            capture_posthog_event(
                "backend_api_request",
                distinct_id=request.state.posthog_distinct_id or request_id,
                properties={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "request_id": request_id,
                    "environment": settings.environment,
                },
            )

        return response

    app.include_router(v1_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"message": "NutriAI API is running", "docs": "/docs"}

    return app


app = create_app()
