from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import trafilatura

if TYPE_CHECKING:
    from playwright.async_api import Browser

logger = logging.getLogger(__name__)

MIN_CONTENT_LENGTH = 200

# File extensions that trigger browser downloads rather than page renders.
_BINARY_EXTENSIONS = frozenset(
    {".pdf", ".zip", ".gz", ".tar", ".exe", ".dmg", ".docx", ".xlsx", ".pptx"}
)


def _is_binary_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in _BINARY_EXTENSIONS)


# Shared browser instance and semaphore — initialised by init_playwright() at startup.
_browser: Browser | None = None
_semaphore: asyncio.Semaphore | None = None


async def init_playwright() -> None:
    """Launch a shared Chromium browser. Call once at application startup."""
    global _browser, _semaphore
    if os.environ.get("PLAYWRIGHT_ENABLED") != "true":
        return
    from playwright.async_api import async_playwright  # lazy import

    try:
        max_pages = int(os.environ.get("PLAYWRIGHT_CONCURRENCY", "4"))
    except ValueError:
        logger.warning("Invalid PLAYWRIGHT_CONCURRENCY value; defaulting to 4")
        max_pages = 4
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

    1. Try trafilatura (plain HTTP, run in thread pool) — fast, no overhead.
       Bounded by `timeout` seconds so a slow site can't eat the global budget.
    2. If content is below MIN_CONTENT_LENGTH and a shared Playwright browser
       is available, fall back to headless Chromium rendering.

    Returns extracted HTML string, or empty string on failure.
    """
    loop = asyncio.get_running_loop()
    try:
        content = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch_static, url),
            timeout=timeout,
        )
    except TimeoutError:
        logger.debug("Static fetch timed out for %s", url)
        content = ""
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
    if _browser is None or _semaphore is None:
        raise RuntimeError("_fetch_headless called before init_playwright()")
    if _is_binary_url(url):
        return ""
    try:
        async with _semaphore:
            page = await _browser.new_page()
            try:
                await page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
                try:
                    html = await page.content()
                except Exception:
                    # page.content() can fail if a redirect fires after domcontentloaded.
                    # Wait for the load event and retry once.
                    await page.wait_for_load_state("load", timeout=timeout * 1000)
                    html = await page.content()
            finally:
                await page.close()
        result: str | None = trafilatura.extract(html, output_format="html", include_comments=False)
        return result or ""
    except Exception:
        logger.exception("Playwright fetch failed for %s", url)
        return ""
