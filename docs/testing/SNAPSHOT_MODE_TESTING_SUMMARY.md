# Snapshot Mode Testing Summary

**Date:** October 21, 2025  
**Status:** ⚠️ In Progress - Database Schema Issue Found

---

## 🎯 Objective

Test true snapshot mode ingestion that bypasses all git history and processes files directly from the filesystem.

---

## 📊 Test Progress

### Test 1: Initial Snapshot Mode (Job: `425389aa`)
- **Target:** `/repo/services/ecosystem-mcp`
- **Status:** Failed - Mode not recognized
- **Issue:** `snapshot` mode fell through to default (quick mode with git)
- **Fix:** Added `snapshot` mode handling to `_get_commits_for_mode()`

### Test 2: Implemented Snapshot Mode (Job: `eeaa57ec`)
- **Target:** `/repo/services/ecosystem-mcp/src/api`
- **Status:** Running but with errors
- **Issue 1:** Normalizer signature mismatch
  - Error: `TextNormalizer.normalize() missing 1 required positional argument: 'metadata'`
  - Fix: Changed call from `normalize(content, {metadata})` to `normalize(content, file_path, metadata)`
- **Issue 2:** Database schema missing column
  - Error: `column documents.ingestion_mode does not exist`
  - Status: **BLOCKING** - Current issue

### Test 3: Clean API Directory (Job: `b1943b41`)
- **Target:** `/repo/services/ecosystem-mcp/src/api/routes`
- **Status:** Stuck in "queued" for 20+ seconds
- **Reason:** Previous job still running and blocking worker

---

## 🐛 Bugs Found

### Bug #11: Database Schema Mismatch ❌ CRITICAL
**Symptom:** SQL error when checking for duplicate documents
```sql
column documents.ingestion_mode does not exist
```

**Impact:**
- Snapshot mode cannot store documents
- Worker gets stuck processing files
- New jobs cannot start (worker blocked)

**Root Cause:**
The `DocumentRepository` is querying for a column `ingestion_mode` that doesn't exist in the database schema.

**Fix Required:**
1. Check the documents table schema
2. Either:
   - Add the missing column via migration
   - Remove the column reference from queries
   - Update repository to use existing columns

---

## 💡 Implementation Details

### Snapshot Mode Logic Added

**File:** `job_processor.py`

**Key Changes:**

1. **Mode Recognition** (Lines 641-644)
```python
if mode == "snapshot":
    logger.info("📸 Snapshot mode: skipping git history...")
    return []  # Empty list signals snapshot mode
```

2. **Snapshot Handler** (Lines 496-502)
```python
if job.mode == "snapshot" and not commits:
    logger.info("📸 Snapshot mode: processing current filesystem state")
    snapshot_result = await self._process_snapshot_mode(job)
    return snapshot_result
```

3. **New Methods:**
   - `_process_snapshot_mode()` - Main snapshot processing
   - `_process_snapshot_document()` - Per-file processing

**Features:**
- ✅ Filesystem scanning (os.walk)
- ✅ Directory filtering (excludes .git, __pycache__, venv, etc.)
- ✅ Binary file detection and skipping
- ✅ Batch processing (50 files per batch)
- ✅ Content hashing for deduplication
- ✅ Normalization support
- ✅ Progress updates
- ❌ Database storage (blocked by schema issue)

---

## 📈 Statistics

### Files Scanned (Job `eeaa57ec`)
- **Total Found:** Unknown (still processing)
- **Processed:** 0 (database errors)
- **Failed:** Many (all hitting schema error)
- **Skipped:** Unknown

### Performance
- **Scan Speed:** Fast (filesystem walk)
- **Processing Speed:** Blocked by database errors
- **Memory Usage:** Good (batch processing)

---

## 🚀 Next Steps

### Immediate Priority: Fix Database Schema (Bug #11)

**Option A: Add Missing Column**
```sql
ALTER TABLE documents ADD COLUMN ingestion_mode VARCHAR(50);
```

**Option B: Remove Column Reference**
- Update `DocumentRepository.get_by_content_hash()` to not query `ingestion_mode`
- Use existing columns instead

**Option C: Database Migration**
- Create proper migration script
- Handle both new and existing databases

**Recommended:** Option B (quickest, safest)

### Medium Priority: Improve Snapshot Mode

1. **Better Filtering**
   - Add configurable file type filters
   - Exclude binary files earlier
   - Add size limits

2. **Enhanced Logging**
   - Log scan progress (files found)
   - Log processing batches
   - Show meaningful progress percentages

3. **Error Recovery**
   - Continue on individual file errors
   - Track failed files separately
   - Provide detailed error reports

### Testing Priority

1. Fix database schema
2. Restart services
3. Test with clean, small directory
4. Verify documents are stored
5. Check embeddings are generated
6. Test RAG queries on snapshot-ingested docs

---

## 🎓 Lessons Learned

### 1. Database Schema Validation Critical
- Schema changes need migrations
- Code and DB must stay in sync
- Preflight schema validation would help

### 2. Worker Blocking Issues
- One long-running job blocks all others
- Need better job timeout handling
- Consider parallel workers

### 3. Method Signatures Matter
- Normalizers have strict interfaces
- Type hints would have caught this earlier
- Integration tests needed

### 4. Binary File Handling
- Many files in data directories are binary
- Need better binary detection
- Should skip earlier in pipeline

---

## 📁 Files Modified

1. `services/ecosystem-mcp/src/services/ingestion/job_processor.py`
   - Added snapshot mode recognition
   - Implemented `_process_snapshot_mode()`
   - Implemented `_process_snapshot_document()`
   - Fixed normalizer call signature

2. Documentation Created:
   - `BUG_9_ROOT_CAUSE_FOUND.md`
   - `WEEK_5_DAY2_FINAL_UPDATE.md`
   - `DEBUGGING_SESSION_SUMMARY.md`
   - `SNAPSHOT_MODE_TESTING_SUMMARY.md` (this file)

---

## ✅ Success Criteria

- [x] Snapshot mode recognized
- [x] Git history bypassed
- [x] Filesystem scanning works
- [x] Binary files skipped
- [x] Normalizer called correctly
- [ ] Documents stored in database **← BLOCKED**
- [ ] Embeddings generated
- [ ] RAG queries work on snapshot docs
- [ ] Performance acceptable

---

## 🔗 Related Issues

- Bug #9: Jobs stuck (RESOLVED ✅)
- Bug #10: GitPython errors (Workaround: snapshot mode)
- Bug #11: Database schema mismatch (ACTIVE ❌)

---

**Current Status:** Waiting for database schema fix to continue testing.

**Recommendation:** Fix Bug #11 immediately, then resume snapshot mode testing with a small, clean directory.

