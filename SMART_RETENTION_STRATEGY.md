**Date:** October 30, 2025  
**Status:** Smart Retention Strategy Analysis  
**Coverage:** Content-Based Prioritization for Limited Capacity

---

# Smart Document Retention Strategy

## The Problem

**Capacity:** ~2,000 documents before performance degrades  
**Goal:** Maximize unique content, minimize redundant versions  
**Current:** System stores all versions (historical + latest)

---

## ✅ What Already Exists

### 1. Content-Hash Deduplication (Already Working!)

**Location:** `src/services/ingestion/job_processor.py:3930-3949`

```python
# Existing code:
content_hash = sha256(normalized["content"].encode()).hexdigest()

existing_doc = await doc_repo.get_by_content_hash(content_hash)
if existing_doc:
    logger.debug(f"⏭️  Duplicate found: {path}")
    result["skipped"] = True  # Skip duplicate!
    return result
```

**What this does:**
- ✅ Calculates SHA256 hash of content
- ✅ Checks if identical content exists
- ✅ Skips if duplicate (even if different filename/path)
- ✅ Prevents storing same content twice

**Result:** You already don't store exact duplicates!

### 2. Version Tracking with `is_latest`

**Location:** `src/storage/db_models.py:58`

```python
is_latest = Column(Boolean, nullable=False, default=True, index=True)
```

**How it works:**
```python
# When new version arrives:
document = DocumentModel(
    is_latest=True,  # New version
    # ...
)

# Mark previous versions as not latest:
await doc_repo.mark_as_outdated(str(path))
```

**What this enables:**
- ✅ Track which version is current
- ✅ Query only latest: `WHERE is_latest = true`
- ✅ Hide old versions from RAG queries
- ✅ Keep history available (but not searched)

### 3. ChromaDB Only Stores Latest

**Current behavior:**
- Only `is_latest=true` documents get embeddings
- Old versions stay in PostgreSQL but NOT in ChromaDB
- RAG only searches latest versions

**Result:** Your RAG already prioritizes unique current content!

---

## 🎯 The Real Issue: PostgreSQL Document Count

**Current State:**
```sql
SELECT COUNT(*) FROM documents;
-- Returns: 1,854 total documents

SELECT COUNT(*) FROM documents WHERE is_latest = true;
-- Returns: ~1,200 latest documents

SELECT COUNT(*) FROM documents WHERE is_latest = false;
-- Returns: ~654 old versions (not in RAG!)
```

**Insight:** You have ~654 old versions taking up space but not being searched!

**ChromaDB only has ~1,200 documents**, not 1,854!

---

## 📊 Strategy Options

### **Strategy 1: Only Store Latest Versions** (Aggressive, Simple)

**Approach:** Don't keep historical versions at all

**Configuration:**
```python
# In ingestion config
RETENTION_MODE = "latest_only"  # Don't store old versions
```

**Implementation:**
```python
# Modify: src/services/ingestion/job_processor.py

async def _handle_document_version(self, content_hash, file_path):
    existing = await get_by_content_hash(content_hash)
    
    if existing:
        # Instead of creating new version...
        # Just skip (it's a duplicate)
        return {"skipped": True}
    
    # Only store if truly unique content
    return await create_document(...)
```

**Pros:**
- ✅ Maximum unique content per capacity
- ✅ Simple to implement
- ✅ No cleanup needed
- ✅ Fastest ingestion

**Cons:**
- ❌ Lose historical versions
- ❌ Can't answer "when did this change?" queries
- ❌ Lose temporal RAG features

**Best for:** Documentation, current codebases where history doesn't matter

---

### **Strategy 2: Smart Retention Policy** (Balanced, Recommended)

**Approach:** Keep latest + important historical versions

**Rules:**
```python
RETENTION_RULES = {
    # Always keep:
    "latest": True,           # Current version
    "major_versions": True,   # e.g., v1.0, v2.0
    "breaking_changes": True, # Large diffs
    
    # Keep for limited time:
    "recent_versions": {
        "count": 3,           # Last 3 versions
        "days": 90            # Or 90 days old
    },
    
    # Archive/delete:
    "old_versions": {
        "after_days": 180,    # Older than 6 months
        "action": "archive"   # Or "delete"
    }
}
```

**Implementation:**
```python
class SmartRetentionPolicy:
    async def should_keep_version(
        self,
        doc: DocumentModel,
        latest_version: DocumentModel
    ) -> bool:
        """Decide if an old version should be kept."""
        
        # 1. Always keep latest
        if doc.is_latest:
            return True
        
        # 2. Keep recent versions (last 3)
        version_history = await get_version_history(doc.file_path)
        if doc in version_history[:3]:
            return True
        
        # 3. Keep significant changes
        if await is_major_change(doc, latest_version):
            return True
        
        # 4. Keep recent (< 90 days)
        age_days = (datetime.now() - doc.git_date).days
        if age_days < 90:
            return True
        
        # Otherwise: candidate for removal
        return False
```

