# 🔧 Ingestion System Improvements Plan

**Date:** October 14, 2025  
**Status:** 🔄 Implementation in Progress

---

## 🎯 Requested Improvements

### 1. ✅ Start ChromaDB Service
**Status:** ChromaDB is embedded, not a separate service!
- Uses `PersistentClient` (local file storage)
- Path: `./data/chroma_db`
- No separate container needed
- Already initialized on first use

### 2. 🔧 Add Health Checks & Auto-Restart
**Implementation:**
- Add ChromaDB health check before each operation
- Auto-restart ChromaDB client on failure
- Graceful retry with exponential backoff
- Circuit breaker already exists - enhance it

### 3. 📝 Duplicate Metadata Enrichment
**Implementation:**
- On duplicate detection, compare metadata
- Update existing document with missing fields
- Merge tags, update word counts
- Keep latest timestamps
- Log enrichment activity

### 4. 📊 Change "Failed" to "Skipped" for Duplicates
**Implementation:**
- Add `skipped_documents` counter to job model
- Separate `failed` (errors) from `skipped` (duplicates)
- Update API responses
- Update dashboard display
- Clarify job statistics

### 5. 🔄 Graceful Retry Mechanisms
**Implementation:**
- Retry ChromaDB operations on connection loss
- Exponential backoff (1s, 2s, 4s, 8s...)
- Max 3 retries before marking as failed
- Log all retry attempts
- Re-initialize client if needed

---

## 📋 Implementation Tasks

### Task 1: Update Database Model ✅ READY

**File:** `src/storage/db_models.py`

**Add field:**
```python
class IngestionJobModel(Base):
    # ... existing fields ...
    skipped_documents = Column(Integer, default=0)  # NEW
```

**Migration:**
```sql
ALTER TABLE ingestion_jobs ADD COLUMN skipped_documents INTEGER DEFAULT 0;
```

---

### Task 2: Enhance ChromaDB Client ✅ READY

**File:** `src/storage/chromadb_client.py`

**Add auto-restart logic:**
```python
async def ensure_connected(self) -> bool:
    """Ensure ChromaDB is connected, restart if needed."""
    try:
        # Quick health check
        _ = self.collection.count()
        return True
    except Exception as e:
        logger.warning(f"ChromaDB connection lost: {e}, restarting...")
        try:
            # Reinitialize client
            self.client = chromadb.PersistentClient(
                path=self.path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("✅ ChromaDB client restarted successfully")
            return True
        except Exception as restart_error:
            logger.error(f"❌ Failed to restart ChromaDB: {restart_error}")
            return False
```

**Add retry wrapper:**
```python
async def add_embeddings_with_retry(
    self,
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
    ids: List[str],
    documents: Optional[List[str]] = None,
    max_retries: int = 3
) -> bool:
    """Add embeddings with automatic retry."""
    for attempt in range(max_retries):
        try:
            # Ensure connected
            if not await self.ensure_connected():
                logger.error(f"ChromaDB not connected (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            
            # Try to add embeddings
            await self.add_embeddings(embeddings, metadatas, ids, documents)
            return True
            
        except Exception as e:
            logger.error(f"Failed to add embeddings (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
            else:
                logger.error(f"❌ Failed after {max_retries} attempts")
                return False
    
    return False
```

---

### Task 3: Implement Metadata Enrichment ✅ READY

**File:** `src/services/ingestion/job_processor.py`

**Replace duplicate skip with enrichment:**
```python
# Current code (line 344-348):
existing_doc = await doc_repo.get_by_content_hash(content_hash)
if existing_doc:
    logger.debug(f"⏭️  Skipping duplicate document: {path}")
    result["error"] = "duplicate"
    return result

# NEW CODE:
existing_doc = await doc_repo.get_by_content_hash(content_hash)
if existing_doc:
    logger.debug(f"⏭️  Duplicate found: {path}, checking for metadata enrichment...")
    
    # Check if we can enrich existing metadata
    enriched = await self._enrich_duplicate_metadata(
        existing_doc,
        normalized["metadata"],
        doc_repo,
        session
    )
    
    if enriched:
        logger.info(f"✨ Enriched metadata for: {path}")
        result["enriched"] = True
    
    result["skipped"] = True  # Mark as skipped, not error
    return result
```

