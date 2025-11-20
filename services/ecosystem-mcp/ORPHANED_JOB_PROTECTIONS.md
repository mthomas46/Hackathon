**Date:** November 19, 2025  
**Status:** Comprehensive Orphaned Job Protections Implemented  
**Coverage:** Retry Limits, Timeouts, Auto-cleanup, Redis Recovery  

---

# Orphaned Job Protection System

## Overview

This document describes the comprehensive protection mechanisms implemented to prevent orphaned ingestion jobs from clogging the system and causing resource exhaustion.

## Problem Statement

Orphaned jobs occur when:
1. **Container restart**: A job is processing when the container restarts, leaving it stuck in "processing" status
2. **Worker crash**: The worker process dies while processing a job
3. **Redis queue deletion**: Manual Redis stream deletion removes the consumer group, causing NOGROUP errors
4. **Infinite retry loops**: Jobs get re-queued indefinitely without a maximum retry limit

### Symptoms of Orphaned Jobs

- Jobs stuck in "processing" status with no active worker
- Redis queue fills with duplicate messages for the same job
- Worker unable to read from stream (NOGROUP error)
- System performance degradation over time
- Database growth from accumulating old jobs

---

## Protection Mechanisms

### 1. Retry Count Tracking

**File**: `services/ecosystem-mcp/src/services/ingestion/orphaned_job_detector.py`

Every time an orphaned job is detected and re-queued, the system increments a `orphan_retry_count` in the job's metadata.

```python
# Configuration
MAX_ORPHAN_RETRIES = 3  # Maximum retry attempts
```

**Metadata Tracking**:
```json
{
  "orphan_retry_count": 2,
  "last_requeue_at": "2025-11-19T21:15:30.123456",
  "orphaned_detected_at": "2025-11-19T21:15:30.123456",
  "orphaned_age_seconds": 1800.5,
  "orphaned_action": "requeued"
}
```

**Behavior**:
- Retry 0: First orphan detection → Re-queue
- Retry 1: Second orphan detection → Re-queue  
- Retry 2: Third orphan detection → Re-queue
- Retry 3: Fourth orphan detection → **FAIL** (max retries exceeded)

### 2. Maximum Retry Limit

**Configuration**:
```python
MAX_ORPHAN_RETRIES = 3  # Fail after 3 re-queue attempts
```

**Enforcement Logic**:
```python
if retry_count >= MAX_ORPHAN_RETRIES:
    logger.error(f"❌ Job {job.id} exceeded max retries ({MAX_ORPHAN_RETRIES}) - FAILING")
    
    job.status = "failed"
    job.error_message = f"Job exceeded maximum retry attempts ({MAX_ORPHAN_RETRIES})"
    metadata["orphaned_action"] = "failed_max_retries"
```

**Result**:
- Job is marked as "failed" in the database
- Error message indicates max retries exceeded
- Job is NOT re-queued to Redis
- User can restart manually if needed

### 3. Job Hard Timeout

**Configuration**:
```python
JOB_HARD_TIMEOUT = timedelta(hours=4)  # 4 hour maximum processing time
```

**Enforcement Logic**:
```python
if age > JOB_HARD_TIMEOUT:
    logger.error(f"❌ Job {job.id} exceeded hard timeout ({JOB_HARD_TIMEOUT}) - FAILING")
    
    job.status = "failed"
    job.error_message = f"Job exceeded hard timeout of {JOB_HARD_TIMEOUT} (age: {age})"
    metadata["orphaned_action"] = "failed_timeout"
```

**Purpose**:
- Prevents jobs from running indefinitely
- Catches jobs stuck in processing for > 4 hours
- Frees up system resources
- Signals genuine job failures (not just orphaned)

### 4. Age-Based Re-queue Threshold

**Configuration**:
```python
ORPHAN_AGE_THRESHOLD = timedelta(hours=1)  # Only requeue jobs < 1 hour old
REQUEUE_AGE_LIMIT = timedelta(hours=1)  # Same as above
```

**Enforcement Logic**:
```python
if age > ORPHAN_AGE_THRESHOLD:
    logger.warning(f"⏰ Job {job.id} too old to requeue (age: {age}) - FAILING")
    
    job.status = "failed"
    job.error_message = f"Job orphaned after container restart (age: {age}, retry_count: {retry_count})"
    metadata["orphaned_action"] = "failed_old"
```

