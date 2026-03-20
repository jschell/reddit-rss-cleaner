from __future__ import annotations

import asyncio
import dataclasses
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version as _pkg_version

import httpx
from fastapi import FastAPI, HTTPException, Response

from reddit_rss_cleaner.builder import build_rss_feed
from reddit_rss_cleaner.cache import TTLCache
from reddit_rss_cleaner.content_fetcher import (
    close_playwright,
    fetch_article_content,
    init_playwright,
)
from reddit_rss_cleaner.fetcher import fetch_reddit_rss
from reddit_rss_cleaner.parser import parse_feed

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_playwright()
    yield
    await close_playwright()


app = FastAPI(
    title="Reddit RSS Cleaner",
    description="Rewrites Reddit RSS feeds to use external article URLs.",
    version=_pkg_version("reddit-rss-cleaner"),
    lifespan=lifespan,
)

VALID_SORTS = frozenset({"new", "hot", "top", "rising"})


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        logger.warning("Invalid %s value; defaulting to %d", name, default)
        return default


_cache: TTLCache = TTLCache(ttl_seconds=_env_int("CACHE_TTL", 300))


def clear_cache() -> None:
    """Clear the feed cache. Exposed for use in tests."""
    _cache.clear()


@app.get("/r/{subreddit}/{sort}", response_class=Response)
async def subreddit_feed(subreddit: str, sort: str) -> Response:
    """Return cleaned RSS for a subreddit."""
    if sort not in VALID_SORTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort '{sort}'. Valid sorts: {sorted(VALID_SORTS)}",
        )

    cache_key = f"{subreddit}:{sort}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="application/rss+xml")

    try:
        timeout = _env_int("REQUEST_TIMEOUT", 15)
        raw_rss = await fetch_reddit_rss(subreddit, sort, timeout=timeout)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 404:
            logger.warning("r/%s not found (404)", subreddit)
            raise HTTPException(
                status_code=404, detail=f"Subreddit r/{subreddit} not found"
            ) from exc
        if status == 403:
            logger.error("Reddit blocked request for r/%s/%s: 403 Forbidden", subreddit, sort)
            raise HTTPException(status_code=502, detail="Reddit returned 403 Forbidden") from exc
        if status == 429:
            logger.error("Reddit rate limit hit for r/%s/%s: 429", subreddit, sort)
            raise HTTPException(status_code=502, detail="Reddit rate limit exceeded (429)") from exc
        logger.error("Reddit returned HTTP %s for r/%s/%s", status, subreddit, sort)
        raise HTTPException(status_code=502, detail=f"Reddit returned HTTP {status}") from exc
    except httpx.TimeoutException as exc:
        logger.error("Request to Reddit timed out for r/%s/%s: %s", subreddit, sort, exc)
        raise HTTPException(status_code=502, detail="Request to Reddit timed out") from exc
    except httpx.RequestError as exc:
        logger.error("Network error fetching r/%s/%s: %s", subreddit, sort, exc)
        raise HTTPException(status_code=502, detail=f"Network error: {exc}") from exc

    entries = parse_feed(raw_rss)
    if not entries:
        raise HTTPException(status_code=404, detail=f"No entries found in r/{subreddit}/{sort}")

    if os.environ.get("CONTENT_FETCH_ENABLED") == "true":
        content_timeout = _env_int("CONTENT_TIMEOUT", 10)
        content_budget = _env_int("CONTENT_FETCH_BUDGET", 20)

        loop_tasks: list[asyncio.Task[str]] = [
            asyncio.create_task(
                fetch_article_content(e.entry_url, content_timeout)
                if not e.is_self_post
                else asyncio.sleep(0, result="")
            )
            for e in entries
        ]
        done, pending = await asyncio.wait(loop_tasks, timeout=content_budget)
        if pending:
            logger.warning(
                "Content fetching exceeded %ds budget for r/%s/%s; %d/%d article(s) timed out",
                content_budget,
                subreddit,
                sort,
                len(pending),
                len(loop_tasks),
            )
            for t in pending:
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        fetched: list[str] = []
        for t in loop_tasks:
            try:
                fetched.append(t.result() if t in done else "")
            except Exception:
                fetched.append("")
        entries = [
            dataclasses.replace(e, fetched_content=c) for e, c in zip(entries, fetched, strict=True)
        ]

    feed_xml = build_rss_feed(subreddit, sort, entries)
    _cache.set(cache_key, feed_xml)
    return Response(content=feed_xml, media_type="application/rss+xml")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe for Docker/Portainer."""
    return {"status": "ok"}


@app.get("/")
async def index() -> dict[str, str]:
    """Usage info."""
    return {
        "service": "reddit-rss-cleaner",
        "usage": "GET /r/{subreddit}/{sort}",
        "valid_sorts": "new, hot, top, rising",
        "health": "/health",
    }


def run() -> None:
    """Entry point for `reddit-rss-cleaner` CLI script."""
    import uvicorn

    port = _env_int("PORT", 5000)
    log_level = os.environ.get("LOG_LEVEL", "info")
    uvicorn.run("reddit_rss_cleaner.main:app", host="0.0.0.0", port=port, log_level=log_level)