**Add enrichment method:**
```python
async def _enrich_duplicate_metadata(
    self,
    existing_doc,
    new_metadata: Dict[str, Any],
    doc_repo,
    session
) -> bool:
    """
    Enrich existing document with missing metadata from duplicate.
    
    Returns:
        True if any metadata was added, False otherwise
    """
    enriched = False
    current_metadata = existing_doc.doc_metadata or {}
    
    # Fields to potentially enrich
    enrichable_fields = [
        'author', 'last_modified', 'tags', 'description',
        'word_count', 'has_code', 'has_diagrams', 'language'
    ]
    
    for field in enrichable_fields:
        # If field is missing or empty in existing doc
        if field not in current_metadata or not current_metadata[field]:
            # And new metadata has it
            if field in new_metadata and new_metadata[field]:
                current_metadata[field] = new_metadata[field]
                enriched = True
                logger.debug(f"  + Added {field}: {new_metadata[field]}")
    
    # Special handling for tags (merge, don't replace)
    if 'tags' in new_metadata and new_metadata['tags']:
        existing_tags = set(current_metadata.get('tags', []))
        new_tags = set(new_metadata['tags'])
        merged_tags = existing_tags | new_tags
        
        if len(merged_tags) > len(existing_tags):
            current_metadata['tags'] = list(merged_tags)
            enriched = True
            logger.debug(f"  + Merged tags: {merged_tags - existing_tags}")
    
    # Update if enriched
    if enriched:
        existing_doc.doc_metadata = current_metadata
        existing_doc.updated_at = datetime.utcnow()
        await session.commit()
    
    return enriched
```

---

### Task 4: Update Job Tracking ✅ READY

**File:** `src/services/ingestion/job_processor.py`

**Update job counters:**
```python
# Initialize counters (at job start)
processed_count = 0
failed_count = 0
skipped_count = 0  # NEW
embedding_count = 0

# In processing loop:
result = await self._process_file(file_change, commit, job)

if result.get("success"):
    processed_count += 1
    if result.get("embedding_generated"):
        embedding_count += 1
elif result.get("skipped"):  # NEW
    skipped_count += 1
elif result.get("enriched"):  # NEW
    skipped_count += 1
    logger.info(f"Enriched duplicate: {result.get('path')}")
else:
    failed_count += 1
    logger.warning(f"Failed: {result.get('path')} - {result.get('error')}")

# Update job in database
await job_repo.update_job(
    job_id,
    processed_documents=processed_count,
    failed_documents=failed_count,
    skipped_documents=skipped_count,  # NEW
    embeddings_generated=embedding_count
)
```

---

### Task 5: Update API Models ✅ READY

**File:** `src/api/routes/admin.py`

**Update response model:**
```python
class JobStatus(BaseModel):
    """Ingestion job status."""
    job_id: str
    mode: str
    status: str
    started_at: str
    completed_at: Optional[str]
    processed_documents: int
    total_documents: Optional[int]
    failed_documents: int
    skipped_documents: int = 0  # NEW
    embeddings_generated: int
    total_cost_usd: float
    error_message: Optional[str]
```

**Update endpoint:**
```python
async def get_all_jobs():
    # ... existing code ...
    job_list.append({
        "job_id": str(job.id),
        "mode": job.mode,
        "status": job.status,
        # ... existing fields ...
        "failed_documents": job.failed_documents or 0,
        "skipped_documents": job.skipped_documents or 0,  # NEW
        "embeddings_generated": job.embeddings_generated or 0,
        # ...
    })
```

