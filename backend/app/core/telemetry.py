"""OpenTelemetry bootstrap for Axiom export."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI

from app.core.config import Settings
from app.core.logging import RequestContextFilter, get_logger

logger = get_logger("app.core.telemetry")


@dataclass
class TelemetryRuntime:
    """Process-wide telemetry state."""

    initialized: bool = False
    log_handler: logging.Handler | None = None
    tracer_provider: Any | None = None
    logger_provider: Any | None = None
    config_signature: tuple[str, ...] | None = None


_RUNTIME = TelemetryRuntime()


def _build_axiom_headers(token: str, dataset: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Axiom-Dataset": dataset,
    }


def _mark_managed(handler: logging.Handler) -> logging.Handler:
    setattr(handler, "_nutriai_managed_handler", True)
    handler.addFilter(RequestContextFilter())
    return handler


def _config_signature(settings: Settings) -> tuple[str, ...]:
    return (
        settings.axiom_domain,
        settings.axiom_backend_logs_dataset,
        settings.axiom_traces_dataset,
        settings.otel_service_namespace,
        str(settings.otel_trace_sample_rate),
    )


def _attach_log_handler(handler: logging.Handler) -> None:
    root = logging.getLogger()
    if handler not in root.handlers:
        root.addHandler(handler)


def _should_export_traces(settings: Settings) -> bool:
    traces_dataset = settings.axiom_traces_dataset.strip()
    if not traces_dataset:
        return False
    if traces_dataset == settings.axiom_backend_logs_dataset:
        return False
    return True


def initialize_telemetry(app: FastAPI, settings: Settings) -> None:
    """Initialize trace and log export when Axiom and OTel are configured."""
    if not settings.axiom_api_token:
        logger.info("axiom_telemetry_disabled", extra={"reason": "missing_axiom_api_token"})
        return

    signature = _config_signature(settings)
    if _RUNTIME.initialized and _RUNTIME.config_signature == signature:
        if _RUNTIME.log_handler is not None:
            _attach_log_handler(_RUNTIME.log_handler)
        _instrument_app(app, _RUNTIME.tracer_provider)
        return
    if _RUNTIME.initialized and _RUNTIME.config_signature != signature:
        logger.warning("telemetry_reconfiguration_skipped", extra={"reason": "provider_already_initialized"})
        if _RUNTIME.log_handler is not None:
            _attach_log_handler(_RUNTIME.log_handler)
        _instrument_app(app, _RUNTIME.tracer_provider)
        return

    try:
        from opentelemetry import _logs, trace
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
    except ModuleNotFoundError as exc:
        logger.warning(
            "opentelemetry_packages_missing",
            extra={"missing_module": getattr(exc, "name", "opentelemetry")},
        )
        return

    resource = Resource.create(
        {
            "service.name": "nutriai-backend",
            "service.version": "1.0.0",
            "service.namespace": settings.otel_service_namespace,
            "deployment.environment": settings.environment,
        }
    )

    base_url = settings.get_axiom_base_url()
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(TraceIdRatioBased(settings.otel_trace_sample_rate)),
    )

    traces_export_enabled = _should_export_traces(settings)
    if traces_export_enabled:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=f"{base_url}/v1/traces",
                    headers=_build_axiom_headers(settings.axiom_api_token, settings.axiom_traces_dataset),
                )
            )
        )
    else:
        logger.info(
            "axiom_trace_export_disabled",
            extra={
                "reason": "missing_or_shared_dataset",
                "traces_dataset": settings.axiom_traces_dataset,
                "logs_dataset": settings.axiom_backend_logs_dataset,
            },
        )

    if not _RUNTIME.initialized:
        trace.set_tracer_provider(tracer_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=f"{base_url}/v1/logs",
                headers=_build_axiom_headers(settings.axiom_api_token, settings.axiom_backend_logs_dataset),
            )
        )
    )

    if not _RUNTIME.initialized:
        _logs.set_logger_provider(logger_provider)

    log_handler = _mark_managed(LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider))
    _attach_log_handler(log_handler)
    _instrument_app(app, tracer_provider if not _RUNTIME.initialized else trace.get_tracer_provider())

    _RUNTIME.initialized = True
    _RUNTIME.log_handler = log_handler
    _RUNTIME.tracer_provider = tracer_provider
    _RUNTIME.logger_provider = logger_provider
    _RUNTIME.config_signature = signature

    logger.info(
        "axiom_telemetry_initialized",
        extra={
            "axiom_domain": base_url,
            "logs_dataset": settings.axiom_backend_logs_dataset,
            "traces_dataset": settings.axiom_traces_dataset,
            "traces_export_enabled": traces_export_enabled,
        },
    )


def _instrument_app(app: FastAPI, tracer_provider: Any) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ModuleNotFoundError:
        return

    if getattr(app.state, "_nutriai_otel_instrumented", False):
        return

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
    app.state._nutriai_otel_instrumented = True


def flush_telemetry() -> None:
    """Best-effort flush for graceful shutdown."""
    try:
        if _RUNTIME.tracer_provider is not None:
            _RUNTIME.tracer_provider.force_flush()
    except Exception:
        logger.exception("trace_flush_failed")

    try:
        if _RUNTIME.logger_provider is not None:
            _RUNTIME.logger_provider.force_flush()
    except Exception:
        logger.exception("log_flush_failed")