**Rationale**:
- Jobs orphaned for > 1 hour are unlikely to be recoverable
- Prevents stale jobs from being re-queued repeatedly
- Balances recovery vs. cleanup

### 5. Redis Consumer Group Auto-Recreation

**File**: `services/ecosystem-mcp/src/utils/redis_client.py`

**New Method**:
```python
async def ensure_consumer_group_exists(self, stream_name: str) -> bool:
    """
    Explicitly check and ensure consumer group exists for a stream.
    
    This is useful for auto-recovery after manual stream deletion.
    """
```

**Integration**:
```python
# In ingestion_worker.py, before reading from stream:
await redis.ensure_consumer_group_exists(redis.INGESTION_STREAM)
```

**Behavior**:
1. Check if consumer group exists for the stream
2. If missing, create it automatically with `MKSTREAM`
3. Log warning about missing group
4. Return success/failure status

**Prevents**:
- `NOGROUP` errors after manual Redis stream deletion
- Worker stuck in infinite loop unable to read messages
- Need for manual intervention to recreate consumer groups

### 6. Periodic Job Cleanup Service

**File**: `services/ecosystem-mcp/src/services/ingestion/job_cleanup_service.py`

**Configuration**:
```python
CLEANUP_INTERVAL_HOURS = 24  # Run cleanup once per day
JOB_RETENTION_DAYS = 7       # Keep jobs for 7 days
BATCH_SIZE = 100             # Delete in batches
```

**Features**:
- Runs automatically every 24 hours
- Deletes completed/failed jobs older than 7 days
- Batch processing (100 jobs at a time) to avoid DB overload
- Graceful shutdown support
- Statistics tracking

**Cleanup Logic**:
```python
async def _run_cleanup(self) -> int:
    cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
    
    # Find old completed/failed jobs
    query = select(IngestionJobModel).where(
        IngestionJobModel.status.in_(["completed", "failed"]),
        IngestionJobModel.completed_at < cutoff_date
    ).limit(self.batch_size)
    
    # Delete in batches
    for job in jobs:
        await session.delete(job)
    
    await session.commit()
```

**Statistics**:
```json
{
  "total_cleaned": 1234,
  "last_cleanup_at": "2025-11-19T21:00:00",
  "last_cleanup_count": 45,
  "cleanup_runs": 7,
  "errors": 0
}
```

**Integration**:
- Started automatically on application startup via `app.py`
- Runs in background asyncio task
- Does NOT block main application

---

## Detection and Recovery Flow

### Orphaned Job Detection Flow

```
Container Starts
  ↓
Orphaned Job Detector Runs
  ↓
Find all jobs with status='processing'
  ↓
For each job:
  ├─ Check if message exists in Redis queue
  │  └─ If YES: Job is active, skip
  │  └─ If NO: Job is orphaned, continue
  ↓
  ├─ Check retry count
  │  └─ If >= 3: FAIL (max retries exceeded)
  │  └─ If < 3: Continue
  ↓
  ├─ Check job age
  │  └─ If > 4 hours: FAIL (hard timeout)
  │  └─ If > 1 hour: FAIL (too old to recover)
  │  └─ If < 1 hour: Continue
  ↓
  └─ Re-queue job
     ├─ Increment retry_count
     ├─ Update metadata
     ├─ Add to Redis stream
     └─ Log recovery attempt
```

### Worker Message Reading Flow

```
Worker Polling Loop
  ↓
Call _get_next_job()
  ↓
Ensure consumer group exists
  ├─ Check if group exists in Redis
  │  └─ If NO: Create group with MKSTREAM
  │  └─ If YES: Continue
  ↓
Read from Redis stream
  ├─ XREADGROUP with 1s block, 3s timeout
  │  └─ On success: Process message
  │  └─ On timeout: Sleep and retry
  │  └─ On NOGROUP error: Auto-recovery kicks in
  ↓
Process job or sleep
```

---

## Configuration Reference

