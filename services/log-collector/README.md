# Log Collector

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Tests: [tests/unit/log_collector](../../tests/unit/log_collector)

## Key Features
- Receives structured logs from services and stores in-memory for quick inspection.
- Provides listing/statistics endpoints for debugging.
- Standardized middlewares and health endpoints.

## Goal
- Minimal FastAPI service to ingest and aggregate logs across services.
- Provides stats and query endpoints for Reporting.

## Overview and role in the ecosystem
- Central aggregation point for development/testing logs without external dependencies.
- Enables quick debugging and dashboard-like summaries through `/logs` and `/stats`.

## Endpoints
| Method | Path        | Description |
|--------|-------------|-------------|
| GET    | /health     | Health check |
| POST   | /logs       | Ingest single log |
| POST   | /logs/batch | Ingest batch |
| GET    | /logs       | List logs (service, level, limit) |
| GET    | /stats      | Summary statistics |

## Config
- In-memory ring buffer, max 5,000 logs (adjust `_max_logs` in `main.py`).

## Environment
| Name | Description | Default |
|------|-------------|---------|
| PORT | Service port | 5080 |

## Run
- `uvicorn services.log_collector.main:app --reload --port 5080`

## Notes
- Dev/test only. Replace with external backend (e.g., Loki/ELK) later.

## Related
- Orchestrator: [../orchestrator/README.md](../orchestrator/README.md)

## Testing
- Unit tests: [tests/unit/log_collector](../../tests/unit/log_collector)
- Strategies:
  - Ensure per-test isolation of in-memory logs; fixtures may clear module state
  - Flexible stats expectations to account for accumulated logs in suite runs

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
