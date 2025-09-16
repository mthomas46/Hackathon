# Doc Store

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

Tests: [tests/unit/doc_store](../../tests/unit/doc_store)

## Key Features
- SQLite-backed store with FTS5 for document search and semantic fallback.
- Advanced analytics and insights with storage trends, quality metrics, and temporal analysis.
- Enhanced search with filtering, faceting, sorting, and metadata-based queries.
- Quality scoring (stale, redundant, low_views, missing_owner) and list APIs.
- Enveloped write endpoint `/documents/enveloped` and standard `/documents`.
- `/search`, `/search/advanced`, `/analytics`, `/analytics/summary`, `/documents/_list`, `/documents/quality`, `/info`, `/metrics`.

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
| GET    | /info                    | Service information |
| GET    | /config/effective        | Effective configuration |
| GET    | /metrics                 | Service metrics |
| POST   | /documents               | Create document |
| POST   | /documents/enveloped     | Strict DocumentEnvelope write |
| GET    | /documents/{id}          | Get by id |
| PATCH  | /documents/{id}/metadata | Patch metadata |
| GET    | /documents/_list         | List recent documents |
| POST   | /analyses                | Create analysis |
| GET    | /analyses?document_id=   | List analyses for document |
| GET    | /search?q=               | FTS with semantic fallback |
| POST   | /search/advanced         | Advanced search with filters/facets |
| GET    | /documents/quality       | Quality signals |
| GET    | /analytics               | Comprehensive analytics |
| GET    | /analytics/summary       | Analytics summary with insights |
| GET    | /style/examples          | List style examples |
| GET    | /documents/{id}/versions | Get document versions |
| GET    | /documents/{id}/versions/{n} | Get specific version |
| GET    | /documents/{id}/versions/{a}/compare/{b} | Compare versions |
| POST   | /documents/{id}/rollback | Rollback to version |
| POST   | /documents/{id}/versions/cleanup | Cleanup old versions |
| POST   | /relationships | Add relationship |
| GET    | /documents/{id}/relationships | Get document relationships |
| GET    | /graph/paths/{start}/{end} | Find relationship paths |
| GET    | /graph/statistics | Graph statistics |
| POST   | /documents/{id}/relationships/extract | Extract relationships |
| GET    | /cache/stats | Cache statistics |
| POST   | /cache/invalidate | Invalidate cache |
| POST   | /cache/warmup | Warm up cache |
| POST   | /cache/optimize | Optimize cache |

## Related
- Orchestrator: [../orchestrator/README.md](../orchestrator/README.md)
- Analysis Service: [../analysis-service/README.md](../analysis-service/README.md)

## Testing
- Unit tests: [tests/unit/doc_store](../../tests/unit/doc_store)
- Strategies:
  - Flexible assertions for success envelopes vs direct data
  - Handle `/documents/_list` vs nested `data.items` responses in mocks
  - FTS `/search` results presence rather than exact IDs in all scenarios

## Analytics & Insights

The doc-store provides comprehensive analytics capabilities to understand document storage patterns, quality trends, and ecosystem usage:

### Analytics Endpoints
- **GET /analytics**: Detailed analytics with configurable time periods
  - Storage statistics (size, compression, distribution)
  - Quality metrics (analysis coverage, staleness, model performance)
  - Temporal trends (creation rates, analysis patterns)
  - Content insights (duplication, source distribution, most analyzed documents)
  - Relationship insights (analysis coverage, collaboration patterns)

- **GET /analytics/summary**: High-level summary with key insights and recommendations
  - Executive summary of storage and quality metrics
  - Automated insights based on patterns and trends
  - Actionable recommendations for optimization

### Advanced Search
- **POST /search/advanced**: Powerful search with filtering and faceting
  - Full-text search with FTS5 and semantic fallback
  - Metadata filtering (content_type, source_type, language, tags)
  - Date range filtering and analysis status filtering
  - Multiple sorting options (relevance, date, size, analysis count)
  - Pagination and faceted results for enhanced discovery
  - Rich result metadata (analysis counts, scores, content length)

