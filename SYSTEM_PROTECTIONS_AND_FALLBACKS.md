# 🛡️ System Protections & Fallbacks - Implementation Plan

**Date:** October 16, 2025  
**Purpose:** Add comprehensive protections for all issues discovered and resolved  
**Status:** 📋 PLANNING

---

## 🎯 Problems Solved So Far (Requiring Protection)

### **1. Phantom Job Processing**
**Problem:** Worker continues processing deleted/cancelled jobs indefinitely.

**Current Solution:** Periodic check every 10 files.

**Missing Protections:**
- ❌ No automatic detection on startup
- ❌ No job timeout (could run for weeks)
- ❌ No way to manually cancel a job
- ❌ No alert if job stuck for > N hours
- ❌ No cleanup of old "processing" jobs

---

### **2. SQLAlchemy JSONB Update Failures**
**Problem:** Database updates fail silently, progress stuck at 0.

**Current Solution:** `flag_modified()` for JSONB fields.

**Missing Protections:**
- ❌ No validation that flag_modified is called
- ❌ No retry mechanism on update failure
- ❌ No alert on repeated update failures
- ❌ No automated testing for JSONB updates
- ❌ Other files may have same issue (not audited)

---

### **3. Orphaned Jobs After Container Restart**
**Problem:** Job in PostgreSQL: "processing", Redis queue: empty.

**Current Solution:** Manual job recreation.

**Missing Protections:**
- ❌ No automatic detection on startup
- ❌ No re-queue mechanism
- ❌ No job recovery from checkpoint
- ❌ No Redis message persistence verification
- ❌ No graceful shutdown before restart

---

### **4. Python Module Caching After Code Changes**
**Problem:** `docker cp` + restart doesn't reload Python code.

**Current Solution:** Full container rebuild.

**Missing Protections:**
- ❌ No documented deployment process
- ❌ No automated deployment script
- ❌ No verification that new code loaded
- ❌ No version tracking in worker logs
- ❌ Easy to forget and use `docker cp` again

---

### **5. UI Showing Stale Data**
**Problem:** Auto-refresh not working, manual refresh needed.

**Current Solution:** 3-second auto-refresh.

**Missing Protections:**
- ❌ No visual indicator of last update time
- ❌ No warning if data is stale (> 60s old)
- ❌ No offline/connection error handling
- ❌ No retry on API failure
- ❌ No loading state during refresh

---

## 🔧 Comprehensive Protection Plan

---

## **PRIORITY 1: Critical Runtime Protections**

### **1.1 Fail Job Endpoint**
**Purpose:** Allow manual cancellation of stuck jobs.

**Implementation:**
```python
# Route: POST /api/v1/admin/ingest/{job_id}/fail
@router.post("/ingest/{job_id}/fail")
async def fail_job(
    job_id: UUID,
    request: FailJobRequest
):
    """
    Manually fail a job.
    
    - Updates job status to 'failed'
    - Sets error message
    - Removes from Redis queue if present
    - Triggers worker to stop processing
    """
    async with db.session() as session:
        repo = IngestionJobRepository(session)
        job = await repo.get_by_id(job_id)
        
        if not job:
            raise HTTPException(404, "Job not found")
        
        if job.status not in ["queued", "processing"]:
            raise HTTPException(400, f"Cannot fail job in {job.status} state")
        
        # Update job
        job.status = "failed"
        job.error_message = request.error or "Manually cancelled"
        job.finished_at = datetime.utcnow()
        
        flag_modified(job, "job_metadata")
        await repo.update(job)
        await session.commit()
        
        # Remove from Redis if queued
        redis = get_redis_client()
        # Delete pending messages for this job
        
        return {"message": f"Job {job_id} failed successfully"}
```

**Testing:**
- Unit test: Job status changes to "failed"
- Integration test: Worker stops processing within 10 files
- E2E test: UI shows job as failed

---

### **1.2 Orphaned Job Detection on Startup**
**Purpose:** Automatically detect and handle jobs left in "processing" state.

