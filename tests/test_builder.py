from __future__ import annotations

import hashlib

from reddit_rss_cleaner.builder import build_rss_feed
from reddit_rss_cleaner.parser import ParsedEntry

EXTERNAL_ENTRY = ParsedEntry(
    title="Test Article",
    entry_url="https://example.com/article",
    comments_url="https://www.reddit.com/r/netsec/comments/abc123/test/",
    author="/u/testuser",
    published_iso="2024-01-01T12:00:00Z",
    content_html="<p>Some content</p>",
    is_self_post=False,
)

SELF_POST_ENTRY = ParsedEntry(
    title="Self Post",
    entry_url="https://www.reddit.com/r/netsec/comments/def456/self/",
    comments_url="https://www.reddit.com/r/netsec/comments/def456/self/",
    author="/u/selfposter",
    published_iso="2024-01-01T11:00:00Z",
    content_html="<p>Self post content</p>",
    is_self_post=True,
)


def test_feed_has_correct_title() -> None:
    xml = build_rss_feed("netsec", "new", [EXTERNAL_ENTRY])
    assert "/r/netsec" in xml
    assert "new" in xml


def test_feed_has_correct_channel_link() -> None:
    xml = build_rss_feed("netsec", "new", [EXTERNAL_ENTRY])
    assert "https://www.reddit.com/r/netsec/new" in xml


def test_feed_has_description() -> None:
    xml = build_rss_feed("netsec", "new", [EXTERNAL_ENTRY])
    assert "netsec" in xml


def test_external_entry_link_is_article_url() -> None:
    xml = build_rss_feed("netsec", "new", [EXTERNAL_ENTRY])
    assert "https://example.com/article" in xml


def test_self_post_entry_link_is_comments_url() -> None:
    xml = build_rss_feed("netsec", "new", [SELF_POST_ENTRY])
    assert "https://www.reddit.com/r/netsec/comments/def456/self/" in xml


def test_entry_id_is_stable() -> None:
    xml1 = build_rss_feed("netsec", "new", [EXTERNAL_ENTRY])
    xml2 = build_rss_feed("netsec", "new", [EXTERNAL_ENTRY])
    expected_id = hashlib.sha1(EXTERNAL_ENTRY.comments_url.encode()).hexdigest()
    assert expected_id in xml1
    assert xml1 == xml2


def test_external_entry_has_content_prepend() -> None:
    xml = build_rss_feed("netsec", "new", [EXTERNAL_ENTRY])
    assert "📄 Article" in xml
    assert "💬 Comments" in xml


def test_self_post_has_no_content_prepend() -> None:
    xml = build_rss_feed("netsec", "new", [SELF_POST_ENTRY])
    assert "📄 Article" not in xml


def test_fetched_content_used_instead_of_reddit_html() -> None:
    entry = ParsedEntry(
        title="Test Article",
        entry_url="https://example.com/article",
        comments_url="https://www.reddit.com/r/netsec/comments/abc123/test/",
        author="/u/testuser",
        published_iso="2024-01-01T12:00:00Z",
        content_html="<p>reddit snippet</p>",
        is_self_post=False,
        fetched_content="<p>full fetched article body</p>",
    )
    xml = build_rss_feed("netsec", "new", [entry])
    assert "full fetched article body" in xml
    assert "reddit snippet" not in xml


def test_reddit_html_used_when_fetched_content_empty() -> None:
    entry = ParsedEntry(
        title="Test Article",
        entry_url="https://example.com/article",
        comments_url="https://www.reddit.com/r/netsec/comments/abc123/test/",
        author="/u/testuser",
        published_iso="2024-01-01T12:00:00Z",
        content_html="<p>reddit snippet</p>",
        is_self_post=False,
        fetched_content="",
    )
    xml = build_rss_feed("netsec", "new", [entry])
    assert "reddit snippet" in xml


def test_invalid_published_iso_is_skipped_without_raising() -> None:
    """build_rss_feed must not raise when published_iso can't be parsed."""
    entry = ParsedEntry(
        title="Test Article",
        entry_url="https://example.com/article",
        comments_url="https://www.reddit.com/r/netsec/comments/abc123/test/",
        author="/u/testuser",
        published_iso="not-a-date",
        content_html="<p>content</p>",
        is_self_post=False,
    )
    xml = build_rss_feed("netsec", "new", [entry])
    # Feed is still generated; the broken date is silently omitted
    assert "Test Article" in xml


def test_empty_published_iso_is_skipped_without_raising() -> None:
    entry = ParsedEntry(
        title="No Date Article",
        entry_url="https://example.com/article",
        comments_url="https://www.reddit.com/r/netsec/comments/abc123/test/",
        author="/u/testuser",
        published_iso="",
        content_html="<p>content</p>",
        is_self_post=False,
    )
    xml = build_rss_feed("netsec", "new", [entry])
    assert "No Date Article" in xml
