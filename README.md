# reddit-rss-cleaner

A lightweight self-hosted service that rewrites Reddit RSS feeds to link directly to external articles instead of Reddit's comment pages. Designed to pair with [Miniflux](https://miniflux.app/) or any feed reader that follows `<link>` URLs.

## How it works

Reddit's RSS feeds set `<link>` to the comments page for every entry — even when the post is a link to an external article. This service sits between your feed reader and Reddit:

1. Fetches the raw Reddit Atom feed
2. Parses the `[link]` anchor from each entry's HTML content to extract the external article URL
3. Rebuilds a clean RSS 2.0 feed with corrected `<link>` URLs and a prepended *Article / Comments* navigation header
4. Self-posts (where `[link]` points back to Reddit) are detected and left as-is
5. Optionally fetches the full article body from the external URL and embeds it directly in the feed entry (opt-in — see [Content fetching](#content-fetching))

## API

| Endpoint | Description |
|---|---|
| `GET /r/{subreddit}/{sort}` | Cleaned RSS feed. Valid sorts: `new`, `hot`, `top`, `rising` |
| `GET /health` | Liveness probe — returns `{"status": "ok"}` |
| `GET /` | Usage info |

Example: `http://localhost:5000/r/netsec/new`

## Configuration

All configuration is via environment variables.

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Listen port |
| `CACHE_TTL` | `300` | Feed cache lifetime in seconds |
| `REQUEST_TIMEOUT` | `15` | Reddit fetch timeout in seconds |
| `LOG_LEVEL` | `info` | Uvicorn log level (`debug`, `info`, `warning`, `error`) |
| `CONTENT_FETCH_ENABLED` | *(unset)* | Set to `true` to fetch full article content and embed it in each feed entry |
| `CONTENT_TIMEOUT` | `10` | Per-article fetch timeout in seconds — applies to both the trafilatura static fetch and Playwright page load |
| `CONTENT_FETCH_BUDGET` | `20` | Total wall-clock budget in seconds for fetching all articles in a feed. Articles that don't complete within the budget are returned without content. Set this higher than `CONTENT_TIMEOUT` and lower than Miniflux's `CLIENT_TIMEOUT`. |
| `PLAYWRIGHT_ENABLED` | *(unset)* | Set to `true` to enable headless Chromium fallback for JavaScript-rendered pages |
| `PLAYWRIGHT_CONCURRENCY` | `4` | Maximum number of simultaneous Playwright browser pages (used when `PLAYWRIGHT_ENABLED=true`) |

## Content fetching

When `CONTENT_FETCH_ENABLED=true` the service fetches each external article URL and embeds the extracted body text directly in the RSS `<description>`. This lets your feed reader display the full article without opening a browser.

**Strategy (in order):**

1. **trafilatura** (plain HTTP) — fast, zero overhead, works for most static sites.
2. **Playwright headless Chromium** (optional fallback) — used when the static fetch returns too little content and `PLAYWRIGHT_ENABLED=true`. Handles JavaScript-rendered pages (SPAs, paywalled previews, etc.).

Self-posts are never fetched — their content is already inline in the Reddit feed.

### Enabling Playwright

A pre-built image with Chromium included is published to Docker Hub alongside the standard image:

| Tag | Chromium | Size |
|---|---|---|
| `latest` | No | ~260 MB |
| `latest-playwright` | Yes | ~1.8 GB |

Versioned tags follow the same pattern: `0.2.0-playwright`, `0.2-playwright`, `0.2-playwright`.

Use the playwright image in your stack:

```yaml
  reddit-rss-cleaner:
    image: jschell/reddit-rss-cleaner:latest-playwright
    environment:
      CONTENT_FETCH_ENABLED: "true"
      CONTENT_TIMEOUT: "15"
      CONTENT_FETCH_BUDGET: "60"
      PLAYWRIGHT_ENABLED: "true"
      PLAYWRIGHT_CONCURRENCY: "4"
```

To build the playwright image yourself instead:

```bash
docker build --build-arg PLAYWRIGHT_ENABLED=true -t reddit-rss-cleaner .
```

Without Chromium installed (i.e. using the standard image), setting `PLAYWRIGHT_ENABLED=true` at runtime has no effect.

## Running with Docker

```bash
docker build -t reddit-rss-cleaner .
docker run -d -p 5000:5000 reddit-rss-cleaner
```

## Miniflux integration

The service acts as a transparent proxy — subscribe to it exactly as you would subscribe to a Reddit feed directly, just replacing `www.reddit.com` with the address of this service.

### Docker stack (recommended)

Place both containers on a shared network so Miniflux can reach the cleaner by service name without exposing it to the host.

> **Important:** Miniflux blocks outgoing requests to private/internal IP ranges by default (SSRF protection). Because `reddit-rss-cleaner` sits on an internal Docker network, you must set `FETCHER_ALLOW_PRIVATE_NETWORKS: "1"` on the Miniflux service or feed fetching will fail with a network error.

```yaml
services:
  miniflux:
    image: miniflux/miniflux:latest
    depends_on:
      db:
        condition: service_healthy
      reddit-rss-cleaner:
        condition: service_healthy
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgres://miniflux:secret@db/miniflux?sslmode=disable
      RUN_MIGRATIONS: "1"
      CREATE_ADMIN: "1"
      ADMIN_USERNAME: admin
      ADMIN_PASSWORD: changeme
      FETCHER_ALLOW_PRIVATE_NETWORKS: "1"  # required — cleaner is on a private Docker network
      CLIENT_TIMEOUT: "70"                 # must exceed the cleaner's CONTENT_FETCH_BUDGET + overhead
    networks:
      - internal

  reddit-rss-cleaner:
    image: jschell/reddit-rss-cleaner:latest-playwright
    restart: unless-stopped
    environment:
      CACHE_TTL: "300"
      LOG_LEVEL: info
      CONTENT_FETCH_ENABLED: "true"
      CONTENT_TIMEOUT: "15"        # per-article timeout (static fetch + Playwright page load)
      CONTENT_FETCH_BUDGET: "60"   # total budget for all articles in one feed request
      PLAYWRIGHT_ENABLED: "true"
      PLAYWRIGHT_CONCURRENCY: "4"  # max simultaneous Playwright pages
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
      interval: 30s
      retries: 3
      start_period: 15s  # allow time for Playwright browser to initialise
    networks:
      - internal
    # Do NOT expose a host port — Miniflux reaches it via the internal network

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: miniflux
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: miniflux
    volumes:
      - /path/to/db:/var/lib/postgresql/data  # bind mount — no named volume needed
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "miniflux"]
      interval: 5s
      retries: 5
    networks:
      - internal

networks:
  internal:
```

### Adding feeds in Miniflux

Inside the Docker network the service is reachable as `http://reddit-rss-cleaner:5000`. Use that address as the feed URL:

```
http://reddit-rss-cleaner:5000/r/netsec/new
http://reddit-rss-cleaner:5000/r/programming/hot
http://reddit-rss-cleaner:5000/r/rust/new
```

If you are running the cleaner outside Docker (e.g. on a different host or via a reverse proxy), substitute the appropriate hostname or IP.

### Fetch interval

Reddit's public RSS feeds update roughly every few minutes. A Miniflux fetch interval of **15–30 minutes** is a reasonable default and avoids unnecessary load.

The service caches each feed for `CACHE_TTL` seconds (default 5 minutes), so rapid polling from Miniflux will not hammer Reddit.

## Development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run --frozen pytest -v
uv run --frozen ruff check .
uv run --frozen pyright
```

CI runs the same four checks on every push via GitHub Actions (`.github/workflows/ci.yml`).

## Releases

Releases are automated. Merging to `main` triggers `release.yml`, which uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) to analyse commits, bump `pyproject.toml`, and push a `v*` tag. That tag fires `publish.yml`, which builds and pushes the Docker image to Docker Hub.

Version bumps are driven by [Conventional Commits](https://www.conventionalcommits.org/):

| Commit prefix | Version bump |
|---|---|
| `fix:` | patch — `0.1.0` → `0.1.1` |
| `feat:` | minor — `0.1.0` → `0.2.0` |
| `feat!:` or `BREAKING CHANGE:` footer | major — `0.1.0` → `1.0.0` |
| `chore:`, `docs:`, `test:`, `refactor:` | no release |

Examples:

```
feat: add /r/{subreddit}/top endpoint
fix: handle empty content list in feedparser entries
feat!: drop support for Python 3.11
```

Commits that don't match any release type (e.g. `chore: update deps`) are merged normally without triggering a release.

## License

MIT