**Implementation:**
```python
async def detect_orphaned_jobs():
    """
    Run on service startup.
    Finds jobs in 'processing' state with no Redis message.
    """
    db = get_database()
    redis = get_redis_client()
    
    async with db.session() as session:
        repo = IngestionJobRepository(session)
        processing_jobs = await repo.get_by_status("processing")
        
        for job in processing_jobs:
            # Check if job has Redis message
            has_message = await redis_has_job_message(redis, job.id)
            
            if not has_message:
                logger.warning(f"Orphaned job detected: {job.id}")
                
                # Check last update time
                last_update = job.job_metadata.get("last_update") if job.job_metadata else None
                if last_update:
                    age = datetime.utcnow() - datetime.fromisoformat(last_update)
                    
                    if age > timedelta(hours=1):
                        # Old job - likely from container crash
                        logger.warning(f"Failing orphaned job {job.id} (age: {age})")
                        job.status = "failed"
                        job.error_message = "Job orphaned after container restart"
                        job.finished_at = datetime.utcnow()
                        
                        flag_modified(job, "job_metadata")
                        await repo.update(job)
                        await session.commit()
                    else:
                        # Recent job - try to recover
                        logger.info(f"Re-queuing recent orphaned job {job.id}")
                        await redis.xadd(
                            redis.INGESTION_STREAM,
                            {"job_id": str(job.id)}
                        )
```

**Hook into Startup:**
```python
@app.on_event("startup")
async def startup():
    # ... existing startup code ...
    await detect_orphaned_jobs()
    logger.info("✅ Orphaned job detection complete")
```

**Testing:**
- Simulate container crash
- Verify orphaned jobs are detected
- Verify old jobs are failed
- Verify recent jobs are re-queued

---

### **1.3 Automatic Job Timeout**
**Purpose:** Prevent jobs from running indefinitely.

**Implementation:**
```python
# Add to job_processor._process_commit loop
async def check_job_timeout(job: IngestionJobModel) -> bool:
    """Check if job has exceeded maximum runtime."""
    MAX_JOB_RUNTIME = timedelta(hours=24)
    
    if job.started_at:
        runtime = datetime.utcnow() - job.started_at
        
        if runtime > MAX_JOB_RUNTIME:
            logger.error(f"Job {job.id} exceeded timeout ({runtime} > {MAX_JOB_RUNTIME})")
            
            # Fail the job
            db = get_database()
            async with db.session() as session:
                repo = IngestionJobRepository(session)
                current_job = await repo.get_by_id(job.id)
                
                if current_job:
                    current_job.status = "failed"
                    current_job.error_message = f"Job timeout: exceeded {MAX_JOB_RUNTIME}"
                    current_job.finished_at = datetime.utcnow()
                    
                    flag_modified(current_job, "job_metadata")
                    await repo.update(current_job)
                    await session.commit()
            
            return True  # Timed out
    
    return False  # Still running
```

**Add to Processing Loop:**
```python
# In job_processor._process_commit
for idx, file_change in enumerate(filtered_files):
    # Check timeout every 100 files
    if idx > 0 and idx % 100 == 0:
        if await check_job_timeout(job):
            logger.error("Job timeout detected, stopping processing")
            result["error"] = "Job timeout"
            break
    
    # ... existing processing code ...
```

**Testing:**
- Mock datetime to simulate 25-hour runtime
- Verify job is failed with timeout error
- Verify worker stops processing

---

### **1.4 Worker Heartbeat**
**Purpose:** Detect truly stuck workers (not processing any files).

**Implementation:**
```python
async def update_worker_heartbeat(job: IngestionJobModel):
    """Update job metadata with worker heartbeat."""
    try:
        db = get_database()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            current_job = await repo.get_by_id(job.id)
            
            if current_job:
                metadata = current_job.job_metadata.copy() if current_job.job_metadata else {}
                metadata["worker_heartbeat"] = datetime.utcnow().isoformat()
                metadata["worker_id"] = self.worker_id  # If available
                current_job.job_metadata = metadata
                
                flag_modified(current_job, "job_metadata")
                await repo.update(current_job)
                await session.commit()
    except Exception as e:
        logger.debug(f"Failed to update heartbeat: {e}")

# Call every 30 seconds in processing loop
if idx > 0 and idx % 30 == 0:
    await update_worker_heartbeat(job)
```

