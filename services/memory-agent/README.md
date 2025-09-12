# Memory Agent

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Tests: [tests/unit/memory_agent](../../tests/unit/memory_agent)

## Key Features
- Lightweight in-memory store for operational context and summaries.
- TTL and max-items configurable; simple list APIs for debugging.
- Standard request ID and metrics middleware.

## Goal
- Provide short-term memory for ecosystem operations, LLM summaries, and document/API summaries. Acts as the main operational "memory" and "context" store.

## Overview and role in the ecosystem
- Temporary, queryable context store for summaries and operational breadcrumbs.
- Helps correlate events and findings across services and timelines.

## Endpoints (initial)
| Method | Path                 | Description |
|--------|----------------------|-------------|
| GET    | /health              | Liveness and count |
| POST   | /memory/put          | Store a MemoryItem |
| GET    | /memory/list         | List recent memory items (type, key, limit) |

## Integration
- Emits structured logs to `log-collector` when `LOG_COLLECTOR_URL` is set.

## Related
- Log Collector: [../log-collector/README.md](../log-collector/README.md)

## Testing
- Unit tests: [tests/unit/memory_agent](../../tests/unit/memory_agent)
- Strategies:
  - Validate TTL and list filters via mock items

## Events
- Subscribes to: `ingestion.requested`, `docs.ingested.*`, `apis.ingested.swagger`, `findings.created`.
- Appends summaries to in-memory ring buffer (configurable `_max_items`).

## Future
- Add TTL/expiration, persistence (e.g., Redis/SQLite), semantic search, and query DSL.

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
