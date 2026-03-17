from __future__ import annotations

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/133.0.0.0 Safari/537.36"
)


async def fetch_reddit_rss(
    subreddit: str,
    sort: str,
    timeout: int = 15,
) -> str:
    """
    Fetch raw RSS XML from Reddit.

    Critical requirements:
    - HTTP/1.1 only (http2=False) — Reddit blocks HTTP/2 from non-browser clients
    - Spoofed Chrome user-agent — Reddit blocks non-browser UAs
    - Raises httpx.HTTPStatusError on non-2xx
    - Raises httpx.RequestError on network failures
    """
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.rss"
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(http2=False, headers=headers, follow_redirects=True) as client:
        response = await client.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
