---
title: "Ecosystem MCP - Complete Code Reference"
service: "ecosystem-mcp"
category: "reference"
tags: ["code", "reference", "modules", "classes", "functions", "source-code", "implementation"]
related: ["architecture/OVERVIEW.md", "DATABASE_SCHEMA.md", "API_ENDPOINTS_COMPLETE.md"]
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "advanced"
semantic_keywords: ["source code", "implementation", "classes", "modules", "packages", "functions", "services", "utilities", "repositories", "models"]
llm_search_hints: ["where is X implemented", "what does Y do", "how does Z work", "find code for", "locate implementation"]
---

# Ecosystem MCP - Complete Code Reference

**Comprehensive source code documentation for LLM agents**

*Generated from actual codebase analysis: 2025-10-28*

---

## 🗂️ Source Code Organization

```
src/
├── api/                    # FastAPI application & routes
├── config/                 # Configuration management
├── ingestion/              # Legacy ingestion (being deprecated)
├── models/                 # Pydantic data models
├── repositories/           # Database repositories
├── services/               # Business logic layer
├── storage/                # Database & storage layer
└── utils/                  # Utility functions & helpers
```

---

## 1️⃣ API Layer (`src/api/`)

### FastAPI Application

**File**: `src/api/app.py`  
**Purpose**: Main FastAPI application factory  
**Key Functions**:
- `create_app()` - Creates configured FastAPI application
- `setup_signal_handlers()` - Graceful shutdown handling  
**Routes Registered**: 51 route modules, 273 endpoints

**Semantic Tags**: `#fastapi #application #server #routes #middleware #cors`

---

### Route Modules (`src/api/routes/`)

**Total Files**: 51 route files  
**Total Endpoints**: 273 REST endpoints

#### Health & Monitoring Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `health.py` | 4 | Basic health, deep health, worker health, metrics |
| `monitoring.py` | 2 | System monitoring, resource tracking |
| `diagnostics.py` | 3 | Diagnostic checks for all services |
| `metrics.py` | 1 | Prometheus metrics endpoint |

**Semantic Tags**: `#health-check #monitoring #diagnostics #prometheus #metrics #observability`

---

#### RAG Query Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `ask.py` | 2 | Simple question answering with RAG |
| `query.py` | 7 | Standard RAG queries with filters |
| `query_enhanced.py` | 3 | Enhanced RAG with multi-signal ranking |
| `context_aware_query.py` | 5 | Context-filtered RAG queries |
| `temporal_rag.py` | 6 | Time-aware RAG (point-in-time, evolution) |
| `multi_pass.py` | 2 | Multi-pass research queries |
| `dynamic_rag.py` | 5 | Dynamic temporal RAG |

**Semantic Tags**: `#rag #query #search #llm #question-answering #semantic-search #temporal #context-aware #multi-pass`

---

#### Document Management Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `documents.py` | 4 | CRUD operations for documents |
| `search.py` | 1 | Semantic document search |
| `embeddings.py` | 3 | Embedding generation & management |

**Semantic Tags**: `#documents #crud #search #embeddings #vectors`

---

#### Ingestion Management Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `admin.py` | 32 | Job management, ingestion, queue control |
| `ingestion_logs.py` | 2 | View ingestion logs |
| `job_progress.py` | 3 | Real-time job progress tracking |
| `job_recovery.py` | 4 | Recover failed jobs |
| `retry_admin.py` | 6 | Retry queue management |
| `workers.py` | 5 | Worker health & management |

**Semantic Tags**: `#ingestion #jobs #workers #queue #retry #recovery #admin #management`

---

#### Analysis & Discovery Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `analysis.py` | 6 | Repository analysis & detection |
| `discovery.py` | 3 | Repository discovery & scanning |
| `discovery_admin.py` | 6 | Discovery plan management |
| `orchestration.py` | 9 | Parallel execution orchestration |

**Semantic Tags**: `#analysis #discovery #orchestration #repository #detection #scanning`

