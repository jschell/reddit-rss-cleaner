from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from conftest import FIXTURE_RSS_XML
from httpx import ASGITransport, AsyncClient

from reddit_rss_cleaner.main import app


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_subreddit_feed_returns_200_rss(client: AsyncClient) -> None:
    with patch(
        "reddit_rss_cleaner.main.fetch_reddit_rss",
        new=AsyncMock(return_value=FIXTURE_RSS_XML),
    ):
        response = await client.get("/r/netsec/new")
    assert response.status_code == 200
    assert "application/rss+xml" in response.headers["content-type"]


async def test_invalid_sort_returns_400(client: AsyncClient) -> None:
    response = await client.get("/r/netsec/invalid")
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


async def test_reddit_403_returns_502(client: AsyncClient) -> None:
    mock_request = httpx.Request("GET", "https://www.reddit.com/r/netsec/new.rss")
    mock_response = httpx.Response(403, request=mock_request)
    with patch(
        "reddit_rss_cleaner.main.fetch_reddit_rss",
        new=AsyncMock(
            side_effect=httpx.HTTPStatusError("403", request=mock_request, response=mock_response)
        ),
    ):
        response = await client.get("/r/netsec/new")
    assert response.status_code == 502


async def test_cache_hit_calls_fetcher_once(client: AsyncClient) -> None:
    mock = AsyncMock(return_value=FIXTURE_RSS_XML)
    with patch("reddit_rss_cleaner.main.fetch_reddit_rss", new=mock):
        r1 = await client.get("/r/netsec/new")
        r2 = await client.get("/r/netsec/new")
    assert r1.status_code == 200
    assert r2.status_code == 200
    mock.assert_called_once()


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_content_fetch_enriches_external_entries(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTENT_FETCH_ENABLED", "true")
    fetched = "<p>full article body</p>"
    mock_rss = patch(
        "reddit_rss_cleaner.main.fetch_reddit_rss", new=AsyncMock(return_value=FIXTURE_RSS_XML)
    )
    mock_content = patch(
        "reddit_rss_cleaner.main.fetch_article_content", new=AsyncMock(return_value=fetched)
    )
    with mock_rss, mock_content:
        response = await client.get("/r/netsec/new")
    assert response.status_code == 200
    assert "full article body" in response.text


async def test_content_fetch_skipped_when_env_not_set(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CONTENT_FETCH_ENABLED", raising=False)
    mock_rss = patch(
        "reddit_rss_cleaner.main.fetch_reddit_rss", new=AsyncMock(return_value=FIXTURE_RSS_XML)
    )
    mock_content = patch(
        "reddit_rss_cleaner.main.fetch_article_content",
        new=AsyncMock(return_value="<p>fetched</p>"),
    )
    with mock_rss, mock_content as mock_fetch:
        response = await client.get("/r/netsec/new")
    assert response.status_code == 200
    mock_fetch.assert_not_called()


async def test_content_fetch_skips_self_posts(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTENT_FETCH_ENABLED", "true")
    fetch_calls: list[str] = []

    async def mock_fetch(url: str, timeout: int = 10) -> str:
        fetch_calls.append(url)
        return "<p>fetched</p>"

    mock_rss = patch(
        "reddit_rss_cleaner.main.fetch_reddit_rss", new=AsyncMock(return_value=FIXTURE_RSS_XML)
    )
    mock_content = patch("reddit_rss_cleaner.main.fetch_article_content", side_effect=mock_fetch)
    with mock_rss, mock_content:
        await client.get("/r/netsec/new")

    # fixture has one external post and one self-post; only external should be fetched
    assert all("reddit.com" not in url for url in fetch_calls)


async def test_content_fetch_budget_timeout_returns_feed_without_content(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTENT_FETCH_ENABLED", "true")
    monkeypatch.setenv("CONTENT_FETCH_BUDGET", "1")

    async def slow_fetch(url: str, timeout: int = 10) -> str:
        raise TimeoutError

    mock_rss = patch(
        "reddit_rss_cleaner.main.fetch_reddit_rss", new=AsyncMock(return_value=FIXTURE_RSS_XML)
    )
    mock_content = patch("reddit_rss_cleaner.main.fetch_article_content", side_effect=slow_fetch)
    with mock_rss, mock_content:
        response = await client.get("/r/netsec/new")

    assert response.status_code == 200
    assert "application/rss+xml" in response.headers["content-type"]


async def test_content_fetch_budget_timeout_with_hanging_tasks(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: hanging fetches must be cancelled and awaited so no orphaned futures escape."""
    monkeypatch.setenv("CONTENT_FETCH_ENABLED", "true")
    monkeypatch.setenv("CONTENT_FETCH_BUDGET", "1")

    cancelled: list[bool] = []

    async def hanging_fetch(url: str, timeout: int = 10) -> str:
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            cancelled.append(True)
            raise
        return ""

    mock_rss = patch(
        "reddit_rss_cleaner.main.fetch_reddit_rss", new=AsyncMock(return_value=FIXTURE_RSS_XML)
    )
    mock_content = patch("reddit_rss_cleaner.main.fetch_article_content", side_effect=hanging_fetch)
    with mock_rss, mock_content:
        response = await client.get("/r/netsec/new")

    assert response.status_code == 200
    assert "application/rss+xml" in response.headers["content-type"]
    # Pending tasks must have been cancelled (not left as orphaned futures)
    assert cancelled, "hanging tasks were not cancelled before returning"