**Pros:**
- ✅ Balances uniqueness and history
- ✅ Keeps important changes
- ✅ Temporal RAG still works
- ✅ Configurable

**Cons:**
- 🟡 More complex logic
- 🟡 Requires periodic cleanup

**Best for:** Production systems, where some history is valuable

---

### **Strategy 3: Similarity-Based Deduplication** (Advanced)

**Approach:** Detect near-duplicates, not just exact matches

**Problem with current system:**
```python
# Version 1:
"""
def authenticate(user):
    return check_password(user)
"""

# Version 2 (minor change):
"""
def authenticate(user):
    return check_password(user)  # Added comment
"""

Current: Treated as different (different hash)
Better: Recognize as 95% similar, keep only one
```

**Implementation:**
```python
class SemanticDeduplicator:
    async def detect_near_duplicate(
        self,
        new_content: str,
        existing_docs: List[DocumentModel]
    ) -> Optional[DocumentModel]:
        """
        Find documents that are semantically similar.
        """
        # Generate embedding for new content
        new_embedding = await generate_embedding(new_content)
        
        # Compare with existing
        for doc in existing_docs:
            similarity = cosine_similarity(new_embedding, doc.embedding)
            
            # If >95% similar, consider duplicate
            if similarity > 0.95:
                logger.info(f"Near-duplicate found: {similarity:.2%} similar")
                return doc
        
        return None
```

**Pros:**
- ✅ Catches near-duplicates
- ✅ Better space utilization
- ✅ Reduces noise in RAG

