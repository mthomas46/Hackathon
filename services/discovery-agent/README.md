# Discovery Agent

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Tests: [tests/unit/discovery_agent](../../tests/unit/discovery_agent)

## Key Features
- Parses inline or remote OpenAPI specs and extracts endpoints.
- Self-registers services with the orchestrator registry.
- Supports in-process ASGI tests with `http://testserver`.
- Standardized middleware and clients.

## Goal
- Automatically discover service endpoints from OpenAPI and register them with the orchestrator.

## Overview and role in the ecosystem
- Automates registry population by parsing OpenAPI and informing the Orchestrator about live endpoints.
- Bridges between code/services and system discovery for downstream workflows and UI routing.

## Endpoints
| Method | Path      | Description |
|--------|-----------|-------------|
| GET    | /health   | Liveness |
| POST   | /discover | Fetch OpenAPI (optional), extract endpoints, register with orchestrator |

## Configuration
- `ORCHESTRATOR_URL` (default `http://orchestrator:5099`)
- `LOG_COLLECTOR_URL`: If set, emits structured logs to log-collector.

## Environment
| Name | Description | Default |
|------|-------------|---------|
| ORCHESTRATOR_URL | Orchestrator base URL | http://orchestrator:5099 |
| LOG_COLLECTOR_URL | Optional log endpoint | - |

## Usage
- Call `/discover` for each service (github-agent, jira-agent, confluence-agent, swagger-agent, consistency-engine, reporting, memory-agent, frontend).
- For services exposing OpenAPI (FastAPI), use `<base_url>/openapi.json`.

## Related
- Orchestrator: [../orchestrator/README.md](../orchestrator/README.md)

## Testing
- Unit tests: [tests/unit/discovery_agent](../../tests/unit/discovery_agent)
- Strategies:
  - Expect standardized error envelopes for validation/network errors
  - Validation: 422 for malformed JSON (FastAPI default)
  - Self-register and OpenAPI fetch paths with mock HTTP errors handled gracefully

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers: `services/shared/clients.py`.
