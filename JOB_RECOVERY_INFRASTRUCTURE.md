# Job Recovery Infrastructure

## Overview

Comprehensive checkpoint-based recovery system for long-running jobs (ingestion, embeddings, documentation). Enables graceful interruption and resumption from last successful checkpoint.

## Features

### Core Capabilities
- ✅ **Automatic Checkpointing**: Creates checkpoints at key intervals
- ✅ **State Persistence**: Saves progress to database
- ✅ **Graceful Recovery**: Resume from last checkpoint
- ✅ **Progress Tracking**: Monitor completion status
- ✅ **Idempotent Operations**: Skip already-processed items
- ✅ **Error Resilience**: Continue after failures

### Job Types Supported

1. **Ingestion Jobs**
   - Checkpoint per commit
   - Skip processed files
   - Resume from last commit
   
2. **Embedding Generation**
   - Checkpoint every N documents (default: 50)
   - Batch processing with progress tracking
   - Skip documents with existing embeddings
   
3. **Documentation Generation**
   - Checkpoint per pass
   - Save intermediate documents
   - Resume from last completed pass

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                   Job Recovery System                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │   Checkpoint     │      │    Recovery      │        │
│  │    Manager       │◄────►│    Manager       │        │
│  └──────────────────┘      └──────────────────┘        │
│           │                         │                    │
│           ▼                         ▼                    │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │   PostgreSQL     │      │  Recoverable     │        │
│  │   (Metadata)     │      │   Job Classes    │        │
│  └──────────────────┘      └──────────────────┘        │
│                                     │                    │
│           ┌─────────────────────────┼────────┐         │
│           ▼                         ▼        ▼          │
│  ┌────────────────┐  ┌──────────────────┐ ┌───────┐   │
│  │   Ingestion    │  │   Embeddings     │ │  Doc  │   │
│  │    Processor   │  │    Generator     │ │ Gen   │   │
│  └────────────────┘  └──────────────────┘ └───────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Job Start**
   ```
   Job Start → Check for Checkpoints → Resume or Start Fresh
   ```

2. **Processing**
   ```
   Process Item → Create Checkpoint → Update Status → Continue
   ```

3. **Interruption**
   ```
   Interruption → Save Current State → Mark In-Progress
   ```

4. **Recovery**
   ```
   Resume Request → Load Checkpoints → Resume from Last → Continue
   ```

## Implementation

### 1. Core Recovery Module

**File**: `services/ecosystem-mcp/src/utils/job_recovery.py`

Key Classes:
- `JobCheckpoint`: Represents a checkpoint with metadata
- `JobRecoveryManager`: Manages checkpoint lifecycle
- `RecoverableJob`: Base class for recoverable jobs

### 2. Job-Specific Implementations

#### Ingestion Recovery
**File**: `services/ecosystem-mcp/src/services/ingestion/recoverable_job_processor.py`

Features:
- Checkpoint after each commit
- Resume from last processed commit
- Skip already-ingested files
- Preserve counters across restarts

#### Embeddings Recovery
**File**: `services/ecosystem-mcp/src/services/embeddings/recoverable_embedding_generator.py`

Features:
- Checkpoint every 50 documents (configurable)
- Batch processing with progress tracking
- Skip documents with existing embeddings
- Resume from last batch offset

#### Documentation Recovery
**File**: `services/ecosystem-mcp/src/services/documentation/recoverable_doc_generator.py`

Features:
- Checkpoint after each pass
- Save intermediate documents
- Resume from last completed pass
- Preserve question generation state

### 3. API Endpoints

**File**: `services/ecosystem-mcp/src/api/routes/job_recovery.py`

Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/recovery/status/{job_id}` | Get recovery status for a job |
| GET | `/api/v1/recovery/checkpoints/{job_id}` | List all checkpoints |
| POST | `/api/v1/recovery/resume` | Resume an interrupted job |
| DELETE | `/api/v1/recovery/checkpoints/{job_id}` | Cleanup old checkpoints |

### 4. Dashboard Integration

**File**: `services/ecosystem-mcp-dashboard/dashboard_views/job_recovery_manager.py`

Features:
- View job recovery status
- Resume interrupted jobs
- Browse checkpoints
- Cleanup old checkpoints

## Usage

### Check Job Status

```bash
curl http://localhost:8000/api/v1/recovery/status/{JOB_ID}
```

Response:
```json
{
  "job_id": "abc123",
  "job_type": "ingestion",
  "can_resume": true,
  "last_checkpoint": {
    "checkpoint_id": "commit_a1b2c3d4_5",
    "sequence": 4,
    "status": "completed",
    "data": {
      "processed": 150,
      "failed": 2,
      "skipped": 10
    }
  },
  "resume_from_sequence": 5,
  "incomplete_count": 2,
  "progress": {
    "completed_checkpoints": 5,
    "total_checkpoints": 7
  }
}
```

### Resume a Job

```bash
curl -X POST http://localhost:8000/api/v1/recovery/resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc123",
    "job_type": "ingestion"
  }'
