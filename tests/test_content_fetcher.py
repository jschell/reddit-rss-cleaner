from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from reddit_rss_cleaner.content_fetcher import (
    _fetch_headless,  # pyright: ignore[reportPrivateUsage]
    fetch_article_content,
)

FETCH_URL = "reddit_rss_cleaner.content_fetcher.trafilatura.fetch_url"
EXTRACT = "reddit_rss_cleaner.content_fetcher.trafilatura.extract"


def _make_mock_browser() -> MagicMock:
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.content = AsyncMock(return_value="<html/>")
    mock_page.close = AsyncMock()

    mock_browser = MagicMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    return mock_browser


class TestFetchArticleContentStatic:
    async def test_returns_content_when_trafilatura_succeeds(self) -> None:
        long_content = "A" * 300
        with (
            patch(FETCH_URL, return_value="<html>...</html>"),
            patch(EXTRACT, return_value=long_content),
        ):
            result = await fetch_article_content("https://example.com/article")
        assert result == long_content

    async def test_returns_empty_when_fetch_url_returns_none(self) -> None:
        with patch(FETCH_URL, return_value=None):
            result = await fetch_article_content("https://example.com/article")
        assert result == ""

    async def test_returns_empty_when_extract_returns_none(self) -> None:
        with (
            patch(FETCH_URL, return_value="<html/>"),
            patch(EXTRACT, return_value=None),
        ):
            result = await fetch_article_content("https://example.com/article")
        assert result == ""

    async def test_falls_back_to_playwright_when_content_too_short(self) -> None:
        short_content = "A" * 50
        long_content = "B" * 300

        with (
            patch(FETCH_URL, return_value="<html/>"),
            patch(EXTRACT, return_value=short_content),
            patch(
                "reddit_rss_cleaner.content_fetcher._fetch_headless",
                new_callable=AsyncMock,
                return_value=long_content,
            ),
            patch("reddit_rss_cleaner.content_fetcher._browser", _make_mock_browser()),
        ):
            result = await fetch_article_content("https://example.com/article")

        assert result == long_content

    async def test_no_playwright_fallback_when_browser_not_initialised(self) -> None:
        short_content = "A" * 50

        with (
            patch(FETCH_URL, return_value="<html/>"),
            patch(EXTRACT, return_value=short_content),
            patch("reddit_rss_cleaner.content_fetcher._browser", None),
            patch(
                "reddit_rss_cleaner.content_fetcher._fetch_headless",
                new_callable=AsyncMock,
            ) as mock_headless,
        ):
            result = await fetch_article_content("https://example.com/article")

        mock_headless.assert_not_called()
        assert result == short_content

    async def test_returns_empty_when_static_fetch_times_out(self) -> None:
        async def slow_fetch() -> str:
            await asyncio.sleep(10)
            return "A" * 300

        with (
            patch("reddit_rss_cleaner.content_fetcher._browser", None),
            patch(
                "reddit_rss_cleaner.content_fetcher.asyncio.get_running_loop",
            ) as mock_get_loop,
        ):
            mock_loop = MagicMock()
            mock_loop.run_in_executor = MagicMock(return_value=slow_fetch())
            mock_get_loop.return_value = mock_loop
            result = await fetch_article_content("https://example.com/slow", timeout=1)

        assert result == ""

    async def test_does_not_fall_back_when_static_content_long_enough(self) -> None:
        long_content = "A" * 300

        with (
            patch(FETCH_URL, return_value="<html/>"),
            patch(EXTRACT, return_value=long_content),
            patch("reddit_rss_cleaner.content_fetcher._browser", _make_mock_browser()),
            patch(
                "reddit_rss_cleaner.content_fetcher._fetch_headless",
                new_callable=AsyncMock,
            ) as mock_headless,
        ):
            result = await fetch_article_content("https://example.com/article")

        mock_headless.assert_not_called()
        assert result == long_content


class TestFetchHeadless:
    async def test_returns_extracted_content(self) -> None:
        body = "x" * 300
        rendered_html = f"<html><body><article>Full content here {body}</article></body></html>"
        long_content = "Full content here " + body

        mock_browser = _make_mock_browser()
        mock_browser.new_page.return_value.content = AsyncMock(return_value=rendered_html)

        with (
            patch("reddit_rss_cleaner.content_fetcher._browser", mock_browser),
            patch(
                "reddit_rss_cleaner.content_fetcher._semaphore",
                asyncio.Semaphore(4),
            ),
            patch(EXTRACT, return_value=long_content),
        ):
            result = await _fetch_headless("https://example.com/article", timeout=10)

        assert result == long_content

    async def test_returns_empty_on_playwright_exception(self) -> None:
        mock_browser = MagicMock()
        mock_browser.new_page = AsyncMock(side_effect=Exception("browser crashed"))

        with (
            patch("reddit_rss_cleaner.content_fetcher._browser", mock_browser),
            patch(
                "reddit_rss_cleaner.content_fetcher._semaphore",
                asyncio.Semaphore(4),
            ),
        ):
            result = await _fetch_headless("https://example.com/article", timeout=10)

        assert result == ""

    async def test_goto_uses_domcontentloaded(self) -> None:
        """Regression: wait_until must be domcontentloaded, not networkidle."""
        mock_browser = _make_mock_browser()

        with (
            patch("reddit_rss_cleaner.content_fetcher._browser", mock_browser),
            patch("reddit_rss_cleaner.content_fetcher._semaphore", asyncio.Semaphore(4)),
            patch(EXTRACT, return_value="content"),
        ):
            await _fetch_headless("https://example.com/article", timeout=10)

        mock_page = mock_browser.new_page.return_value
        _, kwargs = mock_page.goto.call_args
        assert kwargs.get("wait_until") == "domcontentloaded"
