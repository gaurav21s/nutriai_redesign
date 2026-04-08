"""Structured logging and per-request context helpers."""

from __future__ import annotations

import json
import logging
import random
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

_REQUEST_CONTEXT: ContextVar[RequestLogContext | None] = ContextVar("request_log_context", default=None)
_DEFAULT_LOG_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__.keys())


@dataclass
class RequestLogContext:
    """Mutable request-scoped logging context."""

    request_id: str
    environment: str
    service_name: str = "nutriai-backend"
    service_version: str = "1.0.0"
    service_namespace: str | None = None
    path: str = ""
    route: str = ""
    method: str = ""
    feature: str = "general"
    user_agent: str = ""
    request_size_bytes: int | None = None
    response_size_bytes: int | None = None
    query_param_count: int = 0
    status_code: int | None = None
    latency_ms: float | None = None
    outcome: str = "success"
    error_code: str | None = None
    error_message: str | None = None
    clerk_user_id: str | None = None
    user_email: str | None = None
    client_session_id: str | None = None
    client_event_id: str | None = None
    client_route: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    sampled: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


class RequestContextFilter(logging.Filter):
    """Attach request-scoped correlation data to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = get_request_context()
        if context is None:
            return True

        refresh_trace_context()

        for field_name in (
            "request_id",
            "path",
            "route",
            "method",
            "feature",
            "status_code",
            "latency_ms",
            "clerk_user_id",
            "user_email",
            "client_session_id",
            "client_event_id",
            "client_route",
            "trace_id",
            "span_id",
            "outcome",
            "error_code",
            "service_name",
            "service_namespace",
            "environment",
        ):
            value = getattr(context, field_name)
            if value is not None and not hasattr(record, field_name):
                setattr(record, field_name, value)

        return True


class JsonFormatter(logging.Formatter):
    """Formatter that emits stable JSON payloads."""

    def format(self, record: logging.LogRecord) -> str:
        if hasattr(record, "wide_event"):
            return json.dumps(getattr(record, "wide_event"), ensure_ascii=True, default=str)

        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "event_type": "log",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field_name in (
            "request_id",
            "trace_id",
            "span_id",
            "path",
            "route",
            "method",
            "feature",
            "status_code",
            "latency_ms",
            "clerk_user_id",
            "user_email",
            "client_session_id",
            "client_event_id",
            "client_route",
            "outcome",
            "error_code",
            "service_name",
            "service_namespace",
            "environment",
        ):
            if hasattr(record, field_name):
                payload[field_name] = getattr(record, field_name)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _DEFAULT_LOG_RECORD_FIELDS
            and key
            not in {
                "wide_event",
                "message",
                "asctime",
            }
        }
        if extra_fields:
            payload["context"] = extra_fields

        return json.dumps(payload, ensure_ascii=True, default=str)


def _mark_managed(handler: logging.Handler) -> logging.Handler:
    setattr(handler, "_nutriai_managed_handler", True)
    handler.addFilter(RequestContextFilter())
    return handler


def configure_logging(level: str = "INFO") -> None:
    """Configure process-wide JSON logging while preserving test capture handlers."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    preserved_handlers: list[logging.Handler] = []
    for handler in root.handlers:
        if getattr(handler, "_nutriai_managed_handler", False):
            handler.close()
            continue
        preserved_handlers.append(handler)

    stream_handler = _mark_managed(logging.StreamHandler())
    stream_handler.setFormatter(JsonFormatter())

    root.handlers = [*preserved_handlers, stream_handler]

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True


def set_request_context(context: RequestLogContext | None) -> None:
    """Bind request context to the current execution context."""
    _REQUEST_CONTEXT.set(context)


def begin_request_context(**kwargs: Any) -> RequestLogContext:
    """Create and bind a new request context."""
    context = RequestLogContext(**kwargs)
    set_request_context(context)
    return context


def get_request_context() -> RequestLogContext | None:
    """Return the active request context, if any."""
    return _REQUEST_CONTEXT.get()


def update_request_context(**kwargs: Any) -> RequestLogContext | None:
    """Mutate the active request context with new values."""
    context = get_request_context()
    if context is None:
        return None

    for key, value in kwargs.items():
        if value is None:
            continue
        if key == "extra" and isinstance(value, dict):
            context.extra.update(value)
            continue
        if hasattr(context, key):
            setattr(context, key, value)
    return context


def clear_request_context() -> None:
    """Clear the active request context."""
    set_request_context(None)


def refresh_trace_context() -> RequestLogContext | None:
    """Copy current OpenTelemetry span identifiers into the request context."""
    context = get_request_context()
    if context is None:
        return None

    try:
        from opentelemetry import trace
    except ModuleNotFoundError:
        return context

    span = trace.get_current_span()
    span_context = span.get_span_context() if span is not None else None
    if span_context and span_context.is_valid:
        context.trace_id = f"{span_context.trace_id:032x}"
        context.span_id = f"{span_context.span_id:016x}"

    return context


def classify_feature(path: str) -> str:
    """Map request paths to product features."""
    lowered = path.lower()

    if "/food-insights/" in lowered:
        return "food_insight"
    if "/ingredient-checks/" in lowered:
        return "ingredient_checker"
    if "/meal-plans/" in lowered:
        return "meal_planner"
    if "/recipes/" in lowered:
        return "recipe_finder"
    if "/quizzes/" in lowered:
        return "nutri_quiz"
    if "/nutri-chat/" in lowered:
        return "nutri_chat"
    if "/recommendations/" in lowered:
        return "recommendations"
    if "/calculators/" in lowered:
        return "nutri_calc"
    if "/subscriptions/" in lowered:
        return "subscription"
    if "/articles" in lowered:
        return "articles"
    if "/health" in lowered:
        return "health"
    return "general"


def classify_outcome(status_code: int | None, error_code: str | None) -> str:
    """Return a stable request outcome label."""
    if error_code:
        return "error"
    if status_code is None:
        return "unknown"
    if status_code >= 500:
        return "server_error"
    if status_code >= 400:
        return "client_error"
    return "success"


def should_sample_request(context: RequestLogContext, settings: Any) -> bool:
    """Outcome-based sampling for request summary events."""
    if context.clerk_user_id and context.clerk_user_id in settings.get_log_vip_user_ids():
        return True

    if settings.environment in {"local", "development"}:
        return True

    if context.error_code or (context.status_code is not None and context.status_code >= 400):
        return True

    if context.latency_ms is not None and context.latency_ms >= settings.log_slow_request_ms:
        return True

    sample_rate = min(max(float(settings.log_success_sample_rate), 0.0), 1.0)
    if sample_rate >= 1:
        return True
    if sample_rate <= 0:
        return False
    return random.random() <= sample_rate


def build_request_summary_event(context: RequestLogContext) -> dict[str, Any]:
    """Build the canonical wide-event payload for a request."""
    payload = asdict(context)
    payload.update(
        {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "event_type": "request_summary",
        }
    )
    return payload


def emit_request_summary(logger: logging.Logger, settings: Any) -> dict[str, Any] | None:
    """Emit the single canonical request event if sampling keeps it."""
    context = refresh_trace_context()
    if context is None:
        return None

    context.sampled = should_sample_request(context, settings)
    if not context.sampled:
        return None

    event = build_request_summary_event(context)
    logger.info(
        "request_summary",
        extra={
            "wide_event": event,
            "event_name": "request_summary",
            "request_id": context.request_id,
        },
    )
    return event


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
