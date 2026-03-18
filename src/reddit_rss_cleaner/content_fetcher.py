from __future__ import annotations

import logging
import os

import trafilatura
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

MIN_CONTENT_LENGTH = 200


async def fetch_article_content(url: str, timeout: int = 10) -> str:
    """
    Fetch and extract article content from a URL.

    1. Try trafilatura (plain HTTP) — fast, no overhead.
    2. If content is below MIN_CONTENT_LENGTH and PLAYWRIGHT_ENABLED=true,
       fall back to headless Chromium rendering.

    Returns extracted HTML string, or empty string on failure.
    """
    content = _fetch_static(url)
    if content and len(content) >= MIN_CONTENT_LENGTH:
        return content
    if os.environ.get("PLAYWRIGHT_ENABLED") == "true":
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
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            html = await page.content()
            await browser.close()
        result: str | None = trafilatura.extract(html, output_format="html", include_comments=False)
        return result or ""
    except Exception:
        logger.exception("Playwright fetch failed for %s", url)
        return ""
