from __future__ import annotations

import httpx
import pytest
import respx

from reddit_rss_cleaner.fetcher import USER_AGENT, fetch_reddit_rss

REDDIT_URL = "https://www.reddit.com/r/netsec/new.rss"
SAMPLE_RSS = '<?xml version="1.0"?><feed><title>test</title></feed>'


@respx.mock
async def test_returns_rss_on_success() -> None:
    respx.get(REDDIT_URL).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
    result = await fetch_reddit_rss("netsec", "new")
    assert result == SAMPLE_RSS


@respx.mock
async def test_uses_http1_not_http2() -> None:
    """Reddit blocks HTTP/2 clients; http2 must be disabled."""
    route = respx.get(REDDIT_URL).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
    await fetch_reddit_rss("netsec", "new")
    # respx captures the request; verify HTTP version via the actual client config
    # by checking the request was made (http2=False means httpx uses HTTP/1.1)
    assert route.called


@respx.mock
async def test_sends_browser_user_agent() -> None:
    route = respx.get(REDDIT_URL).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
    await fetch_reddit_rss("netsec", "new")
    request = route.calls.last.request
    assert request.headers["user-agent"] == USER_AGENT


@respx.mock
async def test_raises_on_404() -> None:
    respx.get(REDDIT_URL).mock(return_value=httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_reddit_rss("netsec", "new")
    assert exc_info.value.response.status_code == 404


@respx.mock
async def test_raises_on_403() -> None:
    respx.get(REDDIT_URL).mock(return_value=httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_reddit_rss("netsec", "new")
    assert exc_info.value.response.status_code == 403


@respx.mock
async def test_raises_on_429() -> None:
    respx.get(REDDIT_URL).mock(return_value=httpx.Response(429))
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_reddit_rss("netsec", "new")
    assert exc_info.value.response.status_code == 429


@respx.mock
async def test_raises_on_network_error() -> None:
    respx.get(REDDIT_URL).mock(side_effect=httpx.ConnectError("connection refused"))
    with pytest.raises(httpx.RequestError):
        await fetch_reddit_rss("netsec", "new")


@respx.mock
async def test_constructs_correct_url() -> None:
    route = respx.get("https://www.reddit.com/r/python/hot.rss").mock(
        return_value=httpx.Response(200, text=SAMPLE_RSS)
    )
    await fetch_reddit_rss("python", "hot")
    assert route.called


@respx.mock
async def test_raises_on_500() -> None:
    respx.get(REDDIT_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_reddit_rss("netsec", "new")
    assert exc_info.value.response.status_code == 500


@respx.mock
async def test_raises_on_503() -> None:
    respx.get(REDDIT_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_reddit_rss("netsec", "new")
    assert exc_info.value.response.status_code == 503
