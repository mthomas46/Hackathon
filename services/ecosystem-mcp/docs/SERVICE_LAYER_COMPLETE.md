---
title: "Ecosystem MCP - Complete Service Layer Documentation"
service: "ecosystem-mcp"
category: "architecture"
tags: ["services", "business-logic", "layer", "classes", "rag", "ingestion", "analysis", "documentation"]
related: ["CODE_REFERENCE.md", "architecture/OVERVIEW.md", "DATABASE_SCHEMA.md"]
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "advanced"
semantic_keywords: ["services", "business logic", "domain logic", "processing", "orchestration", "managers"]
llm_search_hints: ["what services exist", "service responsibilities", "service interactions", "service dependencies", "business logic location"]
---

# Ecosystem MCP - Complete Service Layer Documentation

**Comprehensive guide to all 24 service packages**

*Based on actual source code audit: 2025-10-28*

---

## 📊 Service Layer Overview

**Location**: `src/services/`  
**Total Packages**: 24 service packages  
**Purpose**: Business logic and domain operations  
**Pattern**: Service-oriented architecture with dependency injection

---

## 🗂️ Service Categories

### 1️⃣ Core RAG Services (5 services)
### 2️⃣ Ingestion & Processing (3 services)
### 3️⃣ Analysis & Discovery (3 services)
### 4️⃣ Documentation Generation (2 services)
### 5️⃣ Data Management (3 services)
### 6️⃣ Infrastructure Services (8 services)

---

## 1️⃣ Core RAG Services

### `src/services/rag/` - RAG Services

**Purpose**: Retrieval-Augmented Generation for intelligent Q&A

**Files**: 8 Python files  
**Classes**: 5 main service classes

#### RAGService

**File**: `rag_service.py`  
**Purpose**: Basic RAG with semantic search + LLM synthesis

**Key Methods**:
```python
async def ask(
    question: str,
    n_results: int = 10,
    context: Optional[List[Dict]] = None,
    prefer_recent: bool = True,
    temperature: float = 0.7,
    response_length: int = 1000
) -> Dict[str, Any]
```

**Features**:
- Semantic search with ChromaDB
- LLM-based answer synthesis
- Source citation tracking
- Recency scoring (15% weight)
- Version boost (10%)

**Dependencies**:
- ChromaDB for vector search
- OllamaRouter for LLM
- EmbeddingService for query embedding

**Semantic Tags**: `#rag #basic #semantic-search #synthesis #qa #retrieval-augmented-generation`

---

#### EnhancedRAGService

**File**: `enhanced_rag_service.py`  
**Purpose**: RAG with optional multi-signal ranking

**Extends**: `RAGService`

**Key Methods**:
```python
async def ask(
    question: str,
    n_results: int = 10,
    context: Optional[List[Dict]] = None,
    use_enhancements: bool = True,
    ...
) -> Dict[str, Any]

def _apply_enhancements(
    documents: List[Dict],
    query: str
) -> List[Dict]

def _rank_documents(
    documents: List[Dict],
    query: str
) -> List[Dict]
```

**Features**:
- **Glossary matching**: Boost docs containing glossary terms
- **Priority rules**: Context-specific document prioritization
- **Exclusion rules**: Filter out irrelevant documents
- **Multi-signal ranking**: Combine semantic, glossary, quality, recency
- **Backward compatible**: Works without config

**Config**: `.rag-config/rag_config.yaml` (optional)

**Ranking Signals**:
1. **Semantic similarity**: 50% weight (base)
2. **Glossary match**: +15% boost
3. **Quality score**: +10% boost
4. **Recency**: +15% boost
5. **Priority rules**: +20% boost

**Semantic Tags**: `#enhanced-rag #multi-signal #ranking #glossary #priorities #quality #optional-config`

---

#### ContextAwareRAG

**File**: `context_aware_rag.py`  
**Purpose**: RAG with hierarchical context filtering

**Key Methods**:
```python
async def query_with_context(
    query: str,
    repo_id: Optional[str] = None,
    context_id: Optional[str] = None,
    context_level: Optional[ContextLevel] = None,
    service_filter: Optional[str] = None,
    tech_filter: Optional[List[str]] = None,
    language_filter: Optional[str] = None,
    time_range: Optional[timedelta] = None,
    limit: int = 10
) -> Dict[str, Any]
```

**Context Levels**:
- `ROOT` - Repository root
- `SERVICE` - Microservice level
- `MODULE` - Module/package level
- `COMPONENT` - File/class level

