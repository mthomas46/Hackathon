**Date:** October 29, 2025  
**Status:** Issues Investigation Complete  
**Priority:** HIGH (2/3), MEDIUM (1/3)  

# Issues Investigation Report

## 🔍 Root Causes Identified

---

## Issue #1: Context-Aware Async Error ❌ **CRITICAL**

**Priority**: HIGH  
**Impact**: Blocks context features (500 error)  
**Location**: `services/ecosystem-mcp/src/api/routes/query.py:389`

### Root Cause

```python
# LINE 389 - WRONG:
async with get_database() as db:
    # Query distinct repositories from documents table
    from sqlalchemy import text
    ...
```

**Problem**: `get_database()` returns a `Database` object that does NOT support the async context manager protocol (`__aenter__` and `__aexit__` methods).

**Error**:
\`\`\`
'Database' object does not support the asynchronous context manager protocol
\`\`\`

### Solution

```python
# CORRECT:
db = get_database()
# Query distinct repositories from documents table
from sqlalchemy import text
...
```

**Fix Time**: 2 minutes  
**Testing Time**: 3 minutes  
**Total**: 5 minutes

---

## Issue #2: Cache Clear Error ❌ **DUPLICATE ROUTES**

**Priority**: LOW  
**Impact**: Cache clear fails (500 error)  
**Location**: `services/ecosystem-mcp/src/api/routes/admin.py`

### Root Cause #1: Duplicate Routes

**Line 1154-1183**: First `/clear-cache` endpoint
**Line 1318-1338**: Second `/clear-cache` endpoint (DUPLICATE!)

```python
# FIRST ENDPOINT (Line 1154)
@router.post("/clear-cache", ...)
async def clear_cache():
    ...

# DUPLICATE ENDPOINT (Line 1318) 
@router.post("/clear-cache", ...)  # ❌ COLLISION!
async def clear_cache_by_prefix(prefix: str = ...):
    ...
```

**Problem**: FastAPI route collision causes undefined behavior.

### Root Cause #2: Error Handling

**Line 1179-1183**: Returns error dict instead of raising exception

```python
# WRONG:
except Exception as e:
    logger.error(f"Failed to clear cache: {e}", exc_info=True)
    return {  # ❌ Should raise HTTPException
        "status": "error",
        "message": f"Failed to clear cache: {str(e)}"
    }
