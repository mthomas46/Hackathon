# Ecosystem MCP Platform - Technical Design Document

**Version:** 1.0.0  
**Date:** October 17, 2025  
**Status:** ✅ Production Ready  
**Author:** Engineering Team

---

## Summary

The **Ecosystem MCP Platform** is an intelligent refactoring knowledge base and RAG (Retrieval Augmented Generation) system that enables AI agents and developers to access, analyze, and learn from project documentation. The platform consists of three microservices:

1. **ecosystem-mcp** - Core service (FastAPI) with MCP integration, document ingestion, RAG, and embedding generation
2. **ecosystem-mcp-dashboard** - Streamlit-based management interface for monitoring and operations
3. **ecosystem-mcp-embedding** - Dedicated FastEmbed/ONNX service for high-performance embedding generation (10-50× faster than Ollama)

---

## Business Objective(s)

### Primary Objectives

✅ **Developer Productivity Enhancement**
- Enable rapid access to historical refactoring patterns and documentation
- Reduce time spent searching for implementation examples
- Provide AI-powered recommendations based on actual project history

✅ **Knowledge Preservation & Transfer**
- Capture and index complete git history with versioning
- Enable semantic search across all documentation
- Preserve institutional knowledge through content-addressable storage

✅ **AI-Powered Development Workflow**
- Integration with Cursor IDE via Model Context Protocol (MCP)
- Intelligent model routing (Ollama local → Cursor free → Claude premium)
- Cost-optimized AI operations with intelligent tier selection

✅ **Enterprise-Grade Operations**
- Production-ready monitoring and observability
- Fault-tolerant document ingestion with recovery
- Horizontal scaling capabilities for high throughput

---

## Functional Requirements

### User Journey: Developer

1. **Initial Setup:**
   - Configure MCP connection in Cursor IDE
   - Start services via docker-compose
   - Validate health via dashboard

2. **Document Ingestion:**
   - Select repository path (host or container)
   - Choose ingestion mode (quick/standard/historical/full)
   - Monitor real-time progress via dashboard
   - Resume from checkpoint on interruption

3. **Semantic Search:**
   - Ask natural language questions via RAG interface
   - Receive context-aware answers with source citations
   - View document versions and git history
   - Export results for offline use

4. **Multi-Pass RAG:**
   - Submit complex queries requiring iterative refinement
   - Monitor 5-pass iterative improvement process
   - Receive comprehensive answers with analysis

5. **Monitoring & Operations:**
   - View system health and metrics
   - Monitor cache hit rates and performance
   - Manage ingestion jobs (cancel, retry, clear)
   - Generate embeddings on demand

### User Journey: Administrator

1. **System Management:**
   - Monitor service health across all components
   - View and manage Docker containers
   - Access PostgreSQL/Redis/ChromaDB directly
   - Configure system parameters

2. **Performance Tuning:**
   - View cache analytics and hit rates
   - Monitor embedding generation performance
   - Adjust batch sizes and parallelism
   - Enable/disable optimizations

3. **Troubleshooting:**
   - Access centralized logs
   - View git error classifications
   - Monitor worker health and queues
   - Trigger manual recovery operations

### Happy Path

**Document Ingestion → RAG Query → Result:**

```
1. User starts ingestion (POST /api/v1/admin/ingest)
   → Validates git repository
   → Creates ingestion job
   → Worker picks up job from Redis stream

2. Background Worker processes documents:
   → Scans git history (parallel commit processing)
   → Bloom filter checks for duplicates (2× speedup)
   → Normalizes content (Python/Markdown/Text)
   → Generates embeddings via FastEmbed service (10-50× faster)
   → Stores in PostgreSQL + ChromaDB

3. User submits RAG query (POST /api/v1/query/enhanced)
   → Generates query embedding via FastEmbed
   → Searches ChromaDB for similar documents
   → Retrieves top N results
   → Routes to appropriate LLM (Ollama/Cursor/Claude)
   → Returns answer with source citations

4. Results displayed in dashboard:
   → Answer with confidence score
   → Source documents with links
   → Performance metrics (timing, cache hits)
   → Option to regenerate or refine
```

### Exceptional Cases

**Connection Failures:**
- Embedding service unavailable → Automatic fallback to Ollama
- Redis disconnected → Graceful degradation (no caching, no job queue)
- PostgreSQL down → Service returns HTTP 503, monitoring alerts

**Data Integrity:**
- Duplicate documents → Bloom filter + content hash deduplication
- Git corruption → Centralized error handler with skip/retry logic
- Failed embeddings → Transaction rollback, job marked as partial failure

**Resource Constraints:**
- Memory pressure → Lazy loading/unloading of embedding models (auto-unload after 5 min)
- High load → Horizontal scaling of embedding service (linear throughput)
- Queue backup → Orphaned job detection and cleanup

**User Errors:**
- Invalid path → Pre-flight validation with helpful error messages
- Non-git repository → Detect and offer temporal versioning fallback
- Insufficient permissions → Clear error with remediation steps

### Expected Limitations

- **Git Repository Size:** Optimal for repositories < 10GB. Larger repos may require full ingestion mode with extended processing time (1-3 hours).
- **Embedding Storage:** ChromaDB performs best with < 100K documents. Beyond this, search latency may increase.
- **Concurrent Writes:** ChromaDB uses single-writer model. Parallel ingestion uses Redis stream coordination.
- **Model Context Window:** LLM responses limited by model context (8K tokens for Llama 3.1, 200K for Claude).
- **Real-time Updates:** Ingestion is near-real-time (minutes), not instantaneous. Designed for batch processing.

---

## Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ECOSYSTEM MCP PLATFORM                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              ECOSYSTEM-MCP-DASHBOARD (Port 8501)             │  │
│  │                        (Streamlit)                            │  │
│  │                                                               │  │
│  │  • Home  • Health  • RAG Query  • Multi-Pass RAG            │  │
│  │  • Documents  • Ingestion Manager  • ChromaDB Explorer       │  │
│  │  • Embeddings Manager  • Cache Analytics  • Metrics          │  │
│  │  • Doc Generator  • Recovery Manager  • Timeline Viewer      │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │ HTTP                                 │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │          ECOSYSTEM-MCP-SERVICE (Port 8000)                   │  │
│  │                  (FastAPI + MCP)                              │  │
│  │                                                               │  │
│  │  API Layer (50+ endpoints):                                  │  │
│  │  • /api/v1/query/enhanced - RAG queries                      │  │
│  │  • /api/v1/admin/ingest - Document ingestion                 │  │
│  │  • /api/v1/documents - Document CRUD                         │  │
│  │  • /api/v1/admin/embeddings - Embedding management           │  │
│  │  • /api/v1/infrastructure - Health & diagnostics             │  │
│  │                                                               │  │
│  │  Services:                                                    │  │
│  │  • IngestionWorker (background, Redis Streams)               │  │
│  │  • JobProcessor (parallel commit processing, 2×CPU cores)    │  │
│  │  • RAGService (semantic search + LLM generation)             │  │
│  │  • ModelRouter (Ollama → Cursor → Claude)                    │  │
│  │  • GitService (versioning, history traversal)                │  │
│  │  • CheckpointManager (resumable operations)                  │  │
│  │  • CommitOptimizer (Bloom filter, batch checks)              │  │
│  └───────┬────────────┬────────────┬──────────────┬─────────────┘  │
│          │            │            │              │                 │
│          ▼            ▼            ▼              ▼                 │
│  ┌──────────────┐ ┌─────────┐ ┌─────────┐ ┌────────────────────┐  │
│  │  PostgreSQL  │ │  Redis  │ │ChromaDB │ │ EMBEDDING-SERVICE  │  │
│  │   (5432)     │ │ (6379)  │ │ (embed) │ │     (8001)         │  │
│  │              │ │         │ │         │ │                    │  │
│  │ • Documents  │ │ • Queue │ │ •Vectors│ │ • FastEmbed/ONNX   │  │
│  │ • Embeddings │ │ • Cache │ │ •Search │ │ • 10-50× faster    │  │
│  │ • Jobs       │ │ • PubSub│ │ •HNSW   │ │ • Redis cache      │  │
│  │ • Versions   │ │ • Bloom │ │         │ │ • Lazy load/unload │  │
│  └──────────────┘ └─────────┘ └─────────┘ └────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    External LLM Services                      │  │
│  │                                                               │  │
│  │  • Ollama (M4 Max, local) - llama3.1:8b, mistral:7b          │  │
│  │  • Cursor Free Tier - haiku, gpt-3.5-turbo                   │  │
│  │  • Claude (Anthropic) - sonnet-4.5, opus (premium)           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation

### Class Diagrams & Core Objects

#### ecosystem-mcp-service

