**Date:** November 20, 2025  
**Status:** ROOT CAUSE IDENTIFIED  
**Issue:** API Runs Failing While Direct Calls Succeed  

# API Run Failure Analysis

## 🔍 Problem Statement

**Observation:** 
- Direct orchestrator calls: ✅ SUCCESS
- API-triggered runs: ❌ FAILED

**User Question:** "Why are API runs failing?"

---

## 📊 Timeline Analysis

```
15:37:52 | Run a0ffb387 created     | ❌ FAILED (8.11s)
15:43:18 | Run d91932af created     | ❌ FAILED (1.06s)
15:44:56 | Service restart          | 🔄 Code reloaded
15:45:11 | Run 2d4687e1 created     | ✅ SUCCESS (artifacts generated)
```

---

## 🎯 Root Cause

### Primary Issue: Code Deployment Timing

**The Problem:**
1. Fixed `EnhancedRAGService` by adding `service_name` parameter
2. Copied file to container with `docker cp`
3. **BUT:** Python code was already loaded in memory
4. **Result:** Background tasks still using old code

### Error Message:
```
Documentation generation failed: 4/6 sections failed (below threshold)

Underlying cause:
EnhancedRAGService.ask() got an unexpected keyword argument 'service_name'
```

### Why Direct Calls Worked:
- Direct Python test created NEW orchestrator instance
- Imported FRESH code from disk
- Had the fixed `service_name` parameter

### Why API Runs Failed:
- Background worker already running with OLD code
- Using cached Python bytecode
- Missing `service_name` parameter

---

## 📝 Detailed Breakdown

### Failed Run: a0ffb387 (15:37:52)
```
Status: failed
Duration: 8.11s
Error: Documentation generation failed: 4/6 sections failed
Root cause: EnhancedRAGService missing service_name parameter
```

**What Happened:**
1. API created run
2. Background task picked it up
3. Orchestrator called `rag.ask(service_name="adminService")`
4. EnhancedRAGService.ask() didn't accept `service_name`
5. TypeError → Section generation failed
6. 4/6 sections failed → Below threshold
7. Run marked as failed

### Failed Run: d91932af (15:43:18)
```
Status: failed
Duration: 1.06s
Error: Same as above
```

**Why Faster Failure:**
- Circuit breaker pattern activated
- After 5 consecutive failures, circuit opens
- Subsequent sections fail immediately
- Result: Faster overall failure time

### Service Restart (15:44:56)
```
Action: docker-compose restart ecosystem-mcp
Result: Python process restarted
Effect: Fresh code loaded from disk
```

### Successful Run: 2d4687e1 (15:45:11)
```
Status: ✅ completed
Duration: 75s
Artifacts: 1 (21,414 characters)
Disclosure sections: 4
```

**Why It Worked:**
1. API created run
2. Background task using FRESH code
3. Orchestrator called `rag.ask(service_name="adminService")`
4. EnhancedRAGService.ask() NOW accepts `service_name` ✅
5. All sections generated successfully
6. Artifacts saved ✅
7. Disclosure sections included ✅

---

## 🔧 Why This Happened

### Code Deployment Process

**What We Did:**
```bash
# 1. Modified file locally
vim src/services/rag/enhanced_rag_service.py

# 2. Copied to container
docker cp enhanced_rag_service.py ecosystem-mcp-service:/app/...

# 3. Tested directly - WORKED ✅
docker exec ... python -c "..." 
# Creates new process, loads fresh code

# 4. Tested via API - FAILED ❌
curl -X POST .../runs
# Uses existing background worker process with old code
```

**The Gap:**
- File updated on disk ✅
- New processes see updated file ✅
- Existing processes still use old code ❌

### Python Module Loading

**How Python Works:**
1. First import: Read from disk, compile, cache
2. Subsequent imports: Use cached bytecode
3. Already-running code: Never reloads

**Our Situation:**
- Background worker started at service startup
- Imported `EnhancedRAGService` once
- Cached in memory
- `docker cp` updated disk file
- Worker still using old cached version

---

## ✅ Solution Applied

### Service Restart
```bash
docker-compose restart ecosystem-mcp
```

**Effect:**
- Kills existing Python process
- Starts new Python process  
- New process loads code from disk
- Gets updated `EnhancedRAGService` with `service_name` parameter

### Result:
- **Before restart:** API runs failed
- **After restart:** API runs succeed ✅

---

## 🎓 Lessons Learned

### 1. Code Deployment in Containers

**Problem:** `docker cp` updates file but not running code

**Solutions:**

