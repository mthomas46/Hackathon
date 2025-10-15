# 🐛 Missing Embeddings Issue - ChromaDB Circuit Breaker

**Date:** October 14, 2025  
**Job:** `2030f30a-d42c-4bf6-a4cc-6ce84cbb8d8e`  
**Issue:** 326 documents stored, 0 embeddings created  
**Root Cause:** ChromaDB circuit breaker OPEN due to collection ID mismatch  
**Status:** **IDENTIFIED - NEEDS FIX**

---

## 📊 Problem Summary

### What Happened
```
Job Results:
- Documents stored in PostgreSQL: 326 ✅
- Embeddings stored in ChromaDB: 0 ❌
- Embedding coverage: 0.0%

Error in logs:
❌ Failed to add embeddings (attempt 1/3): Circuit breaker 'chromadb' is OPEN
❌ Failed to add embeddings (attempt 2/3): Circuit breaker 'chromadb' is OPEN
❌ Failed to add embeddings (attempt 3/3): Circuit breaker 'chromadb' is OPEN
```

**Result:** Documents saved but embeddings completely failed.

---

## 🔍 Root Cause Analysis

### 1. Circuit Breaker Was OPEN

During ingestion, all embedding storage attempts failed with:
```
Circuit breaker 'chromadb' is OPEN
```

This means the circuit breaker detected too many failures and stopped allowing requests to ChromaDB.

---

### 2. What Triggered the Circuit Breaker?

Health check failures due to **collection ID mismatch**:

```
Health check looking for: Collection [262027bd-e1f6-4bdd-acd5-aae5651efe19]
Actual collection ID:     Collection [e7e83c9a-512a-4f71-ab33-251de0fbc5f6]

Error: Collection [262027bd...] does not exists.
```

**The health check is looking for the wrong collection!**

---

### 3. Why the Mismatch?

Possible causes:
1. **Collection was recreated** at some point with new ID
2. **Health check cached old collection ID**
3. **Multiple ChromaDB instances** with different collections
4. **Collection ID hardcoded** in health check instead of dynamic lookup

---

## 📋 Current State

### ChromaDB Collection

```
Name: ecosystem_docs
ID: e7e83c9a-512a-4f71-ab33-251de0fbc5f6
Count: 0 embeddings
Metadata:
  - description: Ecosystem MCP documents with 384-dim embeddings
  - embedding_model: all-MiniLM-L6-v2
  - embedding_dimensions: 384
```

**Collection exists but is empty!**

---

### PostgreSQL

```
Documents: 2,694
Latest ingestion: 326 documents (all skipped as duplicates)
All documents have content but NO embeddings
```

---

### Circuit Breaker

```
State: OPEN (blocking requests)
Failure count: > 5 (threshold exceeded)
Reason: Collection ID mismatch in health checks
Impact: All embedding operations blocked
```

---

## 🔧 Impact

### What Works ✅
- ✅ Document ingestion (PostgreSQL)
- ✅ Content hash duplicate detection
- ✅ Git commit tracking
- ✅ Metadata storage
- ✅ Document querying

### What's Broken ❌
- ❌ Embedding generation (blocked)
- ❌ Vector similarity search
- ❌ Semantic search
- ❌ RAG queries (will fail)
- ❌ Embedding-based features

---

## 🛠️ Solution

### Immediate Fix Required

#### 1. Fix Health Check Collection ID

**Problem:**
```python
# Health check uses hardcoded or cached collection ID
collection_id = "262027bd-e1f6-4bdd-acd5-aae5651efe19"  # OLD/WRONG
```

**Solution:**
```python
# Health check should use dynamic collection lookup
chroma_client = get_chroma_client()
collection = chroma_client.collection  # Uses actual collection
collection_id = collection.id  # Gets current ID dynamically
```

#### 2. Reset Circuit Breaker

The circuit breaker needs to be reset or allowed to recover:

**Option A: Wait for timeout**
- Circuit breaker timeout: 30 seconds
- Will automatically attempt recovery

**Option B: Restart service**
```bash
docker restart ecosystem-mcp-service
```

**Option C: Manual reset** (if implemented)
```bash
curl -X POST http://localhost:8000/api/v1/admin/circuit-breaker/chromadb/reset
```

---

### Long-Term Fixes

#### 1. Fix Health Check Logic

Location: Likely in `src/storage/chromadb_client.py` or health check module

**Current (broken):**
```python
async def health_check():
    # Checks hardcoded collection ID
    collection = client.get_collection(id="262027bd...")  # ❌ Wrong
```

