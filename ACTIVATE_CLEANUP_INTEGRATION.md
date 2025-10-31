**Date:** October 30, 2025  
**Status:** ✅ Integration Complete - Restart Required  

# Activate Automatic Cleanup Integration

## ⚡ Quick Activation (30 seconds)

The automatic cleanup service has been integrated into your application. To activate it, simply restart the service:

```bash
# Restart the service
docker restart ecosystem-mcp-service

# Wait 10 seconds for startup
sleep 10

# Verify it's working
curl http://localhost:8000/api/v1/maintenance/cleanup/status | jq
```

**Expected output:**
```json
{
  "status": "running",
  "stats": {
    "total_cleanups": 0,
    "last_cleanup_time": null,
    "jobs_deleted": 0,
    "redis_messages_removed": 0,
    "orphaned_jobs_detected": 0,
    ...
  },
  "message": "Cleanup service is operational"
}
```

---

## 📋 Step-by-Step Activation

### Step 1: Restart the Service

```bash
docker restart ecosystem-mcp-service
```

### Step 2: Watch the Startup

```bash
# Watch startup logs (press Ctrl+C when done)
docker logs ecosystem-mcp-service -f
```

**Look for these lines:**
```
✅ Ingestion worker started
✅ Retry worker started
✅ No orphaned jobs detected (or count if found)
✅ Automatic cleanup service started  <-- NEW!
✅ ALL SERVICES INITIALIZED SUCCESSFULLY
```

### Step 3: Verify Integration

```bash
# Run the verification script
./verify_cleanup_integration.sh
```

**Expected: All tests pass (6/6)**

### Step 4: Check Service Status

```bash
# Check status
curl http://localhost:8000/api/v1/maintenance/cleanup/status | jq

# Check health
curl http://localhost:8000/api/v1/maintenance/cleanup/health | jq
```

---

## 🎯 What Happens After Restart

### Immediate (Startup)

1. **Orphaned Job Detection Runs** ✅
   - Scans for stuck jobs from previous runs
   - Your 4 stuck jobs would be caught here
   - Results logged to console

2. **Cleanup Service Starts** ✅
   - Background task begins
   - Ready to clean on schedule

3. **API Endpoints Available** ✅
   - `/api/v1/maintenance/cleanup/*`
   - Visible in Swagger docs

### After 60 Minutes (First Cleanup)

1. **Automatic Cleanup Runs** ✅
   - Orphaned jobs detected
   - Old jobs cleaned
   - Redis messages removed
   - Statistics updated

### Every Hour (Ongoing)

1. **Scheduled Cleanup** ✅
   - Runs automatically
   - No manual intervention
   - Self-healing system

---

## 🔍 Verification Commands

### Quick Check

```bash
# Status
curl -s http://localhost:8000/api/v1/maintenance/cleanup/status | jq '.status'
# Should return: "running"

# Health
curl -s http://localhost:8000/api/v1/maintenance/cleanup/health | jq '.healthy'
# Should return: true
```

### Detailed Check

```bash
# Full status
curl http://localhost:8000/api/v1/maintenance/cleanup/status | jq

# Statistics
curl http://localhost:8000/api/v1/maintenance/cleanup/stats | jq

# Health with details
curl http://localhost:8000/api/v1/maintenance/cleanup/health | jq
```

### Trigger Test Cleanup

```bash
# Run cleanup now (doesn't wait for schedule)
curl -X POST http://localhost:8000/api/v1/maintenance/cleanup/run-now | jq

# Check what was cleaned
curl http://localhost:8000/api/v1/maintenance/cleanup/stats | jq '{
  total_cleanups,
  jobs_deleted,
  redis_messages_removed,
  orphaned_jobs_detected
}'
```

---

## 📊 Monitoring After Activation

### Check Startup Logs

```bash
# See the startup sequence
docker logs ecosystem-mcp-service | grep -A 20 "ECOSYSTEM MCP SERVICE STARTING"
```

### Watch Cleanup Activity

```bash
# Real-time cleanup logs
docker logs ecosystem-mcp-service -f | grep "🧹"

# Recent cleanup events
docker logs ecosystem-mcp-service | grep "cleanup" | tail -20
```

### Monitor Statistics

```bash
# Watch stats update
watch -n 60 'curl -s http://localhost:8000/api/v1/maintenance/cleanup/stats | jq'
```

---

## 🚨 Troubleshooting

### Service Doesn't Start

**Symptom:** No "✅ Automatic cleanup service started" in logs