### Orphaned Job Detection

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_ORPHAN_RETRIES` | `3` | Maximum re-queue attempts before failing |
| `ORPHAN_AGE_THRESHOLD` | `1 hour` | Age threshold for re-queuing |
| `JOB_HARD_TIMEOUT` | `4 hours` | Maximum processing time |
| `REQUEUE_AGE_LIMIT` | `1 hour` | Only requeue jobs younger than this |

### Job Cleanup

| Constant | Value | Description |
|----------|-------|-------------|
| `CLEANUP_INTERVAL_HOURS` | `24` | Hours between cleanup runs |
| `JOB_RETENTION_DAYS` | `7` | Days to retain old jobs |
| `BATCH_SIZE` | `100` | Jobs to delete per batch |

---

## Monitoring and Alerts

### Orphaned Job Statistics

Available via API: `GET /api/v1/admin/orphaned-jobs/detect`

```json
{
  "total_processing": 5,
  "orphaned_found": 2,
  "failed_old": 1,
  "failed_max_retries": 1,
  "failed_timeout": 0,
  "requeued_recent": 0,
  "errors": []
}
```

### Cleanup Service Status

Available via: `get_cleanup_service().get_status()`

```json
{
  "running": true,
  "service_id": "cleanup_281471372617744",
  "cleanup_interval_hours": 24,
  "retention_days": 7,
  "stats": {
    "total_cleaned": 1234,
    "last_cleanup_at": "2025-11-19T21:00:00",
    "last_cleanup_count": 45,
    "cleanup_runs": 7,
    "errors": 0
  }
}
```

### Key Metrics to Monitor

1. **Orphaned Job Count**: Should be 0 or very low during normal operations
2. **Max Retry Failures**: High count indicates systemic issues (investigate root cause)
3. **Timeout Failures**: Jobs consistently hitting 4h timeout need optimization
4. **Cleanup Errors**: Non-zero indicates database or permission issues
5. **Retry Count Distribution**: Most jobs should have 0-1 retries

---

## Recovery Procedures

### Manual Recovery from Orphaned Jobs

If orphaned jobs are detected:

1. **View orphaned jobs**:
   ```bash
   curl http://localhost:8000/api/v1/admin/orphaned-jobs/detect
   ```

2. **Re-queue specific orphaned job**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/admin/orphaned-jobs/requeue?job_id=<UUID>"
   ```

3. **Re-queue all orphaned jobs**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/orphaned-jobs/requeue
   ```

### Manual Recovery from NOGROUP Error

If worker logs show `NOGROUP` errors:

1. **Recreate consumer group**:
   ```bash
   docker exec ecosystem-mcp-redis redis-cli XGROUP CREATE ingestion_queue workers 0 MKSTREAM
   ```

2. **Verify group exists**:
   ```bash
   docker exec ecosystem-mcp-redis redis-cli XINFO GROUPS ingestion_queue
   ```

3. **Restart worker** (automatic recreation will happen):
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/workers/ingestion/restart
   ```

### Manual Job Cleanup

To manually clean old jobs:

```python
from services.ingestion.job_cleanup_service import get_cleanup_service

service = get_cleanup_service()
count = await service._run_cleanup()
print(f"Deleted {count} old jobs")
```

---

## Testing

### Test Orphaned Job Detection

1. **Start a job**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/ingest \
     -H "Content-Type: application/json" \
     -d '{"repo_path": "/work/adminservice", "mode": "snapshot"}'
   ```

2. **Restart container** (simulates orphan):
   ```bash
   docker restart ecosystem-mcp-service
   ```

3. **Check logs for orphan detection**:
   ```bash
   docker logs ecosystem-mcp-service 2>&1 | grep "Orphaned job detected"
   ```

4. **Verify retry count**:
   ```bash
   curl http://localhost:8000/api/v1/admin/ingest/<JOB_ID> | jq '.job_metadata.orphan_retry_count'
   ```

### Test Max Retry Limit

Repeat the above 3 times and verify the job is marked as "failed" after the 3rd retry.

### Test Consumer Group Recreation

1. **Delete Redis stream**:
   ```bash
   docker exec ecosystem-mcp-redis redis-cli DEL ingestion_queue
   ```

2. **Start new job** (should auto-create group):
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/ingest \
     -H "Content-Type: application/json" \
     -d '{"repo_path": "/work/adminservice", "mode": "snapshot"}'
   ```

3. **Verify no NOGROUP errors in logs**.

---

## Best Practices

### For Operators

1. **Monitor orphan rates**: Set up alerts if orphaned_found > 5
2. **Investigate max retry failures**: These indicate systemic issues
3. **Review timeout failures**: Jobs hitting 4h timeout need optimization
4. **Regular Redis health checks**: Ensure consumer groups exist
5. **Database cleanup**: Let automatic cleanup run, but verify it's working

