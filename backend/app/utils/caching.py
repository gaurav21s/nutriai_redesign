"""Simple TTL cache utility for expensive repeat operations."""

from __future__ import annotations

import time
from collections.abc import Hashable
from threading import Lock
from typing import Any


class TTLCache:
    """Thread-safe in-memory TTL cache."""

    def __init__(self, ttl_seconds: int = 600) -> None:
        self.ttl_seconds = ttl_seconds
        self._values: dict[Hashable, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: Hashable) -> Any | None:
        now = time.monotonic()
        with self._lock:
            item = self._values.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at < now:
                self._values.pop(key, None)
                return None
            return value

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._values[key] = (time.monotonic() + self.ttl_seconds, value)

    def clear(self) -> None:
        with self._lock:
            self._values.clear()