```

### List Checkpoints

```bash
curl http://localhost:8000/api/v1/recovery/checkpoints/{JOB_ID}
```

### Cleanup Old Checkpoints

```bash
curl -X DELETE "http://localhost:8000/api/v1/recovery/checkpoints/{JOB_ID}?keep_last=3"
```

## Checkpoint Data Structure

### Ingestion Checkpoint
```json
{
  "checkpoint_id": "commit_a1b2c3d4_5",
  "sequence": 4,
  "status": "completed",
  "data": {
    "commit_sha": "a1b2c3d4",
    "commit_index": 4,
    "commit_num": 5,
    "total_commits": 10,
    "processed": 150,
    "failed": 2,
    "skipped": 10,
    "embeddings": 140,
    "cost": 0.05
  },
  "created_at": "2025-10-15T10:30:00Z",
  "completed_at": "2025-10-15T10:35:00Z"
}
```

### Embeddings Checkpoint
```json
{
  "checkpoint_id": "batch_100_95",
  "sequence": 2,
  "status": "completed",
  "data": {
    "processed": 95,
    "skipped": 5,
    "failed": 0,
    "offset": 100,
    "total": 500,
    "progress_pct": 20.0
  },
  "created_at": "2025-10-15T11:00:00Z",
  "completed_at": "2025-10-15T11:05:00Z"
}
```

### Documentation Checkpoint
```json
{
  "checkpoint_id": "pass_3",
  "sequence": 2,
  "status": "completed",
  "data": {
    "current_pass": 2,
    "pass_id": 3,
    "total_passes": 5,
    "answered": 15,
    "failed": 1,
    "documents": [
      {
        "path": "/app/docs/pass_03_q01_what_is_rag.md",
        "question": "What is RAG?",
        "pass": 3,
        "question_num": 1
      }
    ]
  },
  "created_at": "2025-10-15T12:00:00Z",
  "completed_at": "2025-10-15T12:10:00Z"
}
```

## Configuration

### Checkpoint Intervals

```python
# Ingestion: Per commit (not configurable)
CHECKPOINT_PER_COMMIT = True

# Embeddings: Every N documents
EMBEDDING_CHECKPOINT_INTERVAL = 50  # Default: 50 docs
EMBEDDING_BATCH_SIZE = 10  # Default: 10 docs per batch

# Documentation: Per pass (not configurable)
CHECKPOINT_PER_PASS = True
```

### Cleanup Policy

```python
# Default: Keep last 3-5 checkpoints
DEFAULT_KEEP_LAST = 3
MAX_KEEP_LAST = 10
```

## Error Handling

### Checkpoint Failures

If checkpoint creation fails:
- Log error but continue processing
- Job can still complete successfully
- Recovery may not be possible if all checkpoints fail

### Resume Failures

If resume fails:
- Return detailed error message
- Job remains in interrupted state
- Manual intervention may be required

### Partial Failures

If some items fail during processing:
- Checkpoint marks items as failed
- Processing continues to next items
- Resume will skip already-processed items

## Performance Impact

### Storage Overhead
- Checkpoint size: ~1-5 KB per checkpoint
- Typical job: 5-10 checkpoints
- Total overhead: ~5-50 KB per job

### Processing Overhead
- Checkpoint creation: ~50-100ms
- Database write: ~20-50ms
- Negligible impact on overall job time

### Database Load
- 1 write per checkpoint
- 1 read on resume
- Minimal impact on database

## Testing

### Unit Tests
**File**: `tests/test_job_recovery.py`

Coverage:
- ✅ Checkpoint creation and serialization
- ✅ Recovery manager operations
- ✅ Status updates and queries
- ✅ Resume state calculation
- ✅ Checkpoint cleanup

### Integration Tests
- ✅ End-to-end ingestion recovery
- ✅ End-to-end embeddings recovery
- ✅ End-to-end documentation recovery

### Manual Testing

1. **Ingestion Recovery**
   ```bash
   # Start ingestion job
   # Interrupt after 2-3 commits (Ctrl+C)
   # Resume job
   # Verify: Resumes from last commit
   ```

2. **Embeddings Recovery**
   ```bash
   # Start embedding generation
   # Interrupt after 50+ documents
   # Resume generation
   # Verify: Resumes from last batch
   ```

3. **Documentation Recovery**
   ```bash
   # Start multi-pass documentation
   # Interrupt after 1-2 passes
   # Resume generation
   # Verify: Resumes from next pass
   ```

## Monitoring

### Dashboard
Access: **Dashboard → 🔄 Job Recovery**

Features:
- View job recovery status
- Check checkpoint progress
- Resume interrupted jobs
- Cleanup old checkpoints

### Logs

```bash
# View recovery logs
docker logs ecosystem-mcp-service | grep "Checkpoint"