---

### Task 6: Update Dashboard ✅ READY

**File:** `dashboard_views/ingestion_manager.py`

**Update display:**
```python
# In job status display:
st.markdown(f"**Processed:** {job.get('processed_documents', 0)}")
st.markdown(f"**Skipped:** {job.get('skipped_documents', 0)}")  # NEW (was part of failed)
st.markdown(f"**Failed:** {job.get('failed_documents', 0)}")  # Now only real errors
st.markdown(f"**Embeddings:** {job.get('embeddings_generated', 0)}")
```

---

## 🚀 Implementation Order

### Phase 1: Database Schema ✅
1. Add `skipped_documents` column to `ingestion_jobs` table
2. Run migration or manually add column

### Phase 2: ChromaDB Enhancements ✅
1. Add `ensure_connected()` method
2. Add `add_embeddings_with_retry()` method
3. Update existing methods to use retry logic

### Phase 3: Duplicate Handling ✅
1. Implement `_enrich_duplicate_metadata()` method
2. Update duplicate detection to call enrichment
3. Change `result["error"] = "duplicate"` to `result["skipped"] = True`
4. Add `result["enriched"] = True` when metadata is added

### Phase 4: Job Tracking ✅
1. Add `skipped_count` variable
2. Update counters based on `skipped` flag
3. Update job model with `skipped_documents`

### Phase 5: API Updates ✅
1. Update `JobStatus` model
2. Update all job endpoints to include `skipped_documents`
3. Test API responses

### Phase 6: Dashboard Updates ✅
1. Add "Skipped" display
2. Update metrics to show skipped separately
3. Update filters if needed

### Phase 7: Testing ✅
1. Run test ingestion
2. Verify duplicate detection works
3. Verify metadata enrichment works
4. Verify retry logic works
5. Verify dashboard displays correctly

---

## 🎯 Expected Results

### Before:
```
✅ Processed: 3 documents
❌ Failed: 316 documents (duplicates + errors mixed)
✅ Embeddings: 3 generated
```

### After:
```
✅ Processed: 3 documents
⏭️  Skipped: 316 documents (duplicates, not errors!)
❌ Failed: 0 documents (only real errors)
✅ Embeddings: 3 generated
✨ Enriched: 45 documents (metadata added to duplicates)
```

---

## 📚 Technical Details

### ChromaDB Auto-Restart
- Detects connection loss
- Reinitializes `PersistentClient`
- Recreates collection reference
- Transparent to caller
- Logs all restart attempts

### Metadata Enrichment
- Non-destructive (only adds, never removes)
- Merges arrays (tags, categories)
- Updates scalars if missing
- Preserves original timestamps
- Logs all enrichments

### Retry Logic
- Exponential backoff: 1s, 2s, 4s
- Max 3 attempts per operation
- Logs each attempt
- Returns success/failure boolean
- Caller decides how to handle failure

### Skipped vs Failed
- **Skipped:** Duplicate content, no error
- **Failed:** Actual error during processing
- **Enriched:** Duplicate but metadata was added
- Clear distinction in logs and UI

---

## 🔍 Benefits

**1. Better Visibility:**
- Clear distinction between duplicates and errors
- Easy to see if enrichment is happening
- Accurate failure rates

**2. Better Data Quality:**
- Metadata gets richer over time
- No information loss from duplicates
- Tags and categories accumulate

**3. Better Reliability:**
- Auto-recovery from ChromaDB issues
- Graceful degradation
- No complete failures from transient errors

**4. Better UX:**
- 99% "failure" rate becomes 0% failure, 99% skip
- Users understand what's happening
- Confidence in the system

---

## ✅ Status

**Documentation:** Complete  
**Implementation:** Ready to begin  
**Testing Plan:** Defined  

**Next:** Implement changes in order listed above

---

**This plan provides a complete roadmap for all requested improvements!**

