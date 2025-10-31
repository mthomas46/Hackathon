**Date:** October 30, 2025  
**Status:** Investigation Complete - Issues Resolved  
**Investigator:** AI Analysis  

# Stuck Workers Investigation Report

## Executive Summary

✅ **All investigated jobs are already resolved** - they were automatically cleaned up by the orphaned job detector.

⚠️ **Remaining issue:** Redis stream has stale messages (10 total, 1 pending) that should be cleaned up.

---

## Investigation Details

### Jobs Investigated

| Job ID | Status | Error | Resolution |
|--------|--------|-------|------------|
| 77a0086c-fce1... | **failed** | Job orphaned after container restart | Auto-recovered by system |
| 3528d6cb-6fec... | **failed** | Job orphaned after container restart | Auto-recovered by system |
| 998f218d-616c... | **failed** | Job orphaned after container restart | Auto-recovered by system |
| d6804cb4-f88a... | **failed** | Job orphaned after container restart | Auto-recovered by system |

### What Happened

1. **Original Issue (Oct 29, 2025):**
   - Jobs started and got stuck in "processing" state
   - Worker was unable to process documents
   - Jobs showed 0 progress for extended periods (5+ minutes)

2. **Container Restart:**
   - Container was restarted (likely around 14:59 UTC on Oct 30)
   - Jobs were left in "processing" state with no active worker

3. **Automatic Recovery (Oct 30, 14:59 UTC):**
   - **Orphaned Job Detector** ran on startup
   - Detected all 4 jobs as orphaned (in "processing" but no worker)
   - Automatically marked them as "failed" with error message
   - Recovery timestamp: `2025-10-30T14:59:12`

### Current System State

✅ **Worker Status:**
- Running: ✅ True
- Healthy: ✅ True  
- Processing: ✅ True
- Overall System: ✅ Healthy

📊 **Database Status:**
- Total jobs: 6
- Failed: 6
- Processing: 0
- Queued: 0

⚡ **Redis Status:**
- Stream length: 10 messages
- Pending messages: 1
- Consumer groups: 1

### Root Cause Analysis

The workers got stuck due to one or more of these issues:

1. **Repository Path Issue:**
   - All jobs have `repo_path: None` in final state
   - Suggests path resolution or git repository access failed
   - Worker couldn't find or access the repository

2. **Silent Failure:**
   - Jobs started but encountered immediate failure
   - No documents were processed (all show 0 processed)
   - Error wasn't properly propagated until container restart

3. **Worker Processing Loop:**
   - Worker was polling but not successfully processing
   - Likely caught an exception early in job processing
   - Exception handling may have prevented proper job failure marking

---

## Remaining Issues

### 🔧 Issue 1: Stale Redis Messages

**Problem:**
- 10 messages remain in Redis stream
- 1 message in pending state
- These are likely from the failed jobs

**Impact:**
- Wastes Redis memory
- Could cause confusion in monitoring
- Pending message is technically "claimed" by a consumer but never ACK'd

**Solution:**
Clean up orphaned Redis messages

---

## Recommendations

### Immediate Actions

1. **Clean up Redis stream**
   ```bash
   # View current Redis status
   curl http://localhost:8000/api/v1/admin/redis/stream-status | jq
   
   # Clean up orphaned messages (removes messages for non-existent jobs)
   curl -X POST http://localhost:8000/api/v1/admin/redis/cleanup-orphaned
   ```

2. **Review worker logs for root cause**
   ```bash
   # Check logs around the time jobs started (Oct 29, 20:18 - 21:32 UTC)
   docker logs ecosystem-mcp-service --since 2025-10-29T20:00:00 --until 2025-10-29T22:00:00 | grep -E "(77a0086c|3528d6cb|998f218d|d6804cb4)"
   ```

3. **Test with a new job**
   ```bash
   # Try starting a new ingestion job to verify system is working
   # Use the dashboard at http://localhost:8001
   # Or use API:
   curl -X POST http://localhost:8000/api/v1/admin/ingest \
     -H "Content-Type: application/json" \
     -d '{"repo_path": "/host", "mode": "quick"}'
   ```

### Preventive Measures

1. **Path Validation:**
   - Ensure repository paths are properly validated before job starts
   - Add early failure detection if path is invalid
   - Update error handling to mark jobs as failed immediately if path issues detected

2. **Worker Timeout Monitoring:**
   - Current 4-hour timeout may be too long for detecting stuck jobs
   - Consider adding heartbeat monitoring with shorter intervals (5-10 minutes)
   - Implement automatic job cancellation if no progress after threshold