**Filters**:
- Repository ID
- Service name
- Technology stack (e.g., ["python", "fastapi"])
- Programming language
- Time range (last N days)
- File patterns

**Use Cases**:
- Multi-repo projects
- Microservice architectures
- Technology-specific queries
- Service-level isolation

**Semantic Tags**: `#context-aware #hierarchical #filtering #multi-repo #microservices #isolation`

---

#### TemporalRAGService

**File**: `temporal_rag_service.py`  
**Purpose**: Time-aware document retrieval and analysis

**Key Methods**:
```python
async def query_point_in_time(
    query: str,
    timestamp: datetime,
    n_results: int = 10
) -> Dict[str, Any]

async def query_period_comparison(
    query: str,
    period1_start: datetime,
    period1_end: datetime,
    period2_start: datetime,
    period2_end: datetime,
    n_results: int = 10
) -> Dict[str, Any]

async def track_evolution(
    query: str,
    start_date: datetime,
    end_date: datetime,
    interval: timedelta = timedelta(days=30)
) -> Dict[str, Any]
```

**Features**:
- **Point-in-time queries**: "What did the code look like on 2024-01-01?"
- **Period comparison**: Compare two time periods
- **Evolution tracking**: Track changes over time
- **Confidence scoring**: Based on temporal data completeness
- **LLM synthesis**: Temporal-aware answer generation

**Confidence Levels**:
- `HIGH`: 90%+ documents have temporal data
- `MEDIUM`: 50-90% documents have temporal data
- `LOW`: 10-50% documents have temporal data
- `NONE`: <10% documents have temporal data

**Semantic Tags**: `#temporal #time-aware #evolution #versioning #history #point-in-time #comparison`

---

#### MultiPassQueryService

**File**: `multi_pass_query.py`  
**Purpose**: Complex research-level queries with decomposition

**Key Methods**:
```python
async def process_query(
    query: str,
    num_passes: int = 3,
    num_secondary_questions: int = 3,
    n_results: int = 10,
    temperature: float = 0.7,
    response_length: int = 1000,
    use_enhancements: bool = False,
    progress_callback: Optional[callable] = None
) -> MultiPassResult
```

**Process**:
1. **Section Generation**: Break query into major concepts
2. **Question Expansion**: Generate secondary questions per section
3. **Parallel RAG**: Query each question independently
4. **Section Synthesis**: Synthesize answers per section
5. **Final Synthesis**: Combine all sections into comprehensive answer

**Parallelization**:
- Section generation: Sequential (LLM)
- Question generation: Parallel (per section)
- RAG queries: Parallel (all questions)
- Section synthesis: Parallel (per section)
- Final synthesis: Sequential (LLM)

**Performance**:
- **3 sections × 3 questions** = 9 parallel RAG queries
- **Throughput**: ~10-30 seconds for 10-section analysis
- **Scales**: Up to 10 sections × 10 questions (100 queries)

**Use Cases**:
- Research documentation
- Comprehensive analysis
- Multi-aspect queries
- Deep dives

**Semantic Tags**: `#multi-pass #research #complex-queries #decomposition #synthesis #parallel #deep-analysis`

---

### `src/services/dynamic_rag/` - Dynamic Temporal RAG

**Purpose**: Dynamic temporal context resolution

**Key Classes**:
- `DynamicTemporalRAG` - Automatically resolve temporal context from query

**Features**:
- Auto-detect time references in queries
- Extract date ranges from natural language
- Apply temporal filtering automatically

**Semantic Tags**: `#dynamic #temporal #auto-detection #natural-language #time-extraction`

---

## 2️⃣ Ingestion & Processing Services

### `src/services/ingestion/` - Ingestion Pipeline

**Purpose**: Document ingestion orchestration

**Files**: 10+ Python files  
**Main Class**: `JobProcessor` (4,174 lines!)

**Key Classes**:
- `JobProcessor` - Git history mode
- `SnapshotProcessor` - Fast mode
- `EnhancedJobProcessor` - Enriched mode
- `JobProcessorRouter` - Mode routing
- `CommitOptimizer` - Batch optimization
- `ErrorClassifier` - Error categorization

**Pipeline Stages**:
1. **Discovery**: Scan repository or walk git history
2. **Extraction**: Extract files from commits
3. **Normalization**: Convert to markdown
4. **Embedding**: Generate vectors
5. **Storage**: Save to PostgreSQL + ChromaDB

**Semantic Tags**: `#ingestion #pipeline #git #processing #orchestration #batch #workers`

---

### `src/services/processing/` - Document Processing

**Purpose**: File format normalization

