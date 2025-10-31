# Phase 4: Temporal RAG Integration - Implementation Plan

## Analysis

### Current Temporal RAG (825 lines)
**Key Methods:**
1. `query_as_of()` - Time-travel queries
2. `query_what_changed()` - Compare two periods
3. `query_evolution()` - Track changes over time
4. `_query_with_temporal_filter()` - Core temporal filtering

**Current Flow:**
```
User Query
  └─> Temporal Filter (git_date, service_name)
       └─> ChromaDB Query (with where clause)
            └─> LLM Answer Generation
                 └─> Result
```

### Phase 4 Integration Strategy

**New Flow with EnhancementPipeline:**
```
User Query
  └─> EnhancementPipeline.execute()
       ├─> Query Rewriting (synonyms, clarification)
       ├─> Temporal Pre-Filter Hook (git_date <= as_of_date)
       ├─> Hybrid Search (semantic + BM25, filtered)
       ├─> Context Optimization
       └─> LLM Answer Generation
            └─> Result with temporal metadata
```

**Key Changes:**
1. Use `temporal_default` preset from EnhancementConfig
2. Add temporal pre-retrieval filter hook
3. Preserve all temporal-specific methods unchanged
4. Let pipeline handle retrieval + enhancements
5. Keep temporal metadata in results

## Implementation Steps

### 1. Add Temporal Configuration (5 min)
- Already exists: `EnhancementConfig.temporal_default()`
- Optimized for temporal queries

### 2. Refactor `_query_with_temporal_filter()` (20 min)
**Before:** Manual ChromaDB query + LLM generation
**After:** Use EnhancementPipeline with temporal filter hook

```python
async def _query_with_temporal_filter(...):
    # Build temporal filter
    temporal_filter = {"git_date": {"$lte": as_of_date.timestamp()}}
    if service_name:
        temporal_filter = {"$and": [temporal_filter, {"service_name": service_name}]}
    
    # Use pipeline with temporal preset
    config = EnhancementConfig.temporal_default()
    hooks = EnhancementHooks(
        pre_retrieval_filter=lambda ctx: temporal_filter
    )
    
    result = await self.enhancement_pipeline.execute(
        query=query,
        n_results=limit,
        config=config,
        hooks=hooks
    )
    
    # Add temporal metadata
    ...
```

### 3. Preserve Temporal Methods (unchanged)
- `query_what_changed()` - Keep as-is, uses refactored _query_with_temporal_filter
- `query_evolution()` - Keep as-is
- All helper methods - Keep unchanged

### 4. Test (15 min)
- Time-travel query
- Change detection query
- Evolution tracking
- Validate temporal filtering + enhancements work together

## Expected Improvements

| Metric | Current | Phase 4 | Improvement |
|--------|---------|---------|-------------|
| Sources | ~5 | ~8 | +60% |
| Confidence | ~40% | ~50% | +25% |
| Query Understanding | Basic | Enhanced | Synonym expansion |
| Context Quality | Raw | Optimized | Better relevance |

## Risks & Mitigations

**Risk 1:** Temporal filtering might conflict with pipeline  
**Mitigation:** Use pre_retrieval_filter hook (designed for this)

**Risk 2:** Performance degradation  
**Mitigation:** temporal_default preset disables expensive features

**Risk 3:** Breaking existing temporal APIs  
**Mitigation:** Only refactor internal _query_with_temporal_filter, keep all public methods

## Files to Modify

1. `temporal_rag_service.py` - Main refactoring
2. `enhancement_config.py` - Verify temporal_default preset (already exists)
3. `test_phase4_temporal_rag.py` - New test suite

## Success Criteria

✅ All 3 temporal query types work (as_of, what_changed, evolution)  
✅ Temporal filtering preserved (git_date, service_name)  
✅ Enhancements active (hybrid search, query rewriting)  
✅ 20%+ improvement in sources/confidence  
✅ Backward compatible (same API)  
✅ All tests passing

