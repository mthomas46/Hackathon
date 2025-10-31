# Phase 5: Context-Aware RAG Integration - Implementation Plan

## Analysis

### Current Context-Aware RAG (632 lines)
**Status:** Partially prepared (imports added, pipeline initialized, but not used)

**Key Features:**
1. Hierarchical context filtering (ROOT/SERVICE/MODULE/COMPONENT)
2. Repository-specific filtering
3. Technology stack awareness
4. Service-level isolation
5. Time range filtering
6. Language filtering

**Current Flow:**
```
User Query + Filters
  └─> Build Where Clause (context filters)
       └─> ChromaDB Query (with where clause)
            └─> Enhance with Context Info
                 └─> Calculate Relevance Scores
                      └─> Return Raw Results (NO LLM ANSWER)
```

### Phase 5 Integration Strategy

**New Flow with EnhancementPipeline:**
```
User Query + Filters
  └─> Build Where Clause (context filters)
       └─> EnhancementPipeline.execute()
            ├─> Query Rewriting (synonyms, clarification)
            ├─> Context Pre-Filter Hook (repo_id, service, tech, etc.)
            ├─> Hybrid Search (semantic + BM25, filtered)
            ├─> Context Optimization
            └─> LLM Answer Generation
                 └─> Result with context metadata
```

**Key Changes:**
1. Use `context_aware_default` preset from EnhancementConfig
2. Add context pre-retrieval filter hook
3. **Add LLM answer generation** (currently missing!)
4. Keep all context filtering logic
5. Return results with answer + context metadata

## Implementation Steps

### 1. Refactor `query_with_context()` (30 min)
**Before:** Manual ChromaDB query + raw results
**After:** Use EnhancementPipeline + LLM answer

```python
async def query_with_context(...):
    # Build context filter
    where_clause = self._build_where_clause(...)
    
    # Use pipeline with context preset
    if self.use_enhancements:
        config = EnhancementConfig.context_aware_default()
        
        async def context_filter(ctx):
            return where_clause
        
        hooks = EnhancementHooks(
            pre_retrieval_filter=context_filter
        )
        
        result = await self.enhancement_pipeline.execute(
            query=query,
            n_results=limit,
            config=config,
            hooks=hooks
        )
        
        # Add answer generation (NEW!)
        answer = await self._generate_answer(result["documents"], query, context)
        
        return {
            "query": query,
            "answer": answer,  # NEW!
            "sources": result["documents"],
            "filters": {...},
            "context_info": {...},
            "metadata": {...}
        }
    else:
        # Legacy fallback
        ...
```

### 2. Add Answer Generation Method (15 min)
Currently missing! Need to add:
```python
async def _generate_answer(self, documents, query, context):
    """Generate LLM answer from context-filtered documents."""
    # Build context text
    # Create context-aware prompt
    # Call LLM
    # Return answer
```

### 3. Preserve Helper Methods (unchanged)
- `_build_where_clause()` - Keep as-is
- `_enhance_with_context()` - Keep as-is
- `_calculate_relevance_scores()` - Keep as-is
- All other helpers - Keep unchanged

### 4. Test (15 min)
- Query with repo_id filter
- Query with service filter
- Query with tech stack filter
- Query with hierarchical context
- Validate filtering + enhancements work together

## Expected Improvements

| Metric | Current | Phase 5 | Improvement |
|--------|---------|---------|-------------|
| Answer Generation | ❌ None | ✅ LLM | NEW feature! |
| Sources | ~5 | ~8 | +60% |
| Query Understanding | Basic | Enhanced | Synonym expansion |
| Context Quality | Filtered | Optimized | Better relevance |

## Key Difference from Phase 4

**Phase 4 (Temporal):** Already had LLM answer generation
**Phase 5 (Context-Aware):** Missing LLM answer - need to add it!

This makes Phase 5 even more valuable - not just enhancements, but completing the feature.

## Risks & Mitigations

**Risk 1:** Context filtering might conflict with pipeline  
**Mitigation:** Use pre_retrieval_filter hook (proven in Phase 4)

**Risk 2:** Multiple filter types (repo, service, tech, etc.)  
**Mitigation:** _build_where_clause already handles this perfectly

**Risk 3:** Breaking existing context-aware queries  
**Mitigation:** Keep all public methods, add dual-mode operation

## Files to Modify

1. `context_aware_rag.py` - Main refactoring
2. `enhancement_config.py` - Verify context_aware_default preset (already exists)
3. `test_phase5_context_aware.py` - New test suite

## Success Criteria

✅ Context-aware queries work with all filter types  
✅ LLM answer generation added (NEW!)  
✅ Enhancements active (hybrid search, query rewriting)  
✅ Context filtering preserved (repo, service, tech, etc.)  
✅ 20%+ improvement in sources  
✅ Backward compatible (same API)  
✅ All tests passing
