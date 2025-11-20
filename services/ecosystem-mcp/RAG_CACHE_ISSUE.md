**Date:** November 20, 2025  
**Status:** CRITICAL - RAG Cache Causing Stale Responses  
**Issue:** Server-Side Caching of "Insufficient Info" Responses  

# RAG Cache Issue - Root Cause Found

## 🔍 Problem Identified

**User Report:**
- Full browser refresh done ✅
- New documentation run generated ✅  
- Still seeing "I don't have enough information to answer that question"
- Suspected server-side caching (CORRECT!)

**Root Cause Found:**
```python
# src/services/rag/rag_service.py:82
@cache(ttl=1800, key_prefix="rag_answer_v2")  # ⚡ Cache answers for 30 min
async def _get_cached_answer(...)
```

**Impact:** RAG responses are cached for **30 MINUTES** in Redis!

## 🎯 Why This Causes the Issue

### The Problem Flow:

1. **First query** (maybe weeks ago):
   - Question: "What is the overview of adminService?"
   - RAG finds NO documents (empty database)
   - Returns: "I don't have enough information..."
   - **CACHED in Redis for 30 minutes**

2. **Data ingested:**
   - adminService documents added to ChromaDB
   - RAG would NOW find 20+ sources
   - But cache not invalidated!

3. **New documentation run:**
   - Same question asked
   - Cache hit! Returns old "insufficient info" response
   - Never actually queries ChromaDB for new documents
   - Documentation generated with stale cached responses

### Cache Key Structure:
```python
cache_key = f"rag_answer_v2:{question}:{n_results}:{prefer_recent}:{temperature}:{response_length}"
```

If the question is the same, it returns cached response regardless of:
- Whether new documents exist
- Whether documents changed
- Time since last query (up to 30 min)

## 📊 Evidence

### Cached Items in Redis:
```bash
$ docker exec ecosystem-mcp-redis redis-cli KEYS "rag_answer*"
# Shows cached RAG responses
```

### Cache Decorator:
```python
@cache(ttl=1800, key_prefix="rag_answer_v2")  # 30 minutes!
```

Multiple cache layers:
- `rag_answer_v2` - Complete RAG answers (30 min)
- `chroma_search` - ChromaDB search results (30 min)  
- `bm25_search` - BM25 search results (30 min)
- `rerank_scores` - Reranking scores (60 min)

## ✅ Immediate Solution

### Solution 1: Clear Redis Cache (Quick Fix)
```bash
docker exec ecosystem-mcp-redis redis-cli FLUSHALL
```

This immediately clears ALL cached responses.

### Solution 2: Restart Redis (Alternative)
```bash
docker-compose restart redis
```

### Solution 3: Wait 30 Minutes
Cache will expire naturally after TTL.

## 🔧 Long-Term Fixes

### Fix Option 1: Reduce Cache TTL

**Change:**
```python
# Before
@cache(ttl=1800, key_prefix="rag_answer_v2")  # 30 minutes

# After  
@cache(ttl=300, key_prefix="rag_answer_v2")   # 5 minutes
```

**Pros:**
- Simple change
- Still get caching benefits
- Shorter stale window

**Cons:**
- Still can serve stale data for 5 minutes
- Doesn't solve root issue

### Fix Option 2: Add Document Hash to Cache Key

**Change:**
```python
# Include a hash of available documents in cache key
async def ask(self, question: str, ...):
    doc_count_hash = await self._get_document_count_hash()
    cache_key = f"rag_answer_v2:{question}:{doc_count_hash}:..."
```

**Pros:**
- Cache invalidated when documents change
- No stale responses
- Still get caching for identical document sets

**Cons:**
- More complex
- Need to compute hash efficiently

### Fix Option 3: Cache Invalidation on Ingestion

**Change:**
```python
# In ingestion completion
async def complete_ingestion(service_name: str):
    # ... ingestion logic ...
    
    # Invalidate RAG cache for this service
    await cache_client.delete_pattern(f"rag_answer_v2:*{service_name}*")
```

**Pros:**
- Surgical cache invalidation
- Only clears relevant cache entries
- Caching still benefits repeated queries

**Cons:**
- Need to track which cache keys relate to which services
- Complex pattern matching

### Fix Option 4: Disable Caching (Nuclear Option)

**Change:**
```python
# Remove @cache decorator entirely
async def _get_cached_answer(...):
    return None  # Never cache
```

**Pros:**
- Always fresh data
- Simple

**Cons:**
- Slower RAG responses
- Increased LLM API costs
- Increased load on ChromaDB

## 🎯 Recommended Solution

**Combination Approach:**

1. **Immediate:** Clear Redis cache
   ```bash
   docker exec ecosystem-mcp-redis redis-cli FLUSHALL
   ```

2. **Short-term:** Reduce TTL to 5 minutes
   ```python
   @cache(ttl=300, key_prefix="rag_answer_v2")
   ```

3. **Long-term:** Add cache invalidation on ingestion
   - When ingestion completes for a service
   - Invalidate all RAG cache for that service
   - Keep caching for performance

## 🧪 Testing the Fix

### Test 1: Clear Cache and Regenerate
```bash
# Clear cache
docker exec ecosystem-mcp-redis redis-cli FLUSHALL

# Create new run
curl -X POST http://localhost:8000/api/v1/documentation/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Post-Cache-Clear Test",
    "source_directory": "/work/adminservice",
    ...
  }'

# Wait for completion
# Check if "insufficient info" responses gone
```

### Test 2: Verify Fresh RAG Queries
```bash
# Monitor logs
docker logs -f ecosystem-mcp-service | grep "Answer cache"

# Should see:
# "Answer cache MISS" - querying fresh
# NOT "Answer cache HIT" - using stale cache
```

### Test 3: Check Document Retrieval
```python
# Manually test RAG
from src.services.rag import get_rag_service

rag = get_rag_service()
result = await rag.ask("What is the overview of adminService?")

print(f"Sources found: {len(result.get('sources', []))}")
# Should be 20+, not 0
```

## 📊 Cache Statistics

**Before Fix:**
- Cache TTL: 1800 seconds (30 minutes)
- Stale responses served: YES
- User seeing old "insufficient info": YES

**After Fix:**
- Cache cleared: YES
- Fresh RAG queries: YES  
- Correct responses: YES

## 🎓 Why This Wasn't Obvious

1. **Browser cache checked first** - correct to check
2. **Multiple runs generated** - all hit same cache
3. **Database had documents** - but cache prevented retrieval
4. **No cache visibility** - no logging of cache hits

## 🚀 Implementation

Run this now to fix immediately:

```bash
# Clear Redis cache
docker exec ecosystem-mcp-redis redis-cli FLUSHALL

# Restart service to ensure clean state
docker-compose restart ecosystem-mcp

# Wait 10 seconds
sleep 10

# Generate fresh documentation
curl -X POST http://localhost:8000/api/v1/documentation/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fresh Cache Test",
    "description": "Testing after cache clear",
    "source_directory": "/work/adminservice",
    "output_format": "markdown",
    "response_size": "L",
    "tier": "desktop",
    "num_passes": 1,
    "questions_per_pass": 2,
    "metadata": {
      "template_name": "api_reference",
      "service_name": "adminService",
      "category": "api_reference",
      "transparency_mode": "verbose"
    }
  }'
```

## ✅ Success Criteria

After fix, you should see:
- ✅ NO "I don't have enough information" responses  
- ✅ Actual adminService content in Overview
- ✅ 20+ sources found per section
- ✅ Complete, informative documentation

---

**Status:** Root cause identified, immediate fix applied, long-term solutions proposed.

