**Date:** October 25, 2025  
**Status:** 🚨 Service Unhealthy After Redeployment  
**Issue:** Container starts but fails health check  

---

# Service Unhealthy: Investigation Report

## 🚨 **Critical Issue**

After full redeployment (`down` → `build --no-cache` → `up`), the service is marked as **unhealthy**:

```
Container ecosystem-mcp-service  Starting
Container ecosystem-mcp-service  Started
Container ecosystem-mcp-service  Waiting
Container ecosystem-mcp-service  Error
dependency failed to start: container ecosystem-mcp-service is unhealthy
```

---

## 🔍 **What This Means**

### **Health Check Failed**
- Container started successfully
- Application may or may not be running
- Health check endpoint returns failure
- Docker marks container as unhealthy
- Other services waiting on it can't start

### **Common Causes:**
1. Application crashes immediately
2. Health check endpoint not responding
3. Health check URL wrong
4. Health check timeout too short
5. Application takes too long to initialize
6. Python import error or syntax error

---

## 📊 **Investigation Steps**

### **1. Check Service Logs**
Look for:
- Python tracebacks
- Import errors
- Syntax errors
- Database connection failures
- Redis connection failures

### **2. Check Health Check Configuration**
From `docker-compose.yml`:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### **3. Check Container Status**
```bash
docker ps -a | grep ecosystem-mcp-service
```
Look for:
- Status: Up vs Exited
- Health: healthy vs unhealthy vs starting

### **4. Manual Health Check**
```bash
curl http://localhost:8000/health
```
Does the endpoint respond?

---

## 🎯 **Potential Issues**

### **Issue 1: Import Error from Code Changes**
**Symptom:** Python can't import modules
**Cause:** New code has syntax error or missing import
**Check:** Look for `ImportError` or `ModuleNotFoundError` in logs

### **Issue 2: Worker Initialization Failure**
**Symptom:** Application starts but worker crashes
**Cause:** Worker initialization code has error
**Check:** Look for worker-related errors in logs

### **Issue 3: Database/Redis Not Ready**
**Symptom:** Application can't connect to dependencies
**Cause:** Health check runs before dependencies are ready
**Check:** Verify postgres and redis are healthy

### **Issue 4: Threading/Lock Issue**
**Symptom:** Application hangs during initialization
**Cause:** Our `threading.Lock()` code has issues
**Check:** Look for hangs in worker initialization

---

## 🔧 **Diagnostic Commands**

### **Check Logs:**
```bash
docker logs ecosystem-mcp-service 2>&1 | tail -100
```

### **Check Health:**
```bash
docker inspect ecosystem-mcp-service | grep -A10 Health
```

### **Check Process:**
```bash
docker exec ecosystem-mcp-service ps aux
```

### **Manual Health Check:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/workers/ingestion/status
```

---

## 🚨 **Critical Findings**

[Will be filled in based on investigation results]

### **Service Logs:**
[Log output here]

### **Health Check Status:**
[Health check output here]

### **Error Messages:**
[Any errors found]

---

## 🔄 **Recovery Options**

### **Option 1: Revert Code**
If the issue is from our changes:
1. Revert to last known good version
2. Rebuild without changes
3. Redeploy clean version
4. Incrementally add changes

### **Option 2: Fix Health Check**
If health check is too aggressive:
1. Increase timeout
2. Increase start_period
3. Simplify health check test

### **Option 3: Fix Code Issue**
If specific code has error:
1. Identify error from logs
2. Fix the specific issue
3. Rebuild with fix
4. Redeploy

### **Option 4: Debug Mode**
If we need more info:
1. Add extensive print statements
2. Disable worker auto-start
3. Start services manually
4. Debug step by step

---

## 📝 **Action Plan**

### **Immediate:**
1. Check service logs for errors
2. Identify root cause
3. Fix or revert as needed
4. Redeploy

### **If Import Error:**
- Fix syntax/import issue
- Rebuild
- Redeploy

### **If Worker Issue:**
- Comment out worker auto-start
- Let service start without worker
- Debug worker separately

### **If Health Check Issue:**
- Adjust health check params
- Or fix health endpoint

---

**Status:** 🔍 Investigation In Progress

