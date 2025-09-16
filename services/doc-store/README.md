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
| POST   | /documents/{id}/tags | Tag document |
| GET    | /documents/{id}/tags | Get document tags |
| POST   | /search/tags | Search by tags |
| GET    | /tags/statistics | Tag statistics |
| POST   | /taxonomy/nodes | Create taxonomy node |
| GET    | /taxonomy/tree | Get taxonomy tree |
| POST   | /bulk/documents | Bulk document creation |
| POST   | /bulk/search | Bulk search operations |
| POST   | /bulk/tag | Bulk document tagging |
| GET    | /bulk/operations/{id} | Bulk operation status |
| GET    | /bulk/operations | List bulk operations |
| POST   | /bulk/operations/{id}/cancel | Cancel bulk operation |
| POST   | /webhooks | Register webhook |
| GET    | /webhooks | List webhooks |
| POST   | /events | Emit event |
| GET    | /events | Event history |
| GET    | /webhooks/deliveries | Webhook deliveries |
| GET    | /notifications/stats | Notification stats |
| POST   | /webhooks/{id}/test | Test webhook |
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

## Semantic Tagging & Taxonomy

The doc-store provides advanced semantic tagging capabilities for intelligent content classification and discovery:

### Automatic Tagging
- **Content Analysis**: Extracts entities like programming languages, frameworks, URLs, emails, and file types
- **Metadata Tagging**: Uses document metadata for high-confidence tag generation
- **Confidence Scoring**: Weighted tagging with confidence metrics for quality assessment
- **Category Classification**: Tags organized by categories (programming_language, framework, technical_domain, etc.)

### Semantic Search
- **Tag-Based Search**: Find documents by semantic tags with confidence filtering
- **Category Filtering**: Narrow searches by tag categories
- **Multi-Tag Queries**: Combine multiple tags for precise content discovery
- **Tag Analytics**: Statistics on tag distribution and coverage

### Taxonomy Management
- **Hierarchical Organization**: Parent-child relationships between tags
- **Synonym Support**: Multiple terms mapping to the same concept
- **Category Structure**: Organized tag hierarchies by domain
- **Description Metadata**: Rich descriptions for tag meanings and usage

### Tagging Endpoints
- **POST /documents/{id}/tags**: Automatically tag a document with semantic information
- **GET /documents/{id}/tags**: Retrieve tags for a document with category filtering
- **POST /search/tags**: Search documents by semantic tags with advanced filtering
- **GET /tags/statistics**: Comprehensive tag analytics and usage statistics
- **POST /taxonomy/nodes**: Create taxonomy nodes with descriptions and relationships
- **GET /taxonomy/tree**: Navigate hierarchical tag taxonomy structure

### Automatic Tagging Process
Documents are automatically tagged during creation with:
- Programming languages detected in code blocks
- Frameworks and libraries identified in imports
- Technical domains extracted from content
- File types and extensions recognized
- URLs and external references categorized
- Document types and content characteristics classified

## Bulk Operations & Batch Processing

The doc-store provides high-performance bulk operations for efficient large-scale document management and processing.

### Bulk Document Operations
- **Bulk Creation**: Create multiple documents concurrently with progress tracking
- **Batch Processing**: Asynchronous processing with configurable concurrency limits
- **Error Handling**: Comprehensive error reporting and partial success handling
- **Progress Monitoring**: Real-time status updates and operation tracking

### Batch Search & Analysis
- **Bulk Search**: Execute multiple search queries simultaneously
- **Concurrent Processing**: Parallel search operations for optimal performance
- **Result Aggregation**: Unified result handling with metadata preservation
- **Resource Management**: Controlled concurrency to prevent system overload

### Bulk Tagging Operations
- **Mass Tagging**: Apply semantic tagging to multiple documents at once
- **Progress Tracking**: Monitor tagging progress across large document sets
- **Error Recovery**: Continue processing after individual failures
- **Performance Optimization**: Batched database operations for efficiency

### Operation Management
- **Status Monitoring**: Real-time progress tracking for all bulk operations
- **Operation History**: Complete audit trail of bulk operations
- **Cancellation Support**: Stop running operations to conserve resources
- **Result Retrieval**: Access detailed results and error reports

### Bulk Operations Endpoints
- **POST /bulk/documents**: Create multiple documents with progress tracking
- **POST /bulk/search**: Execute multiple search queries concurrently
- **POST /bulk/tag**: Tag multiple documents with semantic information
- **GET /bulk/operations/{id}**: Monitor specific bulk operation progress
- **GET /bulk/operations**: List and filter bulk operations by status
- **POST /bulk/operations/{id}/cancel**: Cancel running bulk operations

### Performance Characteristics
- Configurable concurrency limits (default: 10 concurrent operations)
- Batch size optimization (default: 100 items per batch)
- Memory-efficient processing with streaming result handling
- Automatic resource cleanup and connection management
- Comprehensive error handling and recovery mechanisms

## Real-Time Notifications & Webhooks

The doc-store provides comprehensive real-time notification capabilities for event-driven integrations and external system synchronization.

### Event System
- **Event Types**: document.created, document.updated, document.deleted, analysis.completed, lifecycle.transition
- **Event Metadata**: Rich context information including timestamps, user IDs, and entity details
- **Event History**: Complete audit trail of all system events with filtering and pagination
- **Real-Time Processing**: Asynchronous event emission and processing

