from __future__ import annotations

import pytest

from reddit_rss_cleaner.main import clear_cache

FIXTURE_RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>/r/netsec</title>
  <id>https://www.reddit.com/r/netsec/new/</id>
  <link rel="alternate" href="https://www.reddit.com/r/netsec/new"/>
  <updated>2024-01-01T12:00:00+00:00</updated>
  <entry>
    <title>Test External Article</title>
    <id>t3_abc123</id>
    <link href="https://www.reddit.com/r/netsec/comments/abc123/test_post/"/>
    <author><name>/u/testuser</name></author>
    <published>2024-01-01T12:00:00+00:00</published>
    <updated>2024-01-01T12:00:00+00:00</updated>
    <content type="html"><![CDATA[<div class="md"><p>submitted by
      <a href="https://www.reddit.com/user/testuser"> /u/testuser</a>
      <span><a href="https://example.com/article">[link]</a></span>
      <span><a href="https://www.reddit.com/r/netsec/comments/abc123/test_post/">[comments]</a></span>
    </p></div>]]></content>
  </entry>
  <entry>
    <title>Self Post Title</title>
    <id>t3_def456</id>
    <link href="https://www.reddit.com/r/netsec/comments/def456/self_post/"/>
    <author><name>/u/selfposter</name></author>
    <published>2024-01-01T11:00:00+00:00</published>
    <updated>2024-01-01T11:00:00+00:00</updated>
    <content type="html"><![CDATA[<div class="md"><p>submitted by
      <a href="https://www.reddit.com/user/selfposter"> /u/selfposter</a>
      <span><a href="https://www.reddit.com/r/netsec/comments/def456/self_post/">[link]</a></span>
      <span><a href="https://www.reddit.com/r/netsec/comments/def456/self_post/">[comments]</a></span>
    </p></div>]]></content>
  </entry>
</feed>
"""


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    """Clear the feed cache before each test."""
    clear_cache()


@pytest.fixture()
def fixture_rss() -> str:
    return FIXTURE_RSS_XML
