---
title: "Ecosystem MCP - Complete Ingestion System Documentation"
service: "ecosystem-mcp"
category: "features"
tags: ["ingestion", "pipeline", "git", "workers", "jobs"]
related: ["../architecture/OVERVIEW.md", "../architecture/DATABASE_SCHEMA.md"]
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
---

# Complete Ingestion System Documentation

**Comprehensive guide to document ingestion pipeline**

*Based on actual implementation audit: 2025-10-28*

---

## 📊 System Overview

**Purpose**: Ingest documents from repositories into the knowledge base

**Architecture**:
- **Job Router**: Routes jobs to appropriate processor
- **Processors**: Snapshot (fast) | Git History (complete) | Enriched (balanced)
- **Workers**: Background processing via Redis Streams
- **Storage**: PostgreSQL (metadata) + ChromaDB (vectors)

---

## 🎯 Ingestion Modes *(Actual Implementation)*

### Mode 1: **Snapshot** (Fast Mode)

**Purpose**: Quick ingestion of current files only

**Process**:
1. Scan repository directory
2. Read current file contents
3. Normalize to markdown
4. Generate embeddings
5. Store (no git history)

**Performance**:
- **Speed**: 10-100× faster than git_history
- **Time**: ~1-5 minutes for 1,000 files
- **Use Case**: Quick validation, testing, non-git repos

**Processor**: `SnapshotProcessor`  
**File**: `src/services/ingestion/snapshot_processor.py`

**Example**:
```python
{
  "mode": "snapshot",
  "repo_path": "/path/to/repo"
}
```

**Metadata Populated**:
- ✅ Service name
- ✅ File path
- ✅ Content hash
- ❌ Git commit SHA
- ❌ Git date
- ❌ Git author

---

### Mode 2: **Git History** (Complete Mode)

**Purpose**: Full git history ingestion with all commits

**Process**:
1. Clone/access git repository
2. Walk commit history (oldest → newest)
3. For each commit:
   - Extract changed files
   - Read file contents at that commit
   - Normalize content
   - Generate embeddings
   - Store with git metadata
4. Build complete document history

**Performance**:
- **Speed**: Slowest (thorough)
- **Time**: ~30-60 minutes for 1,000 commits
- **Use Case**: Complete historical analysis

**Processor**: `JobProcessor`  
**File**: `src/services/ingestion/job_processor.py`

**Example**:
```python
{
  "mode": "git_history",
  "repo_path": "/path/to/repo",
  "commit_depth": 100  # Optional: limit commits
}
```

**Metadata Populated**:
- ✅ Service name
- ✅ File path
- ✅ Content hash
- ✅ Git commit SHA
- ✅ Git date
- ✅ Git author
- ✅ Git author email
- ✅ Git commit message

---

### Mode 3: **Enriched** (Balanced Mode)

**Purpose**: Current files with git metadata + host file timestamps

**Process**:
1. Scan repository directory
2. For each file:
   - Try to get git metadata (last commit affecting file)
   - If git unavailable: use host file timestamps
   - Read current content
   - Normalize content
   - Generate embeddings
   - Store with maximum available metadata
3. Graceful fallback strategy

**Performance**:
- **Speed**: Medium (faster than git_history, slower than snapshot)
- **Time**: ~5-15 minutes for 1,000 files
- **Use Case**: Best balance (temporal data without full history)

**Processor**: `EnhancedJobProcessor`  
**File**: `src/services/ingestion/enhanced_job_processor.py`

**Example**:
```python
{
  "mode": "enriched",
  "repo_path": "/path/to/repo"
}
```

**Metadata Populated**:
- ✅ Service name
- ✅ File path
- ✅ Content hash
- ✅ Git date (or host file mtime)
- ✅ Git author (if available)
- ⚠️ Git commit SHA (if available)
- ⚠️ Git commit message (if available)

**Fallback Strategy**:
```
1. Try git metadata for file → Success? ✅ Use it
2. Git unavailable? → Use os.stat(file).st_mtime
3. Partial git data? → Merge with host timestamps
```

