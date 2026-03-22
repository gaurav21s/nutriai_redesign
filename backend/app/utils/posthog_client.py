"""Central PostHog helpers for backend analytics and monitoring."""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import Any

from fastapi import Request
from posthog import Posthog

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("app.utils.posthog")


def _posthog_disabled(settings: Settings) -> bool:
    return not settings.posthog_project_api_key or "pytest" in sys.modules


@lru_cache(maxsize=1)
def get_posthog_client() -> Posthog:
    settings = get_settings()
    return Posthog(
        settings.posthog_project_api_key or "disabled",
        host=settings.posthog_host,
        disabled=_posthog_disabled(settings),
    )


async def resolve_posthog_distinct_id(request: Request, settings: Settings) -> str | None:
    from app.core.security import bearer_scheme, get_optional_auth_context

    credentials = await bearer_scheme(request)
    auth = await get_optional_auth_context(request=request, credentials=credentials, settings=settings)
    return auth.clerk_user_id if auth else None


def capture_posthog_event(
    event: str,
    *,
    distinct_id: str,
    properties: dict[str, Any] | None = None,
) -> None:
    client = get_posthog_client()

    try:
        client.capture(
            event,
            distinct_id=distinct_id,
            properties=properties or {},
        )
    except Exception:
        logger.exception("posthog_capture_failed", extra={"event": event, "distinct_id": distinct_id})


def shutdown_posthog_client() -> None:
    client = get_posthog_client()
    try:
        client.shutdown()
    except Exception:
        logger.exception("posthog_shutdown_failed")