### Quality Assessment
- **GET /documents/quality**: Intelligent quality scoring and issue detection
  - Stale content identification based on configurable thresholds
  - Low-signal content detection
  - Missing metadata and incomplete document flagging
  - Priority scoring for maintenance focus

## Document Versioning & History

The doc-store provides comprehensive document versioning capabilities to track changes, enable rollbacks, and maintain audit trails:

### Version Control Features
- **Automatic Versioning**: Every document update creates a new version automatically
- **Complete History**: Full version history with content, metadata, and change tracking
- **Version Comparison**: Side-by-side comparison of any two versions
- **Rollback Support**: Ability to revert documents to previous versions
- **Version Cleanup**: Automated cleanup of old versions to manage storage

### Versioning Endpoints
- **GET /documents/{id}/versions**: Retrieve complete version history for a document
  - Pagination support for large version histories
  - Includes version numbers, change summaries, timestamps, and content sizes

- **GET /documents/{id}/versions/{n}**: Get full content and metadata for a specific version
  - Complete document restoration capabilities
  - Metadata and content integrity verification

- **GET /documents/{id}/versions/{a}/compare/{b}**: Compare any two versions
  - Content diff highlighting
  - Metadata change tracking
  - Size and hash comparisons

- **POST /documents/{id}/rollback**: Rollback document to specified version
  - Creates new version record for rollback operation
  - Maintains complete audit trail
  - Optional attribution for change tracking

- **POST /documents/{id}/versions/cleanup**: Manage version storage
  - Configurable retention policies
  - Automatic cleanup of old versions
  - Storage optimization for large document histories

### Version Metadata
Each version tracks:
- Version number (sequential)
- Content hash for integrity
- Full content and metadata snapshots
- Change summary and attribution
- Timestamp and correlation data
- Content size for storage tracking

## Document Relationship Graph

The doc-store provides comprehensive relationship mapping and graph analysis capabilities to understand document interconnections and dependencies:

### Relationship Types
- **references**: Document mentions or links to other documents
- **derived_from**: Document created from or based on another document
- **correlated**: Documents sharing correlation IDs or related contexts
- **analyzed_by**: Analysis results linked to source documents
- **external_reference**: Links to external URLs and resources

### Graph Analysis Features
- **Automatic Relationship Extraction**: Content analysis discovers document references and dependencies
- **Graph Traversal**: Find connection paths between any two documents
- **Relationship Queries**: Explore incoming/outgoing relationships with filtering
- **Graph Statistics**: Comprehensive network analysis including connectivity and density metrics
- **Strength Scoring**: Weighted relationships based on relevance and importance

### Relationship Endpoints
- **POST /relationships**: Manually create relationships between documents
- **GET /documents/{id}/relationships**: Query relationships for specific documents
- **GET /graph/paths/{start}/{end}**: Discover connection paths through the graph
- **GET /graph/statistics**: Network analysis and connectivity metrics
- **POST /documents/{id}/relationships/extract**: Auto-extract relationships from existing documents

### Cache Performance Layer

The doc-store includes a high-performance caching system for optimal query performance:

### Caching Features
- **Redis Integration**: Distributed caching with configurable memory limits
- **Intelligent Invalidation**: Tag-based cache invalidation for data consistency
- **Performance Monitoring**: Hit rates, response times, and memory usage tracking
- **Fallback Support**: Local caching when Redis unavailable
- **Warm-up Capabilities**: Preload frequently accessed data

### Cache Management
- **GET /cache/stats**: Comprehensive performance metrics and statistics
- **POST /cache/invalidate**: Selective cache clearing by tags or operations
- **POST /cache/warmup**: Preload critical data for performance
- **POST /cache/optimize**: Memory optimization and cleanup operations

## Integration
- Emits `docs.stored` DocumentEnvelope on create (if `REDIS_HOST` set).
- Designed to be called by orchestrator/consistency-engine/reporting.
- Analytics data supports monitoring dashboards and automated insights.
- Advanced search powers intelligent document discovery across the ecosystem.
- Versioning enables collaborative workflows and change management across services.
- Relationship graph supports dependency analysis and knowledge mapping.
- Caching layer ensures high performance for large document collections.

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
