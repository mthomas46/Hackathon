# Doc Store

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Tests: [tests/unit/doc_store](../../tests/unit/doc_store)

## Key Features
- SQLite-backed store with FTS5 for document search and semantic fallback.
- Quality scoring (stale, redundant, low_views, missing_owner) and list APIs.
- Enveloped write endpoint `/documents/enveloped` and standard `/documents`.
- `/search`, `/documents/_list`, `/documents/quality`, `/info`, `/metrics`.

## Goal
- Persist documents and LLM/code analyses for deep and ensemble comparisons.
- Provide caching by content_hash/prompt/model and attach correlation metadata.

## Overview and role in the ecosystem
- System of record for content, analyses, and ensemble results.
- Powers search and quality signals for downstream services and UI.

> See also: [Glossary](../../docs/Glossary.md) · [Features & Interactions](../../docs/FEATURES_AND_INTERACTIONS.md)

## Storage
- Default: SQLite (file `services/doc-store/db.sqlite3`). Easy to swap for Postgres later.
- Tables:
  - documents(id, content, content_hash, metadata, created_at)
  - analyses(id, document_id, analyzer, model, prompt_hash, result, score, metadata, created_at)
  - ensembles(id, document_id, config, results, analysis, created_at)
- Indices for performance: content_hash (documents), document_id/prompt_hash/created_at (analyses).

### Postgres migration (suggested)
- Replace SQLite with Postgres by:
  - Running a Postgres container and providing `DOCSTORE_DB=postgresql://user:pass@host:5432/dbname`
  - Using an async driver (e.g., `asyncpg` + SQLAlchemy) and migrating table creation.
  - Adding proper migrations (Alembic) for schema evolution.

## Endpoints
| Method | Path                     | Description |
|--------|--------------------------|-------------|
| GET    | /health                  | Health check |
| POST   | /documents               | Create document |
| POST   | /documents/enveloped     | Strict DocumentEnvelope write |
| GET    | /documents/{id}          | Get by id |
| POST   | /analyses                | Create analysis |
| GET    | /analyses?document_id=   | List analyses for document |
| GET    | /search?q=               | FTS with semantic fallback |
| GET    | /documents/quality       | Quality signals |
| PATCH  | /documents/{id}/metadata | Patch metadata |

## Related
- Orchestrator: [../orchestrator/README.md](../orchestrator/README.md)
- Analysis Service: [../analysis-service/README.md](../analysis-service/README.md)

## Testing
- Unit tests: [tests/unit/doc_store](../../tests/unit/doc_store)
- Strategies:
  - Flexible assertions for success envelopes vs direct data
  - Handle `/documents/_list` vs nested `data.items` responses in mocks
  - FTS `/search` results presence rather than exact IDs in all scenarios

## Integration
- Emits `docs.stored` DocumentEnvelope on create (if `REDIS_HOST` set).
- Designed to be called by orchestrator/consistency-engine/reporting.

## Config
Configuration is config-first via `services/shared/config.get_config_value`.

- `DOCSTORE_DB` (or `doc_store.db_path` in `config/app.yaml`): DB path/DSN (default `services/doc-store/db.sqlite3`)
- `REDIS_HOST` (or `redis.host` in `config/app.yaml`): optional publish of envelope events
- `DOC_STORE_URL` (or `services.DOC_STORE_URL` in `config/app.yaml`): base URL for this service

See `config/app.yaml` for central defaults.

## Environment
| Name | Description | Default |
|------|-------------|---------|
| DOCSTORE_DB | Database path/DSN | services/doc-store/db.sqlite3 |
| REDIS_HOST | Optional Redis for events | - |
| DOC_STORE_URL | Base URL for this service | - |

## Secrets
- Read secrets with `services/shared/credentials.get_secret(name)`.
- Provide via env or Docker/K8s secrets; keep out of git.

## Notes
- For higher concurrency/scale, migrate to Postgres and use async drivers.