**Monitoring Service:**
```python
async def monitor_stuck_workers():
    """
    Background task to detect stuck workers.
    Runs every 5 minutes.
    """
    while True:
        await asyncio.sleep(300)  # 5 minutes
        
        db = get_database()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            processing_jobs = await repo.get_by_status("processing")
            
            for job in processing_jobs:
                last_heartbeat = job.job_metadata.get("worker_heartbeat") if job.job_metadata else None
                
                if last_heartbeat:
                    age = datetime.utcnow() - datetime.fromisoformat(last_heartbeat)
                    
                    if age > timedelta(minutes=10):
                        logger.error(f"Stuck worker detected for job {job.id} (no heartbeat for {age})")
                        # Send alert, fail job, restart worker, etc.
```

**Testing:**
- Simulate worker freeze
- Verify heartbeat stops updating
- Verify alert is triggered

---

## **PRIORITY 2: Data Integrity Protections**

### **2.1 JSONB Update Validation**
**Purpose:** Ensure all JSONB updates use `flag_modified()`.

**Implementation:**
```python
# Create a wrapper class for JSONB fields
class TrackedJSONB:
    """Wrapper that enforces flag_modified usage."""
    
    def __init__(self, obj, field_name):
        self._obj = obj
        self._field = field_name
        self._value = getattr(obj, field_name) or {}
    
    def update(self, updates: dict):
        """Update JSONB field with automatic flag_modified."""
        new_value = self._value.copy()
        new_value.update(updates)
        setattr(self._obj, self._field, new_value)
        flag_modified(self._obj, self._field)
        return new_value
    
    def __getitem__(self, key):
        return self._value[key]
    
    def get(self, key, default=None):
        return self._value.get(key, default)

# Usage:
metadata = TrackedJSONB(job, 'job_metadata')
metadata.update({'progress_pct': 50})  # Automatically calls flag_modified
await session.commit()
```

**Linting Rule:**
```python
# Add to pre-commit hook or CI
# Check for direct JSONB assignment without flag_modified

import ast
import sys

class JSONBAssignmentChecker(ast.NodeVisitor):
    def visit_Assign(self, node):
        # Check for obj.job_metadata[key] = value
        # Without nearby flag_modified call
        # Raise error if found
        pass

# Run on all Python files
```

**Testing:**
- Add pre-commit hook
- Test catches direct assignment
- Test allows TrackedJSONB usage

---

### **2.2 Database Update Retry Mechanism**
**Purpose:** Retry failed database updates with exponential backoff.

**Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
async def update_job_progress_with_retry(
    job: IngestionJobModel,
    # ... other params ...
):
    """Update job progress with automatic retry."""
    try:
        db = get_database()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            # Get fresh job
            current_job = await repo.get_by_id(job.id)
            if not current_job:
                return
            
            # Update metadata
            metadata = current_job.job_metadata.copy() if current_job.job_metadata else {}
            metadata["last_processed_file"] = last_file
            metadata["progress_pct"] = progress_pct
            current_job.job_metadata = metadata
            
            # Update counters
            current_job.processed_documents = processed
            current_job.skipped_documents = skipped
            
            flag_modified(current_job, "job_metadata")
            await repo.update(current_job)
            await session.commit()
            
            logger.debug(f"✅ Job progress updated: {processed} processed")
            
    except Exception as e:
        logger.error(f"❌ Failed to update job progress (attempt {attempt}): {e}")
        raise  # Re-raise for retry
```

**Testing:**
- Mock database to fail twice
- Verify 3 attempts made
- Verify success on 3rd attempt
- Verify exponential backoff

---

### **2.3 Update Failure Monitoring**
**Purpose:** Track and alert on repeated update failures.

**Implementation:**
```python
from collections import defaultdict
from datetime import datetime, timedelta

