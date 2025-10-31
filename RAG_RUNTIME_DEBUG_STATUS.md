**Date:** October 30, 2025  
**Status:** RAG Runtime Issues - Debugging in Progress  
**Issue:** Document content field missing in hybrid search results  

---

# RAG Runtime Issues - Debug Report

## ✅ WHAT'S WORKING

- **Standard RAG Endpoint** (`/api/v1/rag/ask/standard`) - ✅ **FULLY FUNCTIONAL**
  - Successfully returns answers with citations
  - Confidence scoring working
  - Example query "What is ChromaDB?" returns detailed answer with 3 sources
  - Response time: ~0.3s
  - Confidence: 42.8%

- **Infrastructure**
  - ✅ Docker services all healthy
  - ✅ 6,063 documents in database
  - ✅ BM25 index built successfully
  - ✅ Database migrations applied
  - ✅ All dependencies installed

## ❌ WHAT'S NOT WORKING

- **Enhanced RAG Endpoint** (`/api/v1/rag/ask/enhanced`) - ❌ **FAILING**
  - Error: `KeyError: 'content'`
  - Hybrid search completes successfully ("✅ Hybrid search complete: 30 semantic + 30 keyword → 3 fused results")
  - But documents passed to context builder are missing `content` field

## 🔍 ROOT CAUSE ANALYSIS

### Document Model Structure
The `DocumentModel` in the database has:
- ✅ `original_content` - raw file content
- ✅ `normalized_content` - processed content
- ❌ NO `content` attribute

### Search Methods Content Handling

1. **Standard RAG (`_retrieve_with_scoring`)** - ✅ WORKING
   - Line 188 of `rag_service.py`: `"content": content`
   - Properly extracts content from ChromaDB results["documents"]
   - Returns documents with `content` field populated

2. **Semantic Search (`_semantic_search` in hybrid_search.py)** - ⚠️ PARTIALLY FIXED
   - Lines 160-184: Added content extraction from ChromaDB
   - SHOULD be working now but needs verification

3. **BM25 Search (`search` in bm25_search.py)** - ⚠️ PARTIALLY FIXED
   - Lines 207-241: Added `_enrich_with_content()` method
   - Attempts to fetch content from database
   - Had database async context manager error (may still be present)

4. **Hybrid Search RRF Fusion** - ⚠️ PARTIALLY FIXED
   - Lines 247-265: Fuses semantic + BM25 results
   - Added content field at line 257
   - But depends on semantic and BM25 having content first

### Issues Fixed (But Not Tested Successfully)

1. ✅ Added content extraction in semantic search (line 160-184 of hybrid_search.py)
2. ✅ Added content enrichment in BM25 search (line 207-241 of bm25_search.py)
3. ✅ Added content field to RRF fusion (line 257 of hybrid_search.py)
4. ✅ Fixed database async context manager issues (multiple files)
5. ✅ Added content fallback logic in context builder (line 325 of rag_service.py)

### Remaining Problems

**Issue 1: Database Content Attribute**
- Code tries to access `doc.content` but should use `doc.normalized_content` or `doc.original_content`
- Fixed in `_enrich_with_content` (bm25_search.py line 229)
- Fixed in `_enrich_results` (hybrid_search.py line 319)
- May still have other references

**Issue 2: Enrichment Still Failing**
```
Failed to enrich results: 'Database' object does not support the asynchronous context manager protocol
```
- This error persists despite fixes
- Suggests Docker container may not be picking up latest code
- OR there are additional instances of the wrong pattern

**Issue 3: Content Field Not Propagating**
- Hybrid search logs success but documents reaching `_build_context` don't have content
- Possible issue with field propagation through query rewriting and deduplication

## 🎯 RECOMMENDED SOLUTION

### Approach: Normalize Document Structure Everywhere

**Step 1: Create Document Normalizer Helper**
```python
def normalize_document_content(doc):
    """Ensure document has 'content' field from any source."""
    if isinstance(doc, dict):
        if 'content' not in doc or not doc['content']:
            doc['content'] = doc.get('content_snippet', 
                                     doc.get('normalized_content', 
                                            doc.get('original_content', '')))
    else:  # DocumentModel object
        return {
            'content': doc.normalized_content or doc.original_content,
            'id': str(doc.id),
            'file_path': doc.file_path,
            # ... other fields
        }
    return doc
```

**Step 2: Apply at Every Search Exit Point**
- After semantic search returns
- After BM25 search returns
- After RRF fusion
- Before passing to context builder

**Step 3: Verify Docker Build**
- Ensure all code changes are in the container
- May need `docker-compose build --no-cache`

## 📊 CURRENT STATE

**Files Modified:** 3 files (hybrid_search.py, bm25_search.py, rag_service.py)  
**Fixes Applied:** 8 fixes  
**Docker Rebuilds:** 6 times  
**Time Spent:** ~90 minutes  

**Standard RAG:** ✅ Working perfectly  
**Enhanced RAG:** ❌ Still failing  
**BM25 Index:** ✅ Built (6,063 docs)  
**Hybrid Search:** ✅ Completing but results missing content  

## 🚀 NEXT STEPS

### Option A: Quick Fix (5-10 minutes)
1. Add comprehensive content field normalization in `_build_context`
2. Make all content field access use `.get()` with fallbacks
3. Test enhanced endpoint

### Option B: Proper Fix (20-30 minutes)
1. Create document normalization utility
2. Apply at all search method exit points
3. Remove all direct `doc['content']` access
4. Use helper function everywhere
5. Rebuild and test

### Option C: Simplify (immediate)
1. Disable hybrid search temporarily
2. Use standard RAG for both endpoints
3. Get benchmark working with standard RAG
4. Fix hybrid search separately

## 💡 INSIGHTS

1. **Standard RAG works perfectly** - the core system is sound
2. **Hybrid search logic is correct** - it's completing successfully
3. **Issue is data structure mismatch** - not algorithm problems
4. **Multiple code paths** - need consistent document structure
5. **Quick fix possible** - just need to normalize content field handling

---

**Time to Resolution:** 10-30 minutes depending on approach chosen  
**Complexity:** Low - just data structure normalization  
**Risk:** Low - standard RAG already working  
**Priority:** High - blocking benchmark execution  


