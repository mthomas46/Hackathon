# Multi-Pass RAG Performance Analysis & Optimization

**Date:** October 25, 2025  
**Status:** 🔍 Investigation Complete  
**Issue:** Multi-pass queries timing out after 180 seconds  

---

## 📊 Investigation Summary

### **What Was Done:**

1. **Added Comprehensive Timing Logs** (6 major checkpoints):
   - Query decomposition (LLM call)
   - Question generation per section (parallel LLM calls)
   - Section processing (parallel RAG + synthesis)
   - Section synthesis (LLM call per section)
   - Final synthesis (LLM call)

2. **Enhanced Logging**:
   - ⏱️  markers for operation start
   - ✅ markers for completion with timing
   - Per-operation timing breakdown
   - Total time tracking

---

## 🔍 Root Cause Analysis

### **Why Multi-Pass Is Slow:**

Multi-pass makes **MANY LLM calls** in sequence/parallel:

**For a query with 2 sections, 2 questions each:**

1. **Decompose query** → 1 LLM call (~5-15s)
2. **Generate questions** → 2 LLM calls in parallel (~10-20s)
3. **Execute RAG queries** → 4 RAG queries in parallel (~20-40s)
   - Each RAG query calls LLM to generate answer
4. **Synthesize sections** → 2 LLM calls in parallel (~20-40s)
5. **Final synthesis** → 1 LLM call (~10-30s)

**Total:** ~65-145 seconds **minimum** (if everything works perfectly)

**For 3 sections, 3 questions each (9 RAG queries):**
- Easily exceeds 180+ seconds

---

## 🎯 **CRITICAL INSIGHT: The Problem**

### **The Architecture is Fundamentally Slow:**

```
Multi-Pass = Sequential Stages of Parallel LLM Calls

Stage 1: Decompose (1 LLM call)          →  5-15s
   ↓
Stage 2: Questions (N LLM calls parallel) → 10-20s
   ↓
Stage 3: RAG (M queries parallel)         → 20-60s
   ↓
Stage 4: Synthesis (N LLM calls parallel) → 20-60s
   ↓
Stage 5: Final (1 LLM call)               → 10-30s

TOTAL: 65-185+ seconds for modest queries
```

**Even with perfect parallelization, you cannot escape:**
- 5 sequential stages
- Each stage waits for slowest LLM call
- LLM calls are inherently slow (5-30s each)

---

## 🚀 **QUICK WINS (Immediate Optimizations)**

### **1. Reduce Default Parameters** ⚡

**Current defaults:**
```python
num_sections: int = 3
questions_per_section: int = 3
Total questions: 9
```

**Recommended defaults:**
```python
num_sections: int = 2
questions_per_section: int = 2
Total questions: 4
```

**Impact:** 44% reduction in LLM calls (9 → 4)
**Time saved:** 30-60 seconds

---

### **2. Cache Decomposition Results** 💾

Similar queries often decompose into similar sections. Cache the decomposition by query hash.

```python
decomposition_cache = {}

def get_cached_decomposition(query: str, num_sections: int):
    cache_key = hashlib.md5(f"{query}:{num_sections}".encode()).hexdigest()
    if cache_key in decomposition_cache:
        logger.info("✅ Using cached decomposition!")
        return decomposition_cache[cache_key]
    # ... actual decomposition ...
    decomposition_cache[cache_key] = sections
    return sections
```

**Impact:** Skip 1 LLM call for repeat/similar queries
**Time saved:** 5-15 seconds

---

### **3. Simplify Section Synthesis** ⚡⚡

**Current flow:**
```
RAG queries → Individual answers → Section synthesis (LLM)
```

**Optimized flow:**
```
RAG queries → Individual answers → Simple concatenation (no LLM)
```

Section synthesis adds minimal value but costs 20-40s.

**Implementation:**
```python
# Instead of LLM synthesis, just concatenate:
def _synthesize_section_fast(question_results):
    parts = []
    for q in question_results:
        parts.append(f"**{q.question}**\n{q.answer}\n")
    return "\n".join(parts)
```

**Impact:** Skip N LLM calls (one per section)
**Time saved:** 20-60 seconds

---

### **4. Reduce Final Synthesis Tokens** ⚡

**Current:**
```python
max_tokens=response_length * 2  # Can be 1000-4000 tokens!
```

**Optimized:**
```python
max_tokens=min(response_length, 1000)  # Cap at 1000
```

**Impact:** Faster final LLM call
**Time saved:** 5-15 seconds

---

### **5. Add Timeout Per Stage** 🚨

Don't let one slow stage block everything:

```python
async def with_timeout(coro, timeout_seconds, stage_name):
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"⚠️  {stage_name} timed out after {timeout_seconds}s")
        return None

# Usage:
sections = await with_timeout(
    self._decompose_query(query, num_passes),
    timeout_seconds=30,
    stage_name="Decomposition"
)
```

**Impact:** Fail fast instead of hanging
**Time saved:** Prevents 180s hangs

