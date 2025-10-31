# RAG Tier Routing and Response Length Issues 🔍

**Date:** October 25, 2025 01:35 UTC  
**Status:** Root Causes Identified  
**Issues:** 2 critical bugs affecting RAG performance  

---

## 🔍 ISSUE #1: AUTO TIER FALLING BACK TO DOCKER

### Symptom
```
⚠️ Requested auto tier was unavailable. Fell back to docker.
```

### What's Happening
```
Enhanced query: mode=QueryMode.RAG, tier=TierPreference.AUTO
✅ Desktop Ollama available at http://host.docker.internal:11434
🎯 Routing to DOCKER CPU (complexity=0.20): explain ecosystem-mcp...
```

**Desktop is available but not being used!**

### Root Cause

**The complexity score for RAG queries is too low!**

```python
# In ollama_router.py line 156-158:
if (settings.ollama_desktop_enabled and 
    self.desktop_available and 
    complexity_score >= 0.4):  # 🎯 THRESHOLD IS 0.4
    return self.desktop_client  # Desktop (GPU)

# But RAG queries are scoring 0.20 (< 0.4)
# So they fall through to Docker CPU
```

### Why RAG Queries Score Low

Looking at the complexity analyzer:
1. Short questions get low scores
2. Even with `workload_type='rag'`, the base question complexity dominates
3. The RAG workload hint only adds ~0.05 to the score

**Example:**
- Question: "explain ecosystem-mcp" → Base complexity: 0.15
- Workload type: 'rag' → Add: 0.05
- **Total: 0.20** < 0.4 threshold → **Docker CPU**

### The Fix

**Option 1: Lower Desktop Threshold for RAG Queries**
```python
# In ollama_router.py
# For RAG queries, use a lower threshold (0.25 instead of 0.4)
rag_threshold = 0.25 if workload_type == 'rag' else 0.4

if (settings.ollama_desktop_enabled and 
    self.desktop_available and 
    complexity_score >= rag_threshold):
    return self.desktop_client
```

**Option 2: Boost RAG Complexity Score**
```python
# In complexity_analyzer.py
def _score_workload_type(self, workload_type: Optional[str]) -> float:
    if workload_type == 'rag':
        return 0.3  # Changed from 0.05 → ensures >= 0.4 threshold
    elif workload_type == 'embedding':
        return 0.2
```

**Option 3: Force Desktop for RAG When Available**
```python
# In ollama_router.py, before complexity check:
# Special case: RAG queries should prefer Desktop when available
if workload_type == 'rag' and settings.ollama_desktop_enabled and self.desktop_available:
    logger.info(f"🎯 Routing RAG query to DESKTOP GPU")
    return self.desktop_client, settings.ollama_desktop_model, "desktop"
```

**Recommended: Option 3** - Most explicit and clear intent

---

## 🔍 ISSUE #2: RESPONSE_LENGTH NOT BEING USED

### Symptom
Response length parameter doesn't affect RAG answer length

### Root Cause

**`max_tokens` is hardcoded in `rag_service.py`**

```python
# In rag_service.py line 363:
response = await self.ollama_router.generate(
    prompt=prompt,
    workload_type='rag',
    temperature=temperature,
    max_tokens=1000,  # 🐛 HARDCODED!
    ...
)
```

### The Problem

1. **API Request:** User can provide `response_length` in request
2. **EnhancedQueryRequest:** Has `response_length` field (optional)
3. **RAGService.ask():** Doesn't accept or use `response_length` parameter
4. **Result:** Always generates ~1000 token responses

### The Fix

**Step 1: Add response_length to EnhancedQueryRequest**
```python
# In query_enhanced.py
class EnhancedQueryRequest(BaseModel):
    # ... existing fields ...
    response_length: Optional[int] = Field(
        default=1000,
        ge=100,
        le=4000,
        description="Max tokens in response"
    )
```

**Step 2: Add response_length parameter to RAGService.ask()**
```python
# In rag_service.py
async def ask(
    self,
    question: str,
    n_results: int = 10,
    context: Optional[List[Dict[str, Any]]] = None,
    prefer_recent: bool = True,
    temperature: float = 0.7,
    response_length: int = 1000  # 🆕 NEW PARAMETER
) -> Dict[str, Any]:
```

