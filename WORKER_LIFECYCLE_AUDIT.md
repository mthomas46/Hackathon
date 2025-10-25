**Date:** October 25, 2025  
**Status:** 🔍 Critical Audit - Worker Lifecycle Analysis  
**Focus:** Task Management & Singleton Pattern  

---

# Worker Lifecycle Audit: Critical Findings

## 🔍 **Issue Identified**

### **Multiple Worker Instances Created**

**Evidence from Logs:**
```
IngestionWorker initialized (ID: 7199c98f)
IngestionWorker initialized (ID: ac9dfb1c)
IngestionWorker initialized (ID: a84efdc6)
IngestionWorker initialized (ID: 211aeec4)
```

**This indicates the singleton pattern is BROKEN!**

---

## 🚨 **Critical Flaws Found**

### **FLAW #1: Singleton Not Persisting**

**Current Code:**
```python
_worker_instance: Optional[IngestionWorker] = None

def get_ingestion_worker() -> IngestionWorker:
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = IngestionWorker()
    return _worker_instance
```

**Problem:**
- FastAPI creates multiple instances during startup
- Each API request might get different instance
- Status API checks one instance, but another is running

**Impact:**
- Worker status shows False (checking wrong instance)
- Multiple workers might process same job
- Race conditions possible

---

### **FLAW #2: Task Not Awaited**

**Current Code:**
```python
self._task = asyncio.create_task(self._worker_loop())
logger.info(f"✅ Task created: {self._task}")
# ❌ Task is created but never awaited!
# Function returns immediately
```

**Problem:**
- Task is created but not kept alive
- FastAPI lifespan might not hold task reference
- Task could be garbage collected

**Impact:**
- Worker loop might not run
- Or runs briefly then stops
- No persistent execution

---

### **FLAW #3: Worker Loop Hangs**

**From logs:**
```
Task pending at line 147: wait_for=<Future pending>
Task pending at line 211: wait_for=<Future pending>
Task pending at line 245: wait_for=<Future pending>
```

**Problem:**
- Worker loop is waiting on Redis stream
- If no messages, blocks indefinitely
- No heartbeat or timeout
- No logging inside loop

**Impact:**
- Worker appears "running" but not processing
- Silent hang with no feedback
- Impossible to debug

---

### **FLAW #4: No Fail-Fast Markers**

**Missing:**
- No timeout on Redis polling
- No exception handling in loop
- No health check heartbeat
- No "still alive" logging
- No max retry limits

**Impact:**
- Worker can hang forever
- No visibility into failures
- Debug requires guesswork

---

## 🔧 **Required Fixes**

### **Fix #1: Strengthen Singleton Pattern**

```python
import threading

_worker_instance: Optional[IngestionWorker] = None
_worker_lock = threading.Lock()

def get_ingestion_worker() -> IngestionWorker:
    global _worker_instance
    
    with _worker_lock:
        if _worker_instance is None:
            logger.info("🏗️  Creating NEW worker instance")
            _worker_instance = IngestionWorker()
        else:
            logger.info(f"♻️  Reusing EXISTING worker instance (ID: {_worker_instance.worker_id})")
        
        return _worker_instance
```

---

### **Fix #2: Ensure Task Persistence**

```python
async def start(self):
    # ... existing code ...
    
    self.running = True
    self._task = asyncio.create_task(self._worker_loop())
    
    # ✅ CRITICAL: Ensure task is not garbage collected
    asyncio.ensure_future(self._task)
    
    # ✅ Add task done callback for debugging
    self._task.add_done_callback(self._on_task_done)
    
    logger.info("✅ Task created and persisted")

def _on_task_done(self, task):
    if task.cancelled():
        logger.warning("⚠️  Worker task was CANCELLED!")
    elif task.exception():
        logger.error(f"❌ Worker task FAILED: {task.exception()}")
    else:
        logger.info("✅ Worker task completed normally")
```

---

### **Fix #3: Add Heartbeat & Timeouts**