**Domain Models:**
```python
# src/models/document.py
class Document(BaseModel):
    id: str
    file_path: str
    content_hash: str  # SHA-256 for deduplication
    git_commit_sha: Optional[str]
    git_author: Optional[str]
    git_timestamp: Optional[datetime]
    normalized_content: str
    embedding_id: Optional[str]
    is_latest: bool = True
    created_at: datetime
    updated_at: datetime

# src/models/embedding.py
class Embedding(BaseModel):
    id: str
    document_id: str
    vector: List[float]  # 768 dimensions (BGE/nomic-embed-text)
    model: str
    dimensions: int
    created_at: datetime

# src/models/ingestion.py
class IngestionJob(BaseModel):
    id: str
    repo_path: str
    mode: IngestionMode  # quick/standard/historical/full
    status: JobStatus  # queued/processing/completed/failed
    total_documents: int
    processed_documents: int
    skipped_documents: int
    failed_documents: int
    total_embeddings: int
    checkpoint_data: Optional[Dict]  # For recovery
    error_summary: Optional[Dict]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

**Key Services:**
```python
# src/services/ingestion/job_processor.py
class JobProcessor:
    """Orchestrates document ingestion with parallel processing."""
    
    def __init__(
        self,
        worker_id: str,
        use_batch_optimization: bool = True,
        max_concurrent_commits: Optional[int] = None  # Auto-tune to 2×CPU
    )
    
    async def process_job(self, job: IngestionJob) -> JobResult:
        """Process ingestion job with checkpointing and recovery."""
        # Phase 1: Git history scan
        # Phase 2: Parallel commit processing (2×CPU cores)
        # Phase 3: Batch embedding generation
        # Phase 4: Database persistence

# src/services/rag/rag_service.py
class RAGService:
    """Retrieval Augmented Generation orchestration."""
    
    async def query(
        self,
        question: str,
        n_results: int = 5,
        tier: TierPreference = TierPreference.DESKTOP,
        response_length: ResponseLength = ResponseLength.MEDIUM
    ) -> RAGResponse:
        """Execute RAG query with intelligent model routing."""
        # 1. Generate query embedding (FastEmbed)
        # 2. Search ChromaDB for similar documents
        # 3. Route to appropriate LLM tier
        # 4. Generate answer with citations
        # 5. Return response with metadata

# src/services/embeddings/embedding_service.py
class EmbeddingService:
    """Unified embedding generation with automatic fallback."""
    
    async def generate_embedding(self, text: str) -> EmbeddingResult:
        """Generate embedding with FastEmbed, fallback to Ollama."""
        # Primary: FastEmbed service (10-50× faster)
        # Fallback: Ollama nomic-embed-text
```

#### ecosystem-mcp-embedding

**FastEmbed Service:**
```python
# src/services/fastembed_service.py
class FastEmbedService:
    """ONNX-optimized embedding generation with lazy loading."""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
        use_quantization: bool = True,  # INT8 (~50% memory reduction)
        use_memory_mapping: bool = True,  # Faster loading
        lazy_loading: bool = False,  # Load on demand
        auto_unload_timeout: int = 300  # Auto-unload after 5 min
    )
    
    async def generate_embedding(self, text: str) -> EmbeddingResult:
        """Generate single embedding (~7-12ms when loaded)."""
        self._ensure_loaded()  # Lazy load if needed
        # 1. Generate embedding via ONNX
        # 2. Check Redis cache
        # 3. Return result with timing
    
    async def generate_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """TRUE batch processing (10-50× faster than sequential)."""
        # 1. Check Redis cache for each text
        # 2. Generate embeddings for cache misses (batched)
        # 3. Store new embeddings in cache
        # 4. Return all results
```

#### ecosystem-mcp-dashboard

**Dashboard Views:**
```python
# dashboard_views/home.py
def show(api_base_url: str):
    """Home page with service overview and quick actions."""

# dashboard_views/ingestion_manager.py
def show(api_base_url: str):
    """Ingestion job management and monitoring."""
    # • Start new ingestion (path selection, mode)
    # • Monitor active jobs (real-time progress)
    # • View completed jobs (statistics, errors)
    # • Clear completed/failed jobs

# dashboard_views/rag.py
def show(api_base_url: str):
    """Single-pass RAG query interface."""
    # • Question input
    # • Configuration (n_results, temperature, length)
    # • Submit query
    # • Display results with sources

# dashboard_views/embeddings_manager.py
def show(api_base_url: str):
    """Embedding regeneration and management."""
    # • View embedding statistics
    # • Regenerate missing embeddings
    # • Monitor generation progress
    # • Visualizations (t-SNE, UMAP)
```

### Services Changed & Scope

#### ecosystem-mcp-service (Core API & Ingestion)

**New Functionality:**
- ✅ FastEmbed integration with automatic fallback
- ✅ Bloom filter duplicate detection (Phase 2 optimization)
- ✅ Parallel commit processing (auto-tuned to 2×CPU cores)
- ✅ Performance indexes on PostgreSQL
- ✅ Multi-level caching (L1 LRU + L2 Redis)
- ✅ Job recovery and checkpointing
- ✅ Git error classification and handling
- ✅ Temporal versioning for non-git content
- ✅ Documentation run management

**Modified Functionality:**
- ✅ Ingestion pipeline (optimized for 10× speedup)
- ✅ Embedding generation (delegated to embedding service)
- ✅ RAG query (response length control added)
- ✅ Health checks (embedding service integration)

**API Changes:**
- ✅ Added `GET /api/v1/admin/cache/stats` - Cache analytics
- ✅ Added `POST /api/v1/admin/optimization/indexes/create` - Apply DB indexes
- ✅ Added `GET /api/v1/admin/embeddings/regenerate` - Regenerate embeddings
- ✅ Added `POST /api/v1/admin/documentation/generate` - Generate documentation

#### ecosystem-mcp-embedding (New Service)

**Scope:**
- ✅ Dedicated FastEmbed/ONNX service
- ✅ Redis caching (embeddings + normalization)
- ✅ Lazy loading/unloading (memory optimization)
- ✅ INT8 quantization (~50% memory reduction)
- ✅ TRUE batch processing (10-50× faster)
- ✅ Health monitoring and metrics

**API Endpoints:**
- ✅ `POST /embed/single` - Generate single embedding
- ✅ `POST /embed/batch` - Generate batch embeddings
- ✅ `GET /embed/info` - Model and cache info
- ✅ `GET /health` - Health check
- ✅ `GET /analytics/performance` - Performance metrics

#### ecosystem-mcp-dashboard (Management UI)

**New Pages:**
- ✅ Ingestion Manager (start, monitor, recover)
- ✅ Embeddings Manager (regenerate, visualize)
- ✅ ChromaDB Explorer (browse, analyze, visualize)
- ✅ Document Viewer (paginated, filtered browsing)
- ✅ Documentation Generator (with run management)
- ✅ Cache Analytics (hit rates, performance)
- ✅ Job Recovery Manager (resume interrupted jobs)
- ✅ Timeline Viewer (temporal versioning queries)

**Enhanced Pages:**
- ✅ RAG Query (response length control: S/M/L/XL)
- ✅ Multi-Pass RAG (5-pass iterative refinement)
- ✅ Health & Infrastructure (detailed diagnostics)
- ✅ Metrics (cache analytics, embedding quality)

### Domain Models

**Document Lifecycle:**
```
Git Repository
    ↓ (git ls-files / git log)
Scanner
    ↓ (detect file types, extract metadata)
Parser
    ↓ (parse Python/Markdown/Text)
Normalizer
    ↓ (convert to markdown, clean)
Content-Addressable Storage
    ↓ (SHA-256 hash, deduplication)
Embedding Generation
    ↓ (FastEmbed or Ollama)
Storage
    ↓
PostgreSQL (metadata) + ChromaDB (vectors)
```

**Embedding Caching:**
```
Text Input
    ↓
Content Hash (SHA-256)
    ↓
Redis Check (L2 cache)
    ↓ (cache miss)
FastEmbed Generation
    ↓
Redis Store (30 day TTL)
    ↓
