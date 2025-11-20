**Date:** November 20, 2025  
**Status:** Investigating Why Runs Fail with 0 Artifacts  
**Issue:** UI Showing Old Documentation, Recent Runs Failing  

# Runs Failing with 0 Artifacts - Analysis

## 🔍 Problem Summary

**User Reports:**
1. UI showing documentation with "insufficient info" but NO disclosure sections
2. Runs referenced (ad4e1c08, 7f9ff4fd) have 0 artifacts
3. Recent runs appearing to fail immediately

## 📊 Investigation Findings

### Finding 1: Referenced Runs Are Failures

```
Run: 7f9ff4fd-b0f3-4e1c-bab9-7881f26a4d8b
  Status: failed
  Duration: 0.022116s (failed immediately!)
  Artifacts: 0

Run: ad4e1c08-b34c-49f2-bc29-c32a6e86bfb8
  Status: failed
  Duration: 0.040783s (failed immediately!)
  Artifacts: 0
```

**Conclusion:** User CANNOT be viewing output from these runs - they have no artifacts!

### Finding 2: UI is Showing Cached/Old Documentation

The documentation user sees is NOT from these failed runs. It's either:
1. Browser cached from an older successful run
2. UI state holding stale data
3. Viewing wrong run in the UI

### Finding 3: Two Types of Failures

**Type A: Immediate Failures (< 1 second)**
- Recent runs: 7f9ff4fd, ad4e1c08
- Duration: ~0.02-0.04 seconds
- Likely: Code error causing immediate crash

**Type B: Timeout Failures (30+ minutes)**
- Older runs: 49222c45, cdcb7016, a4ee6b1c
- Duration: 1800-3200 seconds
- Likely: Hit timeout limits, hangs

### Finding 4: Templates Exist

```
✅ api_reference template found in database
✅ Orchestrator instantiates successfully
✅ Direct test generation works!
```

But some runs fail with "Template not found: api_reference"

### Finding 5: Test Run Status

Created test run: 3d3ad9a5
- After 65 seconds: Still "running"
- Artifacts: 0
- Not failed, but not completing

## 🎯 Root Causes Identified

### Cause #1: Database Connection Issues ⚠️
Some runs can't find templates that exist, suggesting:
- Database session timing out
- Connection pool exhausted
- Transaction isolation issues

### Cause #2: Worker Processing Issues ⚠️
- Background worker may not be picking up all runs
- Or processing but encountering errors
- Test generation works directly but not via worker

### Cause #3: Timeout Without Error Handling ⚠️
- Some runs running > 65 seconds without completing
- May be stuck in RAG calls or database queries
- Not failing fast enough

### Cause #4: Artifact Saving Failures ⚠️
- Generation may complete but artifact save fails
- Would result in "completed" status but 0 artifacts
- Silent failure after generation

## 🔬 Evidence

### What Works ✅
```python
# Direct orchestrator call succeeds
orchestrator = get_adaptive_orchestrator()
result = await orchestrator.generate_adaptive_documentation(...)
# ✅ Generation successful! Content: 8962 chars
```

### What Fails ❌
```
# Via API + worker
POST /api/v1/documentation/runs
# ❌ Runs fail immediately OR hang
# ❌ 0 artifacts generated
```

## 💡 Hypothesis

**Primary Theory:**
The issue is in the **background worker** or **API integration**, NOT the core orchestrator code.

The orchestrator works fine when called directly, but:
1. Worker may not be properly handling errors
2. Worker may not be passing correct parameters
3. Worker may be using stale database connections
4. Artifact saving may be failing silently

## ✅ Solutions to Implement

### Solution 1: Fix Worker Error Handling

**Current Issue:** Worker fails silently or doesn't log errors properly

**Fix:**
```python
# In documentation_worker.py
try:
    result = await orchestrator.generate_adaptive_documentation(...)
    # Check if result has content
    if not result.get("content"):
        raise ValueError("No content generated")
except Exception as e:
    logger.error(f"Worker failed: {e}", exc_info=True)
    # Update run status with error
    await self._update_run_status(run_id, "failed", str(e))
```

