# reddit-rss-cleaner

A lightweight self-hosted service that rewrites Reddit RSS feeds to link directly to external articles instead of Reddit's comment pages. Designed to pair with [Miniflux](https://miniflux.app/) or any feed reader that follows `<link>` URLs.

## How it works

Reddit's RSS feeds set `<link>` to the comments page for every entry — even when the post is a link to an external article. This service sits between your feed reader and Reddit:

1. Fetches the raw Reddit Atom feed
2. Parses the `[link]` anchor from each entry's HTML content to extract the external article URL
3. Rebuilds a clean RSS 2.0 feed with corrected `<link>` URLs and a prepended *Article / Comments* navigation header
4. Self-posts (where `[link]` points back to Reddit) are detected and left as-is

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

## Running with Docker

```bash
docker build -t reddit-rss-cleaner .
docker run -d -p 5000:5000 reddit-rss-cleaner
```

## Miniflux integration

The service acts as a transparent proxy — subscribe to it exactly as you would subscribe to a Reddit feed directly, just replacing `www.reddit.com` with the address of this service.

### Docker Compose (recommended)

Place both containers on a shared network so Miniflux can reach the cleaner by service name without exposing it to the host.

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
    networks:
      - internal

  reddit-rss-cleaner:
    image: DOCKERHUB_USERNAME/reddit-rss-cleaner:latest
    restart: unless-stopped
    environment:
      CACHE_TTL: "300"
      LOG_LEVEL: info
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
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
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "miniflux"]
      interval: 5s
      retries: 5
    networks:
      - internal

networks:
  internal:

volumes:
  db_data:
```

### Adding feeds in Miniflux

Inside the `docker-compose` network the service is reachable as `http://reddit-rss-cleaner:5000`. Use that address as the feed URL:

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