**Fixed:**
```python
async def health_check():
    # Uses actual collection
    chroma_client = get_chroma_client()
    collection = chroma_client.collection  # ✅ Correct
    count = collection.count()
    return {"status": "healthy", "count": count}
```

---

#### 2. Regenerate Missing Embeddings

Since 2,694 documents exist without embeddings, we need to generate them:

**Option A: Force Re-Ingestion**
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/app", "mode": "full", "force_reingest": true}'
```

**Option B: Batch Embedding Generation**
```python
# Create script to generate embeddings for existing documents
async def generate_missing_embeddings():
    docs = await doc_repo.get_documents_without_embeddings()
    for doc in docs:
        embedding = await embedding_service.generate(doc.content)
        await chroma_client.add_embeddings([embedding], ...)
```

**Option C: Background Job**
- Add background worker to detect and fix missing embeddings
- Run periodically to ensure consistency

---

## 🧪 Verification Steps

### 1. Check Circuit Breaker State
```bash
curl http://localhost:8000/health | jq '.dependencies.chromadb'
```

### 2. Verify Collection ID
```bash
docker exec ecosystem-mcp-service python3 -c "
from src.storage.chromadb_client import get_chroma_client
chroma = get_chroma_client()
print(f'Collection ID: {chroma.collection.id}')
print(f'Count: {chroma.collection.count()}')
"
```

### 3. Test Embedding Storage
```bash
# Try to add a test embedding
curl -X POST http://localhost:8000/api/v1/test/embedding \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

### 4. Monitor Logs
```bash
docker logs ecosystem-mcp-service -f | grep -E "(circuit breaker|embedding|chromadb)"
```

---

## 📈 Expected After Fix

### Immediate
- ✅ Circuit breaker: CLOSED
- ✅ Health checks: Passing
- ✅ Embedding storage: Working

### After Re-Ingestion
```
Before:
  Documents: 2,694
  Embeddings: 0
  Coverage: 0%

After:
  Documents: 2,694
  Embeddings: 2,694
  Coverage: 100%
```

---

## 🎯 Priority

**HIGH PRIORITY** 🔴

**Why:**
- Blocks ALL embedding-based features
- Impacts RAG queries
- No semantic search capability
- System partially non-functional

**Timeline:**
- Immediate: Restart service (temporary fix)
- Short-term: Fix health check (1-2 hours)
- Medium-term: Regenerate embeddings (2-4 hours)

---

## 📝 Action Items

### Immediate (Now)
- [ ] Restart ecosystem-mcp-service to reset circuit breaker
- [ ] Verify circuit breaker closes
- [ ] Test single embedding storage

### Short-Term (Today)
- [ ] Fix health check collection ID logic
- [ ] Deploy fixed code
- [ ] Verify health checks pass

### Medium-Term (Today/Tomorrow)
- [ ] Identify all documents without embeddings
- [ ] Generate missing embeddings (batch process)
- [ ] Verify 100% embedding coverage

### Long-Term (This Week)
- [ ] Add monitoring for embedding coverage
- [ ] Add automatic recovery for missing embeddings
- [ ] Add circuit breaker status to dashboard
- [ ] Add embedding health metrics

---

## 🔗 Related Issues

1. **Data Stats API returns 0** - Separate issue
2. **Collection ID mismatch** - This issue (primary)
3. **Missing embeddings** - This issue (consequence)

---

## 💡 Prevention

### 1. Health Check Best Practices
```python
# ✅ Good: Dynamic lookup
collection = chroma_client.collection

# ❌ Bad: Hardcoded ID
collection = client.get_collection(id="hardcoded-id")
```

### 2. Circuit Breaker Monitoring
- Add circuit breaker state to health endpoint
- Alert on circuit breaker OPEN
- Dashboard display of circuit breaker status

### 3. Embedding Coverage Monitoring
- Track documents vs embeddings ratio
- Alert when coverage < 95%
- Auto-generate missing embeddings

### 4. Better Error Handling
```python
try:
    await chroma_client.add_embeddings(...)
except CircuitBreakerOpenError:
    # Queue for retry when circuit closes
    await retry_queue.add(embedding_task)
```

---

## 🎉 Summary

**Root Cause:** ChromaDB health check looking for wrong collection ID → Repeated failures → Circuit breaker opens → All embedding storage blocked

**Impact:** 2,694 documents without embeddings, semantic search non-functional

**Fix:** 
1. Restart service (immediate)
2. Fix health check (short-term)
3. Regenerate embeddings (medium-term)

**Priority:** HIGH 🔴

---

*Issue Identified: October 14, 2025*  
*Status: Awaiting fix deployment*  
*Estimated Resolution: 2-4 hours*

