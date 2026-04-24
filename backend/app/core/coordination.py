"""Shared coordination helpers for rate limiting, slots, and resource locks."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.core.config import Settings
from app.core.exceptions import ConfigurationException, RateLimitException

_ACTIVE_LIMITS = {"free": 1, "plus": 2, "pro": 3}
_QUEUE_LIMITS = {"free": 3, "plus": 10, "pro": 20}


def validate_shared_coordination(settings: Settings) -> None:
    if settings.environment != "production" or not settings.require_shared_coordination_in_production:
        return
    if not settings.enable_convex_persistence or not settings.convex_http_actions_url or not settings.convex_backend_secret:
        raise ConfigurationException("Production requires Convex persistence for durable operations")
    if not settings.redis_url:
        raise ConfigurationException("Production requires REDIS_URL for shared coordination")


class SharedCoordinator:
    """Best-effort coordination with optional Redis and in-memory dev fallback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._active_counts: dict[tuple[str, str], int] = defaultdict(int)
        self._queued_counts: dict[tuple[str, str], int] = defaultdict(int)
        self._rate_events: dict[str, deque[float]] = defaultdict(deque)
        self._state_lock = asyncio.Lock()
        self._redis: Any | None = None

        if settings.redis_url:
            try:
                from redis.asyncio import Redis  # type: ignore

                self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
            except Exception:
                self._redis = None

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()

    async def register_queue(self, clerk_user_id: str, queue_tier: str, workload_pool: str) -> None:
        key = (clerk_user_id, workload_pool)
        limit = _QUEUE_LIMITS.get(queue_tier, _QUEUE_LIMITS["free"])

        async with self._state_lock:
            queued = self._queued_counts[key]
            if queued >= limit:
                raise RateLimitException(
                    "Too many queued operations",
                    details={"queue_limit": limit, "queue_tier": queue_tier, "workload_pool": workload_pool},
                )
            self._queued_counts[key] = queued + 1

    async def hit_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        threshold = now - window_seconds
        async with self._state_lock:
            bucket = self._rate_events[key]
            while bucket and bucket[0] <= threshold:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    async def mark_dequeued(self, clerk_user_id: str, workload_pool: str) -> None:
        key = (clerk_user_id, workload_pool)
        async with self._state_lock:
            self._queued_counts[key] = max(self._queued_counts[key] - 1, 0)

    @asynccontextmanager
    async def execution_slot(
        self,
        clerk_user_id: str,
        queue_tier: str,
        workload_pool: str,
        *,
        resource_key: str | None = None,
        timeout_seconds: int = 90,
    ) -> AsyncIterator[None]:
        key = (clerk_user_id, workload_pool)
        resource_lock = self._locks[resource_key or f"{workload_pool}:{clerk_user_id}"]
        active_limit = _ACTIVE_LIMITS.get(queue_tier, _ACTIVE_LIMITS["free"])
        started = time.monotonic()

        while True:
            async with self._state_lock:
                if self._active_counts[key] < active_limit:
                    self._active_counts[key] += 1
                    break
            if time.monotonic() - started > timeout_seconds:
                raise RateLimitException(
                    "Operation execution slot timed out",
                    details={"queue_tier": queue_tier, "workload_pool": workload_pool},
                )
            await asyncio.sleep(0.05)

        await resource_lock.acquire()
        try:
            yield
        finally:
            resource_lock.release()
            async with self._state_lock:
                self._active_counts[key] = max(self._active_counts[key] - 1, 0)
