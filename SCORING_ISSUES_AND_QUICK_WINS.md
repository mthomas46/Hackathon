# RAG Scoring Issues & Quick Wins for Accuracy Improvement

**Date:** October 31, 2025  
**Analysis:** Comprehensive investigation of relevance and quality scoring  
**Status:** 3 Critical Issues Identified + Solutions  

---

## Executive Summary

Investigation of 192 source citations across 20 queries revealed **3 critical scoring issues** that are preventing our RAG system from reaching its full potential:

1. **81% of sources have LOW relevance** (<0.4 threshold)
2. **Quality scores missing** from API responses
3. **Score inconsistency** between Standard and Enhanced RAG

**Impact:** These issues are diluting answer quality by including too many irrelevant sources.

**Solution:** 3 quick wins that can improve accuracy by an estimated +5-10% with minimal code changes.

---

## Issue #1: 81% of Sources Have LOW Relevance (<0.4)

### The Problem

**From analysis:**
```
Relevance Score Distribution:
  High (≥0.7):      0 sources (  0.0%)  ⚠️
  Medium (0.4-0.7):  36 sources ( 18.8%)
  Low (<0.4):      156 sources ( 81.2%)  🔴

Average relevance: 0.113 (very low!)
```

**Root Cause:**
- **RRF scoring** in hybrid search produces very small numbers (0.005-0.016)
- Formula: `1/(60 + rank)` results in scores like:
  - Rank 0: 1/60 = 0.0167
  - Rank 10: 1/70 = 0.0143
  - Rank 50: 1/110 = 0.0091
- These are NOT normalized to a useful 0-1 range

**Comparison:**
- Standard RAG: 0.4-0.5 relevance (normalized)
- Phase 1+2+3: 0.005-0.016 relevance (not normalized) ⚠️

### Quick Win #1A: Normalize RRF Scores

**Location:** `services/ecosystem-mcp/src/services/rag/hybrid_search.py:202-280`

**Current Code (Simplified):**
```python
def _reciprocal_rank_fusion(self, semantic_results, keyword_results, ...):
    # Calculate RRF scores
    rrf_score = (
        semantic_weight / (60 + sem_rank) +
        keyword_weight / (60 + key_rank)
    )
    # Returns scores like 0.005-0.016 ⚠️
```

**Fix:**
```python
def _reciprocal_rank_fusion(self, semantic_results, keyword_results, ...):
    fused = []
    max_possible_score = (
        semantic_weight / 60 +
        keyword_weight / 60
    )  # ~0.0333 for default weights
    
    for doc_id in all_doc_ids:
        sem_rank = semantic_ranks.get(doc_id, 1000)
        key_rank = keyword_ranks.get(doc_id, 1000)
        
        rrf_score = (
            semantic_weight / (60 + sem_rank) +
            keyword_weight / (60 + key_rank)
        )
        
        # NORMALIZE to 0-1 range
        normalized_score = rrf_score / max_possible_score
        
        fused.append({
            ...
            "hybrid_score": normalized_score,  # Now 0-1 range ✅
            ...
        })
```

**Expected Impact:** Relevance scores will be 0.3-1.0 instead of 0.005-0.016

### Quick Win #1B: Filter Low-Relevance Sources

**Location:** `services/ecosystem-mcp/src/services/rag/accuracy_enhanced_rag.py:ask_enhanced`

**Add filtering threshold:**
```python
# After retrieving documents
all_documents = [doc for doc in all_documents if doc.get("hybrid_score", 0) > 0.3]
```

**Or in hybrid_search.py after RRF:**
```python
# Filter out low-relevance results
MIN_RELEVANCE_THRESHOLD = 0.3
final_results = [
    doc for doc in fused 
    if doc["hybrid_score"] >= MIN_RELEVANCE_THRESHOLD
]
```

**Expected Impact:**
- Remove bottom 50-70% of sources (noise)
- Keep only relevant documents
- Reduce context clutter
- Improve answer focus

---

## Issue #2: Quality Scores Missing from API Responses

### The Problem

**From analysis:**
```
⚠️  QUALITY SCORES: Not found in sources
   This may indicate quality scores are not being propagated to API responses
```

**Root Cause:**

Quality scores exist in the database:
- `DocumentModel` has `quality_score`, `quality_grade`, `score_breakdown`
- Documents are scored during ingestion
- BUT: They're not included in the API response's `sources` array