```python
async def _worker_loop(self):
    logger.info("🔄 [WORKER-LOOP] STARTING")
    iteration = 0
    last_heartbeat = time.time()
    
    while self.running:
        iteration += 1
        logger.info(f"💓 [WORKER-LOOP] Iteration {iteration} - Still alive!")
        
        try:
            # ✅ FAIL-FAST: Timeout on Redis polling
            messages = await asyncio.wait_for(
                redis.client.xreadgroup(...),
                timeout=10.0  # Fail fast if no response
            )
            
            if not messages:
                logger.debug(f"[WORKER-LOOP] No messages (iteration {iteration})")
                await asyncio.sleep(1)
                continue
            
            logger.info(f"📨 [WORKER-LOOP] Received {len(messages)} messages")
            
            # Process messages...
            
        except asyncio.TimeoutError:
            logger.debug(f"[WORKER-LOOP] Redis poll timeout (iteration {iteration})")
            # ✅ Heartbeat every timeout
            current_time = time.time()
            if current_time - last_heartbeat > 30:
                logger.info(f"💓 [WORKER-LOOP] Heartbeat: Still running (iteration {iteration})")
                last_heartbeat = current_time
        
        except Exception as e:
            logger.error(f"❌ [WORKER-LOOP] Error in iteration {iteration}: {e}", exc_info=True)
            await asyncio.sleep(5)  # Back off on error
    
    logger.warning("🛑 [WORKER-LOOP] STOPPED - running=False")
```

---

### **Fix #4: Enhanced Status Reporting**

```python
def get_status(self) -> Dict[str, Any]:
    """Get detailed worker status."""
    return {
        "running": self.running,
        "worker_id": self.worker_id,
        "current_job_id": str(self.current_job_id) if self.current_job_id else None,
        "task_status": {
            "exists": self._task is not None,
            "done": self._task.done() if self._task else None,
            "cancelled": self._task.cancelled() if self._task else None,
            "exception": str(self._task.exception()) if self._task and self._task.done() and not self._task.cancelled() else None
        },
        "stats": self.job_processor.stats if hasattr(self.job_processor, 'stats') else {},
        "uptime_seconds": time.time() - self._start_time if hasattr(self, '_start_time') else 0
    }
```

---

## 🎯 **Implementation Plan**

### **Phase 1: Diagnostic Logging** (5 min)
1. Add loop iteration logging
2. Add heartbeat every 30s
3. Log task status changes
4. Log singleton reuse

### **Phase 2: Fail-Fast Markers** (10 min)
1. Add timeout to Redis polling
2. Add exception handling in loop
3. Add task done callback
4. Add max retry limit

### **Phase 3: Singleton Fix** (10 min)
1. Add thread lock
2. Log instance creation/reuse
3. Verify single instance in logs

### **Phase 4: Task Persistence** (10 min)
1. Ensure future reference
2. Add done callback
3. Monitor task lifecycle

---

## 📊 **Expected Outcomes**

### **Before Fixes:**
```
Logs: "✅ Ingestion worker started"
Status API: Running = False
Task: Pending, no activity
Visibility: None
```

### **After Fixes:**
```
Logs: 
  "♻️  Reusing EXISTING worker instance (ID: abc123)"
  "💓 [WORKER-LOOP] Iteration 1 - Still alive!"
  "📨 [WORKER-LOOP] Received 1 messages"
  "💓 [WORKER-LOOP] Heartbeat: Still running (iteration 50)"

Status API: Running = True
Task: Active, processing
Visibility: Complete
```

---

## 🔍 **Root Cause Hypothesis**

**Primary Issue:** Singleton pattern broken
- Multiple instances created
- Status API checks wrong instance
- Worker IS running, but we're checking the wrong one!

**Secondary Issue:** No visibility
- Loop has no logging
- No heartbeat
- No fail-fast
- Silent execution

**Solution:** Fix singleton + add extensive logging = instant diagnosis

---

**End of Audit**

**Severity:** CRITICAL  
**Impact:** Blocks all validation  
**Effort:** 35 minutes  
**Priority:** IMMEDIATE

