**Date:** October 29, 2025
**Status:** Dashboard Frontend Audit
**Scope:** All dashboard views

# Dashboard Frontend Audit Report

## 📊 Comprehensive Integration Check

## 🔍 Per-File Analysis

### api_discovery.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/endpoints` | ❌ Unknown |

### api_explorer.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/openapi.json` | ❌ Unknown |
| GET | `{param}/openapi.json` | ❌ Unknown |
| GET | `{param}{param}` | ❌ Unknown |

### cache.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/cache/stats` | ❌ Unknown |
| POST | `{param}/api/v1/admin/clear-cache` | ❌ Unknown |

### chromadb_explorer.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/health` | ❌ Unknown |
| GET | `{param}/api/v1/admin/stats` | ❌ Unknown |
| POST | `{param}/api/v1/query` | ❌ Unknown |
| POST | `{param}/api/v1/query` | ❌ Unknown |
| GET | `{param}/api/v1/embeddings/{param}` | ❌ Unknown |
| GET | `{param}/api/v1/embeddings/sample` | ❌ Unknown |
| GET | `{param}/api/v1/embeddings/export/batch` | ❌ Unknown |
| POST | `{param}/api/v1/query` | ❌ Unknown |

### config_viewer.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/config/current` | ❌ Unknown |
| GET | `{param}/api/v1/config/environment` | ❌ Unknown |
| GET | `{param}/api/v1/config/docker` | ❌ Unknown |
| GET | `{param}/api/v1/config/system` | ❌ Unknown |
| GET | `{param}/api/v1/config/health` | ❌ Unknown |
| GET | `{param}/api/v1/config/diff` | ❌ Unknown |
| GET | `{param}/api/v1/config/validate` | ❌ Unknown |
| GET | `{param}/api/v1/config/validate/{param}` | ❌ Unknown |

### containers.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/containers` | ❌ Unknown |
| POST | `{param}/api/v1/containers/action` | ❌ Unknown |
| POST | `{param}/api/v1/containers/action` | ❌ Unknown |
| POST | `{param}/api/v1/containers/action` | ❌ Unknown |
| POST | `{param}/api/v1/containers/action` | ❌ Unknown |
| POST | `{param}/api/v1/containers/action` | ❌ Unknown |
| GET | `{param}/api/v1/containers/{param}/stats` | ❌ Unknown |
| GET | `{param}/api/v1/containers/{param}/logs?tail=50` | ❌ Unknown |
| GET | `{param}/api/v1/containers/{param}` | ❌ Unknown |

### dead_letter_queue.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/admin/dead-letter/items` | ❌ Unknown |
| DELETE | `{param}/admin/dead-letter/{param}` | ❌ Unknown |
| POST | `{param}/admin/retry-queue/reprocess` | ❌ Unknown |
| POST | `{param}/admin/retry-queue/reprocess` | ❌ Unknown |

### diagnostics.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/diagnostics/health` | ❌ Unknown |
| POST | `{param}/api/v1/diagnostics/test-connection?serv...` | ❌ Unknown |
| GET | `{param}/api/v1/diagnostics/monitor` | ❌ Unknown |

### discovery_orchestration.py

| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `/api/v1/discovery/scan` | ❌ Unknown |
| GET | `/api/v1/discovery/plans` | ❌ Unknown |
| GET | `/api/v1/orchestration/alerts` | ❌ Unknown |
| GET | `/api/v1/orchestration/metrics` | ❌ Unknown |

### doc_generator.py

| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `{param}/api/v1/documentation/runs` | ❌ Unknown |
| PUT | `{param}/api/v1/documentation/runs/{param}/start` | ❌ Unknown |
| POST | `{param}/api/v1/documentation/runs/{param}/docum...` | ❌ Unknown |
| PUT | `{param}/api/v1/documentation/runs/{param}/compl...` | ❌ Unknown |
| POST | `{param}/api/v1/query/enhanced` | ❌ Unknown |

### doc_maintenance.py

| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `/api/v1/maintenance/staleness/detect` | ❌ Unknown |
| POST | `/api/v1/maintenance/coverage/analyze` | ❌ Unknown |
| GET | `/api/v1/maintenance/coverage/gaps` | ❌ Unknown |
| POST | `/api/v1/maintenance/consistency/check` | ❌ Unknown |
| POST | `/api/v1/maintenance/quality/score` | ❌ Unknown |
| GET | `/api/v1/maintenance/quality/report` | ❌ Unknown |
| POST | `/api/v1/maintenance/dependencies/analyze` | ❌ Unknown |
| GET | `/api/v1/maintenance/dependencies/graph` | ❌ Unknown |

### documentation_browser.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/documentation/runs` | ❌ Unknown |
| GET | `{param}/api/v1/documentation/runs/{param}/progr...` | ❌ Unknown |
| GET | `{param}/api/v1/documentation/runs/{param}` | ❌ Unknown |
| GET | `{param}/api/v1/documentation/runs/{param}/expor...` | ❌ Unknown |
| DELETE | `{param}/api/v1/documentation/runs/{param}` | ❌ Unknown |
| GET | `{param}/api/v1/documentation/runs/{param}/docum...` | ❌ Unknown |
| GET | `{param}/api/v1/documentation/documents/{param}` | ❌ Unknown |
| GET | `{param}/api/v1/documentation/runs` | ❌ Unknown |

### documents.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/query/document/{param}` | ❌ Unknown |
| GET | `{param}/api/v1/documents/{param}` | ❌ Unknown |
| GET | `{param}/api/v1/documents` | ❌ Unknown |
| POST | `{param}/api/v1/admin/ingest` | ❌ Unknown |
| GET | `{param}/api/v1/admin/queue-status` | ❌ Unknown |

### embeddings_manager.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/admin/embeddings/stats` | ❌ Unknown |
| GET | `{param}/api/v1/admin/embeddings/stats` | ❌ Unknown |
| GET | `{param}/api/v1/admin/embeddings/health` | ❌ Unknown |
| POST | `{param}/api/v1/admin/embeddings/regenerate` | ❌ Unknown |
| GET | `{param}/api/v1/admin/embeddings/health` | ❌ Unknown |

### health.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/infrastructure/health` | ❌ Unknown |
| GET | `{param}/api/v1/admin/circuit-breakers` | ❌ Unknown |
| GET | `{param}/api/v1/infrastructure/diagnostics` | ❌ Unknown |

### home.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/health` | ❌ Unknown |
| GET | `{param}/api/v1/admin/stats` | ❌ Unknown |

### ingestion_manager.py

| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `{param}/api/v1/admin/ingest/{param}/cancel` | ❌ Unknown |
| POST | `{param}/api/v1/path/validate` | ❌ Unknown |
| POST | `{param}/api/v1/path/validate` | ❌ Unknown |
| GET | `{param}/api/v1/admin/workers/ingestion/status` | ❌ Unknown |
| POST | `{param}/api/v1/admin/workers/ingestion/auto-rec...` | ❌ Unknown |
| POST | `{param}/api/v1/admin/ingest` | ❌ Unknown |
| DELETE | `{param}/api/v1/admin/jobs/completed` | ❌ Unknown |
| DELETE | `{param}/api/v1/admin/jobs/failed` | ❌ Unknown |
| GET | `{param}/api/v1/admin/ingest/status` | ❌ Unknown |
| GET | `{param}/api/v1/admin/ingest/{param}` | ❌ Unknown |
| POST | `{param}/api/v1/admin/ingest/{param}/cancel` | ❌ Unknown |
| DELETE | `{param}/api/v1/admin/data/postgres` | ❌ Unknown |
| DELETE | `{param}/api/v1/admin/data/chromadb` | ❌ Unknown |
| DELETE | `{param}/api/v1/admin/clear-all-cache` | ❌ Unknown |
| DELETE | `{param}/api/v1/admin/data/postgres` | ❌ Unknown |
| DELETE | `{param}/api/v1/admin/data/chromadb` | ❌ Unknown |
| DELETE | `{param}/api/v1/admin/clear-all-cache` | ❌ Unknown |
| GET | `{param}/api/v1/admin/data/stats` | ❌ Unknown |

### job_recovery_manager.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/recovery/status/{param}` | ❌ Unknown |
| POST | `{param}/api/v1/recovery/resume` | ❌ Unknown |
| GET | `{param}/api/v1/recovery/checkpoints/{param}` | ❌ Unknown |
| DELETE | `{param}/api/v1/recovery/checkpoints/{param}` | ❌ Unknown |

