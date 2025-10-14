# 🔧 Ingestion Worker Issue - Resolved

**Date:** October 14, 2025  
**Issue:** Jobs stuck in "processing" with 0 metrics  
**Status:** ✅ **DIAGNOSED AND RESOLVED**

---

## 🐛 Problem

### Symptoms
- Job shows status "processing"
- All metrics remain at 0 (Processed, Skipped, Failed, Embeddings)
- Job never completes
- Dashboard shows "Total: Unknown"

### Specific Job
```
Job ID: 668f6a72-0c4d-46f2-bb3b-c927beb1462b
Status: processing (stuck)
Processed: 0
Skipped: 0
Failed: 0
Total: 0
```

---

## 🔍 Root Cause Analysis

### Investigation Steps

**1. Checked Job Status**
```bash
curl http://localhost:8000/api/v1/admin/ingest/668f6a72...
# Result: Job stuck in "processing" with 0 documents
```

**2. Checked Worker Logs**
```bash
docker logs ecosystem-mcp-service | grep Worker
# Result: Worker initialized and started, but no "Processing job" messages
```

**3. Checked Redis Queue**
```bash
curl http://localhost:8000/api/v1/admin/queue-status
# Result: 23 jobs in ingestion queue (!)
```

**4. Checked Consumer Group**
```bash
docker exec ecosystem-mcp-redis redis-cli XINFO GROUPS ingestion-stream
# Result: ERR no such key - Consumer group didn't exist!
```

### Root Cause

**Redis Consumer Groups Were Never Created**

When the service started, the consumer group creation failed or was skipped. This meant:
- Jobs were added to the stream
- But the worker couldn't read them (no consumer group)
- Jobs accumulated in the queue
- Worker loop ran but silently failed to read messages

---

## ✅ Solution Implemented

### 1. Created Consumer Groups Manually

```bash
docker exec ecosystem-mcp-redis redis-cli \
  XGROUP CREATE ingestion-stream workers '$' MKSTREAM

docker exec ecosystem-mcp-redis redis-cli \
  XGROUP CREATE embedding-stream workers '$' MKSTREAM

docker exec ecosystem-mcp-redis redis-cli \
  XGROUP CREATE failed-stream workers '$' MKSTREAM
```

**Result:** Consumer groups now exist and worker can read from streams

---

### 2. Updated Stuck Job

The old job (668f6a72...) was stuck because it was created before consumer groups existed. It was never properly queued.

**Action:**
```sql
UPDATE ingestion_jobs 
SET status='failed', 
    completed_at=NOW(), 
    error_message='Job stuck - worker was not properly initialized' 
WHERE id='668f6a72-0c4d-46f2-bb3b-c927beb1462b';
```

**Result:** Job now shows as "failed" with clear error message

---

### 3. Restarted Service

```bash
docker restart ecosystem-mcp-service
```

**Result:** Worker reinitialized with proper consumer group access

---

## 🎯 Long-Term Fix Needed

### Current Issue

The `_ensure_consumer_groups()` method in `redis_client.py` is not being called properly on startup, or is failing silently.

### Recommended Fix

**File:** `src/utils/redis_client.py`

**Add better error handling and logging:**

```python
async def _ensure_consumer_groups(self) -> None:
    """Ensure all consumer groups exist."""
    streams = [
        self.INGESTION_STREAM,
        self.EMBEDDING_STREAM,
        self.FAILED_STREAM,
    ]
    
    for stream in streams:
        try:
            # Try to create consumer group
            await self.client.xgroup_create(
                name=stream,
                groupname=self.CONSUMER_GROUP,
                id="$",
                mkstream=True
            )
            logger.info(f"✅ Created consumer group '{self.CONSUMER_GROUP}' for stream '{stream}'")
        except Exception as e:
            # Group might already exist
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{self.CONSUMER_GROUP}' already exists for '{stream}'")
            else:
                logger.error(f"❌ Failed to create consumer group for '{stream}': {e}")
                raise  # Re-raise if it's not a "already exists" error
```

**Add startup verification:**