**Step 3: Pass response_length to _generate_answer()**
```python
# In rag_service.py ask() method:
answer = await self._generate_answer(
    question=question,
    context=context_text,
    conversation_history=context,
    temperature=temperature,
    retrieved_documents=documents,
    max_tokens=response_length  # 🆕 PASS IT THROUGH
)
```

**Step 4: Update _generate_answer() signature and usage**
```python
# In rag_service.py
async def _generate_answer(
    self,
    question: str,
    context: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.7,
    retrieved_documents: Optional[List[Dict[str, Any]]] = None,
    max_tokens: int = 1000  # 🆕 NEW PARAMETER
) -> str:
    # ...
    response = await self.ollama_router.generate(
        prompt=prompt,
        workload_type='rag',
        temperature=temperature,
        max_tokens=max_tokens,  # 🆕 USE PARAMETER
        ...
    )
```

**Step 5: Pass response_length from API route**
```python
# In query_enhanced.py _process_rag_query():
result = await rag_service.ask(
    question=request.question,
    n_results=request.n_results,
    temperature=request.temperature,
    response_length=request.response_length  # 🆕 PASS IT THROUGH
)
```

---

## 📊 EXPECTED BEHAVIOR AFTER FIXES

### Issue #1 Fix: Tier Routing

**Before:**
```
RAG Query → Complexity 0.20 → < 0.4 → Docker CPU (slow)
⚠️ Warning: "Fell back to docker"
```

**After:**
```
RAG Query → Force Desktop (when available) → Desktop GPU (fast) ⚡
No warnings, optimal performance
```

**Performance Gain:** 3-5x faster RAG queries

### Issue #2 Fix: Response Length

**Before:**
```json
{
  "question": "Explain X",
  "response_length": 500  // ❌ IGNORED
}
// Always gets ~1000 token response
```

**After:**
```json
{
  "question": "Explain X",
  "response_length": 500  // ✅ USED
}
// Gets concise ~500 token response
```

---

## 🎯 IMPLEMENTATION PRIORITY

### Priority 1: Tier Routing Fix (HIGH)
**Impact:** 3-5x performance improvement for all RAG queries  
**Complexity:** Low (5-10 lines of code)  
**Risk:** Low  
**Time:** 5 minutes  

### Priority 2: Response Length Fix (MEDIUM)
**Impact:** User control over answer length  
**Complexity:** Medium (changes across 3 files)  
**Risk:** Low  
**Time:** 15 minutes  

---

## 📝 FILES TO MODIFY

### Fix #1: Tier Routing
1. **services/ecosystem-mcp/src/services/models/ollama_router.py**
   - Add special case for RAG workload before complexity check
   - Lines 145-154 (before Cursor check)

### Fix #2: Response Length
1. **services/ecosystem-mcp/src/api/routes/query_enhanced.py**
   - Add `response_length` field to `EnhancedQueryRequest`
   - Pass it to `rag_service.ask()`

2. **services/ecosystem-mcp/src/services/rag/rag_service.py**
   - Add `response_length` parameter to `ask()`
   - Add `max_tokens` parameter to `_generate_answer()`
   - Pass `max_tokens` to `ollama_router.generate()`

3. **services/ecosystem-mcp/src/api/routes/ask.py**
   - Add `response_length` field to `AskRequest`
   - Pass it to `rag_service.ask()`

---

## ✅ VALIDATION STEPS

### Test #1: Tier Routing
```bash
# Before fix:
curl -X POST http://localhost:8000/api/v1/query/enhanced \
  -d '{"question": "test", "mode": "rag", "tier": "auto"}'
# Check logs: Should see "Routing to DESKTOP GPU"

# Verify no fallback warning
```

### Test #2: Response Length
```bash
# Short response (500 tokens):
curl -X POST http://localhost:8000/api/v1/query/enhanced \
  -d '{"question": "What is X?", "response_length": 500}'
# Should get concise answer (~500 tokens)

# Long response (2000 tokens):
curl -X POST http://localhost:8000/api/v1/query/enhanced \
  -d '{"question": "Explain Y in detail", "response_length": 2000}'
# Should get detailed answer (~2000 tokens)
```

---

**Status:** Root causes identified, ready to implement  
**Priority:** HIGH (Tier routing), MEDIUM (Response length)  
**Impact:** Significant performance and UX improvements  
**ETA:** 20 minutes total