**Key Classes**:
- `NormalizerFactory` - Get normalizer by file type
- `PythonNormalizer` - Python → Markdown
- `JavaScriptNormalizer` - JS/TS → Markdown
- `JsonNormalizer` - JSON → Markdown
- Plus 20+ format normalizers

**Supported Formats**:
- Programming: `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, `.cpp`
- Markup: `.md`, `.html`, `.xml`
- Data: `.json`, `.yaml`, `.toml`, `.csv`
- Docs: `.txt`, `.rst`, `.adoc`

**Semantic Tags**: `#processing #normalization #markdown #formats #conversion`

---

### `src/services/git/` - Git Operations

**Purpose**: Git repository interaction

**Key Classes**:
- `GitService` - Git operations wrapper
- `GitErrorHandler` - Error handling & recovery

**Operations**:
- Clone repositories
- Walk commit history
- Extract file contents at specific commits
- Detect repository corruption
- Recover from git errors

**Semantic Tags**: `#git #version-control #commits #history #repository`

---

## 3️⃣ Analysis & Discovery Services

### `src/services/analysis/` - Repository Analysis

**Purpose**: Analyze repository structure and context

**Key Classes**:
- `HierarchicalContextManager` - Manage hierarchical context
- `RepositoryAnalyzer` - Analyze repository metadata
- `TechnologyDetector` - Detect tech stack
- `ArchitectureDetector` - Detect architecture patterns

**Context Levels**:
```
ROOT                      # Repository root
  └─ SERVICE             # Microservice
      └─ MODULE          # Python package / namespace
          └─ COMPONENT   # File / class
```

**Detection Capabilities**:
- **Languages**: Python, JavaScript, TypeScript, Java, Go, etc.
- **Frameworks**: FastAPI, React, Django, Spring, etc.
- **Databases**: PostgreSQL, MySQL, MongoDB, Redis
- **Architecture**: Microservices, MVC, Layered, Clean

**Semantic Tags**: `#analysis #repository #context #hierarchy #detection #tech-stack #architecture`

---

### `src/services/discovery/` - Repository Discovery

**Purpose**: Discover and scan repositories

**Key Classes**:
- `DiscoveryService` - Scan repositories
- `ProcessingPlanGenerator` - Create ingestion plans
- `FileClassifier` - Classify file types

**Process**:
1. Scan repository
2. Classify files (supported/unsupported)
3. Estimate processing time
4. Generate processing plan
5. Execute plan (optional)

**Semantic Tags**: `#discovery #scanning #planning #classification #exploration`

---

### `src/services/orchestration/` - Parallel Execution

**Purpose**: Parallel job orchestration

**Key Classes**:
- `OrchestrationService` - Parallel execution manager
- `BatchProcessor` - Batch processing
- `DependencyResolver` - Resolve task dependencies

**Features**:
- Parallel task execution
- Dependency resolution
- Resource pooling
- Progress tracking

**Semantic Tags**: `#orchestration #parallel #batch #concurrency #scheduling`

---

## 4️⃣ Documentation Generation Services

### `src/services/documentation/` - Doc Generation

**Purpose**: Multi-pass documentation generation

**Key Classes**:
- `DocumentationService` - Main generation orchestrator
- `SectionGenerator` - Generate doc sections
- `ContentSynthesizer` - Synthesize comprehensive content

**Process**:
1. Analyze repository
2. Generate doc structure (sections)
3. Generate questions per section
4. RAG query for each question
5. Synthesize section content
6. Combine into comprehensive documentation

**Output Formats**:
- Markdown files
- HTML documentation
- PDF reports

**Semantic Tags**: `#documentation #generation #synthesis #multi-pass #reports`

---

### `src/services/quality/` - Quality Checks

**Purpose**: Document quality validation

**Key Classes**:
- `QualityChecker` - Check document quality
- `MetricCalculator` - Calculate quality metrics
- `IssuDetector` - Detect quality issues

**Metrics**:
- **Completeness**: 0-100 score
- **Accuracy**: 0-100 score
- **Readability**: Flesch-Kincaid score
- **Overall**: Weighted average

**Issues Detected**:
- Missing sections
- Broken links
- Code examples without syntax
- Outdated information
- Poor formatting

**Semantic Tags**: `#quality #validation #metrics #checking #scoring`

---

## 5️⃣ Data Management Services

### `src/services/embeddings/` - Embedding Generation

**Purpose**: Text vectorization

**Key Classes**:
- `EmbeddingService` - Main embedding service
- `EmbeddingClient` - FastEmbed HTTP client
- `RecoverableEmbeddingGenerator` - Retry-able generation

