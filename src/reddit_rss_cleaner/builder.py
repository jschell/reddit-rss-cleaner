from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from feedgen.feed import FeedGenerator  # type: ignore[import-untyped]

from reddit_rss_cleaner.parser import ParsedEntry

logger = logging.getLogger(__name__)


def build_rss_feed(
    subreddit: str,
    sort: str,
    entries: list[ParsedEntry],
) -> str:
    """
    Reconstruct a corrected RSS feed using feedgen.

    Entry <link> → external article URL (or comments URL for self-posts)
    Entry content → original HTML + prepended Article/Comments links
    Entry id → SHA-1 of comments URL (stable, deduplicated)
    """
    fg: Any = FeedGenerator()
    fg.id(f"https://www.reddit.com/r/{subreddit}/{sort}")
    fg.title(f"/r/{subreddit} - {sort}")
    fg.link(href=f"https://www.reddit.com/r/{subreddit}/{sort}", rel="alternate")
    fg.description(f"Reddit /r/{subreddit} ({sort}) - cleaned RSS feed")
    fg.language("en")

    for entry in entries:
        fe: Any = fg.add_entry(order="append")

        entry_id = hashlib.sha1(entry.comments_url.encode()).hexdigest()
        fe.id(entry_id)
        fe.title(entry.title)
        fe.link(href=entry.entry_url)

        if entry.author:
            fe.author({"name": entry.author})

        if entry.published_iso:
            try:
                dt = datetime.strptime(entry.published_iso, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=UTC
                )
                fe.published(dt)
                fe.updated(dt)
            except ValueError:
                logger.warning("Could not parse published date: %s", entry.published_iso)

        if not entry.is_self_post:
            prepend = (
                f"<p>"
                f'<a href="{entry.entry_url}">📄 Article</a> &nbsp;|&nbsp;'
                f'<a href="{entry.comments_url}">💬 Comments ({subreddit})</a>'
                f"</p>"
            )
            content = prepend + entry.content_html
        else:
            content = entry.content_html

        fe.content(content, type="html")

    rss_bytes: bytes = fg.rss_str(pretty=True)
    return rss_bytes.decode()
