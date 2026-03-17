from __future__ import annotations

import logging
import os

import httpx
from fastapi import FastAPI, HTTPException, Response

from reddit_rss_cleaner.builder import build_rss_feed
from reddit_rss_cleaner.cache import TTLCache
from reddit_rss_cleaner.fetcher import fetch_reddit_rss
from reddit_rss_cleaner.parser import parse_feed

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Reddit RSS Cleaner",
    description="Rewrites Reddit RSS feeds to use external article URLs.",
    version="0.1.0",
)

VALID_SORTS = frozenset({"new", "hot", "top", "rising"})

_cache: TTLCache = TTLCache(ttl_seconds=int(os.environ.get("CACHE_TTL", "300")))


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
        timeout = int(os.environ.get("REQUEST_TIMEOUT", "15"))
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
            logger.error("Reddit rate limit hit for r/%s/%s: 429 Too Many Requests", subreddit, sort)
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

    port = int(os.environ.get("PORT", "5000"))
    log_level = os.environ.get("LOG_LEVEL", "info")
    uvicorn.run("reddit_rss_cleaner.main:app", host="0.0.0.0", port=port, log_level=log_level)
