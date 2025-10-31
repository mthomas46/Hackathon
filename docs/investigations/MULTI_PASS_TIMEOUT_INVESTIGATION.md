# Multi-Pass Timeout Investigation 🔍

**Date:** October 25, 2025 03:45 UTC  
**Issue:** Multi-pass queries timing out even with small parameters  
**Status:** Under Investigation  

---

## 🔍 THE PROBLEM

### What's Happening
```
Test 1: 10 sections × 10 questions (100 queries)
Result: Hung indefinitely ❌

Test 2: 3 sections × 3 questions (9 queries) 
Result: Timed out after 120 seconds ❌

Test 3: Basic RAG query
Result: Works fine (1088 chars, 128 words) ✅
```

### Symptoms
- Multi-pass endpoint hangs/times out
- Even small configurations (9 queries) timeout
- Basic RAG endpoint works perfectly
- Service is healthy (worker running, Redis connected)
- No error logs visible

---

## ✅ WHAT WORKS

### Basic RAG Query (Verified)
```bash
curl -X POST /api/v1/query/enhanced \
  -d '{
    "question": "What are the main API endpoints?",
    "mode": "rag",
    "response_length": 1200
  }'

# Result: ✅ Works fine
# - Answer length: 1088 chars
# - Answer words: 128 words
# - Response time: < 5 seconds
```

### Response Length in Basic RAG (Verified)
- XL verbosity instructions are working
- Dynamic prompts are functioning
- LLM routing is working
- `response_length` parameter is being used

---

## ❌ WHAT DOESN'T WORK

### Multi-Pass Query (Failing)
```bash
curl -X POST /api/v1/query/multi-pass \
  -d '{
    "query": "describe the api offerings",
    "num_passes": 3,
    "num_secondary_questions": 3,
    "response_length": 1200
  }'

# Result: ❌ Timeout after 120+ seconds
# - No response
# - No error logs
# - Service remains responsive to other requests
```

---

## 🔧 POSSIBLE CAUSES

### 1. Syntax Error in Modified Code
**Likelihood:** Medium  
**Check:** Run linter on modified files  
**Files:** 
- `src/services/rag/multi_pass_query.py`
- `src/api/routes/multi_pass.py`

### 2. Infinite Loop in Multi-Pass Logic
**Likelihood:** Medium  
**Check:** Add debug logging to multi-pass execution  
**Potential locations:**
- Section processing loop
- Question generation loop
- Synthesis generation

### 3. Blocking on LLM Call
**Likelihood:** High  
**Check:** Verify async/await usage  
**Potential issue:** Missing `await` on async calls

### 4. ChromaDB Query Hanging
**Likelihood:** Low (basic RAG works)  
**Check:** Test with fewer documents  

### 5. Service Restart Needed
**Likelihood:** Low (already restarted)  
**Check:** Verify deployed code matches local files  

---

## 🧪 DIAGNOSTIC TESTS COMPLETED

### Test 1: Service Health ✅
```bash
docker logs ecosystem-mcp-service
# Result: Worker running, no errors
```

### Test 2: Basic RAG ✅
```bash
POST /api/v1/query/enhanced
# Result: Works perfectly with response_length=1200
```

### Test 3: Small Multi-Pass ❌
```bash
POST /api/v1/query/multi-pass (3×3 queries)
# Result: Timeout after 120 seconds
```

### Test 4: Large Multi-Pass ❌
```bash
POST /api/v1/query/multi-pass (10×10 queries)
# Result: Hung indefinitely
```

---

## 🎯 NEXT STEPS

### Immediate Actions

1. **Check for Syntax Errors**
   ```bash
   python -m py_compile multi_pass_query.py
   read_lints on modified files
   ```

2. **Add Debug Logging**
   - Log entry/exit of each multi-pass stage
   - Log each RAG query execution
   - Log synthesis calls
   - Identify where it's hanging

3. **Verify Async/Await**
   - Check all async function calls have `await`
   - Verify no blocking synchronous calls
   - Check for deadlocks in concurrent execution

4. **Test Minimal Multi-Pass**
   ```python
   # 1 section × 1 question
   num_passes=1
   num_secondary_questions=1
   ```

5. **Check API Routing**
   ```bash
   curl http://localhost:8000/docs
   # Verify /api/v1/query/multi-pass exists
   ```

### Investigation Priority

1. ✅ **High Priority:** Check for syntax errors (linter)
2. ✅ **High Priority:** Add debug logging to find hang point
3. **Medium Priority:** Test minimal configuration (1×1)
4. **Medium Priority:** Verify async/await usage
5. **Low Priority:** Check API routing

---

## 📝 CODE REVIEW CHECKLIST

### Files Modified

1. **`src/services/rag/multi_pass_query.py`**
   - [ ] Check all `async def` have `await` on async calls
   - [ ] Check no infinite loops in processing
   - [ ] Check synthesis prompts are valid
   - [ ] Verify `max_tokens` parameter is valid

2. **`src/api/routes/multi_pass.py`**
   - [ ] Check `response_length` field is valid
   - [ ] Check endpoint exists and is registered
   - [ ] Verify request model is correct

### Potential Bugs

1. **Missing `await`:** Async function called without `await`
2. **Type Error:** `max_tokens` parameter type mismatch
3. **Infinite Loop:** Section/question processing logic
4. **Deadlock:** Concurrent execution issue

---

## 🔧 TEMPORARY WORKAROUND

### Use Basic RAG Instead
```
For now, use /api/v1/query/enhanced with:
- mode: "rag"
- response_length: 1200 (XL)
- n_results: 50

This works perfectly and provides detailed answers.
```

### When to Use Multi-Pass (After Fix)
- Complex queries needing multiple perspectives
- Comprehensive documentation generation
- Deep technical analysis
- Research-level questions

---

## 📊 COMPARISON

### Basic RAG (Working)
- ✅ Fast (< 5 seconds)
- ✅ response_length works
- ✅ XL verbosity works
- ✅ Detailed answers
- ⚠️  Single-pass only

### Multi-Pass (Broken)
- ❌ Hangs/times out
- ❌ Can't test response_length
- ❌ No output
- ✅ Code changes deployed
- ⚠️  Needs debugging

---

## 🎯 SUMMARY

**Issue:** Multi-pass endpoint hanging/timing out  
**Verified Working:** Basic RAG with response_length=1200  
**Next Step:** Debug multi-pass to find hang point  
**Workaround:** Use basic RAG endpoint for now  
**Priority:** High (feature completely non-functional)  

---

**Status:** 🔴 **BLOCKED - NEEDS DEBUG LOGGING**  
**Workaround:** Use `/api/v1/query/enhanced` instead  
**ETA:** Unknown until hang point identified  

