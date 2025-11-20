**Date:** November 20, 2025  
**Status:** Cache Invalidation Implementation Guide  
**Coverage:** Options 2 & 3 Combined Implementation  

# Cache Invalidation Implementation

## 🎯 Goal

Implement intelligent cache invalidation that:
1. **Automatically invalidates** when documents change (Option 2: Document hash)
2. **Explicitly invalidates** after ingestion (Option 3: Post-ingestion clearing)

## 📦 Components Created

### 1. Cache Invalidation Service
**File:** `src/services/rag/cache_invalidation.py`

**Features:**
- `get_document_hash()` - Generate hash from document count/timestamps
- `invalidate_service_cache()` - Clear cache for specific service
- `invalidate_all_rag_cache()` - Nuclear option to clear everything
- `get_cache_stats()` - Monitor cache usage

### 2. RAG Service Updates
**File:** `src/services/rag/rag_service.py`

**Changes Needed:**

```python
# 1. Add cache invalidation service to __init__
def __init__(self):
    self.router = get_ollama_router()
    self.chroma_service = get_chroma_service()
    self._cache_invalidation = None  # ✅ ADDED
    
def _get_cache_invalidation_service(self):
    """Get cache invalidation service (lazy initialization)."""
    if self._cache_invalidation is None:
        from .cache_invalidation import get_cache_invalidation_service
        self._cache_invalidation = get_cache_invalidation_service()
    return self._cache_invalidation

# 2. Update _get_cached_answer to include doc_hash
@cache(ttl=1800, key_prefix="rag_answer_v2")
async def _get_cached_answer(
    self,
    question: str,
    n_results: int,
    prefer_recent: bool,
    temperature: float,
    response_length: int,
    doc_hash: str = ""  # ✅ ADDED
) -> Optional[Dict[str, Any]]:
    # Cache key now includes doc_hash, auto-invalidating when docs change
    logger.debug(f"Cache check with doc_hash={doc_hash}")
    return None

# 3. Update ask() to add service_name and get doc_hash
async def ask(
    self,
    question: str,
    n_results: int = 10,
    context: Optional[List[Dict[str, Any]]] = None,
    prefer_recent: bool = True,
    temperature: float = 0.7,
    response_length: int = 1000,
    use_enhancements: Optional[bool] = None,
    enable_hybrid_search: Optional[bool] = None,
    enable_query_rewriting: Optional[bool] = None,
    enable_context_optimization: Optional[bool] = None,
    service_name: Optional[str] = None  # ✅ ADDED
) -> Dict[str, Any]:
    # Get document hash for cache key versioning
    cache_service = self._get_cache_invalidation_service()
    doc_hash = await cache_service.get_document_hash(service_name=service_name)
    
    # Check cache with doc_hash
    cached_answer = await self._get_cached_answer(
        question=question,
        n_results=n_results,
        prefer_recent=prefer_recent,
        temperature=temperature,
        response_length=response_length,
        doc_hash=doc_hash  # ✅ ADDED
    )
    
    # ... rest of ask() logic ...
    
    # When caching result, include doc_hash in key
    if cache_client:
        cache_key = f"rag_answer_v2:{question}:{n_results}:{prefer_recent}:{temperature}:{response_length}:{doc_hash}"  # ✅ UPDATED
        await cache_client.set(cache_key, result, ttl=1800)
```

### 3. Ingestion Hook
**File:** `src/services/ingestion/job_processor.py`

**Add after ingestion completes:**