**Backends**:
1. **FastEmbed service** (default): 10-50× faster, ONNX-optimized
2. **Ollama** (fallback): Local LLM embedding

**Model**: `nomic-embed-text` (768 dimensions)

**Performance**:
- **Single**: ~50-100ms (FastEmbed) vs ~500ms (Ollama)
- **Batch (100 docs)**: ~2-5 seconds (FastEmbed) vs ~30-50 seconds (Ollama)

**Semantic Tags**: `#embeddings #vectors #fastembed #ollama #vectorization #batch`

---

### `src/services/caching/` - Response Caching

**Purpose**: Cache RAG responses and embeddings

**Key Classes**:
- `CacheService` - Redis-based caching
- `CacheAnalytics` - Cache analytics & hit rates

**Cache Types**:
- **Response cache**: RAG query results (TTL: 1 hour)
- **Embedding cache**: Generated embeddings (TTL: 24 hours)
- **Query cache**: Popular queries (TTL: 30 minutes)

**Performance Impact**:
- **Cache hit**: ~10-50ms response time
- **Cache miss**: ~500-2000ms response time
- **Hit rate**: Typically 40-60%

**Semantic Tags**: `#caching #redis #performance #hit-rate #ttl`

---

### `src/services/search/` - Semantic Search

**Purpose**: Document search service

**Key Classes**:
- `SearchService` - Coordinate search operations
- `QueryExpander` - Expand queries with synonyms
- `ResultRanker` - Rank search results

**Search Types**:
- **Semantic**: Vector similarity search
- **Keyword**: Full-text search
- **Hybrid**: Combined semantic + keyword
- **Filtered**: With metadata filters

**Semantic Tags**: `#search #semantic #keyword #hybrid #ranking #filtering`

---

## 6️⃣ Infrastructure Services

### `src/services/timeline/` - Timeline Management

**Purpose**: Manage temporal timelines

**Key Classes**:
- `TimelineService` - Timeline CRUD operations
- `PeriodGenerator` - Generate time periods
- `ConfidenceCalculator` - Calculate temporal confidence

**Period Strategies**:
- **Monthly**: Fixed monthly periods
- **Quarterly**: Fixed quarterly periods
- **Adaptive**: Dynamically sized periods based on activity

**Semantic Tags**: `#timeline #temporal #periods #confidence #time-management`

---

### `src/services/versioning/` - Version Tracking

**Purpose**: Track document versions

**Key Classes**:
- `VersioningService` - Version management
- `DiffCalculator` - Calculate document diffs
- `ChangeTracker` - Track changes over time

**Semantic Tags**: `#versioning #diff #changes #tracking #history`

---

### `src/services/monitoring/` - System Monitoring

**Purpose**: Monitor system health and performance

**Key Classes**:
- `MonitoringService` - Collect metrics
- `HealthChecker` - Check service health
- `AlertManager` - Manage alerts

**Metrics**:
- Request rates
- Response times
- Error rates
- Resource usage (CPU, memory, disk)
- Queue depths
- Worker health

**Semantic Tags**: `#monitoring #metrics #health #alerts #observability`

---

### `src/services/maintenance/` - System Maintenance

**Purpose**: Maintenance operations

**Key Classes**:
- `MaintenanceService` - Schedule maintenance tasks
- `CleanupManager` - Cleanup old data
- `OptimizationManager` - Optimize indices

**Tasks**:
- Database vacuum
- Index optimization
- Old job cleanup
- Log rotation
- Cache cleanup

**Semantic Tags**: `#maintenance #cleanup #optimization #housekeeping`

---

### `src/services/models/` - LLM Clients

**Purpose**: LLM interaction

**Key Classes**:
- `OllamaClient` - Ollama HTTP client
- `OllamaRouter` - 3-tier LLM routing
- `ClaudeClient` - Claude API client

**3-Tier Routing**:
1. **Desktop Ollama** (port 11434) - Priority 1
2. **Docker Ollama** (host.docker.internal:11434) - Priority 2
3. **Claude API** - Priority 3 (fallback)

**Semantic Tags**: `#llm #ollama #claude #routing #3-tier #client`

---

### `src/services/llm/` - LLM Utilities

**Purpose**: LLM helper functions

**Key Classes**:
- `PromptBuilder` - Build prompts
- `ResponseParser` - Parse LLM responses
- `TokenCounter` - Count tokens

**Semantic Tags**: `#llm #prompts #parsing #tokens #utilities`

---

### Remaining Services (Quick Reference)