---

#### Timeline & Temporal Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `timeline.py` | 12 | Timeline management |
| `temporal_versioning.py` | 9 | Document version tracking |

**Semantic Tags**: `#timeline #temporal #versioning #history #evolution`

---

#### Tree Context Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `tree_admin.py` | 8 | Tree context system management |

**Semantic Tags**: `#tree #context #3d-structure #spatial #proximity`

---

#### Documentation Generation Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `documentation.py` | 6 | Multi-pass documentation generation |
| `documentation_runs.py` | 8 | Generation run management |
| `documentation_incremental.py` | 6 | Incremental doc generation |
| `consolidation.py` | 3 | Document consolidation |
| `reports.py` | 4 | Report generation |
| `maintenance.py` | 19 | Documentation maintenance |
| `quality.py` | 7 | Quality checks & metrics |

**Semantic Tags**: `#documentation #generation #consolidation #reports #quality #maintenance`

---

#### Configuration & System Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `config_viewer.py` | 4 | View system configuration |
| `config_validation.py` | 8 | Validate configuration |
| `standard.py` | 3 | Standard endpoints (about-me, etc.) |
| `infrastructure.py` | 4 | Infrastructure management |

**Semantic Tags**: `#configuration #validation #system #infrastructure #metadata`

---

#### Database Explorer Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `postgres_admin.py` | 6 | PostgreSQL exploration |
| `redis_admin.py` | 7 | Redis key/stream management |
| `containers.py` | 5 | Docker container management |

**Semantic Tags**: `#database #postgresql #redis #explorer #admin #containers`

---

#### Ollama & LLM Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `ollama.py` | 5 | Ollama model interaction |
| `ollama_status.py` | 2 | Ollama health & status |
| `embeddings_admin.py` | 3 | Embedding administration |

**Semantic Tags**: `#ollama #llm #models #embeddings #ai`

---

#### Utility Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `logs.py` | 5 | Log file viewing |
| `cache_stats.py` | 3 | Cache statistics |
| `cache_analytics.py` | 3 | Cache analytics & insights |
| `performance.py` | 7 | Performance metrics |
| `performance_optimization.py` | 4 | Performance tuning |
| `path_resolver.py` | 4 | Path resolution (host ↔ container) |

**Semantic Tags**: `#logs #cache #performance #optimization #analytics #utilities`

---

### Middleware (`src/api/middleware/`)

| File | Purpose |
|------|---------|
| `tracing.py` | Request tracing & logging |

**Semantic Tags**: `#middleware #tracing #logging #request-id`

---

## 2️⃣ Service Layer (`src/services/`)

### RAG Services (`src/services/rag/`)

#### Core Classes

**`RAGService`** (`rag_service.py`)
- **Purpose**: Basic retrieval-augmented generation
- **Key Methods**:
  - `ask()` - Answer question with document context
  - `_search_documents()` - Semantic search
  - `_synthesize_answer()` - LLM synthesis
- **Features**: Recency scoring (15%), version boost (10%), source citation
- **Semantic Tags**: `#rag #llm #synthesis #semantic-search #qa`

**`EnhancedRAGService`** (`enhanced_rag_service.py`)
- **Purpose**: RAG with optional multi-signal ranking
- **Extends**: RAGService
- **Key Methods**:
  - `_apply_enhancements()` - Apply glossary, priorities, exclusions
  - `_rank_documents()` - Multi-signal ranking
- **Features**: Glossary matching, priority rules, context-aware exclusions
- **Config**: Optional `.rag-config/rag_config.yaml`
- **Semantic Tags**: `#enhanced-rag #multi-signal #ranking #glossary #priorities`

**`ContextAwareRAG`** (`context_aware_rag.py`)
- **Purpose**: RAG with hierarchical filtering
- **Key Methods**:
  - `query_with_context()` - Filter by repo/service/module
- **Features**: Repository filtering, tech stack awareness, time range filtering
- **Semantic Tags**: `#context-aware #filtering #hierarchical #repository`