Return Embedding
```

### Business Process Definition

**Document Ingestion Process:**

1. **Validation Phase:**
   - Validate repository path exists
   - Check git repository (or offer temporal versioning)
   - Validate user permissions
   - Create ingestion job record

2. **Scanning Phase:**
   - Scan git history based on mode
   - Build file list with commit info
   - Apply filters (file types, patterns)
   - Estimate total documents

3. **Processing Phase (Parallel):**
   - Load checkpoint if resuming
   - Process commits in parallel (2×CPU cores)
   - Bloom filter duplicate check (fast negative)
   - Batch content hash check (database)
   - Parse and normalize new documents
   - Generate embeddings via FastEmbed (batched)
   - Store in PostgreSQL + ChromaDB
   - Update checkpoint periodically

4. **Finalization Phase:**
   - Mark old versions as `is_latest=false`
   - Update job statistics
   - Generate error summary
   - Clean up temporary resources
   - Trigger completion notifications

**RAG Query Process:**

1. **Query Preprocessing:**
   - Validate input (length, format)
   - Extract query parameters
   - Determine complexity for tier routing

2. **Embedding Generation:**
   - Generate query embedding (FastEmbed)
   - Check cache (likely miss for queries)
   - Return in ~7-12ms

3. **Retrieval Phase:**
   - Search ChromaDB with embedding
   - Apply filters (service, date range)
   - Retrieve top N results
   - Fetch full documents from PostgreSQL

4. **Generation Phase:**
   - Route to appropriate LLM tier
   - Construct prompt with context
   - Generate answer with citations
   - Parse and validate response

5. **Response Formatting:**
   - Format answer with markdown
   - Add source citations with links
   - Include metadata (timing, model, cache hits)
   - Return to user

### Implementation Phases

**✅ Phase 1: Foundation (Completed)**
- Core ingestion pipeline
- PostgreSQL + ChromaDB + Redis setup
- Basic RAG query
- Dashboard skeleton
- Batch operations (100× fewer DB queries)
- Connection pooling

**✅ Phase 2: Speed Optimizations (Completed)**
- Bloom filter duplicate detection
- Parallel commit processing (2×CPU cores)
- Database indexes
- FastEmbed integration
- Automatic Ollama fallback

**✅ Phase 3: Memory Optimizations (Completed)**
- INT8 quantization (~50% memory reduction)
- Memory-mapped model loading
- Lazy loading/unloading (auto-unload after 5 min)
- Separate embedding service architecture

**✅ Phase 4: Advanced Features (Completed)**
- Multi-level caching (L1 LRU + L2 Redis)
- Cache analytics dashboard
- Embedding quality metrics
- Job recovery and checkpointing
- Git error classification
- Temporal versioning
- Documentation run management

**🎯 Phase 5: Production Hardening (Future)**
- Horizontal scaling tests
- Load balancing configuration
- Prometheus/Grafana integration
- Alert management
- Backup/restore procedures
- Disaster recovery plan

---

## Limitations/Unsupported Scenarios

### What This Feature ISN'T Designed To Do

❌ **Real-time Document Indexing**
- **Why:** Ingestion is batch-oriented (minutes), not instantaneous
- **Alternative:** Manual re-ingestion or periodic scheduled jobs

❌ **Multi-tenant Isolation**
- **Why:** Single PostgreSQL database, no tenant partitioning
- **Alternative:** Deploy separate instances per tenant

❌ **Document Editing/Authoring**
- **Why:** Read-only system focused on retrieval, not creation
- **Alternative:** Edit documents externally, re-ingest

❌ **Binary File Analysis**
- **Why:** Limited to text-based formats (code, markdown, text)
- **Alternative:** Extract text from PDFs/DOCX externally

❌ **Real-time Collaboration**
- **Why:** No WebSocket streaming, no user presence
- **Alternative:** Poll API for updates (dashboard auto-refresh)

### Other Documented Limitations

- **ChromaDB Write Concurrency:** Single-writer model prevents concurrent ChromaDB writes. Use Redis stream coordination.
- **Context Window Limits:** LLM responses constrained by model context (8K-200K tokens).
- **Embedding Model Fixed:** BGE-base-en-v1.5 (768 dims) for consistency. Cannot mix models.
- **No Fine-tuning:** Uses pre-trained models only. No custom model training.
- **Git Repository Required:** Optimal workflow requires git repo. Temporal versioning available as fallback.

---

## ETL

### Analytics Export

**Current State:**
- No dedicated analytics export pipeline

**Future Requirements:**
- Export ingestion job statistics (daily/weekly aggregates)
- Export query analytics (popular questions, hit rates)
- Export cache performance (hit/miss rates, memory usage)
- Export embedding quality metrics (coverage, generation times)

**Recommended Approach:**
- Scheduled PostgreSQL queries → CSV/JSON export
- Grafana integration for real-time dashboards
- Data warehouse integration (Snowflake, BigQuery) if needed

---

## Analytics

**Dashboard/Widgets Supported:**

1. **Home Dashboard:**
   - Service health overview
   - Recent activity feed
   - Quick action buttons

2. **Cache Performance:**
   - Real-time hit/miss rates
   - Per-prefix analytics
   - Memory usage trends
   - Performance graphs

3. **Ingestion Metrics:**
   - Job status distribution
   - Document processing rates
   - Error classifications
   - Throughput over time

4. **Embedding Analytics:**
   - Generation performance (FastEmbed vs Ollama)
   - Cache efficiency
   - Coverage statistics
   - Quality metrics

5. **ChromaDB Explorer:**
   - Collection statistics
   - Document distribution
   - Embedding visualizations (t-SNE, UMAP)
   - Similarity heatmaps

---

## Data Model

### New Collections (PostgreSQL)

#### `documents` Table

| Field | Type | Optional | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `file_path` | TEXT | No | Relative path in repo |
| `content_hash` | VARCHAR(64) | No | SHA-256 of normalized content |
| `git_commit_sha` | VARCHAR(40) | Yes | Git commit SHA (if from git) |
| `git_author` | VARCHAR(255) | Yes | Git author email |
| `git_timestamp` | TIMESTAMP | Yes | Git commit timestamp |
| `normalized_content` | TEXT | No | Markdown-normalized content |
| `embedding_id` | UUID | Yes | Foreign key to embeddings |
| `is_latest` | BOOLEAN | No | Is this the latest version? |
| `metadata` | JSONB | Yes | Additional metadata |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Last update time |

**Indexes:**
- `ix_documents_file_path` on `(file_path)` - Fast path lookups
- `ix_documents_git_commit_sha` on `(git_commit_sha)` - Git history queries
- `ix_documents_is_latest` on `(is_latest)` - Current version queries
- `ix_documents_content_hash` on `(content_hash)` - Deduplication

#### `embeddings` Table

| Field | Type | Optional | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `document_id` | UUID | No | Foreign key to documents |
| `vector` | ARRAY[FLOAT] | No | 768-dimensional vector |
| `model` | VARCHAR(100) | No | Model used (BGE/nomic) |
| `dimensions` | INTEGER | No | Vector dimensions (768) |
| `created_at` | TIMESTAMP | No | Generation timestamp |

**Indexes:**
- `ix_embeddings_document_id` on `(document_id)` - Document lookups

#### `ingestion_jobs` Table

| Field | Type | Optional | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `repo_path` | TEXT | No | Repository path |
| `mode` | VARCHAR(20) | No | quick/standard/historical/full |
| `status` | VARCHAR(20) | No | queued/processing/completed/failed |
| `total_documents` | INTEGER | No | Total discovered |
| `processed_documents` | INTEGER | No | Successfully processed |
| `skipped_documents` | INTEGER | No | Skipped (duplicates) |
| `failed_documents` | INTEGER | No | Failed to process |
| `total_embeddings` | INTEGER | No | Embeddings generated |
| `checkpoint_data` | JSONB | Yes | Recovery checkpoint |
| `error_summary` | JSONB | Yes | Error classifications |
| `created_at` | TIMESTAMP | No | Job creation time |
| `started_at` | TIMESTAMP | Yes | Processing start |
| `completed_at` | TIMESTAMP | Yes | Processing completion |

**Indexes:**
- `ix_ingestion_jobs_status` on `(status)` - Active job queries

#### `documentation_runs` Table (New)

| Field | Type | Optional | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `config` | JSONB | No | Generation configuration |
| `status` | VARCHAR(20) | No | running/completed/failed |
| `documents_generated` | INTEGER | No | Count of generated docs |
| `created_at` | TIMESTAMP | No | Run start time |
| `completed_at` | TIMESTAMP | Yes | Run completion |

### Modification to Existing Collections

**None.** All tables are newly created for this platform.

### Backward Compatibility

**N/A** - New system with no legacy data migration required.

### Evolution Process

**Adding New Fields:**
1. Create Alembic migration script
2. Add field with `nullable=True` initially
3. Backfill data if needed
4. Make field `nullable=False` in subsequent migration

**Example:**
```python
# alembic/versions/add_file_size.py
def upgrade():
    op.add_column('documents', sa.Column('file_size', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('documents', 'file_size')
```

### New Database Required?

**Yes** - PostgreSQL database `ecosystem_mcp` is required.

**Additional Databases:**
- ChromaDB (embedded, file-based) - for vector storage
- Redis (in-memory) - for caching, queuing, pub/sub

### Data Migration Required?

**No** - New system with clean schema.

**Future Migrations:**
- Phase 1 → Phase 2: Add performance indexes (no downtime)
- Phase 2 → Phase 3: No schema changes
- Phase 3 → Phase 4: Add `documentation_runs` table (no downtime)

---

## REST API(s)

### New APIs

#### ecosystem-mcp-service (Port 8000)

**Ingestion:**
- `POST /api/v1/admin/ingest` - Start ingestion job
  - **Auth:** None (internal)
  - **Payload:** `{"repo_path": str, "mode": str, "target_subdirectory": Optional[str]}`
  - **Response:** `{"job_id": str, "status": str}`

**RAG Query:**
- `POST /api/v1/query/enhanced` - Execute RAG query
  - **Auth:** None (internal)
  - **Payload:** `{"question": str, "n_results": int, "temperature": float, "response_length": str}`
  - **Response:** `{"answer": str, "sources": List[Dict], "metadata": Dict}`

**Embeddings:**
- `POST /api/v1/admin/embeddings/regenerate` - Regenerate missing embeddings
  - **Auth:** None (internal)
  - **Payload:** `{"force": bool}`
  - **Response:** `{"regenerated_count": int, "status": str}`

**Infrastructure:**
- `GET /api/v1/infrastructure/health` - Detailed health check
  - **Auth:** None
  - **Response:** `{"status": str, "components": Dict}`

**Cache:**
- `GET /api/v1/admin/cache/stats` - Cache analytics
  - **Auth:** None (internal)
  - **Response:** `{"hit_rate": float, "memory_used": int, "keys": int}`

#### ecosystem-mcp-embedding (Port 8001)

**Embeddings:**
- `POST /embed/single` - Generate single embedding
  - **Auth:** None (internal service-to-service)
  - **Payload:** `{"text": str, "model": Optional[str]}`
  - **Response:** `{"embedding": List[float], "dimensions": int, "cached": bool, "duration_ms": float}`

- `POST /embed/batch` - Generate batch embeddings
  - **Auth:** None (internal)
  - **Payload:** `{"texts": List[str], "model": Optional[str]}`
  - **Response:** `{"embeddings": List[List[float]], "cache_hits": int, "duration_ms": float}`

**Analytics:**
- `GET /analytics/performance` - Performance metrics
  - **Auth:** None (internal)
  - **Response:** `{"avg_generation_ms": float, "speedup_factor": float, "cache_hit_rate": float}`

### Enhancements to Existing APIs

**RAG Query - Response Length Control:**
```json
// Before
POST /api/v1/query/enhanced
{
  "question": "How does ingestion work?",
  "n_results": 5
}

// After
POST /api/v1/query/enhanced
{
  "question": "How does ingestion work?",
  "n_results": 5,
  "response_length": "M"  // S (50-150 chars), M (150-400), L (400-800), XL (800-1500)
}
```

### New Service?

**Yes** - `ecosystem-mcp-embedding` is a new dedicated microservice.

**Rationale:**
- ✅ Fault isolation (embedding service crash doesn't affect main service)
- ✅ Horizontal scaling (scale embedding service independently)
- ✅ Resource optimization (dedicated hardware for ONNX/CPU)
- ✅ Independent deployment (update embedding service without main service downtime)

### Security

**Routes WITHOUT Security:**
- All routes - **Justification:** Internal service, runs in Docker private network

**Future Enhancements:**
- API key authentication for external access
- JWT tokens for dashboard → API communication
- Rate limiting per client IP
- CORS configuration for browser access

### Deviations from Standards

**None** - Follows FastAPI/RESTful best practices:
- ✅ OpenAPI/Swagger documentation
- ✅ Standard HTTP status codes
- ✅ JSON request/response format
- ✅ Versioned API paths (`/api/v1/`)

---

## UI

### Mockups

**Status:** No formal mockups. Dashboard built iteratively with Streamlit.

**Sign-off:** Internal project, no external approval required.

### New Pages/Routes

1. **Home** (`/`) - Service overview
2. **Health & Infrastructure** (`/Health_&_Infrastructure`) - Component health
3. **RAG Query** (`/RAG_Query`) - Single-pass query
4. **Multi-Pass RAG Query** (`/Multi-Pass_RAG_Query`) - Iterative refinement
5. **Documents** (`/Documents`) - Document browser
6. **Ingestion Manager** (`/Ingestion_Manager`) - Job management
7. **ChromaDB Explorer** (`/ChromaDB_Explorer`) - Vector database explorer
8. **Embeddings Manager** (`/Embeddings_Manager`) - Embedding operations
9. **Documentation Generator** (`/Documentation_Generator`) - Generate docs
10. **Cache Analytics** (`/Cache_Analytics`) - Cache performance
11. **Metrics** (`/Metrics`) - System metrics
12. **Settings** (`/Settings`) - Configuration

### Removed Routes

**None** - All pages are new.

### New Artifacts/Dependencies

**Python Packages:**
- `streamlit>=1.32.0` - Dashboard framework
- `fastapi>=0.110.0` - API framework
- `fastembed>=0.2.0` - ONNX embeddings
- `chromadb>=0.4.0` - Vector database
- `sqlalchemy>=2.0.0` - PostgreSQL ORM
- `redis>=5.0.0` - Caching and queuing
- `httpx>=0.27.0` - HTTP client
- `pydantic>=2.0.0` - Data validation

**System Dependencies:**
- PostgreSQL 15+
- Redis 7+
- Python 3.11+
- Docker 24+

### CloudFlare CDN

**Not applicable** - Internal service, no static assets served via CDN.

### Third-Party Systems

**None** - No customized pages in Zuora, SF, Okta, etc.

---

## Integration(s)

### Internal Integrations

**ecosystem-mcp-service ↔ ecosystem-mcp-embedding:**
- **Protocol:** HTTP/JSON
- **Endpoints:** `/embed/single`, `/embed/batch`
- **Fallback:** Automatic fallback to Ollama if unavailable
- **Network:** Docker private network (`ecosystem-mcp`)

**ecosystem-mcp-dashboard ↔ ecosystem-mcp-service:**
- **Protocol:** HTTP/JSON
- **Endpoints:** 50+ API endpoints
- **Auth:** None (internal)
- **Network:** Docker private network (`ecosystem-mcp`)

### External Integrations

**Ollama (Local LLM):**
- **Vendor:** Open-source (Ollama Inc.)
- **Protocol:** HTTP REST API
- **Endpoint:** `http://localhost:11434`
- **Models:** llama3.1:8b, mistral:7b, nomic-embed-text
- **Cost:** Free (self-hosted)
- **Sandbox:** N/A (local)

**Anthropic Claude (Optional):**
- **Vendor:** Anthropic
- **Protocol:** HTTP REST API
- **Endpoint:** `https://api.anthropic.com/v1`
- **Models:** claude-sonnet-4.5, claude-opus
- **Cost:** $3/M input tokens, $15/M output tokens
- **Limits:** 40,000 TPM (tokens per minute)
- **Sandbox:** Yes (separate API key)

**Cursor Free Tier (Optional):**
- **Vendor:** Cursor Inc.
- **Protocol:** MCP (Model Context Protocol)
- **Endpoint:** `http://host.docker.internal:3000`
- **Models:** haiku, gpt-3.5-turbo
- **Cost:** Free (500 queries/month)
- **Limits:** Rate limited, best-effort availability

### Vendor Recommendations

**Followed:**
- ✅ Ollama: Using recommended models (llama3.1:8b-instruct-q8_0 for M4 Max)
- ✅ Anthropic: Following rate limit best practices, using client SDK

### Vendor Billing

**Ollama:** Free (self-hosted)

**Anthropic:**
- Tiered pricing: $3/M input tokens, $15/M output tokens
- No per-transaction fee
- Billed monthly

**Cursor Free Tier:**
- Free up to 500 queries/month
- No overage charges (requests rejected after limit)

### Environment Mapping

| Environment | Ollama | Anthropic | Cursor | Notes |
|-------------|--------|-----------|--------|-------|
| **Development** | Local (11434) | Dev API Key | localhost:3000 | Full access |
| **Staging** | Docker (11434) | Staging API Key | N/A | Limited Claude |
| **Production** | Docker (11434) | Prod API Key | N/A | Ollama primary |

---

## Non-Functional Requirements

### Performance Metrics

**Ingestion:**
- Mode 1 (quick): < 2 minutes for ~100 documents
- Mode 2 (standard): < 10 minutes for ~1K documents
- Mode 3 (historical): < 30 minutes for ~5K documents
- Mode 4 (full): < 3 hours for ~10K documents

**RAG Query:**
- Single-pass: < 2 seconds (Ollama), < 3 seconds (Claude)
- Multi-pass: < 15 seconds (5 passes)

**Embedding Generation:**
- FastEmbed single: < 15ms (loaded), ~3-5s (first after unload)
- FastEmbed batch (10): < 50ms
- FastEmbed batch (100): < 300ms
- Cache hit: < 1ms

**Search:**
- ChromaDB vector search: < 100ms for < 10K documents
- PostgreSQL metadata query: < 50ms

### Logging

**Structured Logging:**
```python
logger.info(
    "Embedding generated",
    extra={
        "duration_ms": 12.3,
        "cached": False,
        "model": "BAAI/bge-base-en-v1.5",
        "dimensions": 768,
        "request_id": "abc123"
    }
)
```

**Log Levels:**
- `DEBUG`: Detailed cache hits/misses, timing
- `INFO`: Job lifecycle, API requests, health checks
- `WARNING`: Fallback to Ollama, slow operations
- `ERROR`: Failed operations, exceptions
- `CRITICAL`: Service crashes, data corruption

**Centralized Logging:**
- Docker logs: `docker logs ecosystem-mcp-service`
- File-based: `logs/app.log` (rotated daily)
- Future: ELK stack (Elasticsearch, Logstash, Kibana)

### Scalability

**Horizontal Scaling:**
- **Embedding Service:** Linear scaling (2 instances = 2× throughput)
- **Main Service:** Read-heavy operations scale horizontally
- **Database:** PostgreSQL connection pooling (20 connections per instance)
- **ChromaDB:** Single-writer model limits write scaling

**Vertical Scaling:**
- **CPU:** Parallel commit processing scales with cores (2×CPU)
- **Memory:** Embedding model ~450MB, ChromaDB ~500MB per 10K docs
- **Disk:** PostgreSQL ~100MB per 10K docs, ChromaDB ~200MB per 10K docs

**Load Testing:**
- Target: 100 concurrent RAG queries (< 5s p95)
- Target: 10 parallel ingestion jobs (full repo)
- Target: 1000 embedding requests/second (4 embedding instances)

---

## Engineering Operational Processes

### Restore/Refresh Process

**Backup Strategy:**
```bash
# PostgreSQL backup (daily)
pg_dump -h localhost -U ecosystem ecosystem_mcp > backup_$(date +%Y%m%d).sql

# ChromaDB backup (daily)
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz data/chroma_db/

# Redis backup (automatic AOF)
redis-cli BGSAVE
```

**Restore Process:**
```bash
# PostgreSQL restore
psql -h localhost -U ecosystem ecosystem_mcp < backup_20251017.sql

# ChromaDB restore
tar -xzf chroma_backup_20251017.tar.gz -C data/

# Redis restore
cp appendonly.aof /data/redis/
docker restart ecosystem-mcp-redis
```

**Refresh Process (Development):**
```bash
# Full environment refresh
docker-compose down -v  # Destroy volumes
docker-compose up -d     # Recreate services
python scripts/ingest.py --mode quick  # Re-ingest
```

### Config Release Process

**Configuration Files:**
- `docker-compose.dev.yml` - Service orchestration
- `services/ecosystem-mcp/src/config.py` - Application settings
- `services/ecosystem-mcp-embedding/src/config/settings.py` - Embedding service settings

**Release Steps:**
1. Update config files in version control
2. Run validation: `python scripts/validate_config.py`
3. Build new Docker images: `docker-compose build`
4. Rolling restart: `docker-compose up -d --no-deps --build ecosystem-mcp-service`
5. Verify health: `curl http://localhost:8000/health`

**No Downtime for:**
- Environment variable changes (rolling restart)
- Code updates (volume-mounted in dev)
- Config adjustments (no DB schema changes)

### APM (Application Performance Monitoring)

**Current State:**
- Manual health checks via `/health` endpoints
- Docker logs for debugging
- Dashboard metrics for monitoring

**Future Integration:**
- **Sentry:** Error tracking and alerting
- **Prometheus:** Metrics collection (counters, gauges, histograms)
- **Grafana:** Real-time dashboards
- **Jaeger:** Distributed tracing

### DevOps Coordination

**Release Readiness Checklist:**
- [ ] Docker images built and tested
- [ ] Database migrations applied
- [ ] Health checks passing
- [ ] Performance tests completed
- [ ] Backup/restore procedures tested
- [ ] Rollback plan documented
- [ ] Monitoring/alerting configured
- [ ] Documentation updated

### Production Support

**Team Preparedness:**
- ✅ Health monitoring dashboard
- ✅ Diagnostic tools and scripts
- ✅ Runbook for common issues
- ✅ On-call rotation (future)
- ✅ Incident response process (future)

**Support Channels:**
- Slack: `#ecosystem-mcp-alerts`
- Email: `ecosystem-mcp-oncall@company.com`
- Dashboard: `http://localhost:8501`

---

## Business Operational Processes

### Documentation and Training

**Documentation:**
- ✅ `README.md` - Quick start and overview
- ✅ `ECOSYSTEM_MCP_TECHNICAL_DESIGN_DOCUMENT.md` - This document
- ✅ `services/ecosystem-mcp/README.md` - Service-specific docs
- ✅ `services/ecosystem-mcp-dashboard/README.md` - Dashboard docs
- ✅ `services/ecosystem-mcp-embedding/README.md` - Embedding service docs
- ✅ OpenAPI/Swagger docs: `http://localhost:8000/docs`

**Training Required:**
- ✅ Basic: Dashboard navigation (15 minutes)
- ✅ Intermediate: Ingestion and RAG queries (30 minutes)
- ✅ Advanced: Troubleshooting and recovery (1 hour)

### Enable Feature/Support

**For Developers:**
1. Access dashboard: `http://localhost:8501`
2. Review documentation: Start with `README.md`
3. Run first ingestion: Use Ingestion Manager
4. Try RAG query: Use RAG Query page

**For Administrators:**
1. Access Docker logs: `docker logs ecosystem-mcp-service`
2. Monitor health: Health & Infrastructure page
3. Manage jobs: Ingestion Manager (cancel, retry, clear)
4. View metrics: Metrics and Cache Analytics pages

**Support Process:**
1. **Check Health:** Dashboard → Health & Infrastructure
2. **Review Logs:** Docker logs or Logs Viewer page
3. **Diagnose:** Diagnostics page for detailed checks
4. **Resolve:** Follow runbook for common issues
5. **Escalate:** Contact on-call engineer if unresolved

### Feature Toggle

**Current State:**
- No feature toggles implemented
- Can disable functionality via environment variables:
  - `EMBEDDING_BACKEND=ollama` - Disable FastEmbed service
  - `ENABLE_CACHE=false` - Disable caching
  - `USE_BLOOM_FILTER=false` - Disable Bloom filter

**Future Enhancements:**
- Database-backed feature flags
- Per-user feature toggles
- A/B testing framework

---

## Testing

### Test Strategy

**Unit Tests:**
```bash
# Main service
cd services/ecosystem-mcp
pytest tests/unit/ -v --cov=src --cov-report=html

# Embedding service
cd services/ecosystem-mcp-embedding
pytest tests/unit/ -v --cov=src --cov-report=html

# Dashboard
cd services/ecosystem-mcp-dashboard
pytest tests/ -v
```

**Integration Tests:**
```bash
# End-to-end ingestion + query
pytest tests/integration/test_e2e_workflow.py -v

# Service-to-service communication
pytest tests/integration/test_embedding_integration.py -v
```

**Smoke Tests:**
```bash
# Quick health check
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8501  # Should return HTML
```

### Test Coverage

**Target:** 80%+ code coverage for core services

**Current Coverage:**
- `ecosystem-mcp-service`: ~75% (focus on ingestion, RAG)
- `ecosystem-mcp-embedding`: ~85% (focus on embedding generation)
- `ecosystem-mcp-dashboard`: ~50% (UI testing limited)

### Automated Testing

**CI/CD Pipeline (Future):**
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Testing Environments

**Local Development:**
- Full stack on localhost
- Docker Compose for services
- Fast iteration (volume mounts)

**Staging:**
- Identical to production
- Separate API keys (Anthropic staging)
- Use for integration testing

**Production:**
- Full monitoring and alerting
- Automated backups
- Limited direct access

---

## Sequence Diagram(s)

### Ingestion Process

```
User           Dashboard       Main Service    Worker         Embedding     PostgreSQL   ChromaDB
 │                 │                │             │                │             │           │
 │─────────────────>│                │             │                │             │           │
 │  Start Ingestion │                │             │                │             │           │
 │                 │────────────────>│             │                │             │           │
 │                 │  POST /ingest   │             │                │             │           │
 │                 │                 │─────────────>│                │             │           │
 │                 │                 │  Queue Job  │                │             │           │
 │                 │<────────────────│             │                │             │           │
 │                 │  {"job_id": ... │             │                │             │           │
 │<─────────────────│                │             │                │             │           │
 │  Job ID         │                │             │                │             │           │
 │                 │                │             │────────────────>│             │           │
 │                 │                │             │  Scan Git Repo  │             │           │
 │                 │                │             │<────────────────│             │           │
 │                 │                │             │  File List      │             │           │
 │                 │                │             │                │             │           │
 │                 │                │             │────────────────────────────────>│           │
 │                 │                │             │  Batch Check Hashes             │           │
 │                 │                │             │<────────────────────────────────│           │
 │                 │                │             │  Existing Hashes                │           │
 │                 │                │             │                │             │           │
 │                 │                │             │─────────────────────>│             │           │
 │                 │                │             │  Parse/Normalize    │             │           │
 │                 │                │             │<─────────────────────│             │           │
 │                 │                │             │  Normalized Content │             │           │
 │                 │                │             │                │             │           │
 │                 │                │             │─────────────────────────────────>│           │
 │                 │                │             │  Generate Embeddings (batch)    │           │
 │                 │                │             │<─────────────────────────────────│           │
 │                 │                │             │  Embeddings                     │           │
 │                 │                │             │                │             │           │
 │                 │                │             │─────────────────────────────────────────────>│
 │                 │                │             │  Store Documents + Embeddings             │
 │                 │                │             │<─────────────────────────────────────────────│
 │                 │                │             │  Success                                  │
 │                 │                │             │                │             │           │
 │                 │                │<─────────────│                │             │           │
 │                 │                │  Job Complete│                │             │           │
 │                 │<────────────────│                │             │             │           │
 │                 │  Job Status     │                │             │             │           │
 │<─────────────────│                │                │             │             │           │
 │  Statistics      │                │                │             │             │           │
```

### RAG Query Process

```
User        Dashboard      Main Service    Embedding Svc   ChromaDB   PostgreSQL   LLM (Ollama/Claude)
 │              │                │                │           │           │               │
 │──────────────>│                │                │           │           │               │
 │  Ask Question│                │                │           │           │               │
 │              │────────────────>│                │           │           │               │
 │              │ POST /query    │                │           │           │               │
 │              │                │────────────────>│           │           │               │
 │              │                │  Embed Query   │           │           │               │
 │              │                │<────────────────│           │           │               │
 │              │                │  Query Vector  │           │           │               │
 │              │                │                │           │           │               │
 │              │                │─────────────────────────────>│           │               │
 │              │                │  Search Vectors (top N)     │           │               │
 │              │                │<─────────────────────────────│           │               │
 │              │                │  Similar Doc IDs            │           │               │
 │              │                │                │           │           │               │
 │              │                │──────────────────────────────────────────>│               │
 │              │                │  Fetch Full Documents                    │               │
 │              │                │<──────────────────────────────────────────│               │
 │              │                │  Document Content                        │               │
 │              │                │                │           │           │               │
 │              │                │─────────────────────────────────────────────────────────>│
 │              │                │  Generate Answer (question + context)                   │
 │              │                │<─────────────────────────────────────────────────────────│
 │              │                │  Answer + Metadata                                       │
 │              │<────────────────│                │           │           │               │
 │              │  Response       │                │           │           │               │
 │<──────────────│                │                │           │           │               │
 │  Answer       │                │                │           │           │               │
```

---

## Risks/Risk Mitigation

### Security Risks

**Risk:** Unauthorized access to API endpoints  
**Mitigation:** Deploy in private Docker network, no external exposure (future: API keys, JWT)

**Risk:** Sensitive data in embeddings/documents  
**Mitigation:** Content-aware routing (avoid sending PII to cloud LLMs), future: data classification

**Risk:** Code injection via document content  
**Mitigation:** Strict input validation, content sanitization, parameterized SQL queries

### Billing/Revenue Risks

**Risk:** Anthropic API costs exceed budget  
**Mitigation:** Daily budget limits, prefer Ollama/Cursor free tier, monitoring and alerts

**Risk:** Embedding costs for large repos  
**Mitigation:** Bloom filter deduplication, content-hash caching, daily budget enforcement

### Compliance Risks

**Risk:** Data residency requirements (EU/US)  
**Mitigation:** Use Ollama (local) for sensitive data, document data flow in privacy policy

**Risk:** Retention policy violations  
**Mitigation:** Implement TTL for cached data (30 days), manual purge procedures

### Platform Stability Risks

**Risk:** ChromaDB write contention (concurrent ingestion)  
**Mitigation:** Single-writer model via Redis stream, fail-fast with clear error messages

**Risk:** Memory exhaustion (embedding model + ChromaDB)  
**Mitigation:** Lazy loading/unloading, INT8 quantization, horizontal scaling

**Risk:** PostgreSQL connection exhaustion  
**Mitigation:** Connection pooling (20 connections), graceful degradation

### Cost Risks

**Risk:** Cloud LLM costs (Claude/OpenAI)  
**Mitigation:** Intelligent tier routing (Ollama first), daily budget limits, cost tracking dashboard

**Risk:** Hosting costs (RAM/CPU for Ollama)  
**Mitigation:** M4 Max optimization (8GB model fits in memory), auto-unload idle models

### Maintenance Window Risks

**Risk:** Schema migrations require downtime  
**Mitigation:** Online migrations (add nullable columns first), rolling restarts, no downtime for Phase 1-4

**Risk:** ChromaDB index rebuild  
**Mitigation:** Infrequent (only on corruption), can run as background job

### SLA Impact

**Current SLA:** None (internal tool)

**Future SLA (if deployed for external users):**
- **Uptime:** 99.9% (8.76 hours downtime/year)
- **Response Time:** p95 < 5 seconds for RAG queries
- **Ingestion:** Mode 1 complete in < 5 minutes

---

## References

### Documentation

**Internal:**
- [Main README](/Users/mykalthomas/Documents/work/Hackathon/README.md)
- [ecosystem-mcp README](/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/README.md)
- [ecosystem-mcp-dashboard README](/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard/README.md)
- [ecosystem-mcp-embedding README](/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-embedding/README.md)

**External:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastEmbed Documentation](https://github.com/qdrant/fastembed)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

### Architecture Documents

- [RAG Query Fix Complete](/Users/mykalthomas/Documents/work/Hackathon/RAG_QUERY_FIX_COMPLETE.md)
- [Lazy Loading Fix Complete](/Users/mykalthomas/Documents/work/Hackathon/LAZY_LOADING_FIX_COMPLETE.md)
- [Phase 2 Implementation Progress](/Users/mykalthomas/Documents/work/Hackathon/PHASE_2_IMPLEMENTATION_PROGRESS.md)
- [Phase 3 Memory Optimization Complete](/Users/mykalthomas/Documents/work/Hackathon/PHASE_3_MEMORY_OPTIMIZATION_COMPLETE.md)
- [All Phases Complete](/Users/mykalthomas/Documents/work/Hackathon/ALL_PHASES_COMPLETE.md)

### Vendor Documentation

**Ollama:**
- [Ollama Official Documentation](https://ollama.com/docs)
- [Model Library](https://ollama.com/library)
- [REST API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)

**Anthropic:**
- [Claude API Documentation](https://docs.anthropic.com/claude/docs)
- [Rate Limits and Pricing](https://docs.anthropic.com/claude/reference/rate-limits)
- [Python SDK](https://github.com/anthropics/anthropic-sdk-python)

**ONNX Runtime:**
- [ONNX Runtime Documentation](https://onnxruntime.ai/docs/)
- [Performance Tuning](https://onnxruntime.ai/docs/performance/)

---

## Appendix

### Performance Benchmarks

**Ingestion (services/ecosystem-mcp directory):**
- **Before Optimizations:** 3 hours (12,171 documents)
- **After Phase 1:** 2 hours (batch operations, connection pooling)
- **After Phase 2:** 1 hour (Bloom filter, parallel processing, FastEmbed)
- **After Phase 3:** 45 minutes (lazy loading, INT8 quantization)

**Embedding Generation:**
- **Ollama (nomic-embed-text):** 50ms per embedding
- **FastEmbed (cold start):** 3-5s first request, then 10-15ms
- **FastEmbed (batch 10):** 50ms total (5ms per embedding)
- **FastEmbed (batch 100):** 300ms total (3ms per embedding)
- **Redis cache hit:** < 1ms

**RAG Query:**
- **Query embedding:** 10-15ms (FastEmbed)
- **ChromaDB search:** 50-100ms (11,504 documents)
- **LLM generation:** 1-2s (Ollama), 2-3s (Claude)
- **Total (Ollama):** 1.5-2.5s
- **Total (Claude):** 2.5-3.5s

### Deployment Checklist

**Pre-Deployment:**
- [ ] Build Docker images (`docker-compose build`)
- [ ] Run tests (`pytest`)
- [ ] Validate configuration (`python scripts/validate_config.py`)
- [ ] Create database backups
- [ ] Review and approve migrations

**Deployment:**
- [ ] Stop services (`docker-compose down`)
- [ ] Apply migrations (`alembic upgrade head`)
- [ ] Start services (`docker-compose up -d`)
- [ ] Verify health (`curl http://localhost:8000/health`)
- [ ] Smoke test (ingestion + query)

**Post-Deployment:**
- [ ] Monitor logs for errors
- [ ] Check dashboard for anomalies
- [ ] Validate cache hit rates
- [ ] Test rollback procedure

---

## Glossary of Terms and Technologies

### A

**Alembic**
- Database migration tool for SQLAlchemy
- Manages schema versions and upgrades/downgrades
- Used for PostgreSQL schema evolution

**Anthropic**
- AI company providing Claude language models
- API-based access with usage-based pricing
- Used for complex reasoning and premium RAG queries

**AOF (Append-Only File)**
- Redis persistence mechanism
- Logs every write operation for durability
- Alternative to RDB snapshots

**API (Application Programming Interface)**
- Interface for communication between services
- RESTful HTTP/JSON in this platform
- OpenAPI/Swagger documented

**Auto-unload**
- Automatic model unloading after idle timeout
- Memory optimization technique
- Default: 300 seconds (5 minutes)

### B

**BGE (BAAI General Embedding)**
- Text embedding models from Beijing Academy of AI
- `bge-base-en-v1.5`: 768 dimensions, excellent quality
- Used in FastEmbed service

**Bloom Filter**
- Probabilistic data structure for set membership
- Fast negative duplicate checks (~1% false positive rate)
- Reduces database queries by 50%+ during ingestion
- Phase 2 optimization

**Batch Processing**
- Processing multiple items simultaneously
- 10-50× faster than sequential for embeddings
- Key FastEmbed advantage over Ollama

### C

**Cache Hit/Miss**
- **Hit**: Data found in cache (< 1ms retrieval)
- **Miss**: Data not in cache (requires generation/query)
- Hit rate target: > 50% in production

**Cache TTL (Time To Live)**
- Duration cached data remains valid
- Embedding cache: 30 days (2,592,000 seconds)
- Prevents stale data and memory bloat

**Checkpoint**
- Saved progress state for resumable operations
- Stored in `ingestion_jobs.checkpoint_data` (JSONB)
- Enables recovery from interruptions

**ChromaDB**
- Open-source vector database for embeddings
- Embedded (no separate server required)
- HNSW indexing for fast similarity search
- Single-writer model (no concurrent writes)

**Circuit Breaker**
- Fault tolerance pattern
- Prevents cascading failures
- Opens after threshold failures, closes after recovery timeout

**Claude**
- Anthropic's family of language models
- Variants: Haiku (fast), Sonnet (balanced), Opus (premium)
- Used for complex RAG queries via intelligent routing

**Content-Addressable Storage**
- Storage system using content hash as identifier
- SHA-256 hash of normalized content
- Enables perfect deduplication
- Temporal versioning fallback for non-git content

**CQRS (Command Query Responsibility Segregation)**
- Architectural pattern separating reads and writes
- Used in broader ecosystem (analysis-service)
- Not strictly enforced in ecosystem-mcp (pragmatic approach)

**Cursor IDE**
- AI-powered code editor
- MCP (Model Context Protocol) integration
- Free tier: 500 queries/month
- Premium: Claude integration

### D

**Dashboard**
- Streamlit web interface (Port 8501)
- 12 pages: Home, Health, RAG, Ingestion, etc.
- Real-time monitoring and management

**DDD (Domain-Driven Design)**
- Software design approach focusing on domain models
- Used in broader ecosystem architecture
- Not strictly enforced in ecosystem-mcp

**Deduplication**
- Eliminating duplicate documents
- Methods: Content hash, Bloom filter, git SHA
- Reduces storage and processing by 50%+

**Docker Compose**
- Multi-container orchestration tool
- `docker-compose.dev.yml`: Development environment
- Manages 6+ services (main, dashboard, embedding, PostgreSQL, Redis, Ollama)

### E

**Embedding**
- Vector representation of text
- 768 dimensions (BGE/nomic-embed-text)
- Enables semantic similarity search
- Generated by FastEmbed or Ollama

**Embedding Service**
- Dedicated microservice (Port 8001)
- FastEmbed + ONNX + Redis caching
- 10-50× faster than Ollama
- Horizontal scaling capable

### F

**FastAPI**
- Modern Python web framework
- Automatic OpenAPI/Swagger docs
- Async/await support (asyncio)
- Used for main service and embedding service

**FastEmbed**
- ONNX-optimized embedding library by Qdrant
- TRUE batch processing (10-50× faster)
- Multiple model support (BGE, sentence-transformers)
- Key Phase 2 optimization

**Fault Isolation**
- Architecture pattern for containing failures
- Embedding service crash doesn't affect main service
- Automatic fallback mechanisms

### G

**Git**
- Version control system
- Source of document history and versioning
- Provides commit SHA, author, timestamp
- Required for optimal ingestion workflow

**Graceful Degradation**
- System continues with reduced functionality
- Example: Redis down → No caching, still functional
- No hard failures for non-critical dependencies

### H

**Health Check**
- Endpoint for monitoring service status
- Format: `GET /health`
- Returns: `{"status": "healthy|unhealthy", "components": {...}}`
- Used by Docker, monitoring systems, dashboard

**HNSW (Hierarchical Navigable Small World)**
- Graph-based algorithm for approximate nearest neighbor search
- Used by ChromaDB for vector indexing
- Enables fast similarity search (< 100ms)

**Horizontal Scaling**
- Adding more instances to handle increased load
- Embedding service: Linear scaling (2 instances = 2× throughput)
- Main service: Read-heavy operations scale well
- ChromaDB: Limited by single-writer model

**httpx**
- Modern async HTTP client for Python
- Used for service-to-service communication
- Connection pooling and keepalive support

### I

**Idempotent**
- Operation that can be repeated without changing result
- Example: Database index creation (IF NOT EXISTS)
- Important for migrations and recovery

**Ingestion**
- Process of scanning, parsing, and indexing documents
- 4 modes: quick (< 2 min), standard (< 10 min), historical (< 30 min), full (< 3 hours)
- Background processing via Redis Streams

**INT8 Quantization**
- Reducing model weights from 32-bit to 8-bit integers
- ~50% memory reduction
- Minimal accuracy loss
- Phase 3 optimization

### J

**Job**
- Unit of work tracked in database
- Types: Ingestion, embedding generation, documentation
- States: queued, processing, completed, failed
- Supports recovery via checkpoints

**JSONB**
- PostgreSQL's binary JSON data type
- Flexible metadata storage
- Indexable and queryable
- Used for `checkpoint_data`, `error_summary`

### L

**Lazy Loading**
- Loading resources only when needed
- Embedding model: Load on first request
- Reduces startup time and memory usage
- Phase 3 optimization

**LLM (Large Language Model)**
- AI model for text generation
- Examples: Llama 3.1, Mistral, Claude
- Used for RAG answer generation

**LRU (Least Recently Used)**
- Cache eviction policy
- Removes least recently accessed items when full
- L1 cache in multi-level caching system

### M

**M4 Max**
- Apple Silicon processor (ARM architecture)
- Neural Engine for AI acceleration
- Optimized for Ollama (8GB models fit in memory)

**MCP (Model Context Protocol)**
- Protocol for AI agent integration
- Cursor IDE integration
- Tools, resources, and prompts
- Enables context-aware AI assistance

**Memory-Mapped Loading**
- Loading files directly from disk into memory
- Faster model loading
- Reduced RAM usage
- Phase 3 optimization

**Microservice**
- Independently deployable service
- 3 services: main (8000), dashboard (8501), embedding (8001)
- Benefits: Fault isolation, independent scaling

**Multi-Pass RAG**
- Iterative refinement of RAG queries
- 5 passes: Initial → Refinement → Deep dive → Synthesis → Final
- Better quality for complex questions
- Takes 10-15 seconds

### N

**Normalization**
- Converting content to consistent format (Markdown)
- Supports: Python, Markdown, Text files
- Cached in Redis (30 day TTL)
- Enables consistent embedding generation

**Nomic-embed-text**
- Open-source embedding model by Nomic AI
- 768 dimensions (matches BGE)
- Available in Ollama
- Legacy fallback for ecosystem-mcp

### O

**Ollama**
- Local LLM runtime (Port 11434)
- Models: llama3.1:8b, mistral:7b, nomic-embed-text
- Free, private, M4 Max optimized
- Primary tier in intelligent routing

**ONNX (Open Neural Network Exchange)**
- Cross-platform model format
- Optimized runtime with SIMD, threading
- Used by FastEmbed for 10-50× speedup
- CPU-optimized (no GPU required)

**OpenAPI/Swagger**
- API documentation standard
- Auto-generated from FastAPI code
- Interactive testing UI at `/docs`
- Complete for all 50+ endpoints

### P

**Parallel Processing**
- Executing multiple operations simultaneously
- Commit processing: 2×CPU cores (auto-tuned)
- Phase 2 optimization
- Key to 3× ingestion speedup

**PostgreSQL**
- Open-source relational database (Port 5432)
- ACID compliance, JSONB support
- Stores: documents, embeddings, jobs, runs
- Connection pooling: 20 connections per instance

**Pydantic**
- Data validation library
- Type-safe models with auto-validation
- OpenAPI schema generation
- Used throughout platform

**Python 3.11+**
- Programming language
- Async/await support (asyncio)
- Type hints for IDE support
- Fast performance (3.11 improvements)

### Q

**Query**
- Search operation (RAG or database)
- RAG query: Natural language → Embedding → ChromaDB → LLM
- Database query: SQL to PostgreSQL

**Queue**
- FIFO (First In, First Out) data structure
- Redis Streams for ingestion jobs
- Ensures sequential ChromaDB writes

### R

**RAG (Retrieval Augmented Generation)**
- Technique for grounding LLM responses in documents
- Steps: Embed query → Search vectors → Retrieve docs → Generate answer
- Single-pass: < 3 seconds
- Multi-pass: 10-15 seconds (5 iterations)

**Redis**
- In-memory data structure store (Port 6379)
- Uses: Caching, queuing (Streams), pub/sub
- Persistence: AOF (Append-Only File)
- Multi-level caching: L2 (L1 is in-memory LRU)

**Redis Streams**
- Log-like data structure
- Persistent message queue
- Consumer groups for job distribution
- Enables fault-tolerant ingestion

**Response Length**
- Configurable answer length for RAG queries
- S (50-150 chars), M (150-400), L (400-800), XL (800-1500)
- Added in Phase 4
- Controls LLM output verbosity

### S

**Semantic Search**
- Search by meaning, not exact text match
- Uses embeddings and vector similarity
- ChromaDB backend
- Enables "How does X work?" queries

**SHA-256**
- Cryptographic hash function (256-bit output)
- Used for content-addressable storage
- Ensures perfect deduplication
- Standard: `hashlib.sha256()`

**Single-Writer Model**
- Only one process writes to ChromaDB at a time
- Prevents index corruption
- Enforced via Redis Streams coordination
- ChromaDB architectural limitation

**Streamlit**
- Python framework for data apps
- Dashboard: 12 pages, real-time updates
- Port 8501
- No frontend coding required

### T

**Temporal Versioning**
- Content versioning without git
- Uses timestamps instead of commit SHAs
- Fallback for non-git repositories
- Enables time-travel queries

**Tier (LLM Routing)**
- Priority level for model selection
- Tiers: Desktop (Ollama) → Cursor Free → Claude Premium
- Intelligent routing based on complexity and availability
- Cost optimization strategy

**Token**
- Unit of text for LLMs (roughly ¾ of a word)
- Context window limits (8K-200K tokens)
- Pricing basis for cloud LLMs ($3-15 per 1M tokens)

**t-SNE (t-distributed Stochastic Neighbor Embedding)**
- Dimensionality reduction technique
- Visualizes high-dimensional embeddings (768D → 2D)
- Available in ChromaDB Explorer
- Reveals document clusters

### U

**UMAP (Uniform Manifold Approximation and Projection)**
- Alternative dimensionality reduction to t-SNE
- Faster, preserves global structure better
- Visualizes embeddings
- Available in ChromaDB Explorer

**Uvicorn**
- ASGI server for FastAPI
- Production-ready
- Async/await support
- Powers main service and embedding service

### V

**Vector**
- Array of floating-point numbers
- Embedding: 768 dimensions
- Represents semantic meaning
- Stored in ChromaDB for similarity search

**Vector Database**
- Specialized database for embeddings
- Example: ChromaDB
- Enables fast similarity search via HNSW indexing
- Alternative: Pinecone, Weaviate, Milvus

**Vertical Scaling**
- Increasing resources (CPU, RAM) of single instance
- Parallel processing scales with CPU cores
- Memory scales with ChromaDB document count
- Complement to horizontal scaling

### W

**Worker**
- Background process for async jobs
- `IngestionWorker`: Processes ingestion jobs
- Redis Streams for job distribution
- Monitored via dashboard

### Acronyms Reference

| Acronym | Full Term | Description |
|---------|-----------|-------------|
| **API** | Application Programming Interface | Service communication interface |
| **AOF** | Append-Only File | Redis persistence format |
| **ASGI** | Asynchronous Server Gateway Interface | Python async web server standard |
| **BGE** | BAAI General Embedding | Text embedding model family |
| **CLI** | Command-Line Interface | Terminal-based interaction |
| **CQRS** | Command Query Responsibility Segregation | Architectural pattern |
| **CRUD** | Create, Read, Update, Delete | Basic database operations |
| **DDD** | Domain-Driven Design | Software design approach |
| **E2E** | End-to-End | Full workflow testing |
| **ETL** | Extract, Transform, Load | Data pipeline pattern |
| **FIFO** | First In, First Out | Queue processing order |
| **GPU** | Graphics Processing Unit | Hardware accelerator (not required) |
| **HNSW** | Hierarchical Navigable Small World | Vector indexing algorithm |
| **HTTP** | Hypertext Transfer Protocol | Web communication protocol |
| **IDE** | Integrated Development Environment | Code editor (Cursor) |
| **INT8** | 8-bit Integer | Quantization format |
| **JSON** | JavaScript Object Notation | Data interchange format |
| **JSONB** | JSON Binary | PostgreSQL JSON storage |
| **JWT** | JSON Web Token | Authentication token format (future) |
| **L1/L2** | Level 1/2 Cache | Cache hierarchy |
| **LLM** | Large Language Model | AI text generation model |
| **LRU** | Least Recently Used | Cache eviction policy |
| **MCP** | Model Context Protocol | AI agent integration protocol |
| **ORM** | Object-Relational Mapping | Database abstraction (SQLAlchemy) |
| **ONNX** | Open Neural Network Exchange | Model format |
| **RAG** | Retrieval Augmented Generation | Document-grounded AI |
| **REST** | Representational State Transfer | API architectural style |
| **SHA** | Secure Hash Algorithm | Cryptographic hash function |
| **SIMD** | Single Instruction, Multiple Data | CPU parallelization |
| **SLA** | Service Level Agreement | Uptime/performance guarantee |
| **SQL** | Structured Query Language | Database query language |
| **TTL** | Time To Live | Cache expiration duration |
| **UI** | User Interface | Dashboard (Streamlit) |
| **UMAP** | Uniform Manifold Approximation and Projection | Visualization technique |
| **UUID** | Universally Unique Identifier | Primary key format |

### Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | Streamlit | 1.32+ | Dashboard UI |
| **API Framework** | FastAPI | 0.110+ | REST API |
| **Language** | Python | 3.11+ | Core implementation |
| **Database** | PostgreSQL | 15+ | Structured data |
| **Vector DB** | ChromaDB | 0.4+ | Embeddings |
| **Cache/Queue** | Redis | 7+ | Caching, streams |
| **Embeddings** | FastEmbed | 0.2+ | ONNX-optimized |
| **LLM (Local)** | Ollama | Latest | llama3.1, mistral |
| **LLM (Cloud)** | Claude | Sonnet/Opus | Premium queries |
| **Validation** | Pydantic | 2.0+ | Data validation |
| **ORM** | SQLAlchemy | 2.0+ | Database ORM |
| **HTTP Client** | httpx | 0.27+ | Async HTTP |
| **Migrations** | Alembic | Latest | Schema versions |
| **Container** | Docker | 24+ | Deployment |
| **Orchestration** | Docker Compose | 2.0+ | Multi-container |
| **Server** | Uvicorn | Latest | ASGI server |

### Model Context

| Model | Provider | Context Window | Cost | Use Case |
|-------|----------|----------------|------|----------|
| **llama3.1:8b** | Ollama (local) | 8K tokens | Free | Simple RAG, summarization |
| **mistral:7b** | Ollama (local) | 8K tokens | Free | Alternative to Llama |
| **nomic-embed-text** | Ollama (local) | N/A | Free | Embeddings (legacy) |
| **BGE-base** | FastEmbed (local) | N/A | Free | Embeddings (primary) |
| **claude-haiku** | Cursor Free | 200K tokens | Free (limited) | Medium complexity |
| **claude-sonnet-4.5** | Anthropic | 200K tokens | $3/$15 per 1M | Complex reasoning |
| **claude-opus** | Anthropic | 200K tokens | $15/$75 per 1M | Premium (unused) |

---

**Document Status:** ✅ Complete  
**Last Updated:** October 17, 2025  
**Next Review:** November 17, 2025

---


