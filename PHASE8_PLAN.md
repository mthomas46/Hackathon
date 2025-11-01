# Phase 8: Update Contextual Query API - Implementation Plan

## Analysis

**Goal:** Expose enhancement configuration via API endpoints for all RAG types.

**Why This Matters:**
- Phases 1-7 added enhancements to the **service layer**
- Phase 8 exposes enhancements at the **API layer**
- Users need to control enhancements via API requests

---

## Current State Assessment

### APIs That Need Updates

| API Route | File | Current State | Needs Update |
|-----------|------|---------------|--------------|
| `/api/v1/rag/ask/enhanced` | `query_enhanced.py` | ✅ Already enhanced | ✅ Check config exposure |
| `/api/v1/rag/ask` | `ask.py` or `standard.py` | 🔄 Phase 3 enhanced | ✅ Expose config |
| `/api/v1/rag/temporal/*` | `temporal_rag.py` | ✅ Phase 4 enhanced | ✅ Expose config |
| `/api/v1/query/context-aware` | `context_aware_query.py` | ✅ Phase 5 enhanced | ✅ Expose config |
| `/api/v1/rag/multi-pass` | `multi_pass.py` | ✅ Phase 6 enhanced | ✅ Expose config |
| `/api/v1/dynamic-rag/*` | `dynamic_rag.py` | ✅ Phase 7 enhanced | ✅ Expose flag |

### Key Question

**Do the APIs already expose enhancement controls?**
- If YES: Validate and document
- If NO: Add parameters to API request models

---

## Phase 8 Strategy

### Option A: Lightweight (Recommended)
**Verify existing API exposure and add missing parameters**

**Tasks:**
1. Audit all RAG API endpoints
2. Check if `use_enhancements` or `enhancement_config` is exposed
3. Add missing parameters where needed
4. Update API documentation
5. Add usage examples

**Time:** 1-2 hours  
**Risk:** LOW

### Option B: Full Enhancement API
**Create comprehensive enhancement configuration API**

**Tasks:**
1. Create `EnhancementConfigRequest` model
2. Update all RAG endpoints to accept config
3. Create preset endpoints (`/config/presets`)
4. Add validation
5. Extensive documentation

**Time:** 4-6 hours  
**Risk:** MEDIUM

**Decision: Use Option A (Lightweight)**

---

## Implementation Plan

### Task 1: Audit Existing APIs (20 min)

Check each API route file for:
- `use_enhancements` parameter
- `enhancement_config` parameter
- Default values
- Request model exposure

### Task 2: Add Missing Parameters (30 min)

For APIs missing enhancement controls:
- Add `use_enhancements: bool = True` to request models
- Pass through to service layer
- Update response models if needed

### Task 3: Update API Documentation (20 min)

- Update OpenAPI/Swagger docs
- Add parameter descriptions
- Include examples for common use cases

### Task 4: Create Quick Reference Guide (20 min)

Document how to:
- Enable/disable enhancements per query
- Use default configs vs custom configs
- Best practices for each RAG type

### Task 5: Test API Changes (20 min)

- Test enhancement toggle via API
- Verify backward compatibility
- Test all RAG types

---

## Expected API Updates

### 1. Enhanced RAG API (`query_enhanced.py`)

**Status:** ✅ Should already be fully enhanced

**Verify:**
```python
class EnhancedQueryRequest(BaseModel):
    question: str
    use_enhancements: bool = True  # ✅ Check this exists
    # ... other fields
```

### 2. Standard RAG API (`ask.py` or `standard.py`)

**Add:**
```python
class RAGQueryRequest(BaseModel):
    question: str
    n_results: int = 10
    use_enhancements: bool = True  # ✨ NEW
```

### 3. Temporal RAG API (`temporal_rag.py`)

**Add:**
```python
class TemporalQueryRequest(BaseModel):
    question: str
    use_enhancements: bool = True  # ✨ NEW
    # ... temporal filters
```

### 4. Context-Aware RAG API (`context_aware_query.py`)

**Add:**
```python
class ContextAwareQueryRequest(BaseModel):
    question: str
    use_enhancements: bool = True  # ✨ NEW
    # ... context filters
```

### 5. Multi-Pass RAG API (`multi_pass.py`)

**Add:**
```python
class MultiPassRequest(BaseModel):
    query: str
    use_enhancements: bool = True  # ✨ NEW (should already be there)
    # ... multi-pass parameters
```

### 6. Dynamic Temporal RAG API (`dynamic_rag.py`)

**Add:**
```python
class DynamicRAGRequest(BaseModel):
    query: str
    use_enhancements: bool = True  # ✨ NEW
    # ... dynamic parameters
```

---

## Quick Reference Guide (To Be Created)

### Enhancement Control Examples

**1. Standard RAG with Enhancements**
```bash
curl -X POST http://localhost:8000/api/v1/rag/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is MCP?",
    "use_enhancements": true
  }'
```

**2. Temporal RAG without Enhancements**
```bash
curl -X POST http://localhost:8000/api/v1/rag/temporal/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How has authentication evolved?",
    "use_enhancements": false
  }'
```

**3. Multi-Pass with Custom Config** (if supported)
```bash
curl -X POST http://localhost:8000/api/v1/rag/multi-pass \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the architecture",
    "use_enhancements": true,
    "num_passes": 3
  }'
```

---

## Success Criteria

✅ All RAG APIs expose `use_enhancements` parameter  
✅ Default is `use_enhancements=true` (enhancements on by default)  
✅ Backward compatible (can disable if needed)  
✅ API documentation updated  
✅ Usage examples provided  
✅ All tests passing  

---

## Files to Modify (Estimated)

1. `ask.py` or `standard.py` (Standard RAG API)
2. `temporal_rag.py` (Temporal RAG API) - likely already done
3. `context_aware_query.py` (Context-Aware API) - likely already done
4. `multi_pass.py` (Multi-Pass API) - likely already done
5. `dynamic_rag.py` (Dynamic Temporal RAG API)
6. API documentation (OpenAPI schema)

---

## Time Estimate

- API Audit: 20 min
- Add Parameters: 30 min
- Documentation: 20 min
- Quick Reference: 20 min
- Testing: 20 min
**Total: ~2 hours**

---

## Risks

| Risk | Mitigation | Status |
|------|------------|--------|
| Breaking API changes | Use optional parameters with defaults | ✅ Low risk |
| Missing documentation | Create comprehensive quick reference | ✅ Planned |
| Test failures | Validate each endpoint individually | ✅ Planned |

---

## Next Steps

1. ✅ Create Phase 8 plan (this document)
2. 🔄 Audit all RAG API endpoints
3. 🔄 Add missing `use_enhancements` parameters
4. 🔄 Update API documentation
5. 🔄 Create quick reference guide
6. 🔄 Test all APIs
7. 🔄 Deploy and document

**Status:** Ready to implement  
**Complexity:** Low  
**Impact:** High (API usability)