**`TemporalRAGService`** (`temporal_rag_service.py`)
- **Purpose**: Time-aware document retrieval
- **Key Methods**:
  - `query_point_in_time()` - Query at specific timestamp
  - `query_period_comparison()` - Compare time periods
  - `track_evolution()` - Track document changes
- **Semantic Tags**: `#temporal #time-aware #evolution #versioning #history`

**`MultiPassQueryService`** (`multi_pass_query.py`)
- **Purpose**: Complex research-level queries
- **Key Methods**:
  - `process_query()` - Multi-pass decomposition
  - `_generate_sections()` - Break into sections
  - `_generate_secondary_questions()` - Expand query
  - `_synthesize_final_answer()` - Combine results
- **Features**: Parallel section processing, section-level synthesis
- **Semantic Tags**: `#multi-pass #research #complex-queries #decomposition #synthesis`

#### Configuration

**`OptionalConfigLoader`** (`config_loader.py`)
- **Purpose**: Load optional RAG configuration
- **File**: `.rag-config/rag_config.yaml`
- **Features**: Glossary terms, exclusion rules, priority rules, query templates
- **Semantic Tags**: `#configuration #rag-config #glossary #priorities #templates`

---

### Embedding Services (`src/services/embeddings/`)

**`EmbeddingService`** (`embedding_service.py`)
- **Purpose**: Generate text embeddings
- **Backends**: FastEmbed service (10-50× faster), Ollama (legacy)
- **Key Methods**:
  - `generate_embedding()` - Single text embedding
  - `generate_batch()` - Batch embedding generation
  - `_generate_with_service()` - FastEmbed backend
  - `_generate_with_ollama()` - Ollama backend
- **Features**: Automatic fallback, circuit breakers, cost tracking
- **Model**: `nomic-embed-text` (768 dimensions)
- **Semantic Tags**: `#embeddings #vectors #fastembed #ollama #batch-processing`

**`EmbeddingClient`** (`embedding_client.py`)
- **Purpose**: HTTP client for FastEmbed service
- **Key Methods**:
  - `generate_embedding()` - Single embedding
  - `generate_batch()` - Batch embeddings
- **Features**: Circuit breaker protection, 30s timeout
- **Semantic Tags**: `#http-client #fastembed #circuit-breaker #resilience`

**`RecoverableEmbeddingGenerator`** (`recoverable_embedding_generator.py`)
- **Purpose**: Retry-able embedding generation
- **Features**: Exponential backoff, error recovery
- **Semantic Tags**: `#retry #recovery #resilience #exponential-backoff`

---

### Ingestion Services (`src/services/ingestion/`)

**`JobProcessor`** (`job_processor.py`)
- **Purpose**: Main ingestion pipeline orchestrator
- **File Size**: 4,174 lines (largest file!)
- **Key Methods**:
  - `process()` - Process ingestion job
  - `_process_commits()` - Walk git history
  - `_extract_documents()` - Extract files from commits
  - `_normalize_document()` - Normalize content
  - `_generate_embeddings()` - Create vectors
  - `_store_document()` - Save to databases
- **Features**: Progress tracking, error aggregation, retry logic, checkpointing
- **Semantic Tags**: `#ingestion #pipeline #git #processing #orchestration`

**`SnapshotProcessor`** (`snapshot_processor.py`)
- **Purpose**: Fast ingestion without git history
- **Key Methods**:
  - `process()` - Process snapshot mode
  - `_scan_directory()` - Walk directory tree
- **Performance**: 10-100× faster than git_history mode
- **Semantic Tags**: `#snapshot #fast-mode #no-git #quick-ingestion`

**`EnhancedJobProcessor`** (`enhanced_job_processor.py`)
- **Purpose**: Enriched mode with git metadata + filesystem fallback
- **Key Methods**:
  - `process()` - Process enriched mode
  - `_get_git_metadata()` - Try git, fallback to filesystem
