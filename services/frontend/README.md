# Frontend Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Tests: [tests/unit/frontend](../../tests/unit/frontend)

## Key Features
- Minimal UI for findings, search, quality, consolidation, and Jira staleness.
- Uses shared HTML helpers for consistent table/list rendering.
- Standard middlewares, `/info`, `/config/effective`, `/metrics`.

## Goal
- Provide a simple UI entry point to view findings and generate reports by calling backend services.

## Overview and role in the ecosystem
- Lightweight UI to visualize findings, quality metrics, and reports.
- Acts as a demo surface and operator dashboard backed by Orchestrator and Doc Store APIs.

## Endpoints (initial)
| Method | Path | Description |
|--------|------|-------------|
| GET | / | Landing page |
| GET | /findings | Render findings |
| GET | /report | Trigger report and render |

## Configuration
Config-first via `services/shared/config.get_config_value` with env override.

- `REPORTING_URL` (or `services.REPORTING_URL` in `config/app.yaml`)
- `CONSISTENCY_ENGINE_URL` (or `services.CONSISTENCY_ENGINE_URL` in `config/app.yaml`)
- `LOG_COLLECTOR_URL` (optional)

## Roadmap
- Replace simple HTML with a modern UI framework.
- AuthN/Z and role-based visibility.
- Live updates via websockets.

## Related
- Orchestrator: [../orchestrator/README.md](../orchestrator/README.md)
- Doc Store: [../doc-store/README.md](../doc-store/README.md)

## Testing
- Unit tests: [tests/unit/frontend](../../tests/unit/frontend)
- Strategies:
  - Endpoint rendering assumptions tested via mock backend data

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers: `services/shared/clients.py`.