**Location:** `services/ecosystem-mcp/src/services/rag/rag_service.py:330-360`

**Current Code:**
```python
def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sources = []
    for i, doc in enumerate(documents, 1):
        sources.append({
            "id": i,
            "file_path": doc["file_path"],
            "relevance_score": relevance_score,
            "adjusted_score": adjusted_score,
            "recency_days": doc.get("recency_days"),
            "updated_at": doc.get("updated_at")
            # ⚠️ quality_score is MISSING!
        })
```

### Quick Win #2: Add Quality Scores to Source Citations

**Fix:**
```python
def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sources = []
    for i, doc in enumerate(documents, 1):
        # Extract quality score from metadata or direct field
        quality_score = (
            doc.get("quality_score") or
            doc.get("metadata", {}).get("quality_score")
        )
        quality_grade = (
            doc.get("quality_grade") or
            doc.get("metadata", {}).get("quality_grade")
        )
        
        sources.append({
            "id": i,
            "file_path": doc["file_path"],
            "relevance_score": relevance_score,
            "adjusted_score": adjusted_score,
            "quality_score": quality_score,  # ✅ ADD THIS
            "quality_grade": quality_grade,  # ✅ ADD THIS
            "recency_days": doc.get("recency_days"),
            "updated_at": doc.get("updated_at")
        })
```

**Expected Impact:**
- Quality scores visible to users
- Can filter by quality in UI
- Better transparency
- Enable quality-based ranking

---

## Issue #3: Too Many Low-Quality Sources

### The Problem

**From analysis:**
```
⚠️  Average 9.6 sources per query (may be too many)
   → Quick win: Reduce n_results or apply stricter filtering
```

**Current behavior:**
- Retrieving 10 sources per query
- But 81% have low relevance (<0.4)
- This means ~8 out of 10 sources are noise!

### Quick Win #3A: Dynamic Source Count

**Location:** `services/ecosystem-mcp/src/services/rag/accuracy_enhanced_rag.py`

**Current:**
```python
initial_n_results = n_results * 2  # Always 20 for n_results=10
```

**Fix - Adaptive based on query complexity:**
```python
# Simple queries need fewer sources
if self._is_simple_query(question):
    initial_n_results = n_results  # 10 sources
else:
    initial_n_results = n_results * 1.5  # 15 sources (not 20)
```

### Quick Win #3B: Quality-Weighted Filtering

**Add after retrieval:**
```python
# Filter and sort by combined score
def _calculate_combined_score(doc):
    relevance = doc.get("hybrid_score", 0.5)
    quality = (doc.get("quality_score") or 50) / 100  # Normalize to 0-1
    return relevance * 0.7 + quality * 0.3  # Weighted combination

all_documents = sorted(all_documents, key=_calculate_combined_score, reverse=True)

# Keep only top N with good combined scores
COMBINED_THRESHOLD = 0.4
all_documents = [
    doc for doc in all_documents[:n_results]
    if _calculate_combined_score(doc) >= COMBINED_THRESHOLD
]
```

**Expected Impact:**
- Fewer sources (5-7 instead of 10)
- Higher average quality
- Less noise in context
- More focused answers

---

## Additional Quick Wins

### Quick Win #4: Boost High-Quality Sources

**Currently:** Quality boost is 0-15% max

**Opportunity:** Make quality impact stronger

**Location:** `services/ecosystem-mcp/src/services/rag/hybrid_search.py:282-297`

**Current:**
```python
boost_factor = 1.0 + (quality_score / 100) * 0.15  # Max 15% boost
```

**Enhanced:**
```python
# More aggressive quality boost
if quality_score >= 80:  # Grade A
    boost_factor = 1.25  # 25% boost
elif quality_score >= 70:  # Grade S
    boost_factor = 1.15  # 15% boost
elif quality_score >= 60:  # Grade B
    boost_factor = 1.05  # 5% boost
else:
    boost_factor = 0.95  # Slight penalty for low quality
```

**Expected Impact:** Better documents surface to top

---

### Quick Win #5: Penalize Stubs and Short Documents

**Add to scoring:**
```python
def _apply_length_penalty(self, documents):
    for doc in documents:
        content = doc.get("content", "")
        length = len(content)
        
        if length < 200:
            # Likely a stub or placeholder
            doc["hybrid_score"] *= 0.7  # 30% penalty
        elif length < 500:
            doc["hybrid_score"] *= 0.9  # 10% penalty
    
    return documents
```

