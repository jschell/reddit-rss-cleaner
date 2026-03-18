from __future__ import annotations

import asyncio
import logging
import os

import trafilatura
from playwright.async_api import Browser, async_playwright

logger = logging.getLogger(__name__)

MIN_CONTENT_LENGTH = 200

# Shared browser instance and semaphore — initialised by init_playwright() at startup.
_browser: Browser | None = None
_semaphore: asyncio.Semaphore | None = None


async def init_playwright() -> None:
    """Launch a shared Chromium browser. Call once at application startup."""
    global _browser, _semaphore
    if os.environ.get("PLAYWRIGHT_ENABLED") != "true":
        return
    max_pages = int(os.environ.get("PLAYWRIGHT_CONCURRENCY", "4"))
    pw = await async_playwright().start()
    _browser = await pw.chromium.launch()
    _semaphore = asyncio.Semaphore(max_pages)
    logger.info("Playwright browser ready (max %d concurrent pages)", max_pages)


async def close_playwright() -> None:
    """Close the shared browser. Call once at application shutdown."""
    global _browser
    if _browser is not None:
        await _browser.close()
        _browser = None
        logger.info("Playwright browser closed")


async def fetch_article_content(url: str, timeout: int = 10) -> str:
    """
    Fetch and extract article content from a URL.

    1. Try trafilatura (plain HTTP) — fast, no overhead.
    2. If content is below MIN_CONTENT_LENGTH and PLAYWRIGHT_ENABLED=true,
       fall back to headless Chromium rendering using the shared browser.

    Returns extracted HTML string, or empty string on failure.
    """
    content = _fetch_static(url)
    if content and len(content) >= MIN_CONTENT_LENGTH:
        return content
    if _browser is not None:
        return await _fetch_headless(url, timeout)
    return content or ""


def _fetch_static(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return ""
    result: str | None = trafilatura.extract(
        downloaded, output_format="html", include_comments=False
    )
    return result or ""


async def _fetch_headless(url: str, timeout: int) -> str:
    assert _browser is not None
    assert _semaphore is not None
    try:
        async with _semaphore:
            page = await _browser.new_page()
            try:
                await page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
                html = await page.content()
            finally:
                await page.close()
        result: str | None = trafilatura.extract(html, output_format="html", include_comments=False)
        return result or ""
    except Exception:
        logger.exception("Playwright fetch failed for %s", url)
        return ""
