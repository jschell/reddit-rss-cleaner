from __future__ import annotations

import logging
import time
from dataclasses import dataclass

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
        link_anchor = soup.find("a", string="[link]")
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
    feed = feedparser.parse(raw_rss)
    entries: list[ParsedEntry] = []

    for entry in feed.entries:
        comments_url: str = entry.get("link", "")
        title: str = entry.get("title", "")
        author: str = entry.get("author", "")

        published_parsed = entry.get("published_parsed")
        if published_parsed is not None:
            published_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", published_parsed)
        else:
            published_iso = ""

        content_html = ""
        content_list = entry.get("content")
        if content_list:
            content_html = content_list[0].get("value", "")
        elif entry.get("summary"):
            content_html = entry.summary

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
