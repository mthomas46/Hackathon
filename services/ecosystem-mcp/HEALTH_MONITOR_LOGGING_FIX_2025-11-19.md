**Date:** November 19, 2025  
**Status:** Health Monitor Logging Enhanced  
**Coverage:** INFO-level Visibility, Detailed Detection Logging  

---

# Worker Health Monitor - Logging Enhancement

## Problem

The worker health monitor was running but its detection logic was invisible because:
1. **Logs at DEBUG level** - Not visible in normal operation
2. **Minimal detection feedback** - No visibility into what jobs were checked
3. **No age calculations** - Couldn't see how long jobs had been queued

### Symptoms

- Health monitor ran 4+ checks
- Jobs stuck in "queued" for > 2 minutes
- No automatic restart triggered
- No logs showing what the monitor was finding

---

## Solution

### 1. ✅ Upgraded Logging to INFO Level

**Changed**:
```python
# Before
logger.debug(f"🏥 Running health check #{self.stats['health_checks']}")
logger.debug("✅ Worker health check passed")

# After  
logger.info(f"🏥 Running health check #{self.stats['health_checks']}")
logger.info("✅ Worker health check passed")
```

**Impact**: All health checks now visible in standard logs

### 2. ✅ Enhanced Stuck Queue Detection Logging

**Added Detailed Job Analysis**:
```python
# New: Shows how many queued jobs were found
logger.info(f"🔍 Found {len(queued_jobs)} queued jobs to check")

# New: Shows the cutoff time being used
logger.info(f"🔍 Checking jobs queued before: {cutoff_time} (threshold: {self.max_queued_seconds}s)")

# New: Shows each job's age and stuck status
for job in queued_jobs:
    age_seconds = (datetime.utcnow() - job.started_at).total_seconds()
    logger.info(
        f"🔍 Job {str(job.id)[:12]}: started_at={job.started_at}, "
        f"age={int(age_seconds)}s, "
        f"stuck={age_seconds > self.max_queued_seconds}"
    )

# New: Summary when no stuck jobs found
logger.info(f"✅ No stuck queued jobs detected (checked {len(queued_jobs)} jobs)")
```

**Impact**: Full visibility into detection logic

### 3. ✅ Added Age Calculations

**Before**:
```python
if job.started_at and job.started_at < cutoff_time:
    logger.warning(f"Job {job.id} stuck in queued (age: {datetime.utcnow() - job.started_at})")
```

**After**:
```python
age = datetime.utcnow() - job.started_at
age_seconds = age.total_seconds()

logger.info(f"Job age: {int(age_seconds)}s, stuck={age_seconds > {self.max_queued_seconds}}")

if job.started_at < cutoff_time:
    logger.warning(f"Job {job.id} stuck in queued (age: {age}, {int(age_seconds)}s)")
```

**Impact**: Clear age calculations visible before decisions

---

## Example Logs

### Health Check Start

```
🏥 Running health check #1
```

### Checking Queued Jobs

```
🔍 Found 2 queued jobs to check
🔍 Checking jobs queued before: 2025-11-19T21:55:00 (threshold: 120s)
🔍 Job d4509ea1-8ae: started_at=2025-11-19T21:51:39, age=205s, stuck=True
🔍 Job f4112e6b-394: started_at=2025-11-19T21:52:10, age=174s, stuck=True
⚠️  Job d4509ea1-8ae3-4944-b055-8b3d7aa62df8 stuck in queued (age: 0:03:25, 205s)
⚠️  Job f4112e6b-3944-4a7c-94a7-5b731fee667d stuck in queued (age: 0:02:54, 174s)
⚠️  2 queued jobs + 5 Redis messages = WORKER STUCK
🔄 Restarting worker: 2 jobs stuck in queued status
✅ Worker restarted successfully (total restarts: 1)
```

### No Stuck Jobs

```
🏥 Running health check #2
🔍 Found 0 queued jobs to check
✅ No stuck queued jobs detected (checked 0 jobs)
✅ Worker health check passed
```

### In Cooldown

```
🏥 Running health check #3
⏳ In restart cooldown (240s remaining)
```

---

## Testing

### How to Verify Enhanced Logging

**1. Watch health check logs** (checks run every 60s after 2-min warmup):
```bash
docker logs -f ecosystem-mcp-service 2>&1 | grep "🏥"
```

