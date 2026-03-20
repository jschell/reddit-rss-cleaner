FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ ./src/
RUN uv sync --frozen --no-dev --no-editable
# Install Chromium for Playwright only when PLAYWRIGHT_ENABLED=true is passed at build time.
# Usage: docker build --build-arg PLAYWRIGHT_ENABLED=true .
#
# We install exactly the Chromium runtime deps for Debian bookworm (debian12) from
# Playwright's own nativeDeps manifest, plus fonts-liberation for basic text rendering.
# This skips the broad "tools" block that --with-deps would add: xvfb, fonts-noto-color-emoji,
# fonts-unifont, fonts-ipafont-gothic, fonts-wqy-zenhei, fonts-tlwg-loma-otf,
# fonts-freefont-ttf, xfonts-scalable — none of which are needed for headless scraping.
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
      && uv run playwright install chromium; \
    fi
EXPOSE 5000
CMD ["uv", "run", "--frozen", "reddit-rss-cleaner"]
