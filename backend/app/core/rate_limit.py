"""In-memory rate limiting helpers."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    """Token-bucket-like limiter implemented with rolling windows."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        threshold = now - window_seconds

        async with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= threshold:
                bucket.popleft()

            if len(bucket) >= limit:
                return False

            bucket.append(now)
            return True
