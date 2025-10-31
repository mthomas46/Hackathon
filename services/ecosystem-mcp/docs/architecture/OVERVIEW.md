---
title: "Ecosystem MCP - Architecture Overview"
service: "ecosystem-mcp"
category: "architecture"
tags: ["architecture", "system-design", "components", "overview"]
related: ["COMPONENTS.md", "DATA_FLOW.md", "../api/ENDPOINTS.md"]
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
---

# Ecosystem MCP - Architecture Overview

**Intelligent Refactoring Knowledge Base with Model Context Protocol Integration**

---

## 🎯 System Purpose

Ecosystem MCP is a production-grade **Retrieval-Augmented Generation (RAG)** service that enables AI agents to access, analyze, and learn from code repositories and documentation. It provides semantic search, pattern recognition, and context-aware suggestions based on git history, code structure, and documentation.

### Core Capabilities

1. **🔌 MCP Integration**: Native Model Context Protocol support for AI agent integration
2. **🧠 Intelligent RAG**: Multi-modal RAG with temporal, context-aware, and standard querying
3. **📚 Document Management**: Git-integrated ingestion with versioning and temporal metadata
4. **🔍 Semantic Search**: Vector-based search with ChromaDB embeddings
5. **⚡ Parallel Processing**: Redis Streams-based worker queue with retry logic
6. **💾 Multi-Store Architecture**: PostgreSQL (metadata) + ChromaDB (vectors) + Redis (queues/cache)
7. **🎛️ 3-Tier LLM Routing**: Desktop Ollama → Docker Ollama → Claude API
8. **📊 Observability**: Prometheus metrics, health checks, and comprehensive monitoring

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ECOSYSTEM MCP SERVICE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   API Layer (FastAPI)                       │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  • REST API (85+ endpoints)                                 │    │
│  │  • OpenAPI/Swagger documentation                            │    │
│  │  • Rate limiting & circuit breakers                         │    │
│  │  • Request validation & error handling                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                           ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │               Service Layer (Business Logic)                │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  RAG Services:                                              │    │
│  │   • Standard RAG (basic Q&A)                                │    │
│  │   • Enhanced RAG (with optional config)                     │    │
│  │   • Temporal RAG (time-aware queries)                       │    │
│  │   • Context-Aware RAG (hierarchical filtering)              │    │
│  │   • Multi-Pass RAG (complex research queries)               │    │
│  │                                                              │    │
│  │  Core Services:                                             │    │
│  │   • Ingestion Pipeline (with retry logic)                   │    │
│  │   • Job Processor (worker management)                       │    │
│  │   • Tree Context Builder (3D directory graphs)              │    │
│  │   • Embedding Service (multi-tier routing)                  │    │
│  │   • Caching Service (Redis + in-memory)                     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                           ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    Storage Layer                            │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  PostgreSQL                                                 │    │
│  │   • Documents (metadata, content, git info)                 │    │
│  │   • Git commits & file history                              │    │
│  │   • Ingestion jobs & progress                               │    │
│  │   • Context nodes (tree structure)                          │    │
│  │   • Timelines & temporal periods                            │    │
│  │                                                              │    │
│  │  ChromaDB (Vector Store)                                    │    │
│  │   • Document embeddings                                     │    │
│  │   • Semantic search indices                                 │    │
│  │   • Metadata filters                                        │    │
│  │                                                              │    │
│  │  Redis                                                      │    │
│  │   • Ingestion queue (Redis Streams)                         │    │
│  │   • Retry queue (failed operations)                         │    │
│  │   • Response cache (TTL-based)                              │    │
│  │   • Worker heartbeats                                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                           ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                External Dependencies                        │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  • Desktop Ollama (local LLM - priority 1)                  │    │
│  │  • Docker Ollama (container LLM - priority 2)               │    │
│  │  • Claude API (advanced tasks - priority 3)                 │    │
│  │  • Git (repository access from host)                        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Breakdown

### 1. API Layer

