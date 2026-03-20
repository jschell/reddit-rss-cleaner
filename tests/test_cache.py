from __future__ import annotations

import time

from reddit_rss_cleaner.cache import TTLCache


class TestTTLCacheGet:
    def test_returns_none_for_missing_key(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        assert cache.get("missing") is None

    def test_returns_value_before_expiry(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        cache.set("k", "v")
        assert cache.get("k") == "v"

    def test_returns_none_after_expiry(self) -> None:
        cache = TTLCache(ttl_seconds=1)
        cache.set("k", "v")
        # Directly backdate the expiry to simulate passage of time without sleeping
        with cache._lock:  # pyright: ignore[reportPrivateUsage]
            value, _ = cache._store["k"]  # pyright: ignore[reportPrivateUsage]
            cache._store["k"] = (value, time.monotonic() - 1)  # pyright: ignore[reportPrivateUsage]
        assert cache.get("k") is None

    def test_expired_entry_is_removed_from_store(self) -> None:
        cache = TTLCache(ttl_seconds=1)
        cache.set("k", "v")
        with cache._lock:  # pyright: ignore[reportPrivateUsage]
            value, _ = cache._store["k"]  # pyright: ignore[reportPrivateUsage]
            cache._store["k"] = (value, time.monotonic() - 1)  # pyright: ignore[reportPrivateUsage]
        cache.get("k")
        with cache._lock:  # pyright: ignore[reportPrivateUsage]
            assert "k" not in cache._store  # pyright: ignore[reportPrivateUsage]


class TestTTLCacheSet:
    def test_overwrites_existing_key(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        cache.set("k", "first")
        cache.set("k", "second")
        assert cache.get("k") == "second"

    def test_multiple_keys_independent(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", "1")
        cache.set("b", "2")
        assert cache.get("a") == "1"
        assert cache.get("b") == "2"


class TestTTLCacheClear:
    def test_clear_removes_all_entries(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_clear_on_empty_cache_is_noop(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        cache.clear()  # should not raise


class TestTTLCachePrune:
    def test_prune_removes_expired_entries(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", "1")
        cache.set("b", "2")
        # Backdate both entries so they are expired
        with cache._lock:  # pyright: ignore[reportPrivateUsage]
            for k in list(cache._store):  # pyright: ignore[reportPrivateUsage]
                v, _ = cache._store[k]  # pyright: ignore[reportPrivateUsage]
                cache._store[k] = (v, time.monotonic() - 1)  # pyright: ignore[reportPrivateUsage]
        removed = cache.prune()
        assert removed == 2
        with cache._lock:  # pyright: ignore[reportPrivateUsage]
            assert len(cache._store) == 0  # pyright: ignore[reportPrivateUsage]

    def test_prune_leaves_live_entries(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        cache.set("live", "v")
        removed = cache.prune()
        assert removed == 0
        assert cache.get("live") == "v"

    def test_prune_returns_zero_on_empty_cache(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        assert cache.prune() == 0
