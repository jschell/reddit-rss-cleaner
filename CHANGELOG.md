# CHANGELOG


## v0.3.8 (2026-03-20)

### Bug Fixes

- Remove pip from runtime image instead of pinning a version
  ([`8889a6c`](https://github.com/jschell/reddit-rss-cleaner/commit/8889a6cc8fa0f81943b6fb6c99959be67252df0b))

pip is never used at runtime — the app runs directly from uv's venv. Removing it eliminates the CVE
  surface entirely and avoids the ongoing toil of updating a version pin each time a new pip
  vulnerability is disclosed.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Upgrade pip to >=26.0 in runtime image to address CVEs
  ([`664396e`](https://github.com/jschell/reddit-rss-cleaner/commit/664396eecfffb6359085bfeaba81c7b49ed61eb4))

Two pip vulnerabilities affect the base python:3.12-slim image: - First CVE fixed in pip 25.3 -
  Second CVE fixed in pip 26.0

Explicitly upgrade pip in the runtime stage to pip>=26.0 to cover both.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.3.7 (2026-03-20)

### Bug Fixes

- Add HEALTHCHECK to Dockerfile so compose service_healthy works
  ([`d555dcc`](https://github.com/jschell/reddit-rss-cleaner/commit/d555dcc14766e08e7db72daa68c047a7ec822dce))

Without a HEALTHCHECK instruction, Docker never marks the container healthy, so any dependent
  service using condition: service_healthy causes the "dependency failed to start: container is
  unhealthy" error.

Uses stdlib urllib (already in the Python image) to probe /health.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Handle PDF downloads and mid-redirect race in headless fetcher
  ([`46d197b`](https://github.com/jschell/reddit-rss-cleaner/commit/46d197b087e13cf5b755ea539208f25f1f549828))

Two Playwright errors observed in production:

1. "Page.goto: Download is starting" — PDF and other binary URLs trigger a browser download instead
  of a page render. Added _is_binary_url() to detect these by extension and return early, skipping
  the headless path entirely.

2. "Unable to retrieve content because the page is navigating" — page.content() races with a
  redirect that fires after domcontentloaded. Now catches the error, waits for the load state, and
  retries page.content() once.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Install curl in runtime image for compose healthcheck
  ([`cb776eb`](https://github.com/jschell/reddit-rss-cleaner/commit/cb776eb9c1fed6da430c7cb537f941613f0903ab))

The stack healthcheck uses curl -f http://localhost:5000/health but python:3.12-slim does not
  include curl, causing the container to be marked unhealthy immediately and blocking dependent
  services.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Code Style

- Fix E501 line too long in test_content_fetcher
  ([`a8f8ee5`](https://github.com/jschell/reddit-rss-cleaner/commit/a8f8ee5dccc6e94f5f0adb06f690d0c7caebb363))

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Ruff format content_fetcher.py
  ([`032bb91`](https://github.com/jschell/reddit-rss-cleaner/commit/032bb9143912465b8c1e6c2d094c1ae338295cfa))

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Documentation

- Remove timeout from healthcheck example (Portainer schema compat)
  ([`3075f70`](https://github.com/jschell/reddit-rss-cleaner/commit/3075f7027ebbea1bbdf45980962a8fc4b55cc656))

Some Portainer versions use a strict compose schema that rejects timeout as a healthcheck property,
  causing deploy to fail with "Additional property timeout is not allowed".

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Restore healthcheck in stack example using curl
  ([`07c0dfc`](https://github.com/jschell/reddit-rss-cleaner/commit/07c0dfcc5c15b91e8ef7755c1ee09e5246193563))

curl is now installed in the runtime image. Restore the full healthcheck block with curl, including
  start_period to allow Playwright time to initialise before checks begin.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Strip healthcheck to test+retries only for Portainer compat
  ([`f84d1be`](https://github.com/jschell/reddit-rss-cleaner/commit/f84d1be1316b838066d6761cdf3e2e2bcdc4411a))

This Portainer version rejects interval, timeout, and start_period as additional properties. Keep
  only test and retries to match the minimal schema it accepts.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Update healthcheck example to use python instead of curl
  ([`d808acf`](https://github.com/jschell/reddit-rss-cleaner/commit/d808acf80036fb37580e0b3e13dd2584e4938669))

curl is not present in python:3.12-slim. Use stdlib urllib via python so no extra packages are
  needed. Also add start_period: 15s to give Playwright time to initialise before health checks
  begin counting.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Update image size table with measured amd64 and arm64 sizes
  ([`feb4e39`](https://github.com/jschell/reddit-rss-cleaner/commit/feb4e398d1afca404609909b8a14f3aa671ab0ce))

Replace the single estimated size column with measured values for both architectures. Playwright
  (Chromium) adds ~910 MB on amd64 and ~638 MB on arm64.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.3.6 (2026-03-20)

### Bug Fixes

- Apply ruff format to main.py
  ([`d7fc724`](https://github.com/jschell/reddit-rss-cleaner/commit/d7fc72426aa7386f9710e138a6d9a21eaa386ea6))

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Assert guards, strip [link], redundant check, cache prune, env int safety, tests
  ([`fec8d99`](https://github.com/jschell/reddit-rss-cleaner/commit/fec8d99255240f84ccf6cc8120829bcb4e4d8c39))

Item 6 – content_fetcher.py: replace assert _browser/assert _semaphore with an explicit if/raise
  RuntimeError so the guard works under python -O and communicates the contract clearly.

Item 7 – parser.py: add .strip() to [link] text comparison so anchors whose text has surrounding
  whitespace are correctly matched.

Item 8 – parser.py: remove redundant leading truthiness check before isinstance(raw_content, list)
  (the isinstance + len check is enough).

Item 9 – cache.py: add TTLCache.prune() to evict all expired entries on demand; without it, entries
  for rarely-accessed keys accumulate until clear() or restart.

Item 10 – main.py + content_fetcher.py: all int(os.environ.get(...)) calls are now wrapped via
  _env_int() helper (main.py) or try/except (content_fetcher.py) so a misconfigured env var logs a
  warning and falls back to the default instead of crashing at startup.

Item 11 – test_builder.py: add tests for invalid and empty published_iso to confirm build_rss_feed
  does not raise.

Item 12 – test_parser.py: add test confirming [link] anchor with surrounding whitespace is matched
  after the .strip() fix.

Item 13 – test_fetcher.py: add 500 and 503 tests to cover the generic HTTPStatusError path beyond
  403/404/429.

Item 14 – test_parser.py: add tests for entries missing content/summary, missing author, and an
  entirely empty feed. Also add test_cache.py: TestTTLCachePrune covering prune().

71 tests passing.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.3.5 (2026-03-20)

### Bug Fixes

- Playwright version bound, FastAPI version, ensure_future, test coverage
  ([`c33aefd`](https://github.com/jschell/reddit-rss-cleaner/commit/c33aefd13beaa324e0b0cd49d61e43b387ebf683))

- Bump playwright optional-dep and dev-group bounds to >=1.49.0; versions below 1.49 do not support
  --only-shell, breaking the Playwright-enabled Docker build - Read FastAPI app version from
  importlib.metadata instead of the hardcoded "0.1.0" string so /openapi.json always reflects
  pyproject.toml - Replace deprecated asyncio.ensure_future() with asyncio.create_task(); also
  removes the per-request _noop() closure, using asyncio.sleep(0) as a zero-cost resolved coroutine
  for self-posts - Add respx to dev dependencies for httpx request mocking - Add
  tests/test_cache.py: unit tests for TTLCache get/set/clear/expiry - Add tests/test_fetcher.py:
  unit tests for fetch_reddit_rss covering HTTP/1.1 enforcement, user-agent header, correct URL
  construction, and error propagation for 403/404/429 and network failures

60 tests passing.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Build System

- Replace playwright --with-deps with explicit chromium runtime deps
  ([`1a4f863`](https://github.com/jschell/reddit-rss-cleaner/commit/1a4f863c5895874a300730cb389623f04eb64589))

The --with-deps flag installs two groups of packages on Debian bookworm: - chromium (21 runtime
  libs) — needed - tools (xvfb + 8 font packages) — not needed for headless scraping

The tools block adds ~86 MB uncompressed and serves no purpose in a container that only ever runs
  Chromium in headless/domcontentloaded mode: - xvfb: X virtual framebuffer — headless Chrome
  doesn't need a display server - fonts-noto-color-emoji, fonts-unifont, fonts-ipafont-gothic,
  fonts-wqy-zenhei, fonts-tlwg-loma-otf, fonts-freefont-ttf, xfonts-scalable — broad CJK/emoji font
  stacks for interactive browsing

Replace with exactly the 21 chromium runtime packages from Playwright 1.58.0's nativeDeps manifest
  for debian12 (bookworm), plus fonts-liberation for minimum text rendering. Standard image is
  unchanged.

Expected reduction: latest-playwright ~1.8 GB → ~1.75 GB.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Documentation

- Broaden Playwright image size estimate to 500-700 MB range
  ([`da52ed7`](https://github.com/jschell/reddit-rss-cleaner/commit/da52ed74499f55738839a234b9ed21a456513587))

The +600 MB figure was a single-point estimate. Chromium is ~281 MB on disk and --with-deps pulls in
  200-400 MB of X11/graphics system libraries on a slim Debian base, putting actual overhead
  anywhere in the 500-700 MB range depending on Playwright version and base image.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Update Playwright image size to measured 1.8 GB
  ([`9f05b5f`](https://github.com/jschell/reddit-rss-cleaner/commit/9f05b5fbc8043c8265dfc03baf99c353c792724f))

Replaces the earlier estimate (+500-700 MB overhead) with the actual measured size of the published
  latest-playwright image.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

- Update standard image size to measured 260 MB
  ([`c729d71`](https://github.com/jschell/reddit-rss-cleaner/commit/c729d7135b70ab2bf0c9123cb9d3c5bb0bd10957))

Both image sizes are now based on actual published arm64 images: - latest: ~260 MB (was ~200 MB
  estimate) - latest-playwright: ~1.8 GB (unchanged)

Real Playwright overhead is ~1.5 GB, not the ~600 MB originally stated.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


## v0.3.4 (2026-03-20)

### Bug Fixes

- Bound trafilatura fetch with timeout and clarify budget warning
  ([`d05dca5`](https://github.com/jschell/reddit-rss-cleaner/commit/d05dca5dc57d31bffd411fca25c6bea0c4c69ce8))

_fetch_static ran in a thread executor with no timeout, allowing a slow site to silently consume the
  entire per-feed content budget before Playwright even got a chance. Wrap the executor call with
  asyncio.wait_for so each article's static fetch is bounded by the same `timeout` parameter used
  for Playwright.

Also fix the misleading "returning feed without content" log message: the code already returns
  content for any tasks that finished before the budget expired — only the still-pending tasks are
  dropped. The new message reports the count of timed-out articles vs. total.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu

### Documentation

- Document CONTENT_FETCH_BUDGET and PLAYWRIGHT_CONCURRENCY env vars
  ([`3180a87`](https://github.com/jschell/reddit-rss-cleaner/commit/3180a870dfb4d610913d755f1bc4147095de3dc1))

Add missing CONTENT_FETCH_BUDGET and PLAYWRIGHT_CONCURRENCY to the configuration table with
  descriptions explaining their relationship to CONTENT_TIMEOUT and Miniflux's CLIENT_TIMEOUT.

Update both compose examples to show the full recommended Playwright configuration including the new
  env vars, CLIENT_TIMEOUT on the Miniflux service, and a bind mount for the db volume.

https://claude.ai/code/session_01SF8NNxFnfLo3RBvSVuvBJu


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