**Expected Impact:** Reduce stub documents in results

---

### Quick Win #6: Add Confidence Threshold

**In confidence scorer:**
```python
# If overall confidence is LOW, warn user
if total_confidence < 50:
    recommendation = "⚠️ Low confidence. Consider:\n" \
                     "1. Rephrasing your question\n" \
                     "2. Adding more context\n" \
                     "3. Verifying the answer"
```

**Expected Impact:** Set user expectations

---

## Implementation Priority

### High Priority (Immediate - 1-2 hours)

1. **✅ Normalize RRF Scores** (Quick Win #1A)
   - **Impact:** Fixes broken relevance scoring
   - **Effort:** 10 lines of code
   - **Risk:** Low

2. **✅ Add Quality Scores to API** (Quick Win #2)
   - **Impact:** Enables quality-based decisions
   - **Effort:** 5 lines of code
   - **Risk:** None

3. **✅ Filter Low-Relevance Sources** (Quick Win #1B)
   - **Impact:** Remove noise from context
   - **Effort:** 3 lines of code
   - **Risk:** Low

### Medium Priority (Next day - 2-4 hours)

4. **✅ Quality-Weighted Filtering** (Quick Win #3B)
   - **Impact:** Better source selection
   - **Effort:** 15 lines of code
   - **Risk:** Low

5. **✅ Boost High-Quality Sources** (Quick Win #4)
   - **Impact:** Surface best documents
   - **Effort:** 10 lines of code
   - **Risk:** Low

### Low Priority (Future)

6. **Dynamic Source Count** (Quick Win #3A)
7. **Length Penalties** (Quick Win #5)
8. **Confidence Thresholds** (Quick Win #6)

---

## Expected Results

### Current State
- Average confidence: 65.4% (Phase 1+2+3)
- 81% sources have low relevance
- Quality scores invisible
- 10 sources per query (mostly noise)

### After Quick Wins
- **Estimated confidence: 70-75%** (+5-10%) ⚡⚡⚡
- <20% sources have low relevance
- Quality scores visible and used
- 5-7 high-quality sources per query

### Why This Works
1. **Better scoring** → Better ranking
2. **Quality filtering** → Less noise
3. **Fewer sources** → More focused context
4. **High-quality boost** → Best docs surface first

---

## Testing Plan

### Before Fixes
```bash
# Run current benchmark
python3 comprehensive_rag_test_all.py
# Save as baseline_before.json
```

### After Each Fix
```bash
# Apply fix
# Run benchmark again
python3 comprehensive_rag_test_all.py
# Compare results
```

### Success Metrics
- ✅ Average relevance score > 0.5 (currently 0.113)
- ✅ Average confidence > 70% (currently 65.4%)
- ✅ Quality scores visible in all responses
- ✅ Fewer sources per query (5-7 vs 10)
- ✅ Higher quality sources (avg quality > 60)

---

## Code Changes Required

### File 1: hybrid_search.py
**Changes:** 3
1. Normalize RRF scores (line ~246)
2. Filter low-relevance results (line ~280)
3. Enhance quality boost (line ~290)

### File 2: rag_service.py
**Changes:** 1
1. Add quality scores to _format_sources (line ~345)

### File 3: accuracy_enhanced_rag.py
**Changes:** 2
1. Add quality-weighted filtering (line ~200)
2. Dynamic source count (line ~180)

**Total Changes:** ~50 lines of code
**Estimated Time:** 2-3 hours
**Risk:** Low (all backward compatible)

---

## Conclusion

These **6 quick wins** address the root causes of low relevance scoring:

1. ✅ Fix broken RRF normalization
2. ✅ Expose quality scores
3. ✅ Filter low-relevance sources
4. ✅ Weight by quality
5. ✅ Boost high-quality documents
6. ✅ Reduce source count

**Expected Impact:** +5-10% confidence improvement with minimal code changes.

**Recommendation:** Implement high-priority fixes immediately (1-2 hours), then measure impact before proceeding to medium priority.

---

**Analysis Date:** October 31, 2025  
**Data Source:** 192 source citations across 20 queries  
**Priority:** HIGH - These fixes directly impact answer quality  
**Status:** Ready for implementation