---

### Mode 4: **Incremental** (Recent Changes)

**Purpose**: Ingest recent git history only

**Process**:
1. Get last ingestion timestamp
2. Walk git history (recent → oldest)
3. Stop at last ingestion or depth limit
4. Process commits like git_history mode
5. Update existing documents if changed

**Performance**:
- **Speed**: Fast (only recent commits)
- **Time**: ~2-10 minutes for 50 commits
- **Use Case**: Regular updates, CI/CD pipelines

**Processor**: `JobProcessor` (with depth limit)

**Example**:
```python
{
  "mode": "incremental",
  "repo_path": "/path/to/repo",
  "commit_depth": 50  # Last 50 commits
}
```

---

## 🏗️ Pipeline Architecture

### Job Routing

**Router**: `JobProcessorRouter`  
**File**: `src/services/ingestion/job_processor_router.py`

```python
class JobProcessorRouter:
    @staticmethod
    async def process(job: IngestionJobModel) -> Dict:
        if job.mode == 'snapshot':
            processor = SnapshotProcessor(...)
        elif job.mode == 'git_history':
            processor = JobProcessor(...)
        elif job.mode == 'enriched':
            processor = EnhancedJobProcessor(...)
        # ... process and return result
```

---

### Pipeline Stages

#### Stage 1: File Discovery

**Snapshot Mode**:
- `Path.glob('**/*')` - Walk directory tree
- Filter by extensions

**Git Mode**:
- `git.Repo.iter_commits()` - Walk commits
- Extract files from each commit

**Enriched Mode**:
- `Path.glob('**/*')` - Walk directory
- `git log --follow <file>` - Get last commit per file

---

#### Stage 2: Content Extraction

**Normalizer Factory**: `NormalizerFactory`  
**File**: `src/services/processing/normalizer_factory.py`

**Supported Formats**:
- `.md` - Markdown (pass-through)
- `.py` - Python (extract docstrings)
- `.js`, `.ts` - JavaScript/TypeScript
- `.json`, `.yaml` - Configuration files
- `.txt` - Plain text
- Plus 20+ more formats

**Normalization**:
1. Detect file type
2. Extract relevant content
3. Convert to markdown
4. Clean formatting
5. Return normalized text

---

#### Stage 3: Embedding Generation

**Service**: `EmbeddingService`  
**File**: `src/services/embeddings/embedding_service.py`

**3-Tier Routing**:
1. **Desktop Ollama** (priority 1)
   - Model: `nomic-embed-text`
   - Dimensions: 768
   - Speed: ~1000 docs/second
   - Cost: Free

2. **Docker Ollama** (priority 2)
   - Fallback if desktop unavailable
   - Same model
   - Slightly slower

3. **Claude API** (priority 3)
   - Last resort
   - High quality
   - Costs money

**Batching**:
- Batch size: 100 documents
- Parallel batches: 4
- Retry on failure: 3 attempts

---

#### Stage 4: Storage

**PostgreSQL Storage**:
- Insert into `documents` table
- Insert into `git_commits` table (if git mode)
- Update `ingestion_jobs` progress

**ChromaDB Storage**:
- Add to `ecosystem_documents` collection
- Store embedding vectors
- Store metadata for filtering

**Transaction Handling**:
- PostgreSQL: Transactional (rollback on error)
- ChromaDB: Best-effort (retry on failure)

---

## 📊 Metadata Completeness Tracking

**Schema Version**: 1

**Required Metadata by Mode**:

```python
REQUIRED_METADATA_BY_MODE = {
    "snapshot": {
        "required_fields": [],
        "version": 1
    },
    "enriched": {
        "required_fields": ["git_date"],
        "optional_fields": ["git_author", "git_author_email", "git_commit_message"],
        "version": 1
    },
    "git_history": {
        "required_fields": ["git_date", "git_commit_sha"],
        "version": 1
    },
    "incremental": {
        "required_fields": ["git_date", "git_commit_sha"],
        "version": 1
    }
}
```