- **Features**: Graceful degradation, temporal metadata
- **Semantic Tags**: `#enriched #hybrid #fallback #temporal-metadata`

**`JobProcessorRouter`** (`job_processor_router.py`)
- **Purpose**: Route jobs to appropriate processor
- **Key Methods**:
  - `route_and_process_job()` - Select processor by mode
- **Modes**: snapshot, git_history, enriched, incremental
- **Semantic Tags**: `#router #dispatcher #mode-selection`

**`ErrorClassifier`** (`error_classifier.py`)
- **Purpose**: Classify and categorize errors
- **Error Types**: FILE_READ, GIT_PARSING, NORMALIZATION, EMBEDDING, STORAGE, CHROMADB, TIMEOUT, UNKNOWN
- **Semantic Tags**: `#errors #classification #types #categorization`

---

### Analysis Services (`src/services/analysis/`)

**`HierarchicalContextManager`** (`hierarchical_context_manager.py`)
- **Purpose**: Manage hierarchical repository context
- **Levels**: ROOT → SERVICE → MODULE → COMPONENT
- **Key Methods**:
  - `create_context()` - Create context node
  - `get_context()` - Retrieve context
  - `resolve_hierarchy()` - Navigate hierarchy
- **Semantic Tags**: `#hierarchy #context #structure #levels #navigation`

---

### Tree Services (`src/services/tree/`)

**Purpose**: 3D spatial tree representation of repository structure

**Key Classes**:
- `TreeBuilder` - Build tree from repository
- `TreeQueryService` - Query by proximity
- `ProximityCalculator` - Calculate spatial distances

**Semantic Tags**: `#tree #3d #spatial #proximity #coordinates #graph`

---

### Model Services (`src/services/models/`)

**`OllamaClient`** (`ollama_client.py`)
- **Purpose**: HTTP client for Ollama API
- **Key Methods**:
  - `generate()` - Generate text
  - `embed()` - Generate embedding
  - `list_models()` - List available models
- **Semantic Tags**: `#ollama #client #llm #http`

**`OllamaRouter`** (`ollama_router.py`)
- **Purpose**: 3-tier LLM routing
- **Tiers**: Desktop Ollama → Docker Ollama → Claude API
- **Key Methods**:
  - `generate()` - Route to best available tier
  - `_try_desktop()` - Try desktop first
  - `_try_docker()` - Fallback to docker
  - `_try_claude()` - Last resort
- **Semantic Tags**: `#routing #3-tier #fallback #resilience #llm-selection`

---

### Processing Services (`src/services/processing/`)

**`NormalizerFactory`** (`normalizer_factory.py`)
- **Purpose**: Convert various file formats to markdown
- **Supported Formats**: .md, .py, .js, .ts, .json, .yaml, .txt, +20 more
- **Key Methods**:
  - `get_normalizer()` - Get normalizer for file type
  - `normalize()` - Convert to markdown
- **Semantic Tags**: `#normalization #markdown #conversion #formats #file-types`

---

## 3️⃣ Storage Layer (`src/storage/`)

### Database Management

**`__init__.py`**
- **Purpose**: Database initialization & session management
- **Key Functions**:
  - `init_database()` - Initialize PostgreSQL connection
  - `get_database()` - Get database instance
  - `get_session()` - Get async session
  - `close_database()` - Cleanup connections
- **Semantic Tags**: `#database #postgresql #sessions #sqlalchemy #async`

### ORM Models (`src/storage/db_models.py`)

**Total Tables**: 15+ tables

**Key Models**:
- `DocumentModel` - Core document storage
- `GitCommitModel` - Git commit history
- `IngestionJobModel` - Job tracking
- `TimelineModel` - Temporal analysis
- `TimePeriodModel` - Time periods
- `ContextNodeModel` - Tree nodes
- `RepositoryContextModel` - Repository metadata
- `DetectedServiceModel` - Microservice detection
- `ProcessingPlanModel` - Discovery plans
- `DocumentationRunModel` - Doc generation
- `QualityCheckModel` - Quality metrics
- `ModelRequestModel` - LLM usage tracking