class UpdateFailureMonitor:
    def __init__(self):
        self.failures = defaultdict(list)  # job_id -> [timestamps]
    
    def record_failure(self, job_id: UUID):
        """Record an update failure."""
        now = datetime.utcnow()
        self.failures[job_id].append(now)
        
        # Clean old failures (> 1 hour)
        self.failures[job_id] = [
            ts for ts in self.failures[job_id]
            if now - ts < timedelta(hours=1)
        ]
        
        # Check if too many failures
        if len(self.failures[job_id]) > 10:
            logger.error(f"🚨 HIGH UPDATE FAILURE RATE for job {job_id}: {len(self.failures[job_id])} failures in 1 hour")
            # Send alert to monitoring system
            # Consider pausing or failing the job
    
    def get_failure_rate(self, job_id: UUID) -> float:
        """Get failures per hour."""
        return len(self.failures.get(job_id, []))

# Global instance
update_monitor = UpdateFailureMonitor()

# Use in update code
try:
    await update_job_progress(...)
except Exception as e:
    update_monitor.record_failure(job.id)
    raise
```

**Testing:**
- Simulate 11 failures in 1 hour
- Verify alert is triggered
- Verify old failures are cleaned

---

## **PRIORITY 3: Recovery & Resilience**

### **3.1 Graceful Container Shutdown**
**Purpose:** Finish current file and checkpoint before stopping.

**Implementation:**
```python
import signal
import asyncio

class GracefulShutdownHandler:
    def __init__(self):
        self.shutdown_requested = False
        self.current_job_id = None
    
    def request_shutdown(self):
        """Signal that shutdown is requested."""
        self.shutdown_requested = True
        logger.info("🛑 Graceful shutdown requested")
    
    async def wait_for_checkpoint(self):
        """Wait for current file to finish."""
        if self.current_job_id:
            logger.info(f"⏳ Waiting for job {self.current_job_id} to checkpoint...")
            # Wait up to 60 seconds for checkpoint
            for _ in range(60):
                if not self.shutdown_requested:
                    break
                await asyncio.sleep(1)

# Global handler
shutdown_handler = GracefulShutdownHandler()

# Register signal handlers
def handle_sigterm(signum, frame):
    shutdown_handler.request_shutdown()

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

# In processing loop
for idx, file_change in enumerate(filtered_files):
    if shutdown_handler.shutdown_requested:
        logger.info("Shutdown requested, saving checkpoint...")
        # Save current position
        await save_checkpoint(job, idx)
        break
    
    # Process file...
```

**Testing:**
- Send SIGTERM during processing
- Verify checkpoint is saved
- Verify processing stops gracefully

---

### **3.2 Job Recovery from Checkpoint**
**Purpose:** Resume interrupted jobs from last saved position.

**Implementation:**
```python
async def resume_job_from_checkpoint(job: IngestionJobModel):
    """Resume a job from its last checkpoint."""
    checkpoint = job.job_metadata.get("checkpoint") if job.job_metadata else None
    
    if checkpoint:
        logger.info(f"📍 Resuming job {job.id} from checkpoint: {checkpoint}")
        
        return {
            "commit_sha": checkpoint.get("commit_sha"),
            "file_index": checkpoint.get("file_index", 0),
            "processed": checkpoint.get("processed", 0),
            "skipped": checkpoint.get("skipped", 0),
            "failed": checkpoint.get("failed", 0)
        }
    
    logger.info(f"🆕 Starting job {job.id} from beginning (no checkpoint)")
    return None

# In job processor
async def process(self, job: IngestionJobModel):
    # Try to resume from checkpoint
    checkpoint = await resume_job_from_checkpoint(job)
    
    if checkpoint:
        # Skip to checkpoint position
        start_commit = checkpoint["commit_sha"]
        start_file_idx = checkpoint["file_index"]
        result["processed"] = checkpoint["processed"]
        result["skipped"] = checkpoint["skipped"]
        result["failed"] = checkpoint["failed"]
    else:
        # Start from beginning
        start_commit = None
        start_file_idx = 0
    
    # Process commits...
