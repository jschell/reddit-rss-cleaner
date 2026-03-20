from __future__ import annotations

import threading
import time


class TTLCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> str | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + self._ttl)

    def prune(self) -> int:
        """Remove all expired entries. Returns the number of entries removed."""
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
        return len(expired)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