### logs_viewer.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/containers` | ❌ Unknown |
| GET | `{param}/api/v1/containers/{param}/logs` | ❌ Unknown |
| GET | `{param}/api/v1/containers` | ❌ Unknown |
| GET | `{param}/api/v1/containers/{param}/logs` | ❌ Unknown |

### metrics.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/admin/stats` | ❌ Unknown |
| GET | `{param}/api/v1/health/datasources` | ❌ Unknown |
| GET | `{param}/api/v1/admin/stats` | ❌ Unknown |

### postgres_explorer.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/postgres/info` | ❌ Unknown |
| GET | `{param}/api/v1/postgres/tables` | ❌ Unknown |
| GET | `{param}/api/v1/postgres/table/{param}` | ❌ Unknown |
| POST | `{param}/api/v1/postgres/query` | ❌ Unknown |
| GET | `{param}/api/v1/postgres/activity` | ❌ Unknown |
| GET | `{param}/api/v1/postgres/locks` | ❌ Unknown |

### quality_dashboard.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/documentation/runs` | ❌ Unknown |
| GET | `{param}/api/v1/quality/metrics/{param}` | ❌ Unknown |
| POST | `{param}/api/v1/quality/validate-run` | ❌ Unknown |
| GET | `{param}/api/v1/quality/review/queue` | ❌ Unknown |
| POST | `{param}/api/v1/quality/review/{param}/assign` | ❌ Unknown |
| POST | `{param}/api/v1/quality/review/{param}/complete` | ❌ Unknown |
| GET | `{param}/api/v1/documentation/runs` | ❌ Unknown |
| GET | `{param}/api/v1/quality/report/{param}` | ❌ Unknown |
| POST | `{param}/api/v1/quality/validate` | ❌ Unknown |
| GET | `{param}/api/v1/documentation/runs` | ❌ Unknown |
| POST | `{param}/api/v1/quality/validate-run` | ❌ Unknown |

### query_enhanced.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/query/tier-status` | ❌ Unknown |
| GET | `{param}/api/v1/query/modes` | ❌ Unknown |
| POST | `{param}/api/v1/query/enhanced` | ❌ Unknown |

### rag.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/query/tier-status` | ❌ Unknown |
| POST | `{param}/api/v1/query/enhanced` | ❌ Unknown |

### rag_config_manager.py

| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `{param}/admin/invalidate-rag-config-cache` | ❌ Unknown |
| POST | `{param}/api/v1/query/enhanced` | ❌ Unknown |
| POST | `{param}/admin/invalidate-rag-config-cache` | ❌ Unknown |

### rag_multi_pass.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/query/tier-status` | ❌ Unknown |
| POST | `{param}/api/v1/query/multi-pass` | ❌ Unknown |

### redis_explorer.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/redis/info` | ❌ Unknown |
| POST | `{param}/api/v1/redis/keys` | ❌ Unknown |
| GET | `{param}/api/v1/redis/key/{param}` | ❌ Unknown |
| DELETE | `{param}/api/v1/redis/key/{param}` | ❌ Unknown |
| POST | `{param}/api/v1/redis/key` | ❌ Unknown |
| GET | `{param}/api/v1/redis/memory` | ❌ Unknown |
| GET | `{param}/api/v1/redis/info` | ❌ Unknown |

### reports_generator.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/api/v1/analysis/contexts` | ❌ Unknown |

### retry_queue.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/admin/retry-queue/stats` | ❌ Unknown |
| GET | `{param}/admin/retry-queue/items` | ❌ Unknown |
| GET | `{param}/admin/retry-worker/status` | ❌ Unknown |
| POST | `{param}/admin/retry-queue/reprocess` | ❌ Unknown |
| POST | `{param}/admin/retry-queue/reprocess` | ❌ Unknown |

### settings.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/health` | ❌ Unknown |

### temporal_rag_query.py

| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `/api/v1/versioning/as-of` | ❌ Unknown |
| POST | `/api/v1/versioning/timeline` | ❌ Unknown |
| GET | `/api/v1/versioning/changes` | ❌ Unknown |
| GET | `/api/v1/versioning/activity-summary` | ❌ Unknown |
| GET | `/api/v1/versioning/activity-summary` | ❌ Unknown |
| GET | `/api/v1/versioning/activity-summary` | ❌ Unknown |