### Solution 2: Add Comprehensive Logging

**Need:** Visibility into worker execution

**Add:**
- Log when worker picks up run
- Log each phase of generation
- Log artifact saving
- Log completion/failure

### Solution 3: Fix Artifact Saving

**Issue:** Artifacts may not be saving even when generation succeeds

**Check:**
- Database session management in artifact save
- Transaction commits
- Foreign key constraints
- Error handling in save operation

### Solution 4: Add Worker Health Checks

**Need:** Know if worker is running and healthy

**Add:**
- Worker heartbeat logging
- Status endpoint showing worker state
- Metrics for runs processed/failed

### Solution 5: Restart/Rebuild Worker

**Quick Fix:** Worker may be in bad state

**Try:**
```bash
# Restart just the service
docker-compose restart ecosystem-mcp

# Or full rebuild
docker-compose down
docker-compose up -d --build ecosystem-mcp
```

## 🧪 Testing Plan

### Test 1: Verify Worker is Running
```bash
docker logs ecosystem-mcp-service 2>&1 | grep "Worker"
# Should see: "Documentation worker started"
```

### Test 2: Check Worker Heartbeat
```bash
docker logs ecosystem-mcp-service 2>&1 | grep "WORKER HEARTBEAT" | tail -5
# Should see recent heartbeats
```

### Test 3: Monitor Run End-to-End
```bash
# Create run
RUN_ID=$(curl ...)

# Monitor logs in real-time
docker logs -f ecosystem-mcp-service 2>&1 | grep "$RUN_ID"
```

### Test 4: Check Artifact Saving
```bash
# After run completes, check database
docker exec ecosystem-mcp-service python -c "
# Query for artifacts
# Should find at least 1
"
```

## 📝 Immediate Actions

1. **Check if worker is running:**
   ```bash
   docker logs ecosystem-mcp-service | grep "Documentation worker"
   ```

2. **Create a test run and monitor logs:**
   ```bash
   # Create run
   # Watch logs in real-time
   docker logs -f ecosystem-mcp-service
   ```

3. **If worker not running:**
   ```bash
   # Restart service
   docker-compose restart ecosystem-mcp
   ```

4. **If worker running but failing:**
   - Check database connection
   - Check template availability
   - Check error logs

## 🎯 Expected vs Actual

### Expected Behavior:
1. Create run via API → "pending"
2. Worker picks up run → "running"
3. Generate documentation → content created
4. Save artifact → DB has artifact
5. Update run → "completed"
6. UI shows → new documentation

### Actual Behavior:
1. Create run via API → "pending" ✅
2. Worker picks up run → "running" (maybe?)
3. Generate documentation → ❓
4. Save artifact → ❌ 0 artifacts
5. Update run → "failed" or stuck "running"
6. UI shows → old cached documentation

## 🚨 Critical Issues

### Issue #1: NO ARTIFACTS BEING SAVED ⚠️⚠️⚠️
**Impact:** HIGH - Users see no new documentation
**Priority:** CRITICAL
**Fix:** Debug artifact saving in Phase 5

### Issue #2: Runs Failing Immediately
**Impact:** HIGH - System appears broken
**Priority:** HIGH
**Fix:** Add error logging, fix worker

### Issue #3: UI Showing Cached Data
**Impact:** MEDIUM - User confusion
**Priority:** MEDIUM
**Fix:** Browser cache clear, UI refresh logic

## 📊 Success Metrics

When fixed, we should see:
- ✅ Runs complete in 60-90 seconds
- ✅ Status: "completed"
- ✅ Artifacts: 1+ in database
- ✅ UI shows new documentation
- ✅ Disclosure sections visible (when appropriate)

## 🔧 Next Steps

1. Check worker logs for errors
2. Add more detailed logging to worker
3. Test artifact saving directly
4. Monitor next run end-to-end
5. Fix any identified issues

---

**Status:** Investigation ongoing, multiple hypotheses identified, fixes proposed.

