# CHANGELOG


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
