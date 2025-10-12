# Ingestion Worker Implementation Plan

**Date**: 2025-10-12  
**Goal**: Implement complete document ingestion pipeline  
**Time Estimate**: 8 hours

---

## Overview

Implement a background worker that processes ingestion jobs from the queue, reads documents from Git commits, normalizes them, generates embeddings, and stores them in ChromaDB for semantic search.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Ingestion Pipeline                        │
└─────────────────────────────────────────────────────────────┘

1. API Endpoint
   ↓
2. Create Ingestion Job → Database
   ↓
3. Queue Job → Redis Stream
   ↓
4. Background Worker (NEW)
   ├─ Read Job from Redis
   ├─ Get Git Commits (GitService)
   ├─ Extract Files per Commit
   ├─ Normalize Documents (MarkdownNormalizer)
   ├─ Generate Embeddings (OllamaClient)
   ├─ Store in ChromaDB
   └─ Update Job Status
   ↓
5. Query System → ChromaDB → Results
```

---

## Phase 1: Worker Architecture (1h)

### 1.1 Worker Service
**File**: `src/services/ingestion/ingestion_worker.py`

**Responsibilities**:
- Poll Redis streams for ingestion jobs
- Process jobs asynchronously
- Handle failures and retries
- Update job status in database

**Key Methods**:
```python
class IngestionWorker:
    async def start()
    async def process_job(job_id: UUID)
    async def stop()
```

### 1.2 Job Processor
**File**: `src/services/ingestion/job_processor.py`

**Responsibilities**:
- Orchestrate the ingestion pipeline
- Read commits from Git
- Process documents
- Generate embeddings
- Store results

**Key Methods**:
```python
class JobProcessor:
    async def process(job: IngestionJob)
    async def process_commit(commit: GitCommit)
    async def process_document(file: str, content: str)
```

### 1.3 Integration Point
**File**: `src/api/app.py`

**Changes**:
- Add worker lifecycle management
- Start worker on application startup
- Stop worker on shutdown

---

## Phase 2: Git Integration (2h)

### 2.1 Enhanced Git Service
**File**: `src/services/git/git_service.py` (enhance existing)

**New Methods**:
```python
async def get_recent_commits(limit: int) -> List[GitCommit]
async def get_commit_files(commit_sha: str) -> List[FileChange]
async def get_file_content(commit_sha: str, file_path: str) -> str
```

### 2.2 File Filtering
**Logic**:
- Include: `.md`, `.py`, `.yaml`, `.yml`, `.json`, `.txt`
- Exclude: `node_modules/`, `.git/`, `__pycache__/`, `.venv/`
- Max file size: 1MB per file

### 2.3 Commit Processing
**Strategy**:
- Process commits in chronological order
- Extract changed files (added/modified)
- Skip deleted files
- Track progress in database

---

## Phase 3: Document Normalization (1.5h)

### 3.1 Normalizer Factory
**File**: `src/services/processing/normalizer_factory.py` (NEW)

**Responsibility**: Create appropriate normalizer based on file type

```python
class NormalizerFactory:
    @staticmethod
    def get_normalizer(file_ext: str) -> BaseNormalizer
```

### 3.2 Markdown Normalizer
**File**: `src/services/processing/markdown_normalizer.py` (enhance existing)

**Enhancements**:
- Add frontmatter extraction
- Code block preservation
- Link handling
- Image reference handling

### 3.3 Python Normalizer
**File**: `src/services/processing/python_normalizer.py` (NEW)

**Capabilities**:
- Extract docstrings
- Preserve code structure
- Generate markdown representation
- Include class/function signatures

### 3.4 Generic Text Normalizer
**File**: `src/services/processing/text_normalizer.py` (NEW)

**Capabilities**:
- Handle YAML, JSON, TXT
- Preserve structure
- Add metadata

---

## Phase 4: Embedding Generation (1.5h)

### 4.1 Embedding Service
**File**: `src/services/embeddings/embedding_service.py` (NEW)

**Responsibilities**:
- Generate embeddings via Ollama
- Batch processing for efficiency
- Error handling and retries
- Cost tracking

**Key Methods**:
```python
class EmbeddingService:
    async def generate_embedding(text: str) -> List[float]
    async def generate_batch(texts: List[str]) -> List[List[float]]
```

### 4.2 Ollama Integration
**Enhancements to**: `src/services/models/ollama_client.py`

**Add**:
- Batch embedding generation
- Circuit breaker integration (already exists)
- Caching (already exists)
- Rate limiting

### 4.3 Token Counting
**File**: `src/services/embeddings/token_counter.py` (NEW)

**Purpose**: Estimate token count for cost tracking

```python
def estimate_tokens(text: str) -> int
```

---

## Phase 5: ChromaDB Storage (1h)

### 5.1 Storage Service
**File**: `src/services/storage/document_storage_service.py` (NEW)

**Responsibilities**:
- Store documents in PostgreSQL
- Store embeddings in ChromaDB
- Maintain consistency
- Handle duplicates

**Key Methods**:
```python
class DocumentStorageService:
    async def store_document(doc: Document, embedding: List[float])
    async def update_document(doc_id: UUID, embedding: List[float])
    async def delete_document(doc_id: UUID)