# Common log patterns
📌 Checkpoint created: job=abc123, checkpoint=commit_1, sequence=0
✅ Checkpoint completed: job=abc123, checkpoint=commit_1
📂 Resuming from checkpoint: completed=5, total=10
🧹 Cleaned up 7 old checkpoints for job abc123
```

## Best Practices

1. **Regular Cleanup**
   - Run checkpoint cleanup weekly
   - Keep last 3-5 checkpoints per job
   - Remove completed jobs after 30 days

2. **Monitoring**
   - Check recovery status for long-running jobs
   - Monitor checkpoint completion rates
   - Alert on excessive failed checkpoints

3. **Error Handling**
   - Always wrap resume operations in try-catch
   - Log all checkpoint operations
   - Provide clear error messages to users

4. **Performance**
   - Use appropriate checkpoint intervals
   - Balance recovery granularity vs overhead
   - Cleanup old checkpoints regularly

## Troubleshooting

### Job Won't Resume

**Symptom**: `can_resume: false`

**Causes**:
- No completed checkpoints
- All checkpoints failed
- Job metadata corrupted

**Solution**:
```bash
# Check checkpoint status
curl http://localhost:8000/api/v1/recovery/checkpoints/{JOB_ID}

# If no completed checkpoints, start fresh
curl -X POST http://localhost:8000/api/v1/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

### Checkpoint Creation Fails

**Symptom**: Logs show "Failed to persist checkpoint"

**Causes**:
- Database connection issues
- Disk space full
- Permissions error

**Solution**:
```bash
# Check database connectivity
docker exec ecosystem-mcp-service pg_isready

# Check disk space
df -h

# Check logs
docker logs ecosystem-mcp-service
```

### Resume Takes Too Long

**Symptom**: Resume request times out

**Causes**:
- Large job with many items to reprocess
- Slow database queries
- Network issues

**Solution**:
- Increase API timeout
- Use batch processing
- Optimize database queries

## Future Enhancements

### Planned Features
- [ ] Distributed checkpoint storage (S3, MinIO)
- [ ] Checkpoint compression
- [ ] Automatic cleanup policies
- [ ] Recovery analytics and reporting
- [ ] Multi-node coordination
- [ ] Checkpoint versioning

### Optimization Opportunities
- [ ] Parallel checkpoint persistence
- [ ] Lazy loading of checkpoint data
- [ ] Checkpoint deduplication
- [ ] Incremental checkpoints (delta-only)

## Conclusion

The job recovery infrastructure provides robust checkpoint-based recovery for all long-running operations in the ecosystem. With automatic checkpointing, graceful resumption, and comprehensive monitoring, jobs can be interrupted and resumed without losing progress.

**Key Benefits**:
- ✅ No manual intervention required
- ✅ Minimal performance overhead
- ✅ Complete progress preservation
- ✅ User-friendly dashboard interface
- ✅ Comprehensive testing coverage

**Next Steps**:
1. Test recovery in your environment
2. Configure checkpoint intervals as needed
3. Set up monitoring and alerting
4. Establish cleanup policies
5. Train team on recovery operations