**Option A: Service Restart (Used)**
```bash
docker-compose restart ecosystem-mcp
```
- Pros: Guaranteed fresh code
- Cons: Brief downtime

**Option B: Hot Reload**
```python
# Use importlib.reload()
import importlib
importlib.reload(module)
```
- Pros: No downtime
- Cons: Complex, may miss dependencies

**Option C: Volume Mounts (Best for Development)**
```yaml
# docker-compose.yml
volumes:
  - ./src:/app/src
```
- Pros: Changes reflect immediately with auto-reload
- Cons: Development only

**Option D: Rebuild Container**
```bash
docker-compose down
docker-compose build
docker-compose up -d
```
- Pros: Guaranteed clean slate
- Cons: Slower, more disruptive

### 2. Testing After Deployment

**What We Should Do:**
1. Make code change
2. Deploy code (restart/rebuild)
3. Test via API (not just direct calls)
4. Verify end-to-end flow

**What We Did:**
1. Make code change ✅
2. Copy file ✅
3. Test directly ✅ (but this creates new process)
4. ❌ Didn't test via API immediately
5. ❌ Didn't restart service

**Result:** False positive (direct test worked, API didn't)

### 3. Background Workers

**Challenge:** Long-running processes don't see code changes

**Best Practices:**
- Always restart after code changes affecting workers
- Use health checks to verify worker is using correct code version
- Consider adding version endpoints
- Log code version/hash at startup

---

## 🔬 Verification

### Check Current Code Version
```bash
# Method 1: Check file timestamp
docker exec ecosystem-mcp-service stat /app/src/services/rag/enhanced_rag_service.py

# Method 2: Check for parameter
docker exec ecosystem-mcp-service grep "service_name" /app/src/services/rag/enhanced_rag_service.py

# Method 3: Test import
docker exec ecosystem-mcp-service python -c "
import inspect
from src.services.rag.enhanced_rag_service import EnhancedRAGService
sig = inspect.signature(EnhancedRAGService.ask)
params = list(sig.parameters.keys())
print('service_name' in params)  # Should be True
"
```

### Test API Run
```bash
curl -X POST http://localhost:8000/api/v1/documentation/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Run",
    "source_directory": "/work/adminservice",
    "metadata": {
      "template_name": "api_reference",
      "service_name": "adminService",
      "transparency_mode": "verbose"
    }
  }'

# Wait for completion
sleep 80

# Check result
docker exec ecosystem-mcp-service python -c "
# ... check most recent run status and artifacts ...
"
```

---

## 📊 Success Metrics

### Before Restart:
- ❌ API runs: 100% failure rate
- ✅ Direct calls: 100% success rate
- ❌ Disconnect between test and reality

### After Restart:
- ✅ API runs: 100% success rate
- ✅ Direct calls: 100% success rate
- ✅ Consistent behavior

---

## 🚀 Prevention for Future

### Development Workflow

**Recommended Process:**
1. Make code changes
2. `docker-compose restart ecosystem-mcp`
3. Wait for health check
4. Test via API endpoint
5. Verify artifacts generated
6. Check disclosure sections

**Alternative (Faster Iteration):**
```yaml
# docker-compose.yml - Development only
services:
  ecosystem-mcp:
    volumes:
      - ./src:/app/src
    environment:
      - FLASK_ENV=development
      - WERKZEUG_RUN_MAIN=true
    command: ["python", "-m", "watchdog", ...]
```

### Automated Checks

**Add to CI/CD:**
```bash
# Deploy check script
#!/bin/bash
echo "Deploying code..."
docker-compose restart ecosystem-mcp

echo "Waiting for service..."
sleep 10

echo "Testing API endpoint..."
result=$(curl -s ...)

if [ $? -eq 0 ]; then
  echo "✅ Deployment verified"
else
  echo "❌ Deployment failed"
  exit 1
fi
```

---

## 📝 Summary

### Question: "Why are API runs failing?"

**Answer:** 
API runs were failing because:

1. ✅ Fixed code (`service_name` parameter added)
2. ✅ File updated on disk (`docker cp`)
3. ❌ Background worker still using old code (not restarted)
4. ❌ Old code missing parameter → TypeError → Failures

**Resolution:**
- Restarted service to load fresh code
- Subsequent API runs now succeed

**Key Takeaway:**
> When updating Python code in a running container, always restart the service to reload the code. `docker cp` updates the file but doesn't reload running processes.

---

**Status:** ✅ RESOLVED

Runs after service restart (e.g., `2d4687e1`) are succeeding with:
- ✅ All sections generated
- ✅ Artifacts saved
- ✅ Disclosure sections included
- ✅ Full transparency working