```

### 5.2 ChromaDB Integration
**Enhancements to**: `src/storage/chromadb_client.py`

**Add**:
- Bulk insert optimization
- Metadata handling
- Collection management
- Query optimization

### 5.3 Transaction Management
**Strategy**:
- Use database transactions
- Rollback on failure
- Eventual consistency with ChromaDB
- Retry logic

---

## Phase 6: Testing & Validation (1h)

### 6.1 Unit Tests
**Files**: `tests/unit/services/ingestion/`

**Coverage**:
- Worker lifecycle
- Job processing logic
- Git integration
- Document normalization
- Embedding generation
- Storage operations

### 6.2 Integration Tests
**Files**: `tests/integration/test_ingestion_pipeline.py`

**Scenarios**:
- End-to-end ingestion flow
- Error handling
- Retry logic
- Data consistency

### 6.3 Manual Validation
**Steps**:
1. Start service
2. Trigger ingestion of 10 commits
3. Verify documents in database
4. Verify embeddings in ChromaDB
5. Test semantic search
6. Validate response quality

---

## Implementation Order

### Step 1: Core Worker (Phase 1)
- Create worker service
- Add lifecycle management
- Implement job polling

### Step 2: Git Integration (Phase 2)
- Enhance Git service
- Add file extraction
- Implement filtering

### Step 3: Normalization (Phase 3)
- Create normalizer factory
- Implement Python normalizer
- Enhance Markdown normalizer

### Step 4: Embeddings (Phase 4)
- Create embedding service
- Add batch processing
- Integrate with Ollama

### Step 5: Storage (Phase 5)
- Create storage service
- Implement bulk operations
- Add transaction management

### Step 6: Testing (Phase 6)
- Write unit tests
- Create integration tests
- Manual validation

---

## Key Design Decisions

### 1. Background Worker Strategy
**Decision**: Use FastAPI BackgroundTasks + Redis Streams  
**Rationale**: Simple, integrated, scalable

**Alternative Considered**: Celery  
**Why Not**: Adds complexity, overkill for single service

### 2. Document Processing
**Decision**: Process synchronously per job, async within job  
**Rationale**: Ensures consistency, easier error handling

**Alternative Considered**: Fully async pipeline  
**Why Not**: More complex error handling

### 3. Embedding Strategy
**Decision**: Generate embeddings on ingestion  
**Rationale**: Faster queries, embeddings cached

**Alternative Considered**: Generate on first query  
**Why Not**: Slow first query, unpredictable latency

### 4. Storage Pattern
**Decision**: PostgreSQL for metadata, ChromaDB for vectors  
**Rationale**: Best tool for each job

**Alternative Considered**: All in ChromaDB  
**Why Not**: Limited relational query capabilities

### 5. Error Handling
**Decision**: Retry with exponential backoff, max 3 attempts  
**Rationale**: Balance between reliability and speed

**Alternative Considered**: Infinite retries  
**Why Not**: Can cause backlog, DLQ needed

---

## Performance Considerations

### 1. Batch Processing
- **Documents**: Process 100 at a time
- **Embeddings**: Generate 10 at a time
- **ChromaDB**: Insert 50 at a time

### 2. Parallelization
- Process commits sequentially (maintain order)
- Process files within commit in parallel
- Generate embeddings in parallel

### 3. Caching
- Cache file content from Git
- Cache embeddings (already implemented)
- Cache normalized documents

### 4. Rate Limiting
- Ollama: 10 requests/second
- ChromaDB: 100 operations/second
- Database: Connection pooling

---

## Monitoring & Observability

### 1. Metrics
- Jobs processed/failed
- Documents ingested
- Embeddings generated
- Processing time per document
- Error rates

### 2. Logging
- Job start/complete
- Document processing
- Errors with context
- Performance metrics

### 3. Health Checks
- Worker status
- Queue depth
- Error rate
- Last successful job

---

## Success Criteria

1. ✅ Worker processes ingestion jobs automatically
2. ✅ 200 commits ingested successfully
3. ✅ Documents stored in database
4. ✅ Embeddings stored in ChromaDB
5. ✅ Semantic search returns relevant results
6. ✅ Error handling works correctly
7. ✅ Performance is acceptable (<5 min for 200 commits)

---

## Rollout Plan

### Phase 1: Development (8h)
- Implement all components
- Unit tests
- Integration tests

### Phase 2: Testing (1h)
- Manual validation
- Performance testing
- Bug fixes

### Phase 3: Deployment (30m)
- Deploy to production
- Monitor for issues
- Validate results

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Git history too large | High | Medium | Add filtering, pagination |
| Ollama slow | Medium | High | Batch processing, caching |
| ChromaDB errors | High | Low | Retry logic, circuit breaker |
| Database deadlocks | Medium | Low | Transaction management |
| Out of memory | High | Low | Stream processing, batching |

---

## Next Steps

1. Create worker service skeleton
2. Implement Git integration
3. Add document normalization
4. Integrate embedding generation
5. Add ChromaDB storage
6. Test end-to-end
7. Deploy and monitor

---

**Status**: Ready to implement  
**Estimated Time**: 8 hours  
**Complexity**: Medium-High  
**Dependencies**: All infrastructure in place ✅

Let's build this! 🚀