**Semantic Tags**: `#orm #sqlalchemy #models #tables #schema #database`

### ChromaDB Client (`src/storage/chromadb_client.py`)

**Purpose**: Vector database client for semantic search

**Key Functions**:
- `init_chroma()` - Initialize ChromaDB
- `get_chroma_client()` - Get client instance
- `close_chroma()` - Cleanup

**Collection**: `ecosystem_documents`  
**Embedding Dimensions**: 768  
**Index Type**: HNSW

**Semantic Tags**: `#chromadb #vectors #embeddings #semantic-search #hnsw`

---

### Repositories (`src/storage/repositories/`)

**Purpose**: Data access layer (Repository pattern)

**Key Repositories**:
- `DocumentRepository` - Document CRUD
- `GitCommitRepository` - Git commit operations
- `IngestionJobRepository` - Job management
- `TimelineRepository` - Timeline operations
- `ContextNodeRepository` - Tree node operations
- `DocumentationRunRepository` - Doc run management

**Pattern**: Each repository provides:
- `create()` - Create entity
- `get()` - Retrieve by ID
- `list()` - List with filters
- `update()` - Update entity
- `delete()` - Delete entity

**Semantic Tags**: `#repository-pattern #data-access #crud #dao #persistence`

---

### Migrations (`src/storage/migrations/`)

**Total Migrations**: 13

**Migration Files** (chronological):
1. `001_initial_schema.py` - Initial tables
2. `002_add_ingestion_jobs.py` - Job tracking
3. `003_add_timelines.py` - Temporal analysis
4. `004_add_tree_context.py` - Tree nodes
5. `005_add_analysis_tables.py` - Discovery & analysis
6. `006_add_documentation_runs.py` - Doc generation
7. `007_add_quality_checks.py` - Quality metrics
8. `008_add_model_requests.py` - LLM tracking
9. `009_add_confidence_tracking.py` - Timeline confidence
10. `010_add_metadata_versioning.py` - Metadata schema version
11. `011_add_error_aggregation.py` - Error tracking
12. `012_add_retry_infrastructure.py` - Retry queues
13. `013_add_context_nodes_table.py` - Context nodes

**Semantic Tags**: `#migrations #schema #database #evolution #versioning`

---

## 4️⃣ Configuration Layer (`src/config/`)

### Settings (`src/config.py`)

**Purpose**: Application configuration from environment variables

**Key Settings**:
- `database_url` - PostgreSQL connection
- `redis_url` - Redis connection
- `chroma_collection_name` - ChromaDB collection
- `ollama_base_url` - Ollama API URL
- `model_strategy` - LLM routing strategy
- `embedding_model` - Embedding model name
- `database_pool_size` - Connection pool size
- `redis_max_connections` - Redis pool size

**Semantic Tags**: `#configuration #settings #environment #env-vars #config`

### Configuration Registry (`src/config/registry.py`)

**Purpose**: Centralized configuration management

**Key Classes**:
- `RegistryLoader` - Load service_registry.yaml
- `ServiceRegistry` - Pydantic model for registry

**File**: `service_registry.yaml`

**Semantic Tags**: `#registry #yaml #centralized-config #validation #pydantic`

### Configuration Types (`src/config/types.py`)

**Purpose**: Pydantic models for configuration validation

**Total Models**: 20+ configuration models

**Key Models**:
- `ServiceIdentityConfig` - Service identity
- `RedisConfig` - Redis configuration
- `DatabaseConfig` - PostgreSQL configuration
- `ChromaDBConfig` - ChromaDB configuration
- `OllamaConfig` - Ollama configuration
- `WorkersConfig` - Worker configuration
- `EmbeddingServiceConfig` - Embedding service config
- `ValidationConfig` - Validation rules

