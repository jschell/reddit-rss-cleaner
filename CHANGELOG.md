# CHANGELOG


## v0.3.3 (2026-03-18)

### Bug Fixes

- Prevent orphaned Playwright futures and reduce fetch timeouts
  ([`a6268a3`](https://github.com/jschell/reddit-rss-cleaner/commit/a6268a306734e3215ce73d0504cf90014d36a5cd))

- Change wait_until="networkidle" to "domcontentloaded" in _fetch_headless; many sites (Medium,
  government sites) never reach networkidle, causing unnecessary 10s timeouts on every Playwright
  fetch.

- Replace asyncio.wait_for(gather(...)) with asyncio.wait() + explicit cancel/await of pending tasks
  when the content budget expires. The old approach force-cancelled coroutines mid-flight, leaving
  Playwright's internal futures orphaned and logging spurious "Future exception was never retrieved"
  / TargetClosedError warnings.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- **types**: Annotate loop_tasks and fetched to resolve pyright errors
  ([`1f865a5`](https://github.com/jschell/reddit-rss-cleaner/commit/1f865a586d5ec9c69db86873544757df196d98ca))

Pyright couldn't infer the element type of the list comprehension passed to asyncio.wait, causing
  reportUnknownMemberType/reportUnknownVariableType errors on lines 122-126. Explicit annotations:

loop_tasks: list[asyncio.Task[str]]

fetched: list[str]

give pyright enough information to verify t.result() and the zip call.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Testing

- Add coverage for domcontentloaded and budget-timeout cancellation
  ([`3955d62`](https://github.com/jschell/reddit-rss-cleaner/commit/3955d62d7cd0439b0d4a7b3c6cd73c328522ed89))

- test_goto_uses_domcontentloaded: asserts page.goto is called with wait_until="domcontentloaded";
  would catch a regression back to networkidle.

- test_content_fetch_budget_timeout_with_hanging_tasks: uses a genuinely hanging coroutine
  (asyncio.sleep(60)) to exercise the asyncio.wait + cancel/await path, and asserts CancelledError
  was received by pending tasks — proving no orphaned futures escape the budget timeout.

Also adds CLAUDE.md requiring test coverage for all code changes.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.3.2 (2026-03-18)

### Bug Fixes

- Prevent Miniflux timeout by unblocking event loop and bounding content-fetch time
  ([`f7835b6`](https://github.com/jschell/reddit-rss-cleaner/commit/f7835b67e2eda9b68516b2a1b970753c60bba014))

Two root causes for the timeout:

1. trafilatura.fetch_url is synchronous — calling it directly in an async context blocked the event
  loop, forcing all 25 article fetches to run serially instead of concurrently. Fixed by wrapping in
  run_in_executor.

2. No overall time budget — with many entries the total content-fetch phase could far exceed
  Miniflux's HTTP client timeout. Added CONTENT_FETCH_BUDGET (default 20 s) via asyncio.wait_for; on
  expiry the feed is returned without article content rather than hanging.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Code Style

- Apply ruff format to main.py
  ([`f4ce024`](https://github.com/jschell/reddit-rss-cleaner/commit/f4ce0245d6e0b7085a1e8807d8246f6d3a4ef573))

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.3.1 (2026-03-18)

### Bug Fixes

- Resolve ruff lint errors (import sort, UP035, E501, F401)
  ([`3f40e2f`](https://github.com/jschell/reddit-rss-cleaner/commit/3f40e2f1b8bd961280c04c10deb682bcfddc0814))

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Reuse shared Playwright browser to prevent Miniflux timeout
  ([`c6a2bb2`](https://github.com/jschell/reddit-rss-cleaner/commit/c6a2bb2e5a68f2ceccdc17168df902bd23df6ab3))

Previously each article launched its own Chromium process inside _fetch_headless, meaning a 25-entry
  feed could spin up 25 concurrent browsers and easily exceed Miniflux's HTTP client timeout.

Now a single browser is launched once at startup via the FastAPI lifespan (init_playwright /
  close_playwright) and shared across all requests. A semaphore (default 4, tunable via
  PLAYWRIGHT_CONCURRENCY) caps the number of concurrent pages so the container isn't overwhelmed.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.3.0 (2026-03-18)

### Documentation

- Document content fetching feature and new env vars
  ([`dd1d1f6`](https://github.com/jschell/reddit-rss-cleaner/commit/dd1d1f645d691127f97ba213a74720c54c6b2642))

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Features

- Publish latest-playwright Docker Hub tag with Chromium included
  ([`97cb20e`](https://github.com/jschell/reddit-rss-cleaner/commit/97cb20e98fd7e1f26504663f5fa7affc021e330d))

Adds a second build+push step to publish.yml that passes PLAYWRIGHT_ENABLED=true at build time and
  pushes versioned -playwright tags (latest-playwright, x.y.z-playwright, etc.) alongside the
  standard tags on every release.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.2.0 (2026-03-18)

### Features

- Add article content fetching with trafilatura and optional Playwright fallback
  ([`24d8699`](https://github.com/jschell/reddit-rss-cleaner/commit/24d8699e51fbf864faa6dd8964c6d6ff21c8f5b0))

- New content_fetcher module: fetches external article HTML using trafilatura (static HTTP); falls
  back to headless Chromium via Playwright when content is too short and PLAYWRIGHT_ENABLED=true -
  ParsedEntry gains fetched_content field (default empty string) - builder prefers fetched_content
  over Reddit-provided HTML for external posts - main orchestrates concurrent content fetching when
  CONTENT_FETCH_ENABLED=true; self-posts are skipped - Dockerfile: optional Playwright + Chromium
  install via --build-arg PLAYWRIGHT_ENABLED=true - Full TDD: red/green cycle for content_fetcher,
  parser, builder, and routes

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.1.5 (2026-03-17)

### Bug Fixes

- Formatting in README.md
  ([`8b2a3d3`](https://github.com/jschell/reddit-rss-cleaner/commit/8b2a3d39e2ac5a2f2ea9a0b52f4fa307d529553c))


## v0.1.4 (2026-03-17)

### Bug Fixes

- Log error details before raising 502 HTTPException
  ([`ecfdcb5`](https://github.com/jschell/reddit-rss-cleaner/commit/ecfdcb5e09a8c7ac998c1b7284f6476b3d5f20bf))

Without this, the cause of upstream failures (403, 429, timeout, network error) was only visible in
  the HTTP response body, not the container logs, making it impossible to diagnose from Portainer.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Shorten 429 log message to satisfy ruff E501
  ([`f1e7a5c`](https://github.com/jschell/reddit-rss-cleaner/commit/f1e7a5ca0c931921305703f5170c6a9d6b3bfad9))

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Documentation

- Clarify FETCHER_ALLOW_PRIVATE_NETWORKS requirement and update stack example
  ([`68d508a`](https://github.com/jschell/reddit-rss-cleaner/commit/68d508ac1874aa1c5f7b00f3f1c3aa06e440f46d))

Miniflux blocks private network IPs by default; without this flag feed fetching silently fails.
  Updated the example stack to match the working config and renamed the section to "Docker stack".

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.1.3 (2026-03-17)

### Bug Fixes

- Remove [skip ci] from PSR commit so publish workflow triggers
  ([`640f37e`](https://github.com/jschell/reddit-rss-cleaner/commit/640f37eff1cf6a3221286fab728dbbb2b9b19f8e))

[skip ci] in the release commit message was suppressing all workflows on the tag push, including
  publish.yml. Replaced with a job-level condition on release.yml to prevent re-triggering.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.1.2 (2026-03-17)

### Bug Fixes

- Use PAT in release workflow so tag push triggers publish
  ([`275e6f8`](https://github.com/jschell/reddit-rss-cleaner/commit/275e6f8bc56ebff45ea329b6d62d846aaa837c8d))

GITHUB_TOKEN-triggered events cannot fire other workflows per GitHub's security model. Switching to
  GH_PAT means the tag push is attributed to a real user, which allows publish.yml to run.

Requires a GH_PAT secret with 'contents: write' scope set in repo Settings → Secrets.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.1.1 (2026-03-17)

### Bug Fixes

- Correct Docker Hub image name in compose example
  ([`df52d52`](https://github.com/jschell/reddit-rss-cleaner/commit/df52d528d234edc71e7073e5dea7f5a7f1fa144e))

Was missing the DOCKERHUB_USERNAME/ prefix, causing Portainer to fail with "pull access denied" when
  deploying the stack.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Install curl in Docker image for healthcheck
  ([`2f56869`](https://github.com/jschell/reddit-rss-cleaner/commit/2f568696f61c916332d3abe9b99962f1cbc0a733))

python:3.12-slim has no curl, so the healthcheck was immediately failing and marking the container
  unhealthy. Also add start_period to give the app time to start before checks begin.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.1.0 (2026-03-17)