### Webhook Management
- **Webhook Registration**: Configure HTTP endpoints for event delivery
- **Event Filtering**: Subscribe to specific event types and entity types
- **Security**: HMAC signature verification for webhook authenticity
- **Retry Logic**: Automatic retry with exponential backoff for failed deliveries
- **Delivery Tracking**: Comprehensive logging of delivery attempts and responses

### Delivery System
- **Asynchronous Delivery**: Non-blocking webhook delivery to prevent system slowdown
- **Concurrent Processing**: Parallel delivery to multiple webhooks
- **Timeout Management**: Configurable timeouts for webhook responses
- **Error Handling**: Detailed error reporting and failure analysis
- **Success Monitoring**: Delivery success rates and performance metrics

### Notification Statistics
- **Event Analytics**: Event type distribution and frequency analysis
- **Delivery Metrics**: Success rates, response times, and failure patterns
- **Webhook Performance**: Individual webhook delivery statistics
- **System Health**: Notification system monitoring and alerting
- **Failure Analysis**: Recent failures and error pattern identification

### Event Types
- **Document Events**: created, updated, deleted, versioned, tagged
- **Analysis Events**: completed, failed, quality_checked
- **Lifecycle Events**: archived, deleted, policy_applied
- **Relationship Events**: linked, unlinked, graph_updated
- **Bulk Operation Events**: started, completed, failed

### Webhook Features
- **Custom Headers**: Support for authentication and custom headers
- **Event Matching**: Flexible event type and entity filtering
- **Signature Verification**: HMAC-SHA256 signature validation
- **Retry Configuration**: Customizable retry counts and timeouts
- **Active/Inactive Status**: Enable/disable webhooks without deletion

### Integration Patterns
- **External Systems**: Real-time synchronization with external applications
- **Monitoring Systems**: Alert generation and dashboard updates
- **Audit Systems**: Compliance and security event forwarding
- **Workflow Triggers**: Automated business process initiation
- **Data Pipelines**: Event-driven data processing and ETL operations

### Notification Endpoints
- **POST /webhooks**: Register new webhook endpoints for event delivery
- **GET /webhooks**: List all configured webhooks and their settings
- **POST /events**: Manually emit events for testing and integration
- **GET /events**: Retrieve event history with advanced filtering
- **GET /webhooks/deliveries**: Monitor webhook delivery success and failures
- **GET /notifications/stats**: Comprehensive notification system analytics
- **POST /webhooks/{id}/test**: Test webhook configuration and connectivity

### Security & Reliability
- **Authentication**: Webhook signature verification for secure delivery
- **Rate Limiting**: Protection against webhook endpoint overload
- **Circuit Breaking**: Automatic failure detection and recovery
- **Audit Logging**: Complete delivery history for compliance
- **Error Isolation**: Individual webhook failures don't affect others

## Notification Service Integration

The doc-store integrates with the centralized notification service for enterprise-grade notification management and delivery.

### Notification Service Features
- **Centralized Notification Management**: All notifications routed through dedicated notification service
- **Owner Resolution**: Automatic mapping of owners to notification targets (email, Slack, webhooks)
- **Deduplication**: Prevents spam by suppressing duplicate notifications within time windows
- **Dead Letter Queue**: Failed notifications automatically queued for retry or analysis
- **Multi-Channel Support**: Webhook, email, and Slack notification channels

### Integration Architecture
- **Event Emission**: Doc-store emits structured events for all significant operations
- **Webhook Registration**: Webhooks configured in doc-store but delivered via notification service
- **Owner Resolution**: Automatic resolution of owners to notification targets
- **Delivery Tracking**: Comprehensive delivery history and success/failure tracking
- **Fallback Support**: Local delivery mechanisms when notification service unavailable

### Supported Event Types
- **Document Events**: `document.created`, `document.updated`, `document.deleted`
- **Analysis Events**: `analysis.completed`, `analysis.failed`, `analysis.quality_checked`
- **Lifecycle Events**: `lifecycle.archived`, `lifecycle.deleted`, `lifecycle.policy_applied`
- **Relationship Events**: `relationship.created`, `relationship.updated`
- **Bulk Operation Events**: `bulk.started`, `bulk.completed`, `bulk.failed`

### Notification Service Endpoints Integration
- **POST /notify**: Direct notification sending through notification service
- **POST /owners/resolve**: Owner to notification target resolution
- **GET /dlq**: Dead letter queue access for failed notifications
- **POST /owners/update**: Owner registry management

### Delivery Flow
1. **Event Emission**: Doc-store emits events for system operations
2. **Webhook Matching**: Registered webhooks matched against event types
3. **Notification Service**: Webhook delivery routed through notification service
4. **Deduplication**: Notification service prevents duplicate notifications
5. **Retry Logic**: Failed deliveries automatically retried with exponential backoff
6. **DLQ Management**: Persistent failures moved to dead letter queue

### Configuration
- **NOTIFICATION_SERVICE_URL**: URL of the notification service (default: http://notification-service:5210)
- **Webhook Configuration**: Webhooks registered through doc-store API but delivered via notification service
- **Owner Mapping**: Owner resolution handled by notification service with caching

### Benefits of Integration
- **Centralized Management**: All notifications managed through single service
- **Enterprise Features**: Deduplication, DLQ, owner resolution built-in
- **Scalability**: Notification service can handle high-volume notification loads
- **Reliability**: Robust retry mechanisms and failure handling
- **Audit Trail**: Complete notification history and delivery tracking

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
