from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from time import struct_time
from typing import Any, cast

import feedparser  # type: ignore[import-untyped]
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedEntry:
    title: str
    entry_url: str  # external article URL (or comments URL for self-posts)
    comments_url: str  # always the Reddit comments URL
    author: str
    published_iso: str  # ISO 8601 UTC string
    content_html: str  # original Reddit HTML content
    is_self_post: bool  # True if [link] points back to reddit.com


def extract_external_url(entry_html: str, fallback_url: str) -> tuple[str, bool]:
    """
    Parse entry HTML, extract [link] anchor href.
    Returns (url, is_self_post).
    """
    try:
        soup = BeautifulSoup(entry_html, "lxml")
        all_anchors = soup.find_all("a")
        link_anchor = next((a for a in all_anchors if a.get_text() == "[link]"), None)
        if link_anchor is None:
            return fallback_url, False
        href = link_anchor.get("href", "")
        if not isinstance(href, str) or not href:
            return fallback_url, False
        if "reddit.com" in href:
            return href, True
        return href, False
    except Exception:
        logger.exception("Failed to parse entry HTML")
        return fallback_url, False


def parse_feed(raw_rss: str) -> list[ParsedEntry]:
    """
    Parse raw Reddit RSS XML into a list of ParsedEntry objects.
    Uses feedparser for RSS parsing, BeautifulSoup for HTML content.
    """
    feed: Any = feedparser.parse(raw_rss)  # pyright: ignore[reportUnknownMemberType]
    entries: list[ParsedEntry] = []

    for entry in feed.entries:
        comments_url = str(entry.get("link") or "")
        title = str(entry.get("title") or "")
        author = str(entry.get("author") or "")

        published_iso = ""
        published_parsed = entry.get("published_parsed")
        if published_parsed is not None and isinstance(published_parsed, struct_time):
            published_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", published_parsed)

        content_html = ""
        raw_content = entry.get("content")
        if raw_content and isinstance(raw_content, list) and raw_content:
            content_item = cast("dict[str, Any]", raw_content[0])
            content_html = str(content_item.get("value") or "")
        if not content_html:
            summary = entry.get("summary")
            if summary and isinstance(summary, str):
                content_html = summary

        entry_url, is_self_post = extract_external_url(content_html, comments_url)

        entries.append(
            ParsedEntry(
                title=title,
                entry_url=entry_url,
                comments_url=comments_url,
                author=author,
                published_iso=published_iso,
                content_html=content_html,
                is_self_post=is_self_post,
            )
        )

    return entries
