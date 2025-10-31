**Date:** October 28, 2025  
**Status:** Comprehensive End-to-End Testing  
**Scope:** Frontend → Backend → Frontend response consumption  

# Comprehensive E2E Testing Plan

## 🎯 Testing Strategy

**Approach:** Test all major code paths systematically
1. Backend API endpoints (new + existing)
2. Frontend API consumption
3. Response handling and display
4. Error scenarios

---

## Phase 1: Deploy Updated Services

### Step 1.1: Rebuild Backend
```bash
cd services/ecosystem-mcp
docker-compose -f ../docker-compose-mcp-ecosystem.yml build --no-cache ecosystem-mcp-service
docker-compose -f ../docker-compose-mcp-ecosystem.yml up -d ecosystem-mcp-service
```

### Step 1.2: Verify Service Health
```bash
curl http://localhost:8000/health
```

---

## Phase 2: Test New Backend Endpoints

### Test 2.1: Deep Health Check ✅
**Endpoint:** `GET /api/v1/infrastructure/health/deep`
**Expected:** Comprehensive health with latency metrics

**Test:**
```bash
curl -s http://localhost:8000/api/v1/infrastructure/health/deep | jq
```

**Validation:**
- ✅ Returns JSON with status
- ✅ Contains dependencies object
- ✅ Has latency_ms for each component
- ✅ Includes disk space info
- ✅ Summary statistics present

---

### Test 2.2: Bulk Delete Documents ✅
**Endpoint:** `POST /api/v1/documents/bulk-delete`
**Expected:** Deletes multiple documents in single transaction

**Test:**
```bash
# Test with empty list (should fail)
curl -X POST http://localhost:8000/api/v1/documents/bulk-delete \
  -H "Content-Type: application/json" \
  -d '{"document_ids": []}' | jq

# Test with valid UUIDs
curl -X POST http://localhost:8000/api/v1/documents/bulk-delete \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["123e4567-e89b-12d3-a456-426614174000"]}' | jq
```

**Validation:**
- ✅ Empty list returns HTTP 400
- ✅ Valid request returns success/failure
- ✅ Response has deleted count
- ✅ Transaction is atomic

---

### Test 2.3: Bulk Update Documents ✅
**Endpoint:** `POST /api/v1/documents/bulk-update`
**Expected:** Updates metadata for multiple documents

**Test:**
```bash
# Test with empty metadata (should fail)
curl -X POST http://localhost:8000/api/v1/documents/bulk-update \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["123e4567-e89b-12d3-a456-426614174000"], "metadata": {}}' | jq

# Test with valid metadata
curl -X POST http://localhost:8000/api/v1/documents/bulk-update \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["123e4567-e89b-12d3-a456-426614174000"], "metadata": {"test": true}}' | jq
```

**Validation:**
- ✅ Empty metadata returns HTTP 400
- ✅ Valid request returns success/failure
- ✅ Response has updated count
- ✅ Transaction is atomic

---

## Phase 3: Test Existing Major Backend Endpoints

### Test 3.1: Basic Health Check ✅
```bash
curl -s http://localhost:8000/health | jq
```

### Test 3.2: Documents List ✅
```bash
curl -s "http://localhost:8000/api/v1/documents?limit=10" | jq
```

### Test 3.3: RAG Query ✅
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this project about?", "n_results": 5}' | jq
```

### Test 3.4: Enhanced RAG Query ✅
```bash
curl -X POST http://localhost:8000/api/v1/query/enhanced \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this project about?", "mode": "rag", "response_length": 500}' | jq
```

### Test 3.5: Ingestion Job Status ✅
```bash
curl -s "http://localhost:8000/api/v1/admin/ingest" | jq
```

### Test 3.6: Worker Status ✅
```bash
curl -s "http://localhost:8000/api/v1/workers" | jq
```

### Test 3.7: Configuration Health ✅
```bash
curl -s "http://localhost:8000/api/v1/config/health" | jq
```

---

## Phase 4: Test Worker Optimizations

### Test 4.1: Worker Heartbeat ✅
**Verification:** Check Redis for heartbeat keys

```bash
# Connect to Redis
docker exec -it $(docker ps -q -f name=redis) redis-cli

# Check for heartbeat keys
KEYS worker_heartbeat:*

# Get heartbeat data
GET worker_heartbeat:<worker_id>
```

**Expected:**
- Keys exist for active workers
- Data contains: worker_id, last_heartbeat, jobs_processed, status
- Keys expire after 30 seconds if worker crashes

---

### Test 4.2: Pending Message Recovery ✅
**Verification:** Check Redis stream pending messages

```bash
# Check pending messages
docker exec -it $(docker ps -q -f name=redis) redis-cli XPENDING ingestion_jobs ingestion_workers
```

**Expected:**
- Stale messages (>5 min idle) are claimed and reprocessed
- Recovery runs every 5 minutes
- Logs show recovery activity

---

## Phase 5: Test Frontend API Consumption

### Test 5.1: Health Dashboard
**Navigate to:** Health page in dashboard
**Action:** Load health status

**Validation:**
- ✅ Basic health displays correctly
- ✅ Component status shown
- ⏳ Deep health (if UI updated)

---

### Test 5.2: Documents List
**Navigate to:** Documents explorer
**Action:** Load document list

**Validation:**
- ✅ Documents displayed in table
- ✅ Pagination works
- ✅ Filters work
- ⏳ Bulk selection (if UI updated)

---

### Test 5.3: RAG Query
**Navigate to:** RAG Query page
**Action:** Submit query

**Validation:**
- ✅ Query submits successfully
- ✅ Answer displayed
- ✅ Documents shown
- ✅ Metadata displayed
- ✅ Response length selector works

---

### Test 5.4: Ingestion Manager
**Navigate to:** Ingestion Manager
**Action:** View job list and start new job

**Validation:**
- ✅ Job list loads
- ✅ Job status updates
- ✅ Progress bars work
- ✅ Error messages clear

---

### Test 5.5: Worker Status
**Navigate to:** Workers page
**Action:** View worker list

**Validation:**
- ✅ Workers listed
- ✅ Status shown
- ⏳ Heartbeat data (if UI updated)

---

## Phase 6: Error Scenario Testing

### Test 6.1: Rate Limit (429)
**Test:** Make many rapid requests
**Expected:** User-friendly rate limit message with countdown

### Test 6.2: Validation Errors (400/422)
**Test:** Send invalid data
**Expected:** Clear validation error messages

### Test 6.3: Server Errors (500)
**Test:** Trigger server error
**Expected:** Graceful error handling, not crash

### Test 6.4: Connection Errors
**Test:** Stop backend service
**Expected:** "Cannot connect" message with retry guidance

---

## Success Criteria

### Backend Endpoints
- [ ] All new endpoints respond correctly
- [ ] All existing endpoints still work
- [ ] Error handling is comprehensive
- [ ] Response formats match expectations

### Worker Optimizations
- [ ] Heartbeats visible in Redis
- [ ] Pending recovery runs periodically
- [ ] No performance degradation

### Frontend Consumption
- [ ] All API calls succeed
- [ ] Responses properly parsed
- [ ] Data displayed correctly
- [ ] Errors handled gracefully

---

**Status:** Ready to execute testing
**Next:** Begin Phase 1 - Deploy Services

