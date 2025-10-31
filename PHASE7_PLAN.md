# Phase 7: Dynamic Temporal RAG Enhancement - Implementation Plan

## Analysis

### Current Dynamic Temporal RAG (2085 lines across 6 modules)

**Architecture:** Specialized pipeline with custom components
- `orchestrator.py` (270 lines) - Main orchestration
- `document_finder.py` (399 lines) - **KEY ENHANCEMENT POINT**
- `topic_extractor.py` - Topic extraction from queries
- `dynamic_timeline_constructor.py` - Timeline building
- `answer_synthesizer.py` - **KEY ENHANCEMENT POINT**
- `citation_formatter.py` - Citation formatting

**Current Flow:**
```
Query → Topic Extraction → Document Finding → Timeline Construction → Answer Synthesis → Citations
```

**Current Limitations:**
- ❌ Document finding uses **semantic search only** (no BM25/hybrid)
- ❌ No query rewriting/expansion
- ❌ No quality boost for document selection
- ❌ Answer synthesis doesn't use confidence scoring
- ❌ No enhancement pipeline integration

### Integration Strategy

**Key Insight:** Dynamic Temporal RAG is too specialized for full EnhancementPipeline integration. Instead, enhance the two critical components:

1. **DocumentFinder** - Add hybrid search + query rewriting
2. **AnswerSynthesizer** - Add confidence scoring (optional - low priority)

## Phase 7 Implementation

### Task 1: Enhance DocumentFinder (20 min)

**Goal:** Add hybrid search and query rewriting to document finding

**Changes to `document_finder.py`:**

```python
class DocumentFinder:
    def __init__(self):
        # Existing code...
        
        # ✨ PHASE 7: Add enhancement services
        from ..rag.hybrid_search import get_hybrid_search_service
        from ..rag.query_rewriter import get_query_rewriter
        
        self.hybrid_search = get_hybrid_search_service()
        self.query_rewriter = get_query_rewriter()
        self.use_enhancements = True  # Can be toggled
    
    async def find_relevant_documents(
        self,
        search_terms: List[str],
        service_name: Optional[str] = None,
        limit: int = 50,
        use_enhancements: bool = True  # ✨ NEW parameter
    ):
        if not use_enhancements or not self.use_enhancements:
            # Fallback to existing semantic search
            return await self._semantic_search(...)
        
        # ✨ PHASE 7: Enhanced document finding
        all_documents = []
        
        # 1. Query rewriting (expand search terms)
        expanded_terms = []
        for term in search_terms:
            rewrite_result = await self.query_rewriter.rewrite(
                term,
                enable_expansion=True,  # Expand synonyms
                enable_clarification=False,  # Terms already specific
                enable_decomposition=False  # Don't split
            )
            expanded_terms.extend(rewrite_result["search_queries"][:2])
        
        # 2. Hybrid search for each term
        for term in expanded_terms:
            results = await self.hybrid_search.search(
                query=term,
                n_results=limit,
                semantic_weight=0.7,
                keyword_weight=0.3,
                where={"service_name": service_name} if service_name else None,
                quality_boost=True  # ✅ Quality-aware
            )
            all_documents.extend(results)
        
        # 3. Deduplicate and convert to RelevantDocument
        unique_docs = self._deduplicate(all_documents)
        return self._convert_to_relevant_docs(unique_docs[:limit])
```

### Task 2: Update Orchestrator to Support Enhancements (5 min)

**Changes to `orchestrator.py`:**

```python
async def execute(
    self,
    query: str,
    service_name: Optional[str] = None,
    citation_format: str = "markdown",
    use_cache: bool = True,
    use_enhancements: bool = True  # ✨ NEW parameter
) -> Dict:
    # ... existing steps ...
    
    # Step 2: Find relevant documents (with enhancements)
    documents = await self.document_finder.find_relevant_documents(
        search_terms=search_terms,
        service_name=service_name,
        limit=50,
        use_enhancements=use_enhancements  # ✨ Pass through
    )
```

## Expected Improvements

| Metric | Before | Phase 7 | Improvement |
|--------|--------|---------|-------------|
| Document Retrieval | Semantic only | Hybrid (70/30) | +40-60% recall |
| Query Coverage | Original terms | Expanded synonyms | +2-3× coverage |
| Quality Weighting | None | Quality boost | Better sources |
| Speed | Fast | Similar | ~Same (parallel) |

## Key Benefits

✅ **Better Document Finding:** Hybrid search finds more relevant docs  
✅ **Query Expansion:** Catch synonyms and related terms  
✅ **Quality Boost:** Prioritize high-quality documents  
✅ **Backward Compatible:** Can disable enhancements  
✅ **Minimal Changes:** Only 2 files modified

## Files to Modify

1. `document_finder.py` (~50 lines added)
2. `orchestrator.py` (~5 lines added)

## Testing Strategy

1. Test enhanced document finding with sample topics
2. Validate query expansion is working
3. Compare document quality before/after
4. Verify backward compatibility (enhancements OFF)

## Time Estimate

- Document Finder: ~20 min
- Orchestrator: ~5 min
- Testing: ~15 min
- Documentation: ~10 min
**Total: ~50 minutes**

## Why Not Full Pipeline Integration?

Dynamic Temporal RAG has specialized components:
- **Topic Extractor** - Custom LLM prompt (not a query)
- **Timeline Constructor** - Git history-based (not documents)
- **Answer Synthesizer** - Temporal context (different from RAG)

These don't fit the standard EnhancementPipeline model. Instead, we enhance the components that DO benefit (DocumentFinder).

## Success Criteria

✅ DocumentFinder uses hybrid search + query rewriting  
✅ Enhanced mode finds 40-60% more relevant documents  
✅ Query expansion catches synonyms  
✅ Backward compatible (can disable)  
✅ All tests passing  
✅ Production-ready

---

**Status:** Ready to implement  
**Risk:** Low (minimal changes, clear benefits)  
**Impact:** High (better document finding = better answers)

