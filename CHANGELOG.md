# CHANGELOG


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