```

**Testing:**
- Start job, interrupt at file 50
- Verify checkpoint saved
- Resume job
- Verify starts at file 51

---

### **3.3 Redis Persistence Verification**
**Purpose:** Ensure Redis messages survive container restarts.

**Implementation:**
```python
async def verify_redis_persistence():
    """
    Verify Redis appendonly.aof is enabled.
    Run on startup.
    """
    redis = get_redis_client()
    
    # Check Redis config
    config = await redis.client.config_get("appendonly")
    
    if config.get("appendonly") != "yes":
        logger.error("❌ Redis appendonly not enabled! Messages will be lost on restart!")
        # Send critical alert
    else:
        logger.info("✅ Redis persistence enabled (appendonly=yes)")
    
    # Check AOF file exists
    info = await redis.client.info("persistence")
    aof_enabled = info.get("aof_enabled", 0)
    
    if aof_enabled == 0:
        logger.error("❌ Redis AOF not active!")
    else:
        logger.info("✅ Redis AOF active")

@app.on_event("startup")
async def startup():
    await verify_redis_persistence()
```

**Testing:**
- Check with appendonly=yes
- Check with appendonly=no
- Verify alerts triggered

---

## **PRIORITY 4: Developer Experience**

### **4.1 Deployment Process Documentation**
**Purpose:** Prevent `docker cp` mistakes.

**Create:** `services/ecosystem-mcp/DEPLOYMENT.md`
```markdown
# Deployment Guide

## ❌ NEVER DO THIS:
```bash
docker cp file.py ecosystem-mcp-service:/app/file.py
docker restart ecosystem-mcp-service
```
**Why:** Python caches modules. Restart doesn't reload code.

## ✅ ALWAYS DO THIS:
```bash
cd /path/to/ecosystem-mcp
docker-compose up -d --force-recreate --build ecosystem-mcp
```
**Why:** Fresh container with `COPY . .` loads new code.

## Quick Deploy Script:
```bash
./scripts/deploy.sh [service_name]
```
```

**Create:** `services/ecosystem-mcp/scripts/deploy.sh`
```bash
#!/bin/bash
set -e

SERVICE=${1:-ecosystem-mcp}
echo "🚀 Deploying $SERVICE..."

cd "$(dirname "$0")/.."

# Build and restart
docker-compose up -d --force-recreate --build $SERVICE

# Wait for health check
echo "⏳ Waiting for health check..."
sleep 10

# Verify
curl -f http://localhost:8000/health || {
    echo "❌ Health check failed!"
    exit 1
}

echo "✅ Deployment complete!"
```

**Testing:**
- Run deploy script
- Verify container rebuilt
- Verify health check passes

---

### **4.2 Code Version Tracking**
**Purpose:** Know what code is running in production.

**Implementation:**
```python
# Add to startup logs
import subprocess