**Technology**: FastAPI 0.109+

**Responsibilities**:
- HTTP request handling
- Request validation (Pydantic models)
- OpenAPI documentation generation
- Rate limiting (slowapi)
- Circuit breaker pattern
- CORS handling
- Error standardization

**Key Features**:
- 85+ REST endpoints across 30+ route modules
- Automatic OpenAPI/Swagger UI generation
- Request timeout middleware
- Metrics collection middleware
- Request ID tracking

**See**: [`COMPONENTS.md#api-layer`](COMPONENTS.md#api-layer) | [`../api/ENDPOINTS.md`](../api/ENDPOINTS.md)

---

### 2. RAG Services

#### A. Standard RAG Service

**Purpose**: Basic question-answering with document retrieval

**Flow**:
1. Query → Generate embedding
2. ChromaDB semantic search (top-k documents)
3. LLM synthesis with retrieved context
4. Response with sources

**Features**:
- Recency scoring (15% weight)
- Version boost (10% weight)
- Source citation tracking
- Conversation context support

#### B. Enhanced RAG Service

**Purpose**: Optional multi-signal ranking with configuration

**Enhancements** (when config exists):
- Glossary term matching (+15% relevance)
- Content quality scoring (+15%)
- Priority rules (file-based)
- Context-aware exclusions
- Token-rich context building

**Graceful Degradation**: Falls back to Standard RAG if no config

#### C. Temporal RAG Service

**Purpose**: Time-aware document retrieval

**Features**:
- Query by specific timestamp (point-in-time)
- Query by date range (period comparison)
- Track document evolution over time
- Time-based relevance boosting

**Use Cases**:
- "What did the API look like in January?"
- "How did the architecture evolve between Q1 and Q2?"
- "Show me changes to authentication in the last 6 months"

#### D. Context-Aware RAG

**Purpose**: Hierarchical filtering by repository structure

**Filters**:
- Repository ID
- Hierarchical context (ROOT → SERVICE → MODULE → COMPONENT)
- Technology stack
- Programming language
- Service name
- File patterns

**Use Cases**:
- "Find authentication code in the backend service"
- "Search TypeScript testing utilities in frontend/"

#### E. Multi-Pass RAG

**Purpose**: Complex research-level queries

**Process**:
1. Query expansion (generate sub-questions)
2. Parallel section processing
3. Per-section document retrieval
4. Section-level synthesis
5. Final synthesis across all sections

**Configuration**:
- Number of sections (default: 5)
- Questions per section (default: 3)
- Documents per section (default: 20)
- Temperature, response length

**Use Cases**:
- "Create comprehensive documentation for service X"
- "Deep analysis of testing strategies across all services"

**See**: [`../features/RAG.md`](../features/RAG.md)

---

### 3. Ingestion Pipeline

**Purpose**: Process files from git repositories and generate embeddings

**Modes**:
1. **Snapshot**: Current files only (fast)
2. **Incremental**: Recent git history (last N commits)
3. **Enriched**: Current files + git metadata + host file timestamps
4. **Full History**: Complete git history (slow, comprehensive)

**Pipeline Stages**:

```
┌──────────┐    ┌───────────┐    ┌────────────┐    ┌──────────┐
│  File    │ →  │  Content  │ →  │  Metadata  │ →  │ Embedding│
│ Discovery│    │Extraction │    │ Extraction │    │Generation│
└──────────┘    └───────────┘    └────────────┘    └──────────┘
      │               │                 │                 │
      ▼               ▼                 ▼                 ▼
  Git walk     Normalize text    Git info +       3-tier LLM
  Directory    Detect language   File stats       routing
  traversal    Clean markup      Author, date
```

**Features**:
- Parallel processing (8 workers)
- Retry logic (3 attempts with exponential backoff)
- Progress tracking (Redis)
- Batch checkpointing
- Skip logic (avoid re-processing)
- Graceful error handling

**See**: [`../features/INGESTION.md`](../features/INGESTION.md)

---

### 4. Tree Context System

**Purpose**: Build 3D spatial representation of repository structure

**Concept**:
- Nodes represent directories
- Depth represents git history (version layers)
- Documents attached to nodes
- Spatial coordinates for proximity queries

**Use Cases**:
- "Find files near authentication module"
- "What's in the same directory as this config file?"
- Visualize repository structure in dashboard

**Storage**:
- PostgreSQL: `context_nodes` table
- Metadata: coordinates, depth, parent relationships
- Document associations via foreign keys

**See**: [`../features/TREE_CONTEXT.md`](../features/TREE_CONTEXT.md)

---

### 5. Worker Management

**Architecture**: Redis Streams-based job queue

**Components**:
1. **Job Producer**: API creates ingestion jobs
2. **Redis Stream**: Persistent queue with consumer groups
3. **Worker Process**: Long-running background service
4. **Retry Queue**: Failed operations for re-processing

**Worker Features**:
- Singleton pattern (prevent duplicates)
- Heartbeat tracking
- Graceful shutdown
- Progress reporting
- Error aggregation

**Health Monitoring**:
- Last heartbeat timestamp
- Active job tracking
- Queue depth metrics
- Failure rate monitoring

**See**: [`../features/WORKERS.md`](../features/WORKERS.md)

---

### 6. Storage Architecture

#### PostgreSQL (Metadata Store)

**Tables**:
- `documents`: Core document metadata
- `git_commits`: Git history
- `ingestion_jobs`: Job tracking
- `context_nodes`: Tree structure
- `timelines`: Temporal periods
- `embedding_cache`: Cached embeddings

**Features**:
- JSONB for flexible metadata
- Full-text search indices
- Foreign key constraints
- Timestamp tracking (UTC)

#### ChromaDB (Vector Store)

**Purpose**: Semantic search via embeddings

**Collections**:
- `ecosystem_documents`: Main collection
- Metadata filters for targeting queries

**Features**:
- HNSW indexing for fast search
- Metadata filtering
- Cosine similarity search

**Limitations**:
- Not designed for concurrent writes
- Sequential ingestion required

#### Redis (Cache & Queue)

**Data Structures**:
- **Streams**: Ingestion queue, retry queue
- **Strings**: Response cache (TTL)
- **Hashes**: Worker heartbeats
- **Sets**: Job tracking

**See**: [`DATA_FLOW.md`](DATA_FLOW.md)

---

## 🎛️ 3-Tier LLM Routing

**Philosophy**: Use the fastest/cheapest model that can handle the task

### Tier 1: Desktop Ollama (Priority 1)

**Models**: 
- `llama3.1:8b` (general tasks)
- `mistral:7b` (summarization)
- `nomic-embed-text` (embeddings)

**Benefits**:
- Free (no API costs)
- Fast (local M4 Max GPU)
- No rate limits
- Privacy (data stays local)

**Use Cases**:
- Embeddings generation
- Simple Q&A
- Summarization
- Metadata extraction

### Tier 2: Docker Ollama (Priority 2)

**Fallback**: If desktop Ollama unavailable

**Same models**, containerized:
- Consistent environment
- Easier deployment
- Still free

### Tier 3: Claude API (Priority 3)

**Model**: `claude-3-sonnet-20240229`

**Use Cases**:
- Complex reasoning
- Code analysis
- Pattern recognition
- When Ollama struggles

**Cost Management**:
- Only used when needed
- Cached responses
- Rate limiting

**See**: [`DESIGN_DECISIONS.md#llm-routing`](DESIGN_DECISIONS.md)

---

## 📊 Data Flow Examples

### Example 1: Standard RAG Query

```
1. User: POST /api/v1/query/enhanced
   Body: { "question": "How does caching work?", "mode": "rag" }

2. Enhanced RAG Service:
   a. Generate embedding (Desktop Ollama)
   b. Query ChromaDB (semantic search, top 10 docs)
   c. Rank by relevance + recency + config signals
   d. Build context (document content + metadata)
   e. LLM synthesis (Desktop Ollama)
   f. Return response with sources

3. Response:
   {
     "answer": "Caching in ecosystem-mcp uses Redis...",
     "sources": [{"document_id": "...", "relevance": 0.95}],
     "metadata": {"documents_searched": 10, "synthesis_model": "ollama"}
   }
```

### Example 2: Enriched Ingestion

```
1. User: POST /api/v1/admin/ingest
   Body: { "directory": "/path/to/repo", "mode": "enriched" }

2. API creates job:
   - Insert into `ingestion_jobs` table
   - Push to Redis Stream "ingestion_queue"
   - Return job_id

3. Worker picks up job:
   a. Discover files (git ls-files + directory walk)
   b. Extract git metadata (commit history, authors, dates)
   c. Fallback to host file timestamps if no git data
   d. For each file:
      - Normalize content
      - Extract metadata
      - Generate embedding (3-tier routing)
      - Store in PostgreSQL + ChromaDB
      - Update progress
   e. Build tree context structure
   f. Mark job complete

4. User polls: GET /api/v1/admin/jobs/{job_id}
   Response shows progress, documents processed, errors
```

---

## 🔐 Security & Resilience

### Circuit Breakers

**Pattern**: Prevent cascade failures

**Implemented For**:
- PostgreSQL connections
- ChromaDB operations
- Redis operations
- Ollama API calls

**States**:
- **Closed**: Normal operation
- **Open**: Too many failures, fast-fail
- **Half-Open**: Testing if service recovered

### Rate Limiting

**Tool**: slowapi

**Limits**:
- 100 requests/minute per IP (global)
- 10 requests/minute for expensive endpoints
- Customizable per-route

### Error Handling

**Strategy**: Graceful degradation

**Examples**:
- ChromaDB down → Use PostgreSQL full-text search
- Ollama down → Fall back to Claude API
- Redis down → Skip caching, continue processing

---

## 📈 Scalability Considerations

### Current Capacity

- **Documents**: Tested up to 50,000
- **Concurrent Users**: 10-20 (single instance)
- **Ingestion Speed**: ~100 docs/minute
- **Search Latency**: <100ms (p95)

### Scaling Strategy

**Vertical Scaling** (current approach):
- More RAM (PostgreSQL caching)
- Faster CPU (embedding generation)
- SSD storage (ChromaDB indexing)

**Horizontal Scaling** (future):
- Multiple worker instances
- Load-balanced API servers
- Distributed ChromaDB (pgvector migration)

---

## 🧪 Testing Strategy

### Unit Tests
- Service logic
- Repository patterns
- Utility functions

### Integration Tests
- API endpoints
- Database operations
- Redis queues

### E2E Tests
- Complete ingestion flow
- RAG query accuracy
- Worker reliability

### Performance Tests
- Concurrent request handling
- Large ingestion jobs
- Search latency under load

**See**: [`../development/TESTING.md`](../development/TESTING.md)

---

## 🔗 Related Documentation

- [Component Details](COMPONENTS.md) - Deep dive into each component
- [Data Flow](DATA_FLOW.md) - Detailed data flow diagrams
- [Design Decisions](DESIGN_DECISIONS.md) - Why we built it this way
- [API Reference](../api/ENDPOINTS.md) - Complete endpoint documentation
- [Feature Guides](../features/) - Feature-specific documentation
- [Deployment Guide](../guides/DEPLOYMENT.md) - Production deployment

---

## 📖 Glossary

- **RAG**: Retrieval-Augmented Generation (LLM + search)
- **Embedding**: Vector representation of text
- **ChromaDB**: Open-source vector database
- **Redis Streams**: Kafka-like message queue in Redis
- **Circuit Breaker**: Fault-tolerance pattern
- **MCP**: Model Context Protocol (AI agent integration)

---

**Last Updated**: 2025-10-28  
**Version**: 2.0.0  
**Status**: Production-Ready


