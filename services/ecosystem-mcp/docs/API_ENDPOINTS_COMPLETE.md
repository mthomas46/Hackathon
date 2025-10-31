---
title: "Ecosystem MCP - Complete API Reference"
service: "ecosystem-mcp"
category: "api"
tags: ["api", "endpoints", "rest", "reference", "openapi"]
related: ["architecture/OVERVIEW.md", "../guides/QUICK_START.md"]
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
---

# Ecosystem MCP - Complete API Reference

**Comprehensive REST API documentation for Ecosystem MCP Service**

---

## 📊 API Statistics

**Based on actual codebase audit (2025-10-28)**:

- **Total Endpoints**: 273 endpoints
- **Route Modules**: 51 route files
- **API Version**: v1
- **Base URL**: `http://localhost:8000`
- **Documentation**: `/docs` (Swagger UI), `/redoc` (ReDoc)
- **OpenAPI Spec**: `/openapi.json`

---

## 🗂️ API Categories

### 1. Health & Monitoring (6 endpoints)
- `GET /health` - Basic health check
- `GET /health/deep` - Deep health check with dependencies
- `GET /health/workers` - Worker health status
- `GET /metrics` - Prometheus metrics
- `GET /api/v1/admin/stats` - Service statistics
- `GET /api/v1/monitoring/system` - System monitoring

### 2. Standard Endpoints (4 endpoints)
- `GET /about-me` - Service information
- `GET /endpoints` - List all endpoints
- `GET /provider-consumer` - Service relationships
- `GET /` - Root endpoint

### 3. RAG Query Endpoints (12 endpoints)

#### Basic RAG
- `POST /api/v1/query` - Standard RAG query
- `POST /api/v1/query/enhanced` - Enhanced RAG with signals
- `POST /api/v1/ask` - Simple question answering

#### Temporal RAG
- `POST /api/v1/temporal-rag/point-in-time` - Query at specific timestamp
- `POST /api/v1/temporal-rag/period-comparison` - Compare time periods
- `POST /api/v1/temporal-rag/evolution` - Track document evolution

#### Context-Aware RAG
- `POST /api/v1/context-aware/query` - RAG with hierarchical filtering

#### Multi-Pass RAG
- `POST /api/v1/multi-pass/query` - Complex research queries
- `POST /api/v1/multi-pass/sections` - Generate query sections

#### Dynamic RAG
- `POST /api/v1/dynamic-rag/query` - Dynamic temporal RAG
- `POST /api/v1/dynamic-rag/topics` - Extract topics from query

