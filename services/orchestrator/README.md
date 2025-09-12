# Orchestrator Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Tests: [tests/unit/orchestrator](../../tests/unit/orchestrator)

## Key Features
## API
| Method | Path | Description |
|--------|------|-------------|
| GET | /health/system | System health |
| GET | /workflows | List workflows |
| GET | /info | Service info |
| GET | /config/effective | Effective config |
| GET | /metrics | Metrics |
| GET | /ready | Readiness |
| POST | /ingest | Request ingestion |
| POST | /workflows/run | Trigger ingestion workflow |
| POST | /demo/e2e | Demo bundle |
| POST | /registry/register | Register a service |
| GET | /registry | List services |
| GET | /infrastructure/dlq/stats | DLQ stats |
| POST | /infrastructure/dlq/retry | DLQ retry |
| GET | /infrastructure/saga/stats | Saga stats |
| GET | /infrastructure/saga/{saga_id} | Saga by id |
| GET | /infrastructure/events/history | Event history |
| POST | /infrastructure/events/replay | Replay events |
| GET | /infrastructure/tracing/stats | Tracing stats |
| GET | /infrastructure/tracing/trace/{trace_id} | Trace by id |
| GET | /infrastructure/tracing/service/{service_name} | Traces for service |
| POST | /infrastructure/events/clear | Clear events |
| GET | /peers | Orchestrator peers |
| POST | /registry/poll-openapi | Poll OpenAPI |
| GET | /workflows/history | Workflow history |
| POST | /jobs/recalc-quality | Recalc quality |
| POST | /jobs/notify-consolidation | Notify consolidation |
| POST | /docstore/save | Save to doc store |

## Environment
| Name | Description | Default |
|------|-------------|---------|
| REDIS_HOST | Redis host for events | redis |
| REPORTING_URL | Reporting base URL | http://reporting:5030 |
| ORCHESTRATOR_PEERS | Comma-separated peers | - |
| DOC_STORE_URL | Doc Store URL | - |
| NOTIFICATION_URL | Notification service URL | http://notification-service:5095 |
- Service registry with peer replication and `/peers` listing.
- Workflow endpoints and scheduled jobs (`/jobs/*`).
- Emits Redis events with trace IDs when configured.
- `/info`, `/config/effective`, `/metrics`, health/ready endpoints.

## Goal
- Coordinate ingestion workflows across agents (GitHub, Jira, Confluence, Swagger) and trigger analyses in the Consistency Engine.
- Act as the control plane API for scheduling, on-demand runs, and status.

## Overview and role in the ecosystem
- Acts as the central control plane: service registry, workflow runner, and operational endpoints.
- Provides eventing, DLQ management, tracing, and peer replication to keep the mesh healthy.
- Exposes job endpoints to kick off cross-service operations (quality recalculation, consolidation notifications).

> See also: [Glossary](../../docs/Glossary.md) · [Features & Interactions](../../docs/FEATURES_AND_INTERACTIONS.md)

## Endpoints (initial)
- `GET /health`: Liveness.
- `GET /ready`: Readiness.
- `POST /ingest`: Request ingestion `{source, scope, correlation_id}` (adds `trace_id`).
- `POST /workflows/run`: Trigger multi-source ingestion.
- `POST /registry/register`: Register a service.
- `GET /registry`: List registered services.
- `POST /registry/sync-peers`: Replicate registry to peer orchestrators.
- `POST /registry/poll-openapi`: Poll OpenAPI and compute drift.
- `POST /report/request`: Proxy to reporting service (`generate`, `life_of_ticket`, `pr_confidence`).
- `POST /summarization/suggest`: Policy-aware summarization via `secure-analyzer`.
- `POST /demo/e2e`: Returns a bundle `{ summary, log_analysis }` using reporting endpoints.

## Configuration
Configuration is config-first via `services/shared/config.get_config_value` with precedence: env > `config/app.yaml` > defaults.

- `PORT`: Service port (default 5099).
- `REPORTING_URL`: Base URL for reporting (default `http://reporting:5030`).
- `REDIS_HOST`: Redis hostname for events (optional).
- `ORCHESTRATOR_PEERS`: Comma-separated peer base URLs (also supported under `orchestrator.ORCHESTRATOR_PEERS` in `config/app.yaml`).
- `LOG_COLLECTOR_URL`: If set, emits structured logs to log-collector.

See also: `config/app.yaml` sections `services`, `redis`, `orchestrator`.

## Secrets
- Use `services/shared/credentials.get_secret(name)` to read secrets (env/secret backends).
- Pass secrets via env or Docker/K8s secrets; do not commit to git.

## Run locally

```bash
# Dev stack with live code
docker compose -f docker-compose.dev.yml up -d orchestrator redis

curl http://localhost:5099/health
```

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers (timeouts/retries/circuit): `services/shared/clients.py`.

## Demo: /demo/e2e
Example:
```bash
curl -s -X POST "$ORCHESTRATOR_URL/demo/e2e" -H 'content-type: application/json' -d '{"format":"json","log_limit":50}' | jq .
```
Response shape:
```json
{
  "summary": {"total": 3, "by_severity": {"low":2, "med":1}},
  "log_analysis": {"overview": {"count": 12, "by_level": {"info":9, "warn":2, "error":1}}, "sample": [ {"service":"orchestrator", "level":"info", "message":"workflow run requested"} ]}
}
```

## Roadmap
- Track workflow status and surface metrics.
- AuthN/Z for operator endpoints.
- End-to-end job that collects logs and returns a Log Analysis report.

## Related
- Doc Store: [../doc-store/README.md](../doc-store/README.md)
- Source Agent: [../source-agent/README.md](../source-agent/README.md)
- Analysis Service: [../analysis-service/README.md](../analysis-service/README.md)

## Testing
- Unit tests: [tests/unit/orchestrator](../../tests/unit/orchestrator)
- Strategies:
  - Registry endpoints (`/registry/*`) with envelope-aware assertions
  - Health/ready checks and config endpoints
  - Workflows/jobs stubs with flexible response validation
