# Worker Issue - Root Cause Analysis

**Date:** October 25, 2025  
**Status:** Root Causes Identified  
**Issue:** Ingestion jobs stuck in "queued" status, never processing  

---

## 🔍 Investigation Summary

### Symptoms
- Jobs created successfully in PostgreSQL (`status = "queued"`)
- Jobs never transition to `"processing"` or complete
- Worker reports as "healthy" and "running"
- No embeddings generated despite documents existing in database

### Root Causes Identified

#### 1. ⚠️  **Orphaned Job Detector Loop** (FIXED)
**Location:** `services/ecosystem-mcp/src/api/app.py:189-203`

**Problem:**
- Orphaned job detector runs on every service restart
- Checks for jobs in "processing" status with no Redis message
- When worker picks up a job, it ACKs the Redis message (removes it from queue)
- Job remains in "processing" status while actively working
- On restart, detector sees: status="processing" + no Redis message = "orphaned"
- Detector re-queues the job
- Creates infinite loop with frequent service restarts

**Evidence:**
```
✅ ALL SERVICES INITIALIZED SUCCESSFULLY (5 occurrences)
⚠️  Orphaned job detected: 1a69f36c-cbd6-4049-a919-4b4426f9cccd
   Re-queuing recent orphaned job 1a69f36c-cbd6-4049-a919-4b4426f9cccd (age: 0:02:59.018324)
```

**Fix Applied:**
- Temporarily disabled orphaned job detector
- Added TODO to re-enable with improved logic (check worker heartbeat, progress updates)

**Code Change:**
```python
# Line 192 in app.py
logger.info("  ⏭️  Orphaned job detection DISABLED (temporary)")
# Commented out detect_orphaned_jobs() call
```

---

#### 2. ⚠️  **Redis Stream Empty Despite Job Creation** (INVESTIGATING)
**Location:** Redis stream `ingestion:jobs`

**Problem:**
- Jobs are successfully added to Redis:
  ```
  ✅ Job added to Redis stream with message_id: 1761366252945-0
  ```
- But Redis stream shows 0 messages:
  ```bash
  $ redis-cli XLEN ingestion:jobs
  0
  ```
- Worker cannot pick up jobs if stream is empty

**Possible Causes:**
1. **Worker consuming too fast:** Messages ACKed immediately after creation
2. **Stream auto-trimming:** Redis configured to purge messages
3. **Consumer group issue:** Messages in pending state, not visible to `XLEN`
4. **Stream deletion:** Something is deleting the stream

**Current State:**
- Redis healthy: 10,727 keys (mostly `embed:*` cache)
- Consumer group exists but shows "ERR no such key" when queried
- Worker polls every 1 second but finds no messages

---

#### 3. 🐛 **No Embeddings Generated** (SECONDARY ISSUE)
**Location:** `services/ecosystem-mcp/src/services/ingestion/job_processor.py`

**Problem:**
- Documents created in PostgreSQL with `embedding_id = null`
- 848+ documents exist without embeddings from previous runs
- Code should detect `needs_embedding = True` and regenerate
- But documents are being "skipped" as duplicates

**Evidence:**
```json
{
  "processed_documents": 0,
  "skipped_documents": 848,
  "failed_documents": 2,
  "embeddings_generated": 0
}
```

**Root Cause:**
- Documents were created during previous failed ingestions
- Embeddings never generated due to errors (e.g., binary files causing DB encoding errors)
- Current code path skips documents if `content_hash` matches, even if `embedding_id` is null
- The `needs_embedding` check exists but is not being reached

**Compounding Factor:**
- Database commit happens at line 1344 BEFORE embedding generation at line 1352
- If any error occurs after commit, document persists without embedding

---

## ✅ Fixes Applied

### 1. Disabled Orphaned Job Detector
- **File:** `services/ecosystem-mcp/src/api/app.py`
- **Change:** Commented out `detect_orphaned_jobs()` call on startup
- **Status:** ✅ Deployed
- **Impact:** Prevents re-queuing loop during debugging

### 2. Added Debug Logging
- **File:** `services/ecosystem-mcp/src/services/ingestion/job_processor.py`
- **Change:** Added duplicate check debug logging
  ```python
  logger.debug(
      f"🔍 Duplicate check: {file_path} - "
      f"embedding_id={existing.embedding_id}, needs_embedding={needs_embedding}"
  )
  ```
- **Status:** ✅ Deployed

---

## 🚧 Next Steps

### Immediate (Required to unblock ingestion)
1. ✅ Investigate Redis stream issue
   - Check if consumer group is stuck
   - Verify worker is polling correctly
   - Test with fresh stream creation
   
2. ⏳ Fix worker polling loop
   - Ensure messages aren't being consumed and lost
   - Add better logging around message acknowledgment
   - Verify Redis stream consumer group configuration

### Short-term (Fix embedding generation)
3. ⏳ Fix embedding generation for existing documents
   - Either: Implement `force_update=true` to regenerate all
   - Or: Wipe database and re-ingest with fixed code

4. ⏳ Fix job processor commit order
   - Move database commit to AFTER embedding generation
   - Or: Use transactions to rollback if embedding fails

### Long-term (Prevent recurrence)
5. ⏳ Re-enable orphaned job detector with improvements
   - Check worker heartbeat (updated in last N minutes)
   - Check job progress (documents processed increasing)
   - Only mark as orphaned if truly stuck

6. ⏳ Add monitoring and alerts
   - Worker polling frequency
   - Redis stream depth
   - Job processing duration
   - Embedding generation success rate

---

## 📊 Current System State

### Worker Status
- **Running:** ✅ Yes
- **Healthy:** ✅ Yes (per API)
- **Polling:** ❓ Unknown (no logs)
- **Processing:** ❌ No jobs picked up

### Redis Status
- **Connected:** ✅ Yes
- **Keys:** 10,727 (mostly `embed:*`)
- **Stream Length:** 0 messages
- **Consumer Group:** Exists but shows "ERR no such key"

### Database Status
- **Jobs Created:** ✅ Yes (multiple queued jobs)
- **Documents:** 848+ without embeddings
- **Embeddings:** 0 generated in recent jobs

### Jobs Status
| Job ID (short) | Status | Mode | Issue |
|---|---|---|---|
| 04988f08 | queued | enriched | Never picked up |
| 56ac6bd1 | queued | snapshot | Added to Redis but not processed |
| 1a69f36c | queued | enriched | Re-queued by orphaned detector (loop) |
| 71035613 | queued | enriched | Re-queued by orphaned detector (loop) |

---

## 🎯 Recommended Action

**Immediate:** Investigate why Redis stream is empty despite jobs being added. This is the primary blocker preventing all job processing.

**Suspected Issue:** Consumer group configuration or worker polling logic preventing messages from being visible/consumable.

**Test:** Create a simple Redis stream test to verify basic stream operations work correctly.

---

**Last Updated:** October 25, 2025 04:30 UTC

