# Code Style and Conventions

## General Principles
- **Naming**: Use descriptive variable names; functions are verbs, variables are nouns
- **Types**: Prefer explicit function signatures for exported APIs; avoid `any`-like erasure
- **Control Flow**: Prefer early returns and shallow nesting; handle error cases first
- **Comments**: Add concise docstrings for non-trivial functions; explain why, not how

## Project-Specific Patterns

### Service Structure
- All services use FastAPI with standard middleware
- Health endpoints: `/health` (required), `/ready` (optional)
- Info endpoints: `/info` for service metadata
- Registry endpoints for service discovery via Orchestrator

### HTTP and API Patterns
- Use `services/shared/clients.py` `ServiceClients` for JSON APIs (includes timeouts, retries, circuit-breaker)
- Keep raw `httpx` only when text/headers are required
- Apply envelope patterns from `services/shared/envelopes.py` with `version_tag="v1"`

### Configuration and Constants
- Load config with `services/shared/config.py` and environment overrides
- Reuse common keys from `services/shared/constants.py`
- Environment variable names centralized in `services/shared/constants.py`

### Middleware and Observability
- Use `RequestIdMiddleware` and `RequestMetricsMiddleware` in all services
- Emit structured logs with service, operation, latency, and correlation id
- Standard envelope responses for success/error

### Testing Conventions
- Tests in `tests/unit/<service>/` structure
- Use helpers in `tests/helpers/` for repeated patterns
- Prefer parameterized tests for similar behaviors
- Health checks: always assert `200` and expected JSON keys
- Use pytest markers from `pytest.ini` (unit, integration, slow, live, etc.)

### HTML and Frontend
- Compose with helpers in `services/shared/html.py` and `services/frontend/utils.py`

## File Organization
- Shared utilities in `services/shared/`
- Service-specific code in `services/<service-name>/`
- Tests mirror service structure under `tests/unit/<service>/`
- Documentation in `docs/` with clear category separation