**Skip Logic**:
```python
# Skip document if already ingested with same or better mode
def should_skip(existing_doc, new_mode):
    if existing_doc.metadata_version < CURRENT_VERSION:
        return False  # Re-ingest for schema upgrade
    
    if existing_doc.ingestion_mode == new_mode:
        if existing_doc.content_hash == new_content_hash:
            return True  # Already up-to-date
    
    # Check metadata completeness
    required = REQUIRED_METADATA_BY_MODE[new_mode]["required_fields"]
    if all(getattr(existing_doc, field) for field in required):
        return True  # Already has required metadata
    
    return False  # Re-ingest to enrich metadata
```

---

## 🔄 Worker System

### Redis Streams Architecture

**Queue**: `ingestion_queue`  
**Consumer Group**: `ingestion_workers`  
**Consumer**: `ingestion_worker_1` (singleton)

**Message Format**:
```python
{
    "job_id": "uuid",
    "mode": "enriched",
    "repo_path": "/path/to/repo",
    "created_at": "2025-10-28T12:00:00Z"
}
```

**Worker Process**:
1. `XREADGROUP` - Poll for messages (5s block)
2. Process job via `JobProcessorRouter`
3. Update progress in Redis hash
4. `XACK` - Acknowledge message
5. Repeat

**Heartbeat**:
- Worker writes heartbeat every 30s
- Key: `worker:ingestion_worker_1:heartbeat`
- Value: `{"last_seen": "timestamp", "status": "active"}`
- TTL: 60s

**Health Check**:
```python
def worker_is_healthy():
    heartbeat = redis.get("worker:ingestion_worker_1:heartbeat")
    if not heartbeat:
        return False
    
    last_seen = parse_timestamp(heartbeat["last_seen"])
    age_seconds = (now() - last_seen).total_seconds()
    
    return age_seconds < 60  # Healthy if seen in last minute
```

---

## 🔁 Retry Infrastructure

### Retry Queue

**Queue**: `retry_queue`  
**Purpose**: Re-process failed operations

**Retry Logic**:
1. Operation fails → Add to retry queue
2. Wait with exponential backoff (1s, 2s, 4s, 8s, 16s)
3. Retry up to 3 times
4. If still failing → Move to dead letter queue

**Error Types** (from actual code):
```python
class ErrorType(Enum):
    FILE_READ = "file_read"
    GIT_PARSING = "git_parsing"
    NORMALIZATION = "normalization"
    EMBEDDING = "embedding"
    STORAGE = "storage"
    CHROMADB = "chromadb"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
```

**Retry Strategy by Error Type**:
- `FILE_READ`: Retry 3× (might be transient)
- `GIT_PARSING`: Retry 1× then skip (likely corrupt)
- `NORMALIZATION`: Retry 2× (might be encoding)
- `EMBEDDING`: Retry 3× (might be rate limit)
- `STORAGE`: Retry 3× (might be connection)
- `TIMEOUT`: Retry 2× with longer timeout
- `UNKNOWN`: Retry 1× then investigate

---

## 📈 Progress Tracking

### Job Progress Model

```python
{
    "job_id": "uuid",
    "status": "running",
    "progress": 0.65,  # 65% complete
    "total_documents": 1000,
    "processed_documents": 650,
    "failed_documents": 5,
    "skipped_documents": 100,
    "elapsed_seconds": 180.5,
    "estimated_remaining_seconds": 95.3,
    "current_phase": "embedding_generation",
    "error_summary": {
        "file_read": 2,
        "normalization": 3
    }
}
```

### Real-Time Updates

**Redis Key**: `job:{job_id}:progress`  
**Update Frequency**: Every 10 documents  
**TTL**: 24 hours

**Polling** (Dashboard):
```python
# Client polls every 2 seconds
progress = redis.get(f"job:{job_id}:progress")
```

**WebSocket** (Future):
```python
# Real-time push to clients
websocket.send(json.dumps(progress))
```

---

## 🛡️ Error Handling

### Error Aggregation

**Feature**: Aggregate errors instead of failing on first error