**Semantic Tags**: `#pydantic #validation #types #models #config-schema`

---

## 5️⃣ Utilities Layer (`src/utils/`)

### Core Utilities

**`logging_config.py`**
- **Purpose**: Configure structured logging
- **Features**: JSON logging, request IDs, correlation tracking
- **Semantic Tags**: `#logging #structured #json #correlation`

**`redis_client.py`**
- **Purpose**: Redis client singleton
- **Features**: Connection pooling, streams support
- **Semantic Tags**: `#redis #client #streams #cache #queue`

**`circuit_breaker.py`**
- **Purpose**: Circuit breaker pattern implementation
- **States**: CLOSED, OPEN, HALF_OPEN
- **Features**: Failure threshold, timeout, automatic recovery
- **Semantic Tags**: `#circuit-breaker #resilience #fault-tolerance #pattern`

**`retry.py`**
- **Purpose**: Retry decorator with exponential backoff
- **Features**: Configurable attempts, backoff multiplier, jitter
- **Semantic Tags**: `#retry #exponential-backoff #resilience #decorator`

**`resilience.py`**
- **Purpose**: Combined resilience decorator (circuit breaker + retry + timeout)
- **Decorator**: `@resilient()`
- **Semantic Tags**: `#resilience #decorator #combined #fault-tolerance`

**`cache_decorator.py`**
- **Purpose**: Response caching decorator
- **Decorator**: `@cache(ttl=300)`
- **Backend**: Redis
- **Semantic Tags**: `#cache #decorator #ttl #redis #memoization`

---

### Validation Utilities

**`config_validator.py`**
- **Purpose**: Validate service_registry.yaml
- **Key Functions**:
  - `validate_registry()` - Validate against schema
  - `check_required_keys()` - Ensure required keys present
- **Semantic Tags**: `#validation #config #yaml #schema`

**`jsonb_validator.py`**
- **Purpose**: Validate JSONB data
- **Features**: Schema validation, type checking
- **Semantic Tags**: `#validation #jsonb #json #schema`

**`system_validator.py`**
- **Purpose**: Validate system requirements
- **Checks**: Database, Redis, ChromaDB, Ollama connectivity
- **Semantic Tags**: `#validation #system #health #connectivity`

---

### Health Check Utilities

**`deep_health_check.py`**
- **Purpose**: Comprehensive dependency health checks
- **Checks**: PostgreSQL, Redis, ChromaDB, Ollama, disk space
- **Response**: Detailed health status with latencies
- **Semantic Tags**: `#health-check #deep #dependencies #monitoring`

**`worker_health.py`**
- **Purpose**: Worker heartbeat & health monitoring
- **Key Functions**:
  - `check_worker_health()` - Check worker status
  - `get_worker_heartbeat()` - Get last heartbeat
- **Semantic Tags**: `#worker #health #heartbeat #monitoring`

---

### Job Management Utilities

**`job_recovery.py`**
- **Purpose**: Recover failed/stale jobs
- **Key Functions**:
  - `recover_job()` - Retry failed job
  - `cleanup_stale_jobs()` - Remove old jobs
- **Semantic Tags**: `#jobs #recovery #cleanup #stale #retry`

**`job_events.py`**
- **Purpose**: Job event tracking
- **Events**: CREATED, STARTED, PROGRESS, COMPLETED, FAILED
- **Semantic Tags**: `#events #tracking #jobs #lifecycle`

---

### Path Utilities

**`host_path_resolver.py`**
- **Purpose**: Resolve paths between host and container
- **Key Functions**:
  - `resolve_host_path()` - Resolve host path for container
  - `resolve_container_path()` - Resolve container path for host
- **Features**: Bidirectional resolution, validation
- **Semantic Tags**: `#path #resolver #host #container #docker`

**`path_translator.py`**
- **Purpose**: Translate paths across file systems
- **Semantic Tags**: `#path #translation #filesystem`

---

### Date/Time Utilities

