**Date:** October 29, 2025  
**Status:** Frontend-Backend Mismatches - DETAILED FIX PLAN  
**Severity:** CRITICAL - 6 endpoints broken  

# Frontend-Backend Mismatch - Detailed Fix Report

## 📊 Executive Summary

**Total Endpoints Tested**: 17  
**Working**: 11 ✅ (64.7%)  
**Broken**: 6 ❌ (35.3%)  

**Root Causes Identified**:
1. ❌ Path prefix mismatches (Temporal RAG)
2. ❌ Missing router registration (Context-Aware RAG)
3. ⚠️ Field name mismatches (Multi-Pass RAG)
4. ❌ Missing endpoint (Admin Metrics)
5. ⏱️ Timeout on empty database (Enhanced RAG)

---

## 🔴 ISSUE #1: Temporal RAG - Path Prefix Mismatch

### Problem

**Frontend Expects**:
\`\`\`
POST /api/v1/temporal/query/date-range
POST /api/v1/temporal/query/point-in-time
POST /api/v1/temporal/query/evolution
\`\`\`

**Backend Has** (from app.py line 435):
\`\`\`python
app.include_router(temporal_rag.router, prefix="/api/v1/rag", tags=["Temporal RAG"])
\`\`\`

**Actual Endpoints** (from temporal_rag.py):
\`\`\`
POST /api/v1/rag/temporal/query
POST /api/v1/rag/temporal/evolution
POST /api/v1/rag/temporal/comparison
POST /api/v1/rag/temporal/query-period
POST /api/v1/rag/temporal/timeline
\`\`\`

### Fix Options

**Option A: Update Frontend** (RECOMMENDED) ✅
- Change all frontend calls from `/api/v1/temporal/query/*` to `/api/v1/rag/temporal/*`
- Pros: Backend is correct, follows RESTful conventions
- Cons: Must update multiple frontend files

**Option B: Change Backend Prefix**
- Change line 435 in app.py: `prefix="/api/v1/temporal"`
- Pros: Frontend doesn't need changes
- Cons: Breaks RESTful conventions (RAG endpoints should be under /rag)

**Option C: Add Alias Routes** (BACKWARD COMPATIBILITY)
- Keep current routes
- Add alias routes for frontend
- Pros: Both work, no breaking changes
- Cons: Maintenance overhead

### Recommended Fix

\`\`\`python
# File: services/ecosystem-mcp-dashboard/dashboard_views/temporal_rag_query.py

# Change this:
response = requests.post(
    f"{api_base_url}/api/v1/temporal/query/date-range",
    json=payload
)

# To this:
response = requests.post(
    f"{api_base_url}/api/v1/rag/temporal/query",
    json=payload
)
\`\`\`

---

## 🔴 ISSUE #2: Context-Aware RAG - Router Not Registered

### Problem

**Frontend Expects**:
\`\`\`
POST /api/v1/query/context-aware
\`\`\`

**Backend Has**: Router exists in `context_aware_query.py`:
\`\`\`python
@router.post("/query/context-aware")
async def query_with_context(...):
    ...
\`\`\`

**But**: Router is NOT registered in app.py! ❌

### Fix

\`\`\`python
# File: services/ecosystem-mcp/src/api/app.py

# Add import at top:
from .routes import context_aware_query

# Add router registration around line 440:
app.include_router(
    context_aware_query.router,
    prefix="/api/v1",
    tags=["Context-Aware RAG"]
)
\`\`\`

**Impact**: HIGH - Entire Context-Aware RAG feature is broken

---

## 🔴 ISSUE #3: Multi-Pass RAG - Field Name Mismatch

### Problem

**Frontend Sends**:
\`\`\`json
{
  "question": "test",
  "num_sections": 2
}
\`\`\`

**Backend Expects**:
\`\`\`json
{
  "query": "test",   // ← Different field name!
  "num_sections": 2
}
\`\`\`

**Error**: 422 Validation Error - Field 'query' required

### Fix Options

**Option A: Update Frontend** ✅
\`\`\`javascript
// Change "question" to "query"
const payload = {
  query: question,  // Was: question: question
  num_sections: numSections
};
\`\`\`

**Option B: Update Backend Schema**
\`\`\`python
class MultiPassQueryRequest(BaseModel):
    question: str = Field(alias="query")  # Accept both
    # OR
    query: str  # Keep current field name
\`\`\`

**Recommended**: Option A (update frontend for consistency)

---

## 🔴 ISSUE #4: Admin Metrics Endpoint Missing

### Problem

**Frontend Expects**:
\`\`\`
GET /api/v1/admin/metrics
\`\`\`

**Backend Reality**: Endpoint does not exist (404)

**Available**: `GET /api/v1/admin/stats` ✅

### Fix Options

**Option A: Update Frontend** (QUICK FIX) ✅
\`\`\`python
# Change:
response = requests.get(f"{api_base_url}/api/v1/admin/metrics")
# To:
response = requests.get(f"{api_base_url}/api/v1/admin/stats")
\`\`\`

**Option B: Add `/metrics` Endpoint**
\`\`\`python
# File: services/ecosystem-mcp/src/api/routes/admin.py

@router.get("/metrics")
async def get_metrics():
    """Alias for /stats endpoint."""
    return await get_admin_stats()
\`\`\`

**Recommended**: Option A (simpler, stats already has all metrics)

---

## ⏱️ ISSUE #5: Enhanced RAG Timeout

### Problem

Request to `/api/v1/query/enhanced` times out after 10 seconds

**Likely Causes**:
1. No documents in database (empty ChromaDB)
2. Query processing too slow
3. No early return on empty DB

### Fix

\`\`\`python
# File: services/ecosystem-mcp/src/api/routes/query.py

@router.post("/query/enhanced")
async def enhanced_query(request: EnhancedQueryRequest):
    # Add early return for empty database
    doc_count = await get_document_count()
    if doc_count == 0:
        return {
            "success": False,
            "error": "No documents in database. Please ingest documents first.",
            "documents_found": 0,
            "answer": None
        }
    
    # Continue with normal processing...
\`\`\`

---

## 📋 Complete Fix Summary

| Issue | Severity | Fix Location | Effort | Priority |
|-------|----------|--------------|--------|----------|
| Temporal RAG paths | CRITICAL | Frontend | 30min | 1 |
| Context-Aware not registered | CRITICAL | Backend app.py | 5min | 2 |
| Multi-pass field name | HIGH | Frontend | 15min | 3 |
| Admin metrics missing | HIGH | Frontend | 5min | 4 |
| Enhanced RAG timeout | MEDIUM | Backend | 20min | 5 |

**Total Fix Time**: ~75 minutes

---

## 🛠️ Implementation Plan

### Phase 1: Critical Fixes (40min)

1. **Register Context-Aware Router** (5min)
   \`\`\`bash
   # Edit: services/ecosystem-mcp/src/api/app.py
   # Add import and router registration
   \`\`\`

2. **Update Temporal RAG Paths** (30min)
   \`\`\`bash
   # Find all frontend files calling temporal endpoints
   grep -r "/api/v1/temporal/query" services/ecosystem-mcp-dashboard/
   
   # Update each file:
   # /api/v1/temporal/query/date-range → /api/v1/rag/temporal/query
   # /api/v1/temporal/query/point-in-time → /api/v1/rag/temporal/query
   # /api/v1/temporal/query/evolution → /api/v1/rag/temporal/evolution
   \`\`\`

3. **Fix Admin Metrics** (5min)
   \`\`\`bash
   # Edit dashboard files
   # Change /admin/metrics → /admin/stats
   \`\`\`

### Phase 2: High Priority Fixes (15min)

4. **Fix Multi-Pass Field Name** (15min)
   \`\`\`bash
   # Edit: services/ecosystem-mcp-dashboard/dashboard_views/rag_multi_pass.py
   # Change "question" → "query" in payload
   \`\`\`

### Phase 3: Performance Fix (20min)

5. **Add Enhanced RAG Empty DB Check** (20min)
   \`\`\`bash
   # Edit: services/ecosystem-mcp/src/api/routes/query.py
   # Add early return if no documents
   \`\`\`

---

## ✅ Testing Checklist

After fixes, test:

- [ ] Temporal RAG date-range query works
- [ ] Temporal RAG point-in-time query works
- [ ] Temporal RAG evolution query works
- [ ] Context-Aware RAG query works
- [ ] Multi-Pass RAG query works
- [ ] Admin metrics/stats page loads
- [ ] Enhanced RAG returns error on empty DB (not timeout)

---

## 🎯 Expected Results After Fixes

**Current Success Rate**: 64.7% (11/17)  
**Expected After Fixes**: 100% (17/17) ✅

**Broken Features**:
- ❌ Temporal RAG → ✅ Working
- ❌ Context-Aware RAG → ✅ Working
- ❌ Multi-Pass RAG → ✅ Working
- ❌ Admin Metrics → ✅ Working
- ⏱️ Enhanced RAG → ✅ Working

---

## 🚀 Next Steps

1. **Implement Phase 1 fixes** (critical path mismatches)
2. **Rebuild services** (`docker-compose build`)
3. **Restart services** (`docker-compose up -d`)
4. **Re-run validation tests**
5. **Test UI manually**
6. **Document API contract** (prevent future mismatches)

---

**Estimated Total Time**: 75 minutes  
**Expected Result**: All endpoints working (100% success rate)  
**Risk**: LOW (all fixes are straightforward path/field updates)