def get_git_commit():
    """Get current git commit hash."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd="/app"
        ).decode().strip()
    except:
        return "unknown"

@app.on_event("startup")
async def startup():
    commit = get_git_commit()
    logger.info(f"🏷️  Running code version: {commit}")
    # Store in metrics/monitoring
```

**Testing:**
- Check logs show git commit
- Verify matches actual commit

---

## **PRIORITY 5: UI/UX Improvements**

### **5.1 Last Updated Timestamp**
**Purpose:** Show user when data was last refreshed.

**Implementation:**
```python
# In ingestion_manager.py

st.caption(f"Last updated: {st.session_state.get('last_refresh', 'Never')}")

if st.button("Refresh Now") or auto_refresh:
    # Fetch data
    response = httpx.get(...)
    
    # Store timestamp
    st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
    
    # Check if data is stale
    if 'last_update' in job:
        job_last_update = datetime.fromisoformat(job['last_update'])
        age = datetime.now() - job_last_update
        
        if age > timedelta(seconds=60):
            st.warning(f"⚠️ Data may be stale (last updated {age.seconds}s ago)")
```

**Testing:**
- Verify timestamp updates on refresh
- Verify warning shown for stale data

---

### **5.2 Connection Error Handling**
**Purpose:** Handle API failures gracefully.

**Implementation:**
```python
try:
    response = httpx.get(
        f"{API_BASE_URL}/admin/ingest/status",
        timeout=10.0
    )
    response.raise_for_status()
    data = response.json()
    
    # Clear error state
    if 'api_error' in st.session_state:
        del st.session_state.api_error
        st.success("✅ Connection restored!")
    
except httpx.TimeoutException:
    st.error("⏱️ API request timed out. Retrying...")
    st.session_state.api_error = "timeout"
    
except httpx.ConnectError:
    st.error("🔌 Cannot connect to API. Is the service running?")
    st.session_state.api_error = "connection"
    st.code("docker ps --filter name=ecosystem-mcp-service")
    
except httpx.HTTPStatusError as e:
    st.error(f"❌ API error: HTTP {e.response.status_code}")
    st.session_state.api_error = f"http_{e.response.status_code}"
```

**Testing:**
- Stop API service
- Verify error message shown
- Start API service
- Verify success message shown

---

## 📋 Implementation Priority

### **Phase 1: Critical (This Week)**
1. ✅ Fail job endpoint
2. ✅ Orphaned job detection on startup
3. ✅ Automatic job timeout
4. ✅ Deployment process documentation

### **Phase 2: High Priority (Next Week)**
5. ✅ Worker heartbeat monitoring
6. ✅ JSONB update validation
7. ✅ Database update retry mechanism
8. ✅ UI last updated timestamp

### **Phase 3: Medium Priority (Next 2 Weeks)**
9. ✅ Graceful shutdown handling
10. ✅ Job recovery from checkpoint
11. ✅ Redis persistence verification
12. ✅ Update failure monitoring

### **Phase 4: Nice to Have (Next Month)**
13. ✅ Code version tracking
14. ✅ Connection error handling
15. ✅ Automated testing for all protections

---

## 🧪 Testing Strategy

### **Unit Tests**
- JSONB flag_modified validation
- TrackedJSONB wrapper class
- Retry mechanism with mocks
- Checkpoint save/load logic

### **Integration Tests**
- Fail endpoint + worker stops
- Orphaned job detection + cleanup
- Job timeout + failure
- Redis persistence + restart

### **E2E Tests**
- Full ingestion with checkpoint resume
- Container restart + job recovery
- UI shows stale data warning
- Deployment script end-to-end

### **Chaos Engineering**
- Kill worker mid-processing
- Stop Redis during job
- Stop PostgreSQL during update
- Network partition simulation

---

## 📊 Success Metrics

### **Reliability**
- Zero orphaned jobs (currently: manual cleanup)
- Zero stuck jobs > 24 hours (currently: possible)
- 99.9% database update success (currently: fails silently)

### **Recovery**
- < 60s to detect orphaned jobs (currently: never)
- < 10s to recover from checkpoint (currently: restart from beginning)
- < 5s to fail job manually (currently: no endpoint)

### **Developer Experience**
- 100% deployments use correct process (currently: manual)
- 0% `docker cp` mistakes (currently: happened multiple times)
- 100% code version tracked (currently: 0%)

---

## ✅ **SUMMARY**

We've solved critical issues but need comprehensive protections:

**Solved:**
1. ✅ Phantom job detection (every 10 files)
2. ✅ JSONB update fix (flag_modified)
3. ✅ Container rebuild process

**Need Protection:**
1. ❌ Manual job cancellation (no fail endpoint)
2. ❌ Orphaned job cleanup (no startup detection)
3. ❌ Stuck job prevention (no timeout)
4. ❌ Update failure monitoring (silent failures)
5. ❌ Deployment mistakes (easy to forget)
6. ❌ Recovery from crashes (no checkpoints)
7. ❌ UI stale data warning (no timestamp)

**Next Steps:**
1. Implement fail endpoint (Priority 1)
2. Add orphaned job detection (Priority 1)
3. Add job timeout (Priority 1)
4. Document deployment (Priority 1)
5. Continue through phases 2-4

**This comprehensive protection system will make the ingestion pipeline production-ready and resilient!** 🚀