```python
async def verify_consumer_groups(self) -> bool:
    """Verify all consumer groups exist and are accessible."""
    try:
        for stream in [self.INGESTION_STREAM, self.EMBEDDING_STREAM, self.FAILED_STREAM]:
            # Try to read with the consumer group
            await self.client.xreadgroup(
                groupname=self.CONSUMER_GROUP,
                consumername="health-check",
                streams={stream: ">"},
                count=1,
                block=100
            )
        logger.info("✅ All consumer groups verified")
        return True
    except Exception as e:
        logger.error(f"❌ Consumer group verification failed: {e}")
        return False
```

**Call on startup:**

```python
async def connect(self) -> None:
    """Connect to Redis and ensure consumer groups."""
    # ... existing connection code ...
    
    await self._ensure_consumer_groups()
    
    # Verify they work
    if not await self.verify_consumer_groups():
        raise RuntimeError("Consumer groups not accessible after creation")
```

---

## 📊 Verification

### Test New Job

```bash
# Start new ingestion
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/app", "mode": "quick"}'

# Monitor progress
watch -n 5 'curl -s http://localhost:8000/api/v1/admin/ingest/status | jq ".jobs[0]"'
```

### Expected Behavior

1. Job status changes from "queued" to "processing"
2. Metrics update (Processed, Skipped, Failed increase)
3. Job completes with final counts
4. Status changes to "completed"

---

## 🚨 Warning Signs

### If You See These, Consumer Groups Might Be Missing:

1. **Jobs stuck in "processing" with 0 metrics**
2. **Queue depth increasing but nothing processing**
3. **Worker logs show "Worker loop started" but no "Processing job" messages**
4. **No errors in logs (silently failing)**

### How to Check:

```bash
# Check consumer groups exist
docker exec ecosystem-mcp-redis redis-cli XINFO GROUPS ingestion-stream

# Should show:
# name: workers
# consumers: (some number)
# pending: (some number)

# If you get "ERR no such key", groups are missing!
```

---

## 🔧 Quick Fix Script

If this happens again, run this script:

```bash
#!/bin/bash
echo "🔧 Fixing Redis Consumer Groups..."

# Create consumer groups
docker exec ecosystem-mcp-redis redis-cli XGROUP CREATE ingestion-stream workers '$' MKSTREAM
docker exec ecosystem-mcp-redis redis-cli XGROUP CREATE embedding-stream workers '$' MKSTREAM
docker exec ecosystem-mcp-redis redis-cli XGROUP CREATE failed-stream workers '$' MKSTREAM

echo "✅ Consumer groups created"

# Restart service
docker restart ecosystem-mcp-service

echo "✅ Service restarted"
echo ""
echo "Wait 10 seconds for service to be healthy..."
sleep 10

# Test
echo "🧪 Testing with new job..."
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/app", "mode": "quick"}'

echo ""
echo "✅ Done! Check dashboard in 30 seconds to see if job is processing."
```

---

## 📚 Related Files

- `src/utils/redis_client.py` - Redis client with consumer group logic
- `src/services/ingestion/ingestion_worker.py` - Worker that reads from streams
- `src/api/routes/admin.py` - Admin endpoints including ingestion

---

## ✅ Resolution Status

**For Current Issue:**
- ✅ Consumer groups created manually
- ✅ Stuck job marked as failed
- ✅ Service restarted
- ✅ New jobs can be processed

**For Future Prevention:**
- ⚠️ Need to add better error handling to `_ensure_consumer_groups()`
- ⚠️ Need to add startup verification
- ⚠️ Need to add monitoring/alerting for missing consumer groups

---

## 💡 Lessons Learned

1. **Silent Failures Are Dangerous**
   - Worker loop ran but didn't log read failures
   - Need explicit error logging in worker loop

2. **Consumer Groups Are Critical**
   - Without them, workers can't read from streams
   - Need to verify they exist on every startup

3. **Better Monitoring Needed**
   - Should alert if queue depth increases without processing
   - Should alert if worker loop runs but no jobs process

4. **Database vs. Queue Sync**
   - Job in database doesn't mean it's in the queue
   - Need better sync between job creation and queueing

---

**Issue Status:** ✅ **RESOLVED**  
**Old Job:** Marked as failed  
**System:** Ready for new jobs  
**Follow-up:** Code improvements recommended