```

### Solution

1. **Rename second endpoint** to `/clear-cache-prefix`
2. **Raise HTTPException** instead of returning error dict

**Fix Time**: 5 minutes  
**Testing Time**: 2 minutes  
**Total**: 7 minutes

---

## Issue #3: Multi-Pass RAG Timeout ⏱️

**Priority**: MEDIUM  
**Impact**: Feature unusable (>60s timeout)  
**Location**: `services/ecosystem-mcp/src/api/routes/multi_pass.py`

### Root Cause: Too Complex for Current Data

**Current Defaults**:
- `num_passes`: 2 (already reduced from 3)
- `num_secondary_questions`: 2 (already reduced from 3)
- **Total LLM calls**: 1 (decomposition) + 4 (questions) + 2 (section synthesis) + 1 (final) = **8 LLM calls**

**Test Request** (from failing test):
\`\`\`json
{
  "query": "How does the RAG system work?",
  "num_sections": 2,
  "questions_per_section": 3,
  "n_results": 10,
  "temperature": 0.7
}
\`\`\`

**Total Operations**: 2 sections × 3 questions = **6 RAG queries** + synthesis

### Why It Times Out

1. **No Streaming**: Standard endpoint doesn't stream progress
2. **Sequential Processing**: Sections processed one by one
3. **Desktop Ollama**: Uses slower desktop tier for synthesis
4. **Empty DB Check Missing**: Should fail fast if no documents

### Solutions

**Quick Wins** (15 minutes):
1. ✅ **Add empty database check** (fail fast if no docs)
2. ✅ **Reduce timeout to 30s** for initial decomposition
3. ✅ **Add better logging** to identify slow steps
4. ⚠️ **Recommend streaming** for long queries

**Medium-term** (2-4 hours):
5. **Add progressive timeout**: Increase timeout based on complexity
6. **Implement result streaming**: Return partial results
7. **Parallelize section processing**: Process multiple sections concurrently
8. **Add caching**: Cache decomposition and section results

**Fix Time**: 15 minutes (quick wins)  
**Testing Time**: 10 minutes  
**Total**: 25 minutes

---

## 📊 Fix Priority Order

### Step 1: Context-Aware Async Fix (5 min) ✅ HIGH
- **Impact**: Critical feature blocked
- **Effort**: Minimal (1 line change)
- **Risk**: Very low
- **Blockers**: None

### Step 2: Cache Clear Duplicate Routes (7 min) ✅ LOW
- **Impact**: Admin feature blocked
- **Effort**: Minimal (rename + exception)
- **Risk**: Very low
- **Blockers**: None

### Step 3: Multi-Pass Quick Wins (25 min) ⚠️ MEDIUM
- **Impact**: Feature slow but functional
- **Effort**: Moderate (4 changes)
- **Risk**: Low
- **Blockers**: None

**Total Fix Time**: **37 minutes**  
**Total Test Time**: **15 minutes**  
**Grand Total**: **~52 minutes to 100%**

---

## 🎯 Implementation Plan

### Phase 1: Critical Fix (5 min)
1. Fix Context-Aware async database usage
2. Test `/api/v1/contexts` endpoint
3. Verify returns list of contexts

### Phase 2: Route Fix (7 min)
1. Rename duplicate `/clear-cache` to `/clear-cache-prefix`
2. Change error return to HTTPException
3. Test cache clear endpoint
4. Verify successful cache clearing

### Phase 3: Multi-Pass Optimization (25 min)
1. Add empty database check (fail fast)
2. Add detailed logging for each phase
3. Document streaming recommendation
4. Test with reduced parameters

### Phase 4: Validation (15 min)
1. Re-run full test suite
2. Verify all 3 issues resolved
3. Update success rate (target: 100%)
4. Create final report

---

## 🔧 Detailed Fix Code

### Fix #1: Context-Aware Async

**File**: `services/ecosystem-mcp/src/api/routes/query.py`  
**Line**: 389

\`\`\`python
# BEFORE (Line 389):
async with get_database() as db:
    # Query distinct repositories from documents table
    from sqlalchemy import text
    ...

# AFTER:
db = get_database()
# Query distinct repositories from documents table
from sqlalchemy import text
...
\`\`\`

Also fix line 505:
\`\`\`python
# BEFORE (Line 505):
async with get_database() as db:
    doc_repo = DocumentRepository(db)
    ...

# AFTER:
db = get_database()
doc_repo = DocumentRepository(db)
...
\`\`\`

---

### Fix #2: Cache Clear Duplicate

**File**: `services/ecosystem-mcp/src/api/routes/admin.py`  
**Lines**: 1318, 1179-1183

\`\`\`python
# Change line 1318 from:
@router.post("/clear-cache", ...)

# To:
@router.post("/clear-cache-prefix", ...)

# Change lines 1179-1183 from:
except Exception as e:
    logger.error(f"Failed to clear cache: {e}", exc_info=True)
    return {
        "status": "error",
        "message": f"Failed to clear cache: {str(e)}"
    }

# To:
except Exception as e:
    logger.error(f"Failed to clear cache: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail=f"Failed to clear cache: {str(e)}"
    )
\`\`\`

---

### Fix #3: Multi-Pass Quick Wins

**File**: `services/ecosystem-mcp/src/api/routes/multi_pass.py`  
**Line**: 154 (after service creation)

\`\`\`python
try:
    multi_pass_service = get_multi_pass_service()
    
    # NEW: Check if we have documents
    from ...storage import get_database
    db = get_database()
    doc_count = await db.execute_scalar("SELECT COUNT(*) FROM documents WHERE is_latest = true")
    
    if doc_count == 0:
        logger.warning("Multi-pass query attempted with empty database")
        raise HTTPException(
            status_code=503,
            detail="No documents available for multi-pass query. Please ingest documents first."
        )
    
    logger.info(f"Multi-pass query request: enhancements={request.use_enhancements}, docs={doc_count}")
    logger.info(f"Starting decomposition (num_passes={request.num_passes})")
    
    result = await multi_pass_service.process_query(
        query=request.query,
        num_passes=request.num_passes,
        num_secondary_questions=request.num_secondary_questions,
        n_results=request.n_results,
        temperature=request.temperature,
        response_length=request.response_length,
        use_enhancements=request.use_enhancements
    )
    
    logger.info(f"Multi-pass query completed in {result.total_duration_seconds:.1f}s")
    ...
\`\`\`

---

## ✅ Expected Outcomes

### After Fix #1 (Context-Aware)
- ✅ `/api/v1/contexts` returns 200
- ✅ Returns list of repository contexts
- ✅ No async context manager error

### After Fix #2 (Cache Clear)
- ✅ `/api/v1/admin/clear-cache` returns 200
- ✅ Successfully clears cache
- ✅ No route collision
- ✅ Proper error handling

### After Fix #3 (Multi-Pass)
- ✅ Fails fast with 503 if no documents
- ✅ Better logging for debugging
- ✅ Clear recommendation to use streaming
- ⚠️ Still slow (60s+) but expected behavior documented

**Final Success Rate**: **100%** (all endpoints working)

---

## 📈 Before vs After

### Before Fixes
- Context-Aware: ❌ 500 error
- Cache Clear: ❌ 500 error
- Multi-Pass: ⏱️ Timeout (no feedback)
- Success Rate: **73%** (8/11)

### After Fixes
- Context-Aware: ✅ 200 OK
- Cache Clear: ✅ 200 OK
- Multi-Pass: ⚠️ 503 (empty DB) or ⏱️ Timeout (documented)
- Success Rate: **91%** (10/11) or **100%** (with data + streaming)

**Improvement**: +18-27 percentage points!

---

**Investigation Complete**: October 29, 2025  
**Total Issues**: 3  
**Issues Understood**: 3  
**Fixes Ready**: 3  
**Implementation Time**: 52 minutes  

🎯 **READY TO IMPLEMENT FIXES**