**`datetime_utils.py`**
- **Purpose**: UTC datetime handling
- **Key Functions**:
  - `ensure_utc_naive()` - Convert to UTC naive datetime
  - `ensure_utc_aware()` - Convert to UTC aware datetime
  - `parse_iso_datetime()` - Parse ISO 8601 strings
- **Semantic Tags**: `#datetime #utc #timezone #parsing`

---

### Monitoring Utilities

**`metrics.py`**
- **Purpose**: Prometheus metrics collection
- **Metrics**: Request counts, latencies, job metrics
- **Semantic Tags**: `#prometheus #metrics #monitoring #observability`

**`terminal_feedback.py`**
- **Purpose**: Terminal progress display
- **Features**: Progress bars, color output, spinners
- **Semantic Tags**: `#terminal #progress #ui #feedback #cli`

---

### Database Utilities

**`database_update_monitor.py`**
- **Purpose**: Monitor database updates
- **Features**: Change detection, audit logging
- **Semantic Tags**: `#database #monitoring #audit #changes`

**`pagination.py`**
- **Purpose**: Paginate database results
- **Key Functions**:
  - `paginate_query()` - Add LIMIT/OFFSET to query
  - `create_page_response()` - Create paginated response
- **Semantic Tags**: `#pagination #database #offset #limit`

---

### Error Handling Utilities

**`exceptions.py`**
- **Purpose**: Custom exception classes
- **Exceptions**:
  - `DatabaseError` - Database failures
  - `ChromaDBError` - Vector store failures
  - `EmbeddingError` - Embedding generation failures
  - `ConfigurationError` - Config validation failures
  - `JobProcessingError` - Job failures
- **Semantic Tags**: `#exceptions #errors #custom #error-handling`

**`partial_success.py`**
- **Purpose**: Handle partial success scenarios
- **Use Case**: Some documents succeed, some fail
- **Semantic Tags**: `#partial-success #error-handling #graceful-degradation`

---

### Startup Utilities

**`preflight.py`**
- **Purpose**: Pre-flight checks before startup
- **Checks**: Config validation, database connectivity, service health
- **Semantic Tags**: `#preflight #startup #validation #health-checks`

**`graceful_shutdown.py`**
- **Purpose**: Handle graceful application shutdown
- **Features**: Cleanup resources, close connections, finish in-flight requests
- **Semantic Tags**: `#shutdown #cleanup #graceful #signal-handling`

---

## 6️⃣ Data Models (`src/models/`)

### Pydantic Models

**`ingestion.py`**
- **Purpose**: Ingestion request/response models
- **Models**:
  - `IngestRequest` - Ingestion job request
  - `IngestResponse` - Ingestion job response
  - `JobStatus` - Job status model
- **Semantic Tags**: `#pydantic #models #ingestion #validation`

**`documentation.py`**
- **Purpose**: Documentation generation models
- **Models**:
  - `DocumentationRequest` - Generation request
  - `DocumentationResponse` - Generation response
- **Semantic Tags**: `#pydantic #models #documentation #generation`

---

## 📚 LLM Agent Navigation Guide

### Finding Code By Purpose

**Question**: "Where is RAG implemented?"  
**Answer**: `src/services/rag/` - RAGService, EnhancedRAGService, ContextAwareRAG, TemporalRAGService, MultiPassQueryService

**Question**: "How are embeddings generated?"  
**Answer**: `src/services/embeddings/embedding_service.py` - EmbeddingService with FastEmbed/Ollama backends

**Question**: "Where is the ingestion pipeline?"  
**Answer**: `src/services/ingestion/job_processor.py` - JobProcessor (4174 lines), plus SnapshotProcessor, EnhancedJobProcessor

**Question**: "How does the API work?"  
**Answer**: `src/api/app.py` - FastAPI application with 51 route modules in `src/api/routes/`

**Question**: "Where is database code?"  
**Answer**: `src/storage/` - ORM models (db_models.py), repositories, ChromaDB client, Redis client

