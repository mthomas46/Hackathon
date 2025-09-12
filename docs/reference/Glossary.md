# Glossary of Terms and Technologies

> A high-signal reference for concepts, contracts, and technologies used across the Documentation Consistency Ecosystem.

## Core Concepts
- **Orchestrator**: Control-plane service coordinating workflows, maintaining a simple service registry, and proxying report/summarization requests.
- **Agents**: Source-specific services (GitHub, Jira, Confluence, Swagger) that normalize external data into internal formats.
- **Consistency Engine (CE)**: Batch analyzer that detects inconsistencies across normalized documents and API schemas.
- **Reporting**: Aggregates findings into reports (life-of-ticket, trends, consolidation) and surfaces notification workflows.
  - Includes Jira Staleness: detects outdated or duplicate Jira tickets using doc-store quality, light semantic overlap, and CE references; optional summary via summarizer-hub.
- **Doc Store**: Lightweight SQLite store for documents/analyses; provides search (FTS), quality signals, and listing APIs.
- **Frontend**: Minimal portal to browse findings, trends, search, and quality signals.

## Canonical Data Models
- **Document**: Normalized source content (e.g., GitHub README, Jira issue, Confluence page) with `content`, `content_hash`, and `metadata`.
- **ApiSchema**: Normalized OpenAPI/Swagger schema with `endpoints` list and versioning.
- **Finding**: Output from CE; includes `type`, `severity`, `description`, `source_refs`, `score`, and `correlation_id`.
- **Envelope**: Stable contract wrapper for inter-service exchange.

### Envelopes (v1)
| Envelope | Required fields |
|---|---|
| `DocumentEnvelope` | `id`, `version_tag` (v1), `timestamp`, `content_hash`, `document{}` |
| `ApiSchemaEnvelope` | `id`, `version_tag` (v1), `timestamp`, `content_hash`, `schema{}` |

```json
{
  "id": "github:org/repo:readme",
  "version_tag": "v1",
  "correlation_id": "abc-123",
  "source_refs": [{"repo": "org/repo"}],
  "content_hash": "...",
  "timestamp": "2025-09-05T12:00:00Z",
  "document": { "id": "github:org/repo:readme", "source_type": "github", "content": "..." }
}
```

## Observability and Operations
- **Correlation ID**: `X-Correlation-ID` propagated across calls.
- **Trace ID**: Lightweight ID added to Redis messages for correlation.
- **Readiness**: `/ready` indicates startup complete (orchestrator, CE).
- **Request Metrics**: Middleware logs route, status, latency, corr-id.
- **Structured Logs**: CE emits per-detector `duration_ms` and `count`.

## Resilience
- **ServiceClients**: Shared httpx-based client with:
  - `HTTP_CLIENT_TIMEOUT` (seconds)
  - `HTTP_RETRY_ATTEMPTS`, `HTTP_RETRY_BASE_MS`
  - `HTTP_CIRCUIT_ENABLED` toggle (with CircuitBreaker wrapper)
- **Backpressure**: CE dedupes, debounces, and caps batch sizes (spillover future).

## Notifications and Ownership
- **Owners**: Derived from metadata: `owner`, `code_owner`, `repo_owner`, `jira_assignee`, `jira_reporter`, `confluence_created_by`, `confluence_last_updated_by`, `confluence_space_owner`.
- **Notification Service**: Resolves owners to targets (`/owners/resolve`), deduplicates sends, and records DLQ for failures.

## Events and Topics (Redis)
- `docs.ingested.github|jira|confluence`
- `apis.ingested.swagger`
- `findings.created` (includes `trace_id`, `severity_counts`)

## Technologies
- **FastAPI**, **Pydantic**, **httpx** (Python web + typing + HTTP)
- **Redis** (asyncio pub/sub)
- **SQLite** with **FTS5** (Doc-store search)
- **Ollama** (local LLM), optional **AWS Bedrock** (via proxy)

## Common Headers
| Header | Purpose |
|---|---|
| `X-Correlation-ID` | End-to-end trace of a logical request |

## Status/Health Endpoints
| Service | Health | Readiness | Metrics |
|---|---|---|---|
| Orchestrator | `/health` | `/ready` | - |
| Consistency Engine | `/health` | `/ready` | `/metrics` |
| Others | `/health` | (as applicable) | - |