### tier_management.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/query/tier-status` | ❌ Unknown |
| GET | `{param}/health` | ❌ Unknown |
| GET | `{param}/api/version` | ❌ Unknown |
| GET | `{param}/api/version` | ❌ Unknown |

### timeline_analysis.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/timelines` | ❌ Unknown |
| POST | `{param}/api/v1/timelines` | ❌ Unknown |
| POST | `{param}/api/v1/rag/temporal/query` | ❌ Unknown |
| GET | `{param}/api/v1/maintenance/quality/overview` | ❌ Unknown |
| GET | `{param}/api/v1/analysis/gaps/analyze` | ❌ Unknown |
| GET | `{param}/api/v1/analysis/drift/detect` | ❌ Unknown |
| POST | `{param}/api/v1/analysis/export` | ❌ Unknown |
| POST | `{param}/api/v1/analysis/export/github-pages/{pa...` | ❌ Unknown |

### timeline_viewer.py

| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `{param}/api/v1/versioning/timeline` | ❌ Unknown |
| POST | `{param}/api/v1/versioning/as-of` | ❌ Unknown |
| POST | `{param}/api/v1/versioning/changes` | ❌ Unknown |
| GET | `{param}/api/v1/versioning/activity-summary` | ❌ Unknown |
| GET | `{param}/api/v1/versioning/deduplication-stats` | ❌ Unknown |

### worker_monitor.py

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `{param}/api/v1/admin/workers/health` | ❌ Unknown |
| POST | `{param}/api/v1/admin/workers/ingestion/restart` | ❌ Unknown |
| POST | `{param}/api/v1/admin/workers/ingestion/auto-rec...` | ❌ Unknown |
| GET | `{param}/api/v1/admin/workers/container/health` | ❌ Unknown |
| GET | `{param}/api/v1/admin/workers/ingestion/status` | ❌ Unknown |

## 📊 Summary

- **Files Scanned**: 37
- **API Calls Found**: 176
- **Valid Endpoints**: 0
- **Unknown Endpoints**: 176

## ⚠️ Unknown Endpoints