### 4. Search & Documents (8 endpoints)
- `POST /api/v1/search` - Semantic search
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/{id}` - Get document by ID
- `POST /api/v1/documents/bulk-delete` - Bulk delete documents
- `POST /api/v1/documents/bulk-update` - Bulk update documents
- `GET /api/v1/document/{document_id}` - Alternative document getter
- `GET /api/v1/documents/by-service/{service_name}` - Filter by service
- `DELETE /api/v1/documents/{document_id}` - Delete document

### 5. Ingestion Management (15 endpoints)
- `POST /api/v1/admin/ingest` - Create ingestion job
- `GET /api/v1/admin/jobs` - List jobs
- `GET /api/v1/admin/jobs/{job_id}` - Get job status
- `DELETE /api/v1/admin/jobs/{job_id}` - Cancel job
- `POST /api/v1/admin/jobs/{job_id}/retry` - Retry failed job
- `GET /api/v1/admin/jobs/{job_id}/progress` - Get job progress
- `GET /api/v1/admin/jobs/{job_id}/errors` - Get job errors
- `GET /api/v1/admin/jobs/{job_id}/logs` - Get ingestion logs
- `POST /api/v1/admin/jobs/bulk-cancel` - Cancel multiple jobs
- `GET /api/v1/admin/queue-status` - Queue status
- `POST /api/v1/admin/reprocess` - Reprocess documents
- `POST /api/v1/job-recovery/recover` - Recover failed jobs
- `POST /api/v1/job-recovery/cleanup-stale` - Cleanup stale jobs
- `GET /api/v1/job-progress/realtime/{job_id}` - Real-time progress
- `POST /api/v1/retry-admin/process-queue` - Process retry queue

### 6. Timeline & Temporal Analysis (20 endpoints)
- `POST /api/v1/timelines` - Create timeline
- `GET /api/v1/timelines` - List timelines
- `GET /api/v1/timelines/{id}` - Get timeline
- `DELETE /api/v1/timelines/{id}` - Delete timeline
- `POST /api/v1/timelines/{id}/periods` - Generate periods
- `GET /api/v1/timelines/{id}/periods` - List periods
- `GET /api/v1/timelines/{id}/query` - Query timeline
- `POST /api/v1/temporal-versioning/versions` - Get document versions
- `POST /api/v1/temporal-versioning/diff` - Compare versions
- `POST /api/v1/temporal-versioning/evolution` - Track evolution
- Plus 10 more temporal analysis endpoints

### 7. Tree Context System (8 endpoints)
- `POST /api/v1/tree/build` - Build tree context
- `GET /api/v1/tree/nodes` - List context nodes
- `GET /api/v1/tree/nodes/{id}` - Get node
- `POST /api/v1/tree/query` - Query by proximity
- `GET /api/v1/tree/stats` - Tree statistics
- `DELETE /api/v1/tree/nodes/{id}` - Delete node
- `POST /api/v1/tree/rebuild` - Rebuild tree
- `GET /api/v1/tree/health` - Tree health check

### 8. Discovery & Analysis (25 endpoints)

#### Discovery
- `POST /api/v1/discovery/scan` - Scan repository
- `GET /api/v1/discovery/plans` - List processing plans
- `GET /api/v1/discovery/plans/{id}` - Get plan
- `DELETE /api/v1/discovery/plans/{id}` - Delete plan
- `POST /api/v1/discovery/plans/{id}/execute` - Execute plan
- `GET /api/v1/discovery/plans/{id}/preview` - Preview plan

#### Analysis
- `POST /api/v1/analysis/repository` - Analyze repository
- `GET /api/v1/analysis/results` - List analysis results
- `GET /api/v1/analysis/results/{id}` - Get analysis
- `POST /api/v1/analysis/compare` - Compare repositories
- `POST /api/v1/analysis/detect-services` - Detect microservices
- `POST /api/v1/analysis/technology-stack` - Analyze tech stack
- `POST /api/v1/analysis/architecture` - Detect architecture

#### Orchestration
- `POST /api/v1/orchestration/execute` - Execute plan with parallelism
- `POST /api/v1/orchestration/batch` - Batch processing
- `GET /api/v1/orchestration/status/{id}` - Execution status
- Plus 10 more orchestration endpoints

### 9. Documentation Generation (18 endpoints)
- `POST /api/v1/documentation/generate` - Generate documentation
- `GET /api/v1/documentation/runs` - List generation runs
- `GET /api/v1/documentation/runs/{id}` - Get run status
- `DELETE /api/v1/documentation/runs/{id}` - Cancel run
- `GET /api/v1/documentation/runs/{id}/documents` - Get generated docs
- `POST /api/v1/documentation/incremental` - Incremental generation
- `POST /api/v1/documentation/consolidate` - Consolidate documents
- `GET /api/v1/documentation/templates` - List templates
- Plus 10 more documentation endpoints

### 10. Maintenance & Quality (15 endpoints)
- `POST /api/v1/maintenance/cleanup` - Cleanup old documents
- `POST /api/v1/maintenance/optimize` - Optimize indices
- `POST /api/v1/maintenance/vacuum` - Database vacuum
- `GET /api/v1/maintenance/health` - Maintenance health
- `POST /api/v1/quality/check` - Quality check
- `GET /api/v1/quality/reports` - Quality reports
- `POST /api/v1/quality/fix` - Fix quality issues
- Plus 8 more maintenance endpoints

### 11. Reports & Consolidation (10 endpoints)
- `POST /api/v1/reports/generate` - Generate report
- `GET /api/v1/reports` - List reports
- `GET /api/v1/reports/{id}` - Get report
- `DELETE /api/v1/reports/{id}` - Delete report
- `POST /api/v1/consolidation/merge` - Merge documents
- `POST /api/v1/consolidation/deduplicate` - Remove duplicates
- Plus 4 more consolidation endpoints

### 12. Configuration & Validation (12 endpoints)
- `GET /api/v1/config/registry` - Get configuration registry
- `GET /api/v1/config/health` - Config health check
- `GET /api/v1/config/diff` - Config diff (expected vs actual)
- `POST /api/v1/config/validate` - Validate configuration
- `GET /api/v1/config/viewer/full` - View full config
- `GET /api/v1/config/viewer/services` - View services config
- Plus 6 more config endpoints

### 13. Database Explorers (20 endpoints)

#### PostgreSQL Admin
- `GET /api/v1/postgres/tables` - List tables
- `GET /api/v1/postgres/tables/{table}/schema` - Get schema
- `POST /api/v1/postgres/query` - Execute query
- `GET /api/v1/postgres/stats` - Database statistics
- Plus 6 more PostgreSQL endpoints

#### Redis Admin
- `GET /api/v1/redis/keys` - List keys
- `GET /api/v1/redis/get/{key}` - Get value
- `POST /api/v1/redis/set` - Set value
- `DELETE /api/v1/redis/delete/{key}` - Delete key
- `GET /api/v1/redis/streams` - List streams
- Plus 5 more Redis endpoints

#### Containers & Infrastructure
- `GET /api/v1/containers` - List containers
- `GET /api/v1/containers/{id}` - Get container
- `POST /api/v1/containers/{id}/restart` - Restart container
- Plus 4 more container endpoints

### 14. Embeddings & Ollama (15 endpoints)
- `POST /api/v1/embed` - Generate embeddings
- `POST /api/v1/generate` - Generate text
- `GET /api/v1/models` - List Ollama models
- `GET /api/v1/ollama/status` - Ollama status
- `POST /api/v1/embeddings/batch` - Batch embeddings
- `GET /api/v1/embeddings/cache` - Embedding cache stats
- Plus 9 more embedding endpoints

### 15. Caching & Performance (15 endpoints)
- `GET /api/v1/admin/cache-stats` - Cache statistics
- `POST /api/v1/admin/cache-clear` - Clear cache
- `GET /api/v1/cache-analytics/hit-rate` - Cache hit rate
- `GET /api/v1/cache-analytics/popular-queries` - Popular queries
- `POST /api/v1/performance/optimize` - Optimize performance
- `GET /api/v1/performance/metrics` - Performance metrics
- Plus 9 more performance endpoints

### 16. Diagnostics & Testing (10 endpoints)
- `GET /api/v1/diagnostics/health` - Diagnostic health check
- `POST /api/v1/diagnostics/test/redis` - Test Redis
- `POST /api/v1/diagnostics/test/postgres` - Test PostgreSQL
- `POST /api/v1/diagnostics/test/chromadb` - Test ChromaDB
- `POST /api/v1/diagnostics/test/ollama` - Test Ollama
- Plus 5 more diagnostic endpoints

### 17. Workers & Background Jobs (8 endpoints)
- `GET /api/v1/admin/workers/health` - Worker health
- `GET /api/v1/admin/workers/stats` - Worker statistics
- `POST /api/v1/admin/workers/restart` - Restart worker
- `GET /api/v1/workers/heartbeat` - Worker heartbeat
- Plus 4 more worker endpoints

### 18. Logs & Debugging (6 endpoints)
- `GET /api/v1/logs/list` - List log files
- `GET /api/v1/logs/tail` - Tail log file
- `GET /api/v1/logs/search` - Search logs
- `POST /api/v1/logs/download` - Download logs
- Plus 2 more log endpoints

### 19. Path Resolution (4 endpoints)
- `POST /api/v1/path/resolve` - Resolve path (host ↔ container)
- `POST /api/v1/path/validate` - Validate path
- `GET /api/v1/path/info` - Get path info
- `POST /api/v1/path/batch-resolve` - Batch path resolution

### 20. Circuit Breakers (3 endpoints)
- `GET /api/v1/admin/circuit-breakers` - Circuit breaker status
- `POST /api/v1/admin/circuit-breakers/{name}/reset` - Reset breaker
- `GET /api/v1/admin/circuit-breakers/stats` - Breaker statistics

---

## 🔑 Authentication

**Current**: No authentication (development mode)

**Planned**:
- API key authentication
- JWT tokens for user sessions
- Service-to-service authentication

---

## 📝 Common Request/Response Patterns

### Standard Success Response

```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "uuid",
    "elapsed_ms": 45
  }
}
```

### Standard Error Response

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "status_code": 400,
  "details": { ... }
}
```

---

## 🚀 Rate Limiting

**Default Limits**:
- Global: 100 requests/minute per IP
- Expensive endpoints (RAG, generation): 10 requests/minute
- Health endpoints: No limit

**Headers**:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

---

## 🔗 Related Documentation

- [Architecture Overview](architecture/OVERVIEW.md)
- [Feature Guides](../features/)
- [Quick Start](../guides/QUICK_START.md)
- [OpenAPI Spec](http://localhost:8000/openapi.json)
- [Swagger UI](http://localhost:8000/docs)

---

**Last Updated**: 2025-10-28  
**API Version**: v1  
**Total Endpoints**: 273  
**Status**: Production-Ready