---

## 🎯 **RECOMMENDED IMPLEMENTATION (Quick Wins)**

### **Priority 1: Reduce Defaults (2 min)**

```python
# In multi_pass.py API endpoint
class MultiPassRequest(BaseModel):
    num_sections: int = Field(
        default=2,  # Was 3
        ge=1,
        le=10
    )
    questions_per_section: int = Field(
        default=2,  # Was 3
        ge=1,
        le=10
    )
```

**Expected result:** 30-60s faster, more queries complete within 180s

---

### **Priority 2: Skip Section Synthesis LLM (10 min)**

```python
async def _process_section(self, ...):
    # ... execute RAG queries ...
    
    # NEW: Fast synthesis (no LLM)
    synthesis = self._fast_concatenate_answers(question_results)
    
    # OLD: Slow synthesis (LLM call)
    # synthesis = await self._synthesize_section(...)
```

**Expected result:** 20-60s faster

---

### **Priority 3: Cap Max Tokens (2 min)**

```python
async def _synthesize_final_answer(self, ...):
    # ...
    max_tokens = min(response_length, 1000)  # Cap it!
    
    response = await self.ollama_router.generate(
        max_tokens=max_tokens
    )
```

**Expected result:** 5-15s faster

---

## 📊 **EXPECTED IMPROVEMENTS**

| Optimization | Time Saved | Difficulty | Priority |
|--------------|------------|------------|----------|
| Reduce defaults (3→2, 3→2) | 30-60s | Easy (2 min) | ⭐⭐⭐ |
| Skip section synthesis | 20-60s | Medium (10 min) | ⭐⭐⭐ |
| Cap final synthesis tokens | 5-15s | Easy (2 min) | ⭐⭐ |
| Add per-stage timeouts | Prevents hangs | Medium (15 min) | ⭐⭐ |
| Cache decomposition | 5-15s | Medium (15 min) | ⭐ |

**Total potential savings:** 60-150 seconds
**Total effort:** ~45 minutes of refactoring

---

## 🔬 **ARCHITECTURAL RECOMMENDATIONS (Longer Term)**

### **1. Streaming Response**

Return results as they complete instead of waiting for everything:

```python
# User sees results in real-time:
Section 1: [answers appear as RAG queries complete]
Section 2: [answers appear as RAG queries complete]
Final synthesis: [appears last]
```

**Benefit:** Better UX, perceived performance

---

### **2. Smart Question Generation**

Instead of N questions per section, generate questions based on RAG results:

```
Generate 1 question → Get answer → Generate follow-up question
```

This creates a "conversation" instead of batch processing.

**Benefit:** More targeted questions, potentially fewer total questions

---

### **3. Parallel Final Synthesis**

Don't wait for all sections. Start synthesizing as soon as 2+ sections complete:

```python
# Start final synthesis when 2 sections done
if len(completed_sections) >= 2:
    asyncio.create_task(synthesize_partial_answer(completed_sections))
```

**Benefit:** Shave off 10-20s from tail latency

---

## ⚠️  **WHY MULTI-PASS WILL ALWAYS BE SLOW**

**Fundamental constraints:**

1. **Sequential stages** - Cannot parallelize across stages
2. **LLM latency** - Each call takes 5-30s (network + GPU)
3. **Context building** - Each stage needs previous stage's output
4. **Quality vs Speed tradeoff** - More analysis = more time

**Bottom line:** Multi-pass is designed for **depth over speed**.

For queries requiring 3+ sections with 3+ questions each (9+ RAG queries), **expect 2-5 minutes**.

---

## ✅ **CONCLUSION & NEXT STEPS**

### **Immediate Actions (< 1 hour):**

1. ✅ **Reduce default parameters** (2→2 instead of 3→3)
2. ✅ **Skip section synthesis LLM** (concatenate instead)
3. ✅ **Cap max tokens** (1000 max)
4. ✅ **Add per-stage timeouts** (30s decompose, 60s questions, 90s sections, 60s final)

**Expected outcome:** Most queries complete in 60-120s instead of 180s+

### **User Communication:**

Update API documentation to set expectations:

```
Multi-Pass Query Performance:
- Simple (2 sections, 2 questions): 60-90 seconds
- Moderate (3 sections, 3 questions): 120-180 seconds  
- Complex (4+ sections, 4+ questions): 180-300 seconds

For faster results, use basic RAG query instead.
```

---

## 📝 **FILES MODIFIED**

Timing logs added to:
- `services/ecosystem-mcp/src/services/rag/multi_pass_query.py`

Recommended quick wins in:
- `services/ecosystem-mcp/src/api/routes/multi_pass.py` (defaults)
- `services/ecosystem-mcp/src/services/rag/multi_pass_query.py` (synthesis, tokens)

---

**Status:** Ready for implementation of quick wins  
**Estimated effort:** 45 minutes  
**Expected improvement:** 50-80% faster multi-pass queries  