**Check:**
```bash
# Look for errors
docker logs ecosystem-mcp-service | grep -i "cleanup" | grep -i "error"

# Check if files exist
docker exec ecosystem-mcp-service test -f src/services/maintenance/automatic_cleanup_service.py && echo "File exists" || echo "File missing"

docker exec ecosystem-mcp-service test -f src/api/routes/maintenance_cleanup.py && echo "File exists" || echo "File missing"
```

**Fix:**
```bash
# Force rebuild if using Docker Compose
docker-compose build ecosystem-mcp-service --no-cache
docker-compose up -d ecosystem-mcp-service
```

### API Endpoints Not Found

**Symptom:** HTTP 404 on cleanup endpoints

**Check:**
```bash
# Verify router is loaded
docker logs ecosystem-mcp-service | grep "maintenance_cleanup"

# Check OpenAPI spec
curl http://localhost:8000/openapi.json | jq '.paths | keys' | grep cleanup
```

**Fix:**
```bash
# Restart service
docker restart ecosystem-mcp-service

# If still not working, check app.py changes were saved
docker exec ecosystem-mcp-service grep -A 3 "Automatic cleanup service management" src/api/app.py
```

### Service Starts But Doesn't Clean

**Symptom:** Status shows "running" but no cleanups happening

**Check:**
```bash
# Check health
curl http://localhost:8000/api/v1/maintenance/cleanup/health | jq

# Look for errors in logs
docker logs ecosystem-mcp-service | grep "cleanup" | grep -i "error"
```

**Fix:**
```bash
# Try manual cleanup
curl -X POST http://localhost:8000/api/v1/maintenance/cleanup/run-now | jq

# Stop and restart service
curl -X POST http://localhost:8000/api/v1/maintenance/cleanup/stop
sleep 2
curl -X POST http://localhost:8000/api/v1/maintenance/cleanup/start
```

---

## ✅ Success Indicators

### You'll Know It's Working When:

1. **Startup Logs Show:**
   ```
   ✅ Automatic cleanup service started
   ```

2. **API Returns 200:**
   ```bash
   curl -w "%{http_code}\n" http://localhost:8000/api/v1/maintenance/cleanup/status -o /dev/null -s
   # Output: 200
   ```

3. **Status Shows Running:**
   ```bash
   curl -s http://localhost:8000/api/v1/maintenance/cleanup/status | jq '.status'
   # Output: "running"
   ```

4. **Health Check Passes:**
   ```bash
   curl -s http://localhost:8000/api/v1/maintenance/cleanup/health | jq '.healthy'
   # Output: true
   ```

5. **Swagger Docs Show Endpoints:**
   - Open: http://localhost:8000/docs
   - Look for "Automatic Cleanup" section
   - Should show 6 endpoints

---

## 🎉 What You Get After Activation

### Immediate Benefits

✅ **Orphaned Job Detection** - Runs on every startup  
✅ **Self-Healing** - Stuck jobs automatically recovered  
✅ **API Control** - Start/stop/monitor via REST API  
✅ **Monitoring** - Stats and health checks available  

### Ongoing Benefits

✅ **Automatic Cleanup** - Every hour, zero maintenance  
✅ **Database Optimization** - Old jobs removed weekly  
✅ **Redis Health** - Orphaned messages cleaned  
✅ **Cost Savings** - Reduced storage and query time  

---

## 📝 Quick Reference

### Essential Commands

```bash
# Activate (restart service)
docker restart ecosystem-mcp-service

# Verify
./verify_cleanup_integration.sh

# Check status
curl http://localhost:8000/api/v1/maintenance/cleanup/status | jq

# Trigger cleanup
curl -X POST http://localhost:8000/api/v1/maintenance/cleanup/run-now | jq

# View logs
docker logs ecosystem-mcp-service -f | grep "🧹"

# Access docs
open http://localhost:8000/docs#/Automatic%20Cleanup
```

### API Endpoints

```
GET  /api/v1/maintenance/cleanup/status   - Get status
GET  /api/v1/maintenance/cleanup/health   - Health check
GET  /api/v1/maintenance/cleanup/stats    - Statistics
POST /api/v1/maintenance/cleanup/start    - Start service
POST /api/v1/maintenance/cleanup/stop     - Stop service
POST /api/v1/maintenance/cleanup/run-now  - Run cleanup now
```

---

## 🚀 Ready to Activate?

Run this single command:

```bash
docker restart ecosystem-mcp-service && sleep 10 && ./verify_cleanup_integration.sh
```

This will:
1. Restart the service (activates integration)
2. Wait 10 seconds for startup
3. Run verification tests

**Expected: 6/6 tests pass** ✅

---

**Status:** 🟡 Restart Required → 🟢 Activated  
**Time:** ~30 seconds  
**Difficulty:** ⭐ (One command)

