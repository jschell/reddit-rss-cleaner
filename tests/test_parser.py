from __future__ import annotations

from reddit_rss_cleaner.parser import ParsedEntry, extract_external_url, parse_feed

EXTERNAL_HTML = """\
<div class="md"><p>submitted by <a href="https://www.reddit.com/user/testuser"> /u/testuser</a>
<span><a href="https://example.com/article">[link]</a></span>
<span><a href="https://www.reddit.com/r/netsec/comments/abc123/test_post/">[comments]</a></span>
</p></div>
"""

SELF_POST_HTML = """\
<div class="md"><p>submitted by <a href="https://www.reddit.com/user/testuser"> /u/testuser</a>
<span><a href="https://www.reddit.com/r/netsec/comments/abc123/self_post/">[link]</a></span>
<span><a href="https://www.reddit.com/r/netsec/comments/abc123/self_post/">[comments]</a></span>
</p></div>
"""

NO_LINK_HTML = """\
<div class="md"><p>submitted by <a href="https://www.reddit.com/user/testuser"> /u/testuser</a>
<span><a href="https://www.reddit.com/r/netsec/comments/abc123/test_post/">[comments]</a></span>
</p></div>
"""

MALFORMED_HTML = "<<<<>>>>"

FALLBACK = "https://fallback.com/comments"


def test_extract_external_url_returns_article_url() -> None:
    url, is_self = extract_external_url(EXTERNAL_HTML, FALLBACK)
    assert url == "https://example.com/article"
    assert is_self is False


def test_extract_external_url_self_post_returns_comments_url() -> None:
    url, is_self = extract_external_url(SELF_POST_HTML, FALLBACK)
    assert "reddit.com" in url
    assert is_self is True


def test_extract_external_url_missing_link_returns_fallback() -> None:
    url, is_self = extract_external_url(NO_LINK_HTML, FALLBACK)
    assert url == FALLBACK
    assert is_self is False


def test_extract_external_url_malformed_html_returns_fallback() -> None:
    # Must not raise an exception
    url, _ = extract_external_url(MALFORMED_HTML, FALLBACK)
    assert url == FALLBACK


def test_parse_feed_returns_list_of_entries(fixture_rss: str) -> None:
    entries = parse_feed(fixture_rss)
    assert isinstance(entries, list)
    assert len(entries) > 0
    assert all(isinstance(e, ParsedEntry) for e in entries)


def test_parse_feed_external_entry_has_article_url(fixture_rss: str) -> None:
    entries = parse_feed(fixture_rss)
    external = next(e for e in entries if not e.is_self_post)
    assert external.entry_url == "https://example.com/article"
    assert "reddit.com" in external.comments_url


def test_parse_feed_self_post_entry(fixture_rss: str) -> None:
    entries = parse_feed(fixture_rss)
    self_post = next(e for e in entries if e.is_self_post)
    assert "reddit.com" in self_post.entry_url
    assert self_post.entry_url == self_post.comments_url


def test_parsed_entry_fetched_content_defaults_empty(fixture_rss: str) -> None:
    entries = parse_feed(fixture_rss)
    assert all(e.fetched_content == "" for e in entries)


def test_parsed_entry_fetched_content_can_be_set() -> None:
    entry = ParsedEntry(
        title="Test",
        entry_url="https://example.com",
        comments_url="https://reddit.com/r/test/comments/abc/",
        author="user",
        published_iso="2024-01-01T00:00:00Z",
        content_html="<p>reddit html</p>",
        is_self_post=False,
        fetched_content="<p>full article content</p>",
    )
    assert entry.fetched_content == "<p>full article content</p>"