### For Developers

1. **Handle job interruptions gracefully**: Save progress frequently
2. **Set realistic timeouts**: 4 hours is generous, but some jobs may need more
3. **Log job progress**: Makes debugging orphaned jobs easier
4. **Test restart scenarios**: Ensure your jobs can be safely retried
5. **Avoid long-running operations**: Break into smaller chunks if possible

### Configuration Tuning

Adjust these values based on your workload:

- **Increase `MAX_ORPHAN_RETRIES`** if frequent container restarts
- **Decrease `JOB_HARD_TIMEOUT`** if jobs should never take > 2 hours
- **Decrease `JOB_RETENTION_DAYS`** if database growth is a concern
- **Increase `CLEANUP_INTERVAL_HOURS`** if cleanup is too frequent
- **Decrease `ORPHAN_AGE_THRESHOLD`** if you want faster job failure

---

## Troubleshooting

### Issue: Jobs keep getting orphaned

**Symptoms**: High orphaned_found count, frequent retries

**Possible Causes**:
- Frequent container restarts
- Worker crashes (check logs for exceptions)
- Insufficient resources (CPU/memory)
- Jobs taking too long (hitting timeout)

**Solution**:
1. Check container restart logs
2. Increase resources if needed
3. Optimize slow jobs
4. Consider increasing `JOB_HARD_TIMEOUT`

### Issue: NOGROUP errors persist

**Symptoms**: Worker logs show repeated NOGROUP errors

**Possible Causes**:
- Redis stream manually deleted
- Consumer group recreation failed
- Redis connection issues

**Solution**:
1. Manually recreate consumer group (see Recovery Procedures)
2. Restart worker to trigger auto-recreation
3. Check Redis health and connectivity

### Issue: Database growing too fast

**Symptoms**: Postgres disk usage increasing rapidly

**Possible Causes**:
- Cleanup service not running
- Job retention too long
- High job creation rate

**Solution**:
1. Verify cleanup service is running: `get_cleanup_service().get_status()`
2. Decrease `JOB_RETENTION_DAYS` to 3 or 5
3. Increase `CLEANUP_INTERVAL_HOURS` to run more frequently
4. Run manual cleanup: `await service._run_cleanup()`

### Issue: Jobs failing with "max retries exceeded"

**Symptoms**: Many jobs with status="failed" and error="exceeded maximum retry attempts"

**Possible Causes**:
- Systemic issue causing repeated orphaning
- Container restart loop
- Worker crashing repeatedly

**Solution**:
1. Investigate root cause of orphaning (check container logs)
2. Fix underlying issue (stability, resources, code bugs)
3. Manually restart failed jobs after fix
4. Consider temporarily increasing `MAX_ORPHAN_RETRIES`

---

## Related Files

| File | Purpose |
|------|---------|
| `src/services/ingestion/orphaned_job_detector.py` | Detection and re-queue logic |
| `src/services/ingestion/job_cleanup_service.py` | Periodic cleanup service |
| `src/utils/redis_client.py` | Consumer group auto-recreation |
| `src/services/ingestion/ingestion_worker.py` | Worker with group validation |
| `src/api/app.py` | Service initialization |
| `src/api/routes/admin.py` | Admin API endpoints |

---

## Change History

| Date | Change | Author |
|------|--------|--------|
| 2025-11-19 | Initial implementation of all protections | AI Assistant |
| 2025-11-19 | Added retry count tracking | AI Assistant |
| 2025-11-19 | Added max retry limit (3 attempts) | AI Assistant |
| 2025-11-19 | Added job hard timeout (4 hours) | AI Assistant |
| 2025-11-19 | Added consumer group auto-recreation | AI Assistant |
| 2025-11-19 | Added periodic cleanup service (7 day retention) | AI Assistant |

---

## Summary

This comprehensive protection system ensures:
- ✅ Orphaned jobs are automatically detected and recovered
- ✅ Jobs don't get stuck in infinite retry loops (max 3 retries)
- ✅ Jobs can't run indefinitely (4 hour hard timeout)
- ✅ Redis consumer groups are automatically recreated if missing
- ✅ Old completed/failed jobs are automatically cleaned up (7 day retention)
- ✅ System resources are protected from exhaustion
- ✅ Operators have visibility into orphaned job metrics

**Result**: A robust, self-healing ingestion system that gracefully handles failures and prevents resource exhaustion.

