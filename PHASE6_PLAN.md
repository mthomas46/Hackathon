# Phase 6: Multi-Pass RAG Integration - Implementation Plan

## Analysis

### Current Multi-Pass RAG (820 lines)
**Status:** Partially prepared (has `use_enhancements` flag but defaults to False)

**Key Features:**
1. Complex query decomposition into sections (N passes)
2. Secondary question generation (M questions per section)
3. Parallel question processing
4. Section-level synthesis
5. Final comprehensive synthesis
6. Progress tracking

**Current Flow (N×M queries):**
```
Complex Query
  └─> Decompose into N Sections
       └─> Generate M Questions per Section  
            └─> Ask N×M RAG Queries (parallel)
                 └─> Synthesize Section Results
                      └─> Final Synthesis
```

### Phase 6 Integration Strategy

**Updated Flow with EnhancementPipeline:**
```
Complex Query
  └─> Decompose into N Sections
       └─> Generate M Questions per Section
            └─> [Enhanced] Ask N×M RAG Queries
                 ├─> Use multipass_default config
                 ├─> Hybrid search (but NO reranking)
                 ├─> NO query rewriting (questions already specific)
                 ├─> Context optimization (critical for N×M)
                 └─> Per-question confidence tracking
                      └─> Synthesize with confidence weights
                           └─> Final Synthesis
```

**Key Changes:**
1. Add `self.multipass_enhancement_config` in `__init__`
2. Change default `use_enhancements=True`
3. Pass enhancement config to section processing
4. Use Enhanced RAG service properly
5. Maintain backward compatibility

## Implementation Steps

### 1. Update `__init__` (5 min)
```python
def __init__(self):
    self.rag_service = get_rag_service()
    self.enhanced_rag_service = get_enhanced_rag_service()  # NEW
    self.ollama_router = get_ollama_router()
    
    # ✨ PHASE 6: Pre-configured enhancement config
    from .enhancements import EnhancementConfig
    self.multipass_enhancement_config = EnhancementConfig.multipass_default()
```

### 2. Update `process_query` Signature (2 min)
- Change default: `use_enhancements=True` (from False)
- Add parameter: `enhancement_config: Optional[EnhancementConfig] = None`

### 3. Update Section Processing (10 min)
- Pass `rag_service` and `config` to `_process_section`
- Use appropriate service (enhanced vs standard)
- Apply `multipass_default` config

### 4. Test (15 min)
- Run multi-pass query with enhancements
- Validate N×M queries use hybrid search
- Verify no reranking (too expensive for N×M)
- Check answer quality

## Expected Improvements

| Metric | Current | Phase 6 | Improvement |
|--------|---------|---------|-------------|
| Sources/question | ~5 | ~8 | +60% |
| Synthesis Quality | Good | Better | Enhanced sources |
| Query Cost | N×M | N×M | Same (but better quality) |
| Reranking | Optional | Disabled | Faster (optimized for N×M) |

## Key Optimization

**Why `multipass_default` disables features:**
- **N×M queries:** 3 passes × 3 questions = 9 total queries
- **Reranking:** Would add 9× reranking overhead = TOO EXPENSIVE
- **Query rewriting:** Questions already specific from LLM = UNNECESSARY
- **Hybrid search:** Enabled for better per-question coverage = VALUABLE
- **Context optimization:** Critical for managing tokens across N×M = ESSENTIAL

## Risks & Mitigations

**Risk 1:** N×M queries might be slow with enhancements  
**Mitigation:** `multipass_default` disables expensive features (reranking, rewriting)

**Risk 2:** Breaking existing multi-pass queries  
**Mitigation:** Keep backward compatibility, add config parameter

**Risk 3:** Synthesis might not improve  
**Mitigation:** Test and validate, can disable if needed

## Files to Modify

1. `multi_pass_query.py` - Main refactoring
2. `enhancement_config.py` - Verify multipass_default preset (already exists ✅)
3. `test_phase6_multipass.py` - New test suite

## Success Criteria

✅ Multi-pass queries use enhancements by default  
✅ N×M queries optimized (no reranking)  
✅ Hybrid search active for better coverage  
✅ Context optimization manages N×M token budget  
✅ Backward compatible (can disable enhancements)  
✅ All tests passing

## Time Estimate

- Analysis: Already done ✅
- Implementation: ~20 min
- Testing: ~15 min
- Documentation: ~10 min
**Total: ~45 minutes**

