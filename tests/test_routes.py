from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from reddit_rss_cleaner.main import app
from conftest import FIXTURE_RSS_XML


@pytest.fixture()
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c  # type: ignore[misc]


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