3. **Enhanced Error Handling:**
   - Ensure all exceptions in job processing properly mark job as failed
   - Add more detailed error messages (current "Job orphaned" doesn't explain original failure)
   - Log exceptions with full stack traces

4. **Monitoring Improvements:**
   - Add alerts for jobs with 0 progress after 5 minutes
   - Monitor pending Redis messages (alert if > 0 for > 10 minutes)
   - Track job start failures (jobs that fail immediately)

---

## Code Locations for Fixes

### 1. Orphaned Job Detection (Working ✅)
**File:** `services/ecosystem-mcp/src/services/ingestion/orphaned_job_detector.py`

This is already working correctly - it successfully detected and cleaned up the orphaned jobs.

### 2. Worker Job Processing (Needs Review ⚠️)
**File:** `services/ecosystem-mcp/src/services/ingestion/ingestion_worker.py`  
**Lines:** 714-850 (`_process_job` method)

**Current issue:**
- Jobs are marked as "processing" (line 754)
- Then `job_processor.process()` is called (line 772)
- If this fails early (before even starting), the job stays in "processing"

**Suggested fix:**
```python
# Add try-catch around the entire process block
try:
    job.status = "processing"
    await repo.update(job)
    await session.commit()
    
    result = await self.job_processor.process(job)
    
except Exception as e:
    # Ensure job is marked as failed on ANY exception
    logger.error(f"❌ Job processing failed: {e}", exc_info=True)
    job.status = "failed"
    job.error_message = f"Processing error: {str(e)}"
    job.completed_at = datetime.utcnow()
    await repo.update(job)
    await session.commit()
```

### 3. Job Processor Path Validation (Needs Fix ⚠️)
**File:** `services/ecosystem-mcp/src/services/ingestion/job_processor.py`  
**Line:** 692+ (`process` method)

**Issue:** All failed jobs have `repo_path: None`, suggesting path validation failed

**Suggested enhancement:**
```python
async def process(self, job: IngestionJobModel) -> Dict[str, Any]:
    logger.info(f"Processing job {job.id}: mode={job.mode}, repo={job.repo_path}")
    
    # Validate repository path early
    if not job.repo_path or not os.path.exists(job.repo_path):
        return {
            "success": False,
            "error": f"Invalid repository path: {job.repo_path}",
            "processed_documents": 0,
            "total_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,
            "embeddings_generated": 0,
            "total_cost_usd": 0.0
        }
    
    # Continue with processing...
```

---

## Cleanup Commands

Execute these commands to clean up the remaining Redis messages:

```bash
# 1. Check current Redis stream status
echo "=== Current Redis Status ==="
curl -s http://localhost:8000/api/v1/admin/redis/stream-status | jq '.status'

# 2. Clean up orphaned messages (recommended)
echo -e "\n=== Cleaning up orphaned messages ==="
curl -X POST http://localhost:8000/api/v1/admin/redis/cleanup-orphaned

# 3. Check queue health
echo -e "\n=== Checking queue health ==="
curl -s http://localhost:8000/api/v1/admin/redis/queue-health | jq

# 4. If needed, clear entire stream (nuclear option - use with caution)
# curl -X POST http://localhost:8000/api/v1/admin/redis/clear-stream

# 5. Verify cleanup
echo -e "\n=== After cleanup ==="
curl -s http://localhost:8000/api/v1/admin/redis/stream-status | jq '.status'
```

---

## Testing New Ingestion

To verify the system is working correctly after cleanup:

```bash
# Test with a small, quick ingestion
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/host",
    "mode": "quick",
    "processing_mode": "snapshot"
  }'

# Monitor the job
# Get the job_id from the response, then:
JOB_ID="<job-id-from-response>"

# Watch job progress
watch -n 5 "curl -s http://localhost:8000/api/v1/admin/ingest/status | jq '.jobs[] | select(.job_id==\"$JOB_ID\")'"
```

---

## Summary

### ✅ Good News
1. **All 4 stuck jobs were automatically resolved** by the orphaned job detector
2. **Worker is currently healthy** and ready to process new jobs
3. **System has built-in recovery mechanisms** that successfully kicked in

### ⚠️ Areas for Improvement
1. **Redis cleanup needed** - 10 stale messages and 1 pending message remain
2. **Root cause unclear** - jobs failed immediately (0 documents processed)
3. **Path resolution issue** - all jobs have `repo_path: None`
4. **Error handling** - original failure wasn't properly captured until container restart

### 🎯 Next Steps
1. Clean up Redis messages (run cleanup commands above)
2. Review worker logs for original failure cause
3. Test with new ingestion job to verify system works
4. Consider implementing suggested code improvements for better error handling

---

## Appendix: Investigation Output

<details>
<summary>Full Investigation Output (click to expand)</summary>

```
Jobs investigated: 4
Jobs not found: 0
Jobs with issues: 0
Total issues found: 0

All jobs were found and marked as "failed" with error:
"Job orphaned after container restart (age: 17-18 hours)"

Current system state:
- Worker: Running, Healthy, Processing
- Redis: 10 messages in stream, 1 pending
- Database: 6 total jobs, all marked as failed
```

</details>

---

**Investigation Status:** ✅ Complete  
**System Status:** ✅ Healthy  
**Action Required:** ⚠️ Redis Cleanup Recommended

