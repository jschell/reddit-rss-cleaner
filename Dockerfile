# ── Builder ───────────────────────────────────────────────────────────────────
# Installs dependencies and the project into a virtual environment.
# uv stays in this stage only — it is not copied to the runtime image (~25 MB).
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./

# When PLAYWRIGHT_ENABLED=true, include the playwright optional-dependency group
# so the Python bindings are present for the headless browser to use.
ARG PLAYWRIGHT_ENABLED=false
RUN if [ "$PLAYWRIGHT_ENABLED" = "true" ]; then \
      uv sync --frozen --no-dev --no-install-project --extra playwright; \
    else \
      uv sync --frozen --no-dev --no-install-project; \
    fi

COPY src/ ./src/
RUN if [ "$PLAYWRIGHT_ENABLED" = "true" ]; then \
      uv sync --frozen --no-dev --extra playwright --no-editable; \
    else \
      uv sync --frozen --no-dev --no-editable; \
    fi

# Strip non-English justext stopword lists (~2.4 MB). The app only scrapes
# English content; all 109 other language files are unused.
RUN find /app/.venv -path "*/justext/stoplists/*.txt" ! -name 'English.txt' -delete

# Strip __pycache__ — Python regenerates on first import; saves 5–20 MB.
RUN find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ── Runtime ───────────────────────────────────────────────────────────────────
# Final image: no uv binary, only the virtual environment and project source.
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# curl is needed by external healthcheck probes (e.g. compose/Portainer stacks).
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chromium for Playwright only when PLAYWRIGHT_ENABLED=true is passed at build time.
# Usage: docker build --build-arg PLAYWRIGHT_ENABLED=true .
#
# System packages: exact Chromium runtime deps for Debian bookworm (debian12) from
# Playwright's own nativeDeps manifest, plus fonts-liberation for basic text rendering.
# This skips the broad "tools" block that --with-deps would add: xvfb, fonts-noto-color-emoji,
# fonts-unifont, fonts-ipafont-gothic, fonts-wqy-zenhei, fonts-tlwg-loma-otf,
# fonts-freefont-ttf, xfonts-scalable — none of which are needed for headless scraping.
#
# --only-shell: since Playwright 1.49, `playwright install` downloads both the full
# headed Chromium build and chromium-headless-shell. For a headless-only server,
# --only-shell skips the headed build and saves ~100 MB.
ARG PLAYWRIGHT_ENABLED=false
RUN if [ "$PLAYWRIGHT_ENABLED" = "true" ]; then \
      apt-get update && apt-get install -y --no-install-recommends \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libglib2.0-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
      && rm -rf /var/lib/apt/lists/* \
      && /app/.venv/bin/playwright install --only-shell chromium; \
    fi

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"
CMD ["/app/.venv/bin/reddit-rss-cleaner"]
