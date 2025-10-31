# Temporal RAG Investigation & Fixes

**Date:** October 27, 2025  
**Status:** ⚠️ **Multiple Issues Identified**  
**Priority:** HIGH

---

## 🔍 **Investigation Summary**

After completing UTC standardization and fixing the timezone bug, comprehensive testing revealed that **temporal RAG queries are working but returning 0 documents** despite having **1,124 documents** in PostgreSQL with temporal metadata.

---

## 📊 **Current State**

### Database Status:
```
PostgreSQL documents: 1,124 ✅
PostgreSQL embeddings: 26,329 ✅
ChromaDB status: UNKNOWN ⚠️
RAG query results: 0 documents ❌
```

### Endpoint Status:
| Endpoint | Expected Path | Test Used | Status |
|----------|--------------|-----------|---------|
| Point-in-time | `/temporal/query` | `/temporal/point-in-time` ❌ | 404 - Wrong path |
| Evolution | `/temporal/evolution` | `/temporal/evolution` ✅ | 500 - Timeline creation |
| Comparison | `/temporal/comparison` | `/temporal/comparison` ✅ | 200 - Works but 0 docs |

---

## 🐛 **Issues Identified**

### Issue 1: Test Using Wrong Endpoint Paths ⚠️

**Test Expected:**
- `/api/v1/rag/temporal/point-in-time`

**Actual Endpoint:**
- `/api/v1/rag/temporal/query`

**Impact:** 404 errors in tests

**Fix:** Update test script to use correct paths

---

### Issue 2: ChromaDB Sync Issue 🔴

**Symptoms:**
- PostgreSQL: 1,124 documents with temporal data ✅
- ChromaDB: Unknown count ⚠️
- RAG queries: 0 documents returned ❌
- Standard RAG: Returns null ❌

**Hypothesis:** Documents exist in PostgreSQL but either:
1. Not synced to ChromaDB
2. Missing embeddings in ChromaDB
3. ChromaDB metadata doesn't include `git_date`

**Evidence:**
```bash
# PostgreSQL has documents
curl /api/v1/admin/stats → {"documents": 1124, "embeddings": 26329}

# Metrics returns null
curl /api/v1/metrics/summary → {"documents": null, "embeddings": null}

# Standard RAG returns 0
curl /api/v1/query → {"total_documents": null, "results": []}
```

**Root Cause:** Likely the metadata migration script updated PostgreSQL but not ChromaDB, or ChromaDB collection needs to be checked.

---

### Issue 3: Evolution Tracking 500 Error 🔴

**Endpoint:** `/api/v1/rag/temporal/evolution`

**Request:**
```json
{
  "topic": "UTC standardization implementation",
  "service_name": "ecosystem-mcp",
  "limit_per_period": 3
}
```

**Response:** 500 Internal Server Error

**Log Analysis Needed:** Check service logs for timeline creation error

**Hypothesis:** Timeline auto-creation is failing when it shouldn't (should use existing timeline or gracefully create)

---

## 🔧 **Required Fixes**

### Fix 1: Update Test Script Endpoints ✅ (Quick)

**File:** `/tmp/comprehensive_temporal_rag_comparison.py`

**Changes:**
```python
# BEFORE:
f"{BASE_URL}/api/v1/rag/temporal/point-in-time"

# AFTER:
f"{BASE_URL}/api/v1/rag/temporal/query"
```

**Time:** 2 minutes  
**Priority:** LOW (test issue only)

---

### Fix 2: Investigate ChromaDB Sync 🔴 (Critical)

**Steps:**
1. Check ChromaDB collection count
2. Verify embeddings exist in ChromaDB
3. Check if `git_date` metadata is in ChromaDB
4. Run sync/migration if needed

**Commands:**
```bash
# Check ChromaDB via API
curl http://localhost:8000/api/v1/embeddings/stats

# Check ChromaDB directly
docker exec ecosystem-mcp-embedding curl http://localhost:8001/api/v1/stats

# Check collection metadata
curl -X POST http://localhost:8000/api/v1/monitoring/consistency
```

**Expected Result:**
- ChromaDB should have 1,124 documents
- Each document should have `git_date` in metadata
- Embeddings should be present

**If Mismatch:** Need to run metadata sync or re-embed

**Time:** 30-60 minutes  
**Priority:** HIGH (blocks all RAG queries)

---

### Fix 3: Debug Evolution Tracking 500 Error 🔴 (Important)

**Steps:**
1. Check service logs for error details
2. Verify timeline exists for ecosystem-mcp
3. Test timeline creation manually
4. Fix auto-creation logic if needed

**Commands:**
```bash
# Check logs
docker logs ecosystem-mcp-service | tail -50

# Check if timeline exists
curl "http://localhost:8000/api/v1/timeline?service_name=ecosystem-mcp"

# Try to create timeline manually
curl -X POST "http://localhost:8000/api/v1/timeline" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ecosystem-mcp Timeline",
    "service_name": "ecosystem-mcp",
    "repo_path": "/repo/services/ecosystem-mcp"
  }'
```