**Implementation**:
```python
class ErrorAggregator:
    def __init__(self):
        self.errors = defaultdict(list)
    
    def add_error(self, error_type: ErrorType, details: dict):
        self.errors[error_type.value].append({
            "timestamp": now(),
            "details": details
        })
    
    def get_summary(self) -> dict:
        return {
            error_type: len(errors)
            for error_type, errors in self.errors.items()
        }
```

**Job Completion**:
- If total_errors / total_documents < 0.1: Status = "completed_with_errors"
- If total_errors / total_documents >= 0.1: Status = "failed"
- Error details saved in `ingestion_jobs.error_aggregation`

---

### Timeout Protection

**Per-Commit Timeout**: 30 seconds  
**Per-File Timeout**: 10 seconds  
**Total Job Timeout**: 4 hours

**Progress-Aware Timeout**:
```python
# Don't timeout if making progress
last_progress_time = time.time()

while processing:
    if made_progress():
        last_progress_time = time.time()
    
    if time.time() - last_progress_time > 300:  # 5 min no progress
        raise TimeoutError("No progress for 5 minutes")
```

---

## 🚀 Performance Optimizations

### 1. Batch Processing

**Embedding Generation**:
- Batch size: 100 documents
- Parallel batches: 4
- Total throughput: ~400 docs/minute

**Database Inserts**:
- Batch size: 50 documents
- Use bulk insert
- Commit every batch

---

### 2. Commit Checkpointing

**Problem**: Large repos timeout  
**Solution**: Checkpoint every N commits

```python
CHECKPOINT_INTERVAL = 10  # commits

for i, commit in enumerate(commits):
    process_commit(commit)
    
    if i % CHECKPOINT_INTERVAL == 0:
        save_checkpoint(i)
        update_progress()
```

**Resume from Checkpoint**:
```python
last_checkpoint = load_checkpoint(job_id)
commits = commits[last_checkpoint:]  # Resume from checkpoint
```

---

### 3. Content Deduplication

**Content Hash**:
```python
content_hash = hashlib.sha256(normalized_content.encode()).hexdigest()
```

**Skip Logic**:
```python
existing_doc = db.query(Document).filter_by(
    file_path=path,
    content_hash=content_hash
).first()

if existing_doc:
    skip_document()  # Already have this version
```

---

### 4. Parallel Workers

**Horizontal Scaling**:
- Each worker has unique consumer ID
- Redis consumer groups ensure no duplicate processing
- Can run N workers in parallel
- Linear scaling (tested up to 8 workers)

---

## 📊 Monitoring & Observability

### Metrics (Prometheus)

```
# Job metrics
ingestion_jobs_total
ingestion_jobs_success
ingestion_jobs_failed
ingestion_documents_processed
ingestion_documents_failed

# Performance metrics
ingestion_duration_seconds
ingestion_file_processing_seconds
ingestion_embedding_generation_seconds
ingestion_storage_write_seconds

# Queue metrics
ingestion_queue_depth
ingestion_queue_lag_seconds
worker_heartbeat_age_seconds
```

### Logging

**Log Levels**:
- DEBUG: Detailed processing info
- INFO: Job lifecycle events
- WARNING: Retryable errors
- ERROR: Permanent failures
- CRITICAL: System-level issues

**Structured Logging**:
```python
logger.info(
    "Job progress update",
    extra={
        "job_id": job_id,
        "progress": 0.65,
        "documents_processed": 650,
        "elapsed_seconds": 180
    }
)
```

---

## 🔗 Related Documentation

- [Architecture Overview](../architecture/OVERVIEW.md)
- [Database Schema](../architecture/DATABASE_SCHEMA.md)
- [API Reference](../api/API_ENDPOINTS_COMPLETE.md)
- [Worker Management](WORKERS.md)
- [Configuration Guide](../guides/CONFIGURATION.md)

---

**Last Updated**: 2025-10-28  
**Ingestion Modes**: 4 (snapshot, git_history, enriched, incremental)  
**Workers**: 1 (singleton, horizontally scalable)  
**Status**: Production-Ready