```python
async def _complete_job(self, job: IngestionJob):
    """Complete ingestion job and invalidate cache."""
    # ... existing completion logic ...
    
    # ✅ Option 3: Explicit cache invalidation after ingestion
    try:
        from ..rag.cache_invalidation import get_cache_invalidation_service
        
        cache_service = get_cache_invalidation_service()
        
        # Get service name from job
        service_name = job.job_metadata.get('service_name') if job.job_metadata else None
        
        if service_name:
            # Invalidate cache for this specific service
            deleted_count = await cache_service.invalidate_service_cache(service_name)
            logger.info(
                f"✅ Cache invalidation: Cleared {deleted_count} entries "
                f"for service '{service_name}' after ingestion"
            )
        else:
            # Fallback: invalidate all RAG cache
            deleted_count = await cache_service.invalidate_all_rag_cache()
            logger.info(
                f"✅ Cache invalidation: Cleared {deleted_count} RAG entries "
                f"(no service name specified)"
            )
    
    except Exception as e:
        logger.error(f"⚠️ Cache invalidation failed: {e}", exc_info=True)
        # Don't fail the job if cache invalidation fails
```

## 🔧 Manual Implementation Steps

### Step 1: Update RAG Service Init
```bash
# File: src/services/rag/rag_service.py
# Line ~76

# Add after self.chroma_service initialization:
self._cache_invalidation = None  # Lazy init for cache invalidation
```

### Step 2: Add Cache Service Getter
```bash
# File: src/services/rag/rag_service.py
# Line ~81 (after __init__)

def _get_cache_invalidation_service(self):
    """Get cache invalidation service (lazy initialization)."""
    if self._cache_invalidation is None:
        from .cache_invalidation import get_cache_invalidation_service
        self._cache_invalidation = get_cache_invalidation_service()
    return self._cache_invalidation
```

### Step 3: Update _get_cached_answer Signature
```bash
# File: src/services/rag/rag_service.py
# Line ~82

# Add doc_hash parameter:
async def _get_cached_answer(
    self,
    question: str,
    n_results: int,
    prefer_recent: bool,
    temperature: float,
    response_length: int,
    doc_hash: str = ""  # NEW
) -> Optional[Dict[str, Any]]:
```

### Step 4: Update ask() Method
```bash
# File: src/services/rag/rag_service.py
# Line ~101

# Add service_name parameter to signature:
async def ask(
    ...existing params...,
    service_name: Optional[str] = None  # NEW
) -> Dict[str, Any]:

# After logger.info("📝 RAG query..."), add:
    # Get document hash for cache versioning
    cache_service = self._get_cache_invalidation_service()
    doc_hash = await cache_service.get_document_hash(service_name=service_name)
    logger.debug(f"Document hash for cache: {doc_hash}")

# Update cached_answer call (line ~151):
    cached_answer = await self._get_cached_answer(
        question=question,
        n_results=n_results,
        prefer_recent=prefer_recent,
        temperature=temperature,
        response_length=response_length,
        doc_hash=doc_hash  # NEW
    )
```

### Step 5: Update Cache Key Generation
```bash
# File: src/services/rag/rag_service.py
# Find where cache_key is built (search for "rag_answer_v2:")

# Update to include doc_hash:
cache_key = f"rag_answer_v2:{question}:{n_results}:{prefer_recent}:{temperature}:{response_length}:{doc_hash}"
```

### Step 6: Hook Into Ingestion
```bash
# File: src/services/ingestion/job_processor.py
# In _complete_job() method, after updating job status

# Add cache invalidation:
try:
    from ..rag.cache_invalidation import get_cache_invalidation_service
    
    cache_service = get_cache_invalidation_service()
    service_name = job.job_metadata.get('service_name') if job.job_metadata else None
    
    if service_name:
        deleted_count = await cache_service.invalidate_service_cache(service_name)
        logger.info(f"✅ Invalidated {deleted_count} cache entries for '{service_name}'")
    else:
        deleted_count = await cache_service.invalidate_all_rag_cache()
        logger.info(f"✅ Invalidated {deleted_count} RAG cache entries")

except Exception as e:
    logger.error(f"Cache invalidation failed: {e}", exc_info=True)
```

## 🧪 Testing