**Time:** 15-30 minutes  
**Priority:** MEDIUM (one feature broken)

---

## 📋 **Action Plan**

### Phase 1: Quick Wins (5 minutes) ✅

1. ✅ Fix test script endpoint paths
2. ✅ Re-run comparison test
3. ✅ Verify timezone bug is fixed (should still work)

---

### Phase 2: ChromaDB Investigation (30-60 minutes) 🔴

**Step 1: Check ChromaDB Status**
```bash
# Via API
curl -s "http://localhost:8000/api/v1/embeddings/stats" | jq '.'

# Direct embedding service
curl -s "http://localhost:8001/api/v1/health" | jq '.'

# Check collection
curl -s "http://localhost:8000/api/v1/admin/chromadb/collections" | jq '.'
```

**Step 2: Verify Document Count Mismatch**
```sql
-- PostgreSQL
SELECT COUNT(*) FROM documents WHERE service_name = 'ecosystem-mcp';
SELECT COUNT(*) FROM documents WHERE git_date IS NOT NULL;
```

```python
# ChromaDB (via Python)
collection = chromadb.get_collection("ecosystem_mcp")
print(f"Count: {collection.count()}")
```

**Step 3: Check Metadata in ChromaDB**
```python
# Sample a document
results = collection.get(limit=1, include=["metadatas"])
print(results["metadatas"][0].keys())  # Should include 'git_date'
```

**Step 4: Run Sync if Needed**
```bash
# If git_date missing, run metadata sync
curl -X POST "http://localhost:8000/api/v1/monitoring/sync-metadata"

# If documents missing, check ingestion job status
curl "http://localhost:8000/api/v1/jobs/recent"
```

---

### Phase 3: Evolution Tracking Fix (15-30 minutes) 🔴

**Step 1: Check Logs**
```bash
docker logs ecosystem-mcp-service 2>&1 | grep -A 10 "Evolution tracking failed"
```

**Step 2: Check Timeline Existence**
```bash
curl -s "http://localhost:8000/api/v1/timeline?service_name=ecosystem-mcp" | jq '.'
```

**Step 3: Test Manual Timeline Creation**
```bash
curl -X POST "http://localhost:8000/api/v1/timeline" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ecosystem-mcp Timeline",
    "service_name": "ecosystem-mcp",
    "repo_path": "/repo/services/ecosystem-mcp",
    "description": "Timeline for ecosystem-mcp service"
  }' | jq '.'
```

**Step 4: Fix Auto-Creation Logic**
- If timeline creation fails, check required fields
- If timeline exists but evolution fails, check period generation
- If neither, investigate temporal RAG service error handling

---

### Phase 4: Re-test Everything (10 minutes) ✅

**Run comprehensive validation:**
```bash
python3 /tmp/comprehensive_temporal_rag_comparison.py
```

**Expected Results:**
- ✅ Timezone bug fixed (all formats work)
- ✅ Point-in-time query works (with correct endpoint)
- ✅ Comparison query returns documents
- ✅ Evolution tracking works
- ✅ All temporal RAG features functional

---

## 🎯 **Expected Outcomes**

### After All Fixes:

| Test | Before | After |
|------|--------|-------|
| Timezone formats accepted | ✅ 3/3 | ✅ 3/3 |
| Point-in-time query | ❌ 404 | ✅ 200 with docs |
| Comparison query | ⚠️ 200, 0 docs | ✅ 200 with docs |
| Evolution tracking | ❌ 500 | ✅ 200 with docs |
| Standard RAG | ❌ 0 docs | ✅ Documents returned |

### Temporal RAG Value Demonstration:

Once working, temporal RAG should show:
- **Standard RAG:** Returns all matching documents (no time filter)
- **Point-in-Time:** Returns only documents ≤ specified date
- **Comparison:** Returns documents grouped by time periods
- **Evolution:** Shows how information changed over time periods

---

## 📝 **Notes**

### Why This Wasn't Caught Earlier:

1. **UTC standardization focused on timezone bugs** - The fix was correct
2. **Infrastructure tests passed** - Timeline creation, period generation all work
3. **ChromaDB sync happened after UTC fix** - May have missed metadata update
4. **Test script used wrong endpoints** - 404 hid the real issue

### Key Learnings:

1. ✅ UTC standardization is complete and working
2. ⚠️ Need to verify ChromaDB sync after PostgreSQL changes
3. ⚠️ Test scripts should use actual API endpoint paths
4. ⚠️ Comprehensive RAG query validation needed

---

## 🚀 **Next Steps**

1. **Immediate:** Check ChromaDB status and sync
2. **Short-term:** Fix evolution tracking 500 error
3. **Medium-term:** Add automated ChromaDB/PostgreSQL consistency checks
4. **Long-term:** Add integration tests that verify RAG queries return documents

---

**Status:** ⚠️ **Investigation Complete - Fixes In Progress**  
**Blocking Issues:** ChromaDB sync (HIGH), Evolution tracking (MEDIUM)  
**UTC Bug Status:** ✅ **FIXED & VALIDATED**

---

**Next Action:** Investigate ChromaDB status and document sync