**Question**: "How is configuration managed?"  
**Answer**: `src/config/` - Settings (config.py), Registry (registry.py), Types (types.py)

**Question**: "Where are utilities?"  
**Answer**: `src/utils/` - Logging, caching, retries, circuit breakers, health checks, validation

---

### Finding Code By Feature

**Feature**: Multi-Pass RAG  
**Location**: `src/services/rag/multi_pass_query.py`  
**Class**: `MultiPassQueryService`

**Feature**: Temporal RAG  
**Location**: `src/services/rag/temporal_rag_service.py`  
**Class**: `TemporalRAGService`

**Feature**: Tree Context  
**Location**: `src/services/tree/`  
**Classes**: `TreeBuilder`, `TreeQueryService`

**Feature**: Worker Management  
**Location**: `src/services/ingestion/` + `src/utils/worker_health.py`

**Feature**: Retry Logic  
**Location**: `src/utils/retry.py` + `src/utils/resilience.py`

**Feature**: Circuit Breakers  
**Location**: `src/utils/circuit_breaker.py`

---

### Finding Code By Technology

**PostgreSQL**: `src/storage/db_models.py`, `src/storage/__init__.py`  
**ChromaDB**: `src/storage/chromadb_client.py`  
**Redis**: `src/utils/redis_client.py`  
**FastAPI**: `src/api/app.py`, `src/api/routes/`  
**Ollama**: `src/services/models/ollama_client.py`, `src/services/embeddings/`  
**Pydantic**: `src/models/`, `src/config/types.py`  
**SQLAlchemy**: `src/storage/db_models.py`, `src/storage/repositories/`

---

## 🔗 Related Documentation

- [Architecture Overview](architecture/OVERVIEW.md) - System design
- [Database Schema](DATABASE_SCHEMA.md) - Complete schema reference
- [API Reference](API_ENDPOINTS_COMPLETE.md) - All endpoints
- [Ingestion Guide](features/INGESTION_COMPLETE.md) - Ingestion pipeline
- [Configuration Guide](guides/CONFIGURATION.md) - Config reference

---

## 🏷️ Complete Tag Index

### By Category
- **Architecture**: `#architecture #system #design #components`
- **API**: `#api #rest #endpoints #routes #fastapi`
- **Database**: `#database #postgresql #chromadb #redis #orm #sqlalchemy`
- **RAG**: `#rag #llm #semantic-search #qa #retrieval #generation`
- **Ingestion**: `#ingestion #pipeline #git #processing #workers`
- **Utilities**: `#utils #helpers #retry #cache #logging #monitoring`
- **Configuration**: `#config #settings #registry #validation`
- **Embeddings**: `#embeddings #vectors #fastembed #ollama`
- **Testing**: `#tests #unit #integration #e2e`

### By Technology
- **Python**: `#python #async #asyncio #decorators`
- **FastAPI**: `#fastapi #routes #middleware #openapi`
- **PostgreSQL**: `#postgresql #sql #database #tables`
- **ChromaDB**: `#chromadb #vectors #hnsw #embeddings`
- **Redis**: `#redis #cache #queue #streams`
- **Ollama**: `#ollama #llm #local-models`
- **Docker**: `#docker #containers #compose`
- **Git**: `#git #version-control #history`

### By Function
- **CRUD**: `#create #read #update #delete #crud`
- **Search**: `#search #query #filter #semantic #temporal`
- **Processing**: `#processing #pipeline #transformation #normalization`
- **Monitoring**: `#monitoring #health #metrics #observability`
- **Error Handling**: `#errors #exceptions #retry #resilience`
- **Performance**: `#performance #optimization #caching #batching`

---

**Last Updated**: 2025-10-28  
**Total Source Files**: 100+ Python files  
**Total Lines of Code**: ~50,000 lines  
**Status**: Production-Ready  
**LLM Optimization**: ✅ Complete


