from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from reddit_rss_cleaner.content_fetcher import (
    _fetch_headless,  # pyright: ignore[reportPrivateUsage]
    fetch_article_content,
)

FETCH_URL = "reddit_rss_cleaner.content_fetcher.trafilatura.fetch_url"
EXTRACT = "reddit_rss_cleaner.content_fetcher.trafilatura.extract"


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

    async def test_falls_back_to_playwright_when_content_too_short(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PLAYWRIGHT_ENABLED", "true")
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
        ):
            result = await fetch_article_content("https://example.com/article")

        assert result == long_content

    async def test_no_playwright_fallback_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PLAYWRIGHT_ENABLED", raising=False)
        short_content = "A" * 50

        with (
            patch(FETCH_URL, return_value="<html/>"),
            patch(EXTRACT, return_value=short_content),
            patch(
                "reddit_rss_cleaner.content_fetcher._fetch_headless",
                new_callable=AsyncMock,
            ) as mock_headless,
        ):
            result = await fetch_article_content("https://example.com/article")

        mock_headless.assert_not_called()
        assert result == short_content

    async def test_does_not_fall_back_when_static_content_long_enough(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PLAYWRIGHT_ENABLED", "true")
        long_content = "A" * 300

        with (
            patch(FETCH_URL, return_value="<html/>"),
            patch(EXTRACT, return_value=long_content),
            patch(
                "reddit_rss_cleaner.content_fetcher._fetch_headless",
                new_callable=AsyncMock,
            ) as mock_headless,
        ):
            result = await fetch_article_content("https://example.com/article")

        mock_headless.assert_not_called()
        assert result == long_content


class TestFetchHeadless:
    async def test_returns_extracted_content(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PLAYWRIGHT_ENABLED", "true")
        body = "x" * 300
        rendered_html = f"<html><body><article>Full content here {body}</article></body></html>"
        long_content = "Full content here " + body

        mock_page = MagicMock()
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value=rendered_html)

        mock_browser = MagicMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()

        mock_chromium = MagicMock()
        mock_chromium.launch = AsyncMock(return_value=mock_browser)

        mock_playwright = MagicMock()
        mock_playwright.chromium = mock_chromium
        mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
        mock_playwright.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "reddit_rss_cleaner.content_fetcher.async_playwright",
                return_value=mock_playwright,
            ),
            patch(EXTRACT, return_value=long_content),
        ):
            result = await _fetch_headless("https://example.com/article", timeout=10)

        assert result == long_content

    async def test_returns_empty_on_playwright_exception(self) -> None:
        with patch(
            "reddit_rss_cleaner.content_fetcher.async_playwright",
            side_effect=Exception("browser crashed"),
        ):
            result = await _fetch_headless("https://example.com/article", timeout=10)

        assert result == ""