| File | Method | Endpoint |
|------|--------|----------|
| api_discovery.py | GET | `{param}/endpoints` |
| api_explorer.py | GET | `{param}/openapi.json` |
| api_explorer.py | GET | `{param}/openapi.json` |
| api_explorer.py | GET | `{param}{param}` |
| cache.py | GET | `{param}/api/v1/cache/stats` |
| cache.py | POST | `{param}/api/v1/admin/clear-cache` |
| chromadb_explorer.py | GET | `{param}/health` |
| chromadb_explorer.py | GET | `{param}/api/v1/admin/stats` |
| chromadb_explorer.py | POST | `{param}/api/v1/query` |
| chromadb_explorer.py | POST | `{param}/api/v1/query` |
| chromadb_explorer.py | GET | `{param}/api/v1/embeddings/{param}` |
| chromadb_explorer.py | GET | `{param}/api/v1/embeddings/sample` |
| chromadb_explorer.py | GET | `{param}/api/v1/embeddings/export/batch` |
| chromadb_explorer.py | POST | `{param}/api/v1/query` |
| config_viewer.py | GET | `{param}/api/v1/config/current` |
| config_viewer.py | GET | `{param}/api/v1/config/environment` |
| config_viewer.py | GET | `{param}/api/v1/config/docker` |
| config_viewer.py | GET | `{param}/api/v1/config/system` |
| config_viewer.py | GET | `{param}/api/v1/config/health` |
| config_viewer.py | GET | `{param}/api/v1/config/diff` |
| config_viewer.py | GET | `{param}/api/v1/config/validate` |
| config_viewer.py | GET | `{param}/api/v1/config/validate/{param}` |
| containers.py | GET | `{param}/api/v1/containers` |
| containers.py | POST | `{param}/api/v1/containers/action` |
| containers.py | POST | `{param}/api/v1/containers/action` |
| containers.py | POST | `{param}/api/v1/containers/action` |
| containers.py | POST | `{param}/api/v1/containers/action` |
| containers.py | POST | `{param}/api/v1/containers/action` |
| containers.py | GET | `{param}/api/v1/containers/{param}/stats` |
| containers.py | GET | `{param}/api/v1/containers/{param}/logs?tail=50` |
| containers.py | GET | `{param}/api/v1/containers/{param}` |
| dead_letter_queue.py | GET | `{param}/admin/dead-letter/items` |
| dead_letter_queue.py | DELETE | `{param}/admin/dead-letter/{param}` |
| dead_letter_queue.py | POST | `{param}/admin/retry-queue/reprocess` |
| dead_letter_queue.py | POST | `{param}/admin/retry-queue/reprocess` |
| diagnostics.py | GET | `{param}/api/v1/diagnostics/health` |
| diagnostics.py | POST | `{param}/api/v1/diagnostics/test-connection?serv...` |
| diagnostics.py | GET | `{param}/api/v1/diagnostics/monitor` |
| discovery_orchestration.py | POST | `/api/v1/discovery/scan` |
| discovery_orchestration.py | GET | `/api/v1/discovery/plans` |
| discovery_orchestration.py | GET | `/api/v1/orchestration/alerts` |
| discovery_orchestration.py | GET | `/api/v1/orchestration/metrics` |
| doc_generator.py | POST | `{param}/api/v1/documentation/runs` |
| doc_generator.py | PUT | `{param}/api/v1/documentation/runs/{param}/start` |
| doc_generator.py | POST | `{param}/api/v1/documentation/runs/{param}/docum...` |
| doc_generator.py | PUT | `{param}/api/v1/documentation/runs/{param}/compl...` |
| doc_generator.py | POST | `{param}/api/v1/query/enhanced` |
| doc_maintenance.py | POST | `/api/v1/maintenance/staleness/detect` |
| doc_maintenance.py | POST | `/api/v1/maintenance/coverage/analyze` |
| doc_maintenance.py | GET | `/api/v1/maintenance/coverage/gaps` |
| doc_maintenance.py | POST | `/api/v1/maintenance/consistency/check` |
| doc_maintenance.py | POST | `/api/v1/maintenance/quality/score` |
| doc_maintenance.py | GET | `/api/v1/maintenance/quality/report` |
| doc_maintenance.py | POST | `/api/v1/maintenance/dependencies/analyze` |
| doc_maintenance.py | GET | `/api/v1/maintenance/dependencies/graph` |
| documentation_browser.py | GET | `{param}/api/v1/documentation/runs` |
| documentation_browser.py | GET | `{param}/api/v1/documentation/runs/{param}/progr...` |
| documentation_browser.py | GET | `{param}/api/v1/documentation/runs/{param}` |
| documentation_browser.py | GET | `{param}/api/v1/documentation/runs/{param}/expor...` |
| documentation_browser.py | DELETE | `{param}/api/v1/documentation/runs/{param}` |
| documentation_browser.py | GET | `{param}/api/v1/documentation/runs/{param}/docum...` |
| documentation_browser.py | GET | `{param}/api/v1/documentation/documents/{param}` |
| documentation_browser.py | GET | `{param}/api/v1/documentation/runs` |
| documents.py | GET | `{param}/api/v1/query/document/{param}` |
| documents.py | GET | `{param}/api/v1/documents/{param}` |
| documents.py | GET | `{param}/api/v1/documents` |
| documents.py | POST | `{param}/api/v1/admin/ingest` |
| documents.py | GET | `{param}/api/v1/admin/queue-status` |
| embeddings_manager.py | GET | `{param}/api/v1/admin/embeddings/stats` |
| embeddings_manager.py | GET | `{param}/api/v1/admin/embeddings/stats` |
| embeddings_manager.py | GET | `{param}/api/v1/admin/embeddings/health` |
| embeddings_manager.py | POST | `{param}/api/v1/admin/embeddings/regenerate` |
| embeddings_manager.py | GET | `{param}/api/v1/admin/embeddings/health` |
| health.py | GET | `{param}/api/v1/infrastructure/health` |
| health.py | GET | `{param}/api/v1/admin/circuit-breakers` |
| health.py | GET | `{param}/api/v1/infrastructure/diagnostics` |
| home.py | GET | `{param}/health` |
| home.py | GET | `{param}/api/v1/admin/stats` |
| ingestion_manager.py | POST | `{param}/api/v1/admin/ingest/{param}/cancel` |
| ingestion_manager.py | POST | `{param}/api/v1/path/validate` |
| ingestion_manager.py | POST | `{param}/api/v1/path/validate` |
| ingestion_manager.py | GET | `{param}/api/v1/admin/workers/ingestion/status` |
| ingestion_manager.py | POST | `{param}/api/v1/admin/workers/ingestion/auto-rec...` |
| ingestion_manager.py | POST | `{param}/api/v1/admin/ingest` |
| ingestion_manager.py | DELETE | `{param}/api/v1/admin/jobs/completed` |
| ingestion_manager.py | DELETE | `{param}/api/v1/admin/jobs/failed` |
| ingestion_manager.py | GET | `{param}/api/v1/admin/ingest/status` |
| ingestion_manager.py | GET | `{param}/api/v1/admin/ingest/{param}` |
| ingestion_manager.py | POST | `{param}/api/v1/admin/ingest/{param}/cancel` |
| ingestion_manager.py | DELETE | `{param}/api/v1/admin/data/postgres` |
| ingestion_manager.py | DELETE | `{param}/api/v1/admin/data/chromadb` |
| ingestion_manager.py | DELETE | `{param}/api/v1/admin/clear-all-cache` |
| ingestion_manager.py | DELETE | `{param}/api/v1/admin/data/postgres` |
| ingestion_manager.py | DELETE | `{param}/api/v1/admin/data/chromadb` |
| ingestion_manager.py | DELETE | `{param}/api/v1/admin/clear-all-cache` |
| ingestion_manager.py | GET | `{param}/api/v1/admin/data/stats` |
| job_recovery_manager.py | GET | `{param}/api/v1/recovery/status/{param}` |
| job_recovery_manager.py | POST | `{param}/api/v1/recovery/resume` |
| job_recovery_manager.py | GET | `{param}/api/v1/recovery/checkpoints/{param}` |
| job_recovery_manager.py | DELETE | `{param}/api/v1/recovery/checkpoints/{param}` |
| logs_viewer.py | GET | `{param}/api/v1/containers` |
| logs_viewer.py | GET | `{param}/api/v1/containers/{param}/logs` |
| logs_viewer.py | GET | `{param}/api/v1/containers` |
| logs_viewer.py | GET | `{param}/api/v1/containers/{param}/logs` |
| metrics.py | GET | `{param}/api/v1/admin/stats` |
| metrics.py | GET | `{param}/api/v1/health/datasources` |
| metrics.py | GET | `{param}/api/v1/admin/stats` |
| postgres_explorer.py | GET | `{param}/api/v1/postgres/info` |
| postgres_explorer.py | GET | `{param}/api/v1/postgres/tables` |
| postgres_explorer.py | GET | `{param}/api/v1/postgres/table/{param}` |
| postgres_explorer.py | POST | `{param}/api/v1/postgres/query` |
| postgres_explorer.py | GET | `{param}/api/v1/postgres/activity` |
| postgres_explorer.py | GET | `{param}/api/v1/postgres/locks` |
| quality_dashboard.py | GET | `{param}/api/v1/documentation/runs` |
| quality_dashboard.py | GET | `{param}/api/v1/quality/metrics/{param}` |
| quality_dashboard.py | POST | `{param}/api/v1/quality/validate-run` |
| quality_dashboard.py | GET | `{param}/api/v1/quality/review/queue` |
| quality_dashboard.py | POST | `{param}/api/v1/quality/review/{param}/assign` |
| quality_dashboard.py | POST | `{param}/api/v1/quality/review/{param}/complete` |
| quality_dashboard.py | GET | `{param}/api/v1/documentation/runs` |
| quality_dashboard.py | GET | `{param}/api/v1/quality/report/{param}` |
| quality_dashboard.py | POST | `{param}/api/v1/quality/validate` |
| quality_dashboard.py | GET | `{param}/api/v1/documentation/runs` |
| quality_dashboard.py | POST | `{param}/api/v1/quality/validate-run` |
| query_enhanced.py | GET | `{param}/api/v1/query/tier-status` |
| query_enhanced.py | GET | `{param}/api/v1/query/modes` |
| query_enhanced.py | POST | `{param}/api/v1/query/enhanced` |
| rag.py | GET | `{param}/api/v1/query/tier-status` |
| rag.py | POST | `{param}/api/v1/query/enhanced` |
| rag_config_manager.py | POST | `{param}/admin/invalidate-rag-config-cache` |
| rag_config_manager.py | POST | `{param}/api/v1/query/enhanced` |
| rag_config_manager.py | POST | `{param}/admin/invalidate-rag-config-cache` |
| rag_multi_pass.py | GET | `{param}/api/v1/query/tier-status` |
| rag_multi_pass.py | POST | `{param}/api/v1/query/multi-pass` |
| redis_explorer.py | GET | `{param}/api/v1/redis/info` |
| redis_explorer.py | POST | `{param}/api/v1/redis/keys` |
| redis_explorer.py | GET | `{param}/api/v1/redis/key/{param}` |
| redis_explorer.py | DELETE | `{param}/api/v1/redis/key/{param}` |
| redis_explorer.py | POST | `{param}/api/v1/redis/key` |
| redis_explorer.py | GET | `{param}/api/v1/redis/memory` |
| redis_explorer.py | GET | `{param}/api/v1/redis/info` |
| reports_generator.py | GET | `/api/v1/analysis/contexts` |
| retry_queue.py | GET | `{param}/admin/retry-queue/stats` |
| retry_queue.py | GET | `{param}/admin/retry-queue/items` |
| retry_queue.py | GET | `{param}/admin/retry-worker/status` |
| retry_queue.py | POST | `{param}/admin/retry-queue/reprocess` |
| retry_queue.py | POST | `{param}/admin/retry-queue/reprocess` |
| settings.py | GET | `{param}/health` |
| temporal_rag_query.py | POST | `/api/v1/versioning/as-of` |
| temporal_rag_query.py | POST | `/api/v1/versioning/timeline` |
| temporal_rag_query.py | GET | `/api/v1/versioning/changes` |
| temporal_rag_query.py | GET | `/api/v1/versioning/activity-summary` |
| temporal_rag_query.py | GET | `/api/v1/versioning/activity-summary` |
| temporal_rag_query.py | GET | `/api/v1/versioning/activity-summary` |
| tier_management.py | GET | `{param}/api/v1/query/tier-status` |
| tier_management.py | GET | `{param}/health` |
| tier_management.py | GET | `{param}/api/version` |
| tier_management.py | GET | `{param}/api/version` |
| timeline_analysis.py | GET | `{param}/api/v1/timelines` |
| timeline_analysis.py | POST | `{param}/api/v1/timelines` |
| timeline_analysis.py | POST | `{param}/api/v1/rag/temporal/query` |
| timeline_analysis.py | GET | `{param}/api/v1/maintenance/quality/overview` |
| timeline_analysis.py | GET | `{param}/api/v1/analysis/gaps/analyze` |
| timeline_analysis.py | GET | `{param}/api/v1/analysis/drift/detect` |
| timeline_analysis.py | POST | `{param}/api/v1/analysis/export` |
| timeline_analysis.py | POST | `{param}/api/v1/analysis/export/github-pages/{pa...` |
| timeline_viewer.py | POST | `{param}/api/v1/versioning/timeline` |
| timeline_viewer.py | POST | `{param}/api/v1/versioning/as-of` |
| timeline_viewer.py | POST | `{param}/api/v1/versioning/changes` |
| timeline_viewer.py | GET | `{param}/api/v1/versioning/activity-summary` |
| timeline_viewer.py | GET | `{param}/api/v1/versioning/deduplication-stats` |
| worker_monitor.py | GET | `{param}/api/v1/admin/workers/health` |
| worker_monitor.py | POST | `{param}/api/v1/admin/workers/ingestion/restart` |
| worker_monitor.py | POST | `{param}/api/v1/admin/workers/ingestion/auto-rec...` |
| worker_monitor.py | GET | `{param}/api/v1/admin/workers/container/health` |
| worker_monitor.py | GET | `{param}/api/v1/admin/workers/ingestion/status` |

## 🎯 Integration Health

**Success Rate**: 0.0%

### 🔴 NEEDS ATTENTION

Several endpoints require investigation.