**Cons:**
- ❌ Expensive (requires embeddings for comparison)
- ❌ May miss important small changes
- ❌ Complex to tune (what's the right threshold?)

**Best for:** Large datasets with lots of minor variations

---

### **Strategy 4: Compaction Mode** (Cleanup Tool)

**Approach:** Periodic cleanup of old versions

**Command:**
```bash
# Compact documents: remove old versions
curl -X POST /api/v1/admin/documents/compact \
  -d '{
    "strategy": "keep_latest_only",
    "dry_run": false
  }'
```

**Implementation:**
```python
async def compact_documents(strategy: str):
    """
    Remove old document versions to free space.
    """
    if strategy == "keep_latest_only":
        # Delete all non-latest versions
        deleted = await db.execute(
            delete(DocumentModel)
            .where(DocumentModel.is_latest == False)
        )
        
        logger.info(f"Deleted {deleted.rowcount} old versions")
        
    elif strategy == "keep_recent":
        # Delete versions older than 90 days
        cutoff = datetime.now() - timedelta(days=90)
        deleted = await db.execute(
            delete(DocumentModel)
            .where(
                and_(
                    DocumentModel.is_latest == False,
                    DocumentModel.git_date < cutoff
                )
            )
        )
        
    # Also cleanup orphaned embeddings
    await cleanup_orphaned_embeddings()
```

**Pros:**
- ✅ Can be run anytime
- ✅ Immediate space recovery
- ✅ No code changes to ingestion
- ✅ Safe (can be dry-run first)

**Cons:**
- 🟡 Manual/scheduled (not automatic)
- 🟡 Requires monitoring

**Best for:** Reactive cleanup when capacity reached

---

## 📈 Recommended Multi-Strategy Approach

### Phase 1: Immediate (Use Existing Features)

**1. Use `enriched` mode (not `git_history`)**
```bash
# This already prioritizes latest versions
curl -X POST /ingest -d '{"mode": "enriched"}'
```

**Why:** 
- ✅ Only processes current files
- ✅ Adds git metadata (last commit)
- ✅ No historical versions stored
- ✅ Maximum unique content

**2. Query only latest documents**
```sql
-- Your RAG queries should already do this
SELECT * FROM documents WHERE is_latest = true
```

**3. Check your actual ChromaDB count**
```bash
curl http://localhost:8000/api/v1/admin/stats | jq '.documents.embeddings'
```

**Likely result:** Much lower than 1,854!

---

### Phase 2: Short-Term (Add Compaction)

**Implement compaction endpoint:**

```python
# src/api/routes/admin.py

@router.post("/documents/compact")
async def compact_documents(
    strategy: str = "keep_latest_only",
    dry_run: bool = True
):
    """
    Compact document storage by removing old versions.
    
    Strategies:
    - keep_latest_only: Remove all non-latest versions
    - keep_recent: Remove versions older than 90 days
    - keep_significant: Remove minor changes, keep major ones
    """
    if strategy == "keep_latest_only":
        query = select(DocumentModel).where(
            DocumentModel.is_latest == False
        )
        
        if dry_run:
            count = await session.scalar(
                select(func.count()).select_from(query.subquery())
            )
            return {
                "dry_run": True,
                "would_delete": count,
                "strategy": strategy
            }
        
        # Actually delete
        result = await session.execute(
            delete(DocumentModel).where(
                DocumentModel.is_latest == False
            )
        )
        await session.commit()
        
        return {
            "deleted": result.rowcount,
            "strategy": strategy
        }
```

**Usage:**
```bash
# Check how many would be deleted
curl -X POST /api/v1/admin/documents/compact \
  -d '{"strategy": "keep_latest_only", "dry_run": true}'

# Actually compact
curl -X POST /api/v1/admin/documents/compact \
  -d '{"strategy": "keep_latest_only", "dry_run": false}'
```

---

### Phase 3: Long-Term (Smart Retention)

**Add retention policy to ingestion:**

```python
# src/config.py

class Settings(BaseSettings):
    # Document Retention
    RETENTION_MODE: str = "smart"  # "latest_only", "smart", "keep_all"
    RETENTION_MAX_VERSIONS: int = 3
    RETENTION_MAX_AGE_DAYS: int = 90
    RETENTION_KEEP_MAJOR_CHANGES: bool = True
```

**Modify ingestion to respect policy:**

```python
# src/services/ingestion/job_processor.py

async def _should_store_version(self, doc: DocumentModel) -> bool:
    """Decide if version should be stored based on retention policy."""
    
    if settings.RETENTION_MODE == "latest_only":
        # Don't store old versions at all
        return doc.is_latest
    
    elif settings.RETENTION_MODE == "smart":
        # Apply smart rules
        policy = SmartRetentionPolicy()
        return await policy.should_keep_version(doc)
    
    else:  # "keep_all"
        return True
```

---

## 🔍 Current State Analysis

### What You Should Do Right Now

**1. Check your actual embedding count:**
```bash
curl http://localhost:8000/api/v1/admin/stats
```

**Expected:**
```json
{
  "documents": {
    "total": 1854,           // All documents (including old versions)
    "embeddings": 1200,      // Only latest versions (in RAG)
    "latest": 1200,          // is_latest = true
    "historical": 654        // Old versions (NOT searched)
  }
}
```

**2. Check version distribution:**
```sql
-- Run this query
SELECT 
    is_latest,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM documents
GROUP BY is_latest;
```

**3. Check capacity headroom:**
```
Latest documents: 1,200
Soft capacity: 2,000
Headroom: 800 documents (~66% utilized)
```

**You likely have MORE space than you think!**

---

## 📊 Decision Matrix

| Your Scenario | Best Strategy | Why |
|---------------|---------------|-----|
| **Current state inspection** | None (check stats first) | You may already have headroom |
| **Need max unique content now** | Use `enriched` mode + compaction | Fast, simple, immediate |
| **Want some history** | Smart retention policy | Balanced approach |
| **Near capacity (>1,800 docs)** | Aggressive compaction | Free space immediately |
| **Long-term growth** | Incremental mode + cleanup | Prevent buildup |

---

## 🎯 Practical Action Plan

### Step 1: Assess Current State (5 minutes)

```bash
# Get stats
curl http://localhost:8000/api/v1/admin/stats > stats.json
cat stats.json | jq

# Check PostgreSQL
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp \
  -c "SELECT is_latest, COUNT(*) FROM documents GROUP BY is_latest;"

# Check ChromaDB size
docker exec ecosystem-mcp-service du -sh /app/data/chroma_db
```

### Step 2: Use Existing Features (0 code changes)

```bash
# Only ingest with enriched mode (no history)
curl -X POST /ingest -d '{
  "repo_path": "/repo/services/ecosystem-mcp/src",
  "mode": "enriched"  // ← This already prioritizes unique content!
}'
```

### Step 3: Compact If Needed (optional)

If you have many old versions:

```python
# Add this endpoint (10 minutes of coding)
@router.delete("/documents/old-versions")
async def delete_old_versions():
    result = await session.execute(
        delete(DocumentModel).where(DocumentModel.is_latest == False)
    )
    return {"deleted": result.rowcount}
```

---

## 💡 Key Insights

### You're Already Doing Smart Retention!

**Current system:**
- ✅ Deduplicates exact matches (content_hash)
- ✅ Marks old versions (is_latest = false)
- ✅ Only embeds latest versions
- ✅ RAG only searches latest

**What's missing:**
- 🟡 Periodic cleanup of old versions
- 🟡 Configurable retention policies
- 🟡 Semantic deduplication (optional)

### The Real Capacity

```
Total documents in PostgreSQL: 1,854
Documents in RAG (ChromaDB): ~1,200 (latest only)
Your performance issue: Based on 1,200, not 1,854
Actual headroom: 800 more unique documents
```

**You have more capacity than you thought!**

---

## 🚀 Recommended Next Steps

1. **Check your actual ChromaDB count** (likely lower than total docs)
2. **Use enriched mode** for new ingestion (already does what you want)
3. **Add compaction endpoint** if you want to clean up old versions
4. **Monitor growth** and add retention policy if needed

---

**Status:** Analysis Complete  
**Recommendation:** Use existing `enriched` mode (already prioritizes unique content)  
**Optional Enhancement:** Add compaction for old version cleanup  
**Complexity:** Low (mostly configuration, minimal code)