**`src/services/tree/`**
- **Purpose**: 3D tree context system
- **Tags**: `#tree #3d #spatial #proximity #graph`

**`src/services/dynamic_rag/`**
- **Purpose**: Dynamic temporal RAG
- **Tags**: `#dynamic #temporal #auto-detection`

---

## 🔄 Service Dependencies

### Dependency Graph

```
API Layer (FastAPI Routes)
  ↓
Service Layer (Business Logic)
  ├─ RAGService → EmbeddingService → OllamaClient
  ├─ RAGService → SearchService → ChromaDB
  ├─ JobProcessor → GitService → Git Library
  ├─ JobProcessor → NormalizerFactory
  ├─ JobProcessor → EmbeddingService
  ├─ JobProcessor → DocumentRepository → PostgreSQL
  ├─ JobProcessor → ChromaDB
  ├─ TimelineService → TimelineRepository → PostgreSQL
  └─ All Services → CacheService → Redis
```

### Cross-Service Communication

**RAG Services**:
- Use `EmbeddingService` for query vectors
- Use `SearchService` for document retrieval
- Use `OllamaRouter` for LLM synthesis
- Use `CacheService` for response caching

**Ingestion Services**:
- Use `GitService` for repository access
- Use `NormalizerFactory` for content conversion
- Use `EmbeddingService` for vector generation
- Use repositories for storage

**Analysis Services**:
- Use `DiscoveryService` for repository scanning
- Use `RepositoryAnalyzer` for metadata extraction
- Use `TechnologyDetector` for tech stack detection

---

## 🎯 Service Patterns

### 1. Singleton Pattern

**Used By**: Most services  
**Implementation**: Module-level singleton with getter

```python
_service_instance: Optional[ServiceClass] = None

def get_service() -> ServiceClass:
    global _service_instance
    if _service_instance is None:
        _service_instance = ServiceClass()
    return _service_instance
```

**Services**:
- `get_rag_service()`
- `get_embedding_service()`
- `get_ollama_router()`
- All service getters

---

### 2. Factory Pattern

**Used By**: NormalizerFactory, RepositoryFactory  
**Purpose**: Create appropriate handler based on file type

```python
class NormalizerFactory:
    @staticmethod
    def get_normalizer(file_extension: str) -> Normalizer:
        if file_extension == '.py':
            return PythonNormalizer()
        elif file_extension == '.js':
            return JavaScriptNormalizer()
        # ... more normalizers
```

---

### 3. Strategy Pattern

**Used By**: OllamaRouter (3-tier routing)  
**Purpose**: Try strategies in order until one succeeds

```python
class OllamaRouter:
    async def generate(self, prompt: str) -> str:
        try:
            return await self._try_desktop(prompt)
        except Exception:
            try:
                return await self._try_docker(prompt)
            except Exception:
                return await self._try_claude(prompt)
```

---

### 4. Repository Pattern

**Used By**: All database access  
**Purpose**: Separate data access from business logic

```python
class DocumentRepository:
    async def create(self, document: Document) -> Document:
        # Database logic here
    
    async def get(self, id: UUID) -> Optional[Document]:
        # Database logic here
```

---

### 5. Circuit Breaker Pattern

**Used By**: EmbeddingClient, external service calls  
**Purpose**: Prevent cascading failures

```python
@resilient(
    circuit_breaker_name="embedding_service",
    timeout_seconds=30.0,
    failure_threshold=10
)
async def generate_embedding(self, text: str):
    # Protected operation
```

---

## 📊 Service Metrics

### Lines of Code by Service

| Service | Files | Lines | Complexity |
|---------|-------|-------|------------|
| ingestion | 10+ | 5,000+ | Very High |
| rag | 8 | 2,000+ | High |
| embeddings | 4 | 1,000+ | Medium |
| analysis | 6 | 1,500+ | High |
| processing | 25+ | 2,000+ | Medium |
| documentation | 5 | 1,000+ | High |
| Others | 50+ | 5,000+ | Varies |
| **Total** | **100+** | **~20,000** | - |

---

## 🔗 Related Documentation

- [Code Reference](CODE_REFERENCE.md) - Complete code catalog
- [Architecture Overview](architecture/OVERVIEW.md) - System design
- [Database Schema](DATABASE_SCHEMA.md) - Data models
- [API Reference](API_ENDPOINTS_COMPLETE.md) - REST endpoints

---

**Last Updated**: 2025-10-28  
**Total Services**: 24 service packages  
**Total Classes**: 100+ service classes  
**Status**: Production-Ready  
**LLM Optimization**: ✅ Complete