### Test 1: Document Hash Changes
```python
# Before ingestion
hash1 = await cache_service.get_document_hash("adminService")

# Ingest new documents
# ... ingestion ...

# After ingestion
hash2 = await cache_service.get_document_hash("adminService")

assert hash1 != hash2  # Hash should change
```

### Test 2: Cache Auto-Invalidation
```python
# Query before ingestion
result1 = await rag.ask("What is adminService?", service_name="adminService")
# Result cached with doc_hash_v1

# Ingest new documents
# ... ingestion ...

# Query after ingestion (same question)
result2 = await rag.ask("What is adminService?", service_name="adminService")
# Cache miss because doc_hash_v2 != doc_hash_v1
# Fresh query executed with new documents
```

### Test 3: Explicit Invalidation
```python
# Before invalidation
stats_before = await cache_service.get_cache_stats("adminService")

# Trigger ingestion completion
# ... ingestion completes ...
# Cache invalidation runs

# After invalidation
stats_after = await cache_service.get_cache_stats("adminService")

assert stats_after["total_cached_keys"] == 0  # All cleared
```

## 📊 How It Works

### Option 2: Document Hash (Automatic)

**Flow:**
1. User queries: "What is adminService overview?"
2. RAG gets document hash: `a1b2c3d4`
3. Cache key: `rag_answer_v2:What is...:10:True:0.7:1000:a1b2c3d4`
4. Result cached

**After ingestion:**
1. User queries same question
2. RAG gets NEW document hash: `e5f6g7h8` (different!)
3. Cache key: `rag_answer_v2:What is...:10:True:0.7:1000:e5f6g7h8`
4. Cache MISS (different hash) → Fresh query with new docs

**Benefits:**
- ✅ Automatic invalidation
- ✅ No manual clearing needed
- ✅ Works across services
- ✅ Still caches identical document sets

### Option 3: Explicit Invalidation (Surgical)

**Flow:**
1. Ingestion completes for "adminService"
2. Cache invalidation triggered
3. Searches Redis for: `*adminService*`
4. Deletes matching keys:
   - `rag_answer_v2:*adminService*`
   - `chroma_search:*adminService*`
   - `bm25_search:*adminService*`
5. Other services' cache unaffected

**Benefits:**
- ✅ Immediate invalidation
- ✅ Service-specific (surgical)
- ✅ Clears all related caches
- ✅ Doesn't wait for next query

### Combined Benefits

**Together, Options 2 + 3 provide:**
1. **Automatic protection** - Doc hash prevents stale data
2. **Immediate clearing** - Explicit invalidation for instant freshness
3. **Efficient caching** - Still benefits from cache between document changes
4. **Service isolation** - One service's ingestion doesn't affect others

## 🎯 Expected Behavior

### Before Implementation:
```
Query → Cache HIT → Stale "insufficient info" response
New docs ingested → Still cached → Still stale for 30 minutes
```

### After Implementation:
```
Query → Cache HIT (doc_hash_v1) → Cached response ✅
New docs ingested → 
  - Doc hash changes (v1 → v2)
  - Explicit invalidation clears old entries
Query → Cache MISS (doc_hash_v2) → Fresh query with new docs ✅
```

## ✅ Success Criteria

After implementation:
- ✅ Fresh data after every ingestion
- ✅ No 30-minute stale window
- ✅ Cache still provides performance benefits
- ✅ Service-specific invalidation
- ✅ No "insufficient info" on newly ingested services

## 📝 Rollback Plan

If issues occur:
1. Disable explicit invalidation (comment out Option 3 code)
2. Rely only on document hash (Option 2)
3. Or temporarily disable caching entirely:
   ```python
   @cache(ttl=0, ...)  # Effectively disables cache
   ```

---

**Status:** Implementation guide ready, awaiting manual integration
**Files Modified:** 3 (cache_invalidation.py created, rag_service.py, job_processor.py)
**Estimated Time:** 30-45 minutes

