### Project Code Style and Standards

This document summarizes conventions used across services, tests, and shared utilities.

- Naming
  - Use descriptive variable names; avoid 1–2 character names.
  - Functions are verbs; variables are nouns. Modules group coherent behaviors.
  - Environment variable names are centralized in `services/shared/constants.py`.

- Types
  - Prefer explicit function signatures for exported APIs.
  - Avoid `any`-like erasure for public-facing interfaces.

- Control flow
  - Prefer early returns and shallow nesting.
  - Handle error cases first; catch exceptions narrowly and continue safely.

- Comments and docstrings
  - Add concise docstrings for non-trivial functions and modules.
  - Explain why, not how; avoid restating obvious code.

- HTTP calls
  - Use `services/shared/clients.py` `ServiceClients` for JSON APIs (timeouts, retries, circuit-breaker).
  - Keep raw `httpx` only when text/headers are required (e.g., CODEOWNERS, http cache).

- Config and constants
  - Load with `services/shared/config.py` and environment overrides.
  - Reuse common keys from `services/shared/constants.py`.

- Envelopes and validation
  - Use `services/shared/envelopes.py` with `version_tag="v1"`.
  - Apply `validate_envelope` to ingress endpoints as appropriate.

- Logging and metrics
  - Use `RequestIdMiddleware` and `RequestMetricsMiddleware` in all services.
  - Emit structured logs with service, operation, latency, and correlation id.

- Tests
  - Group tests by service or feature; add module docstrings.
  - Use helpers in `tests/helpers` for repeated patterns (assertions, payloads).
  - Prefer parameterized tests for similar behaviors.

- HTML rendering
  - Compose with helpers in `services/shared/html.py` and `services/frontend/utils.py`.

This document is a living standard; update it as the codebase evolves.