**Expected Output Every 60 Seconds**:
```
🏥 Running health check #1
🔍 Found X queued jobs to check
✅ Worker health check passed
```

**2. Create a stuck job to test detection**:
```bash
# Create a job
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/work/adminservice", "mode": "snapshot"}'

# Stop the worker (simulate hang)
curl -X POST http://localhost:8000/api/v1/admin/workers/ingestion/stop

# Wait 3 minutes for health monitor to detect and auto-restart
# Watch logs for detailed detection output
```

**3. Check health monitor stats**:
```bash
curl http://localhost:8000/api/v1/admin/workers/health-monitor/status | jq
```

---

## What Changed

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `worker_health_monitor.py` | 177, 183, 201 | Changed DEBUG → INFO |
| `worker_health_monitor.py` | 254-283 | Added detailed job checking logs |
| `worker_health_monitor.py` | 267-275 | Added age calculation logging |
| `worker_health_monitor.py` | 295-296 | Added "no stuck jobs" summary |

---

## Benefits

### Before (DEBUG Logging)
- ❌ No visibility into health checks
- ❌ Couldn't see what jobs were checked
- ❌ No age information
- ❌ Detection logic was a black box

### After (INFO Logging)
- ✅ Every health check logged
- ✅ Every queued job analyzed and logged
- ✅ Age calculations shown
- ✅ Clear detection logic visible
- ✅ Stuck/not-stuck decision explained

---

## Troubleshooting

### Issue: Still not seeing health check logs

**Check**:
1. Health monitor takes 2 minutes to start checking (warmup period)
2. Checks run every 60 seconds after warmup
3. If in restart cooldown (5 min), shows cooldown message

**Verify**:
```bash
# Check health monitor is running
curl http://localhost:8000/api/v1/admin/workers/health-monitor/status | jq '.running'

# Check how many checks have run
curl http://localhost:8000/api/v1/admin/workers/health-monitor/status | jq '.stats.health_checks'
```

### Issue: Detection still not working

**Possible Causes**:
1. Worker is restarted → 5-minute cooldown active
2. Jobs are not actually "queued" in database
3. Jobs queued < 120 seconds
4. Health monitor crashed (check status endpoint)

**Debug**:
```bash
# Check for stuck queued jobs manually
curl -s http://localhost:8000/api/v1/admin/ingest | jq '.jobs[] | select(.status=="queued") | {job_id: .job_id[:12], status, started_at}'

# Check health monitor errors
docker logs ecosystem-mcp-service 2>&1 | grep -i "health.*error"
```

---

## Next Test

### Verify Detection Works

**Timeline**:
- **T+0s**: Service started (21:57:23)
- **T+120s**: First health check runs (21:59:23)
- **T+180s**: Second health check runs (22:00:23)
- **T+240s**: Third health check runs (22:01:23)

**What to Watch**:
1. Look for `🏥 Running health check #N` in logs
2. Check what it finds: `🔍 Found X queued jobs`
3. If stuck jobs exist: See detailed age analysis
4. If > 120s: See restart trigger

**Expected Behavior**:
- If job queued > 120s → Auto-restart worker
- If no stuck jobs → "✅ Worker health check passed"
- If just restarted → "⏳ In restart cooldown"

---

## Related Files

- `worker_health_monitor.py` - Enhanced logging implementation
- `WORKER_HEALTH_MONITOR_2025-11-19.md` - Full system documentation
- `app.py` - Service initialization

---

## Summary

### What Was Fixed

✅ **Logging Level**: DEBUG → INFO for all health checks  
✅ **Stuck Queue Logs**: Detailed analysis of every queued job  
✅ **Age Calculations**: Show job age and stuck threshold  
✅ **Detection Summary**: Clear "stuck" vs "not stuck" output  
✅ **Visibility**: Full transparency into detection logic  

### Impact

- **Before**: Black box - no idea what health monitor was doing
- **After**: Full visibility - see every check, every job, every decision

### Test Status

- ✅ Enhanced logging deployed
- ⏳ Waiting for first health check (T+2 minutes after restart)
- ⏳ Will monitor next stuck job to verify detection

---

**Deployment Status**: ✅ **ENHANCED LOGGING DEPLOYED**  
**Next Health Check**: **~2 minutes after restart (21:59:23)**  
**Operator Action**: 📊 **Watch logs for detailed health check output**

