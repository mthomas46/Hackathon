# Worker Binary File Issue - ROOT CAUSE FOUND! 🎯

**Date:** October 25, 2025 05:10 UTC  
**Status:** ✅ ROOT CAUSE IDENTIFIED  
**Issue:** Worker stuck processing binary files with null bytes  

---

## 🎯 ROOT CAUSE

The worker IS working but getting stuck in an endless loop processing binary files that cannot be stored in PostgreSQL!

### The Evidence

```
CharacterNotInRepertoireError: invalid byte sequence for encoding "UTF8": 0x00

File: `.serena/cache/python/document_symbols_cache_v23-06-25.pkl`
Type: PKL (Python pickle file)
Content: \x04\x16\x00\x01\x00\x00\x00\x00\x00... (binary data with null bytes)
```

### What's Happening

1. ✅ Worker polls Redis stream
2. ✅ Worker picks up job
3. ✅ Worker starts processing files
4. ❌ Worker hits binary file (`.pkl`, `.DS_Store`, etc.)
5. ❌ Tries to insert null bytes (`\x00`) into PostgreSQL VARCHAR column
6. ❌ PostgreSQL rejects with "invalid byte sequence for encoding UTF8: 0x00"
7. ❌ Job fails to complete
8. ❌ Job gets re-queued or remains stuck
9. 🔄 Loop repeats with next binary file

### Redis Stream State

- **Total messages:** 67
- **Lag:** 19 (unread messages)
- **Pending:** 0 (we cleared them)
- **Consumers:** 51 (from all the restarts)

The lag of 19 means there are 19 jobs waiting, probably all hitting the same binary file issue.

---

## 📊 FILES CAUSING ISSUES

Common binary files in the repo:
- `.pkl` files (Python pickle - binary serialization)
- `.DS_Store` (macOS metadata)
- `.pyc` files (Python bytecode)
- Any other binary formats

---

## ✅ SOLUTION

### Option 1: Skip Binary Files (Recommended)
Add binary file detection and skip before processing:

```python
BINARY_EXTENSIONS = {
    '.pkl', '.pyc', '.pyo', '.pyd',
    '.DS_Store', '.so', '.dylib',
    '.egg', '.whl', '.zip', '.tar', '.gz'
}

def is_binary_file(file_path: str) -> bool:
    """Check if file should be skipped as binary."""
    path = Path(file_path)
    
    # Check extension
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    
    # Check filename
    if path.name in {'.DS_Store', 'Thumbs.db'}:
        return True
    
    return False

# In _process_snapshot_document:
if is_binary_file(file_path):
    logger.info(f"⏭️  Skipping binary file: {file_path}")
    return {"success": True, "skipped": True, "reason": "binary_file"}
```

### Option 2: Sanitize Binary Content
Replace null bytes before storing:

```python
# Remove null bytes from content
sanitized_content = original_content.replace('\x00', '')
```

**But this corrupts the data!** ❌

### Option 3: Store Binary Files Separately  
Use PostgreSQL BYTEA column for binary content:

```python
# Add column migration
ALTER TABLE documents ADD COLUMN binary_content BYTEA;
```

**Too complex for now!** ⚠️

---

## 🎯 RECOMMENDED ACTION

**Implement Option 1: Skip Binary Files**

1. Add binary file detection function
2. Check before processing each file
3. Return early with "skipped" status
4. Log skipped files for visibility
5. Count as "skipped" in job metrics

---

## 📈 IMPACT

### Before Fix
- ❌ Jobs hang on binary files
- ❌ Endless error loops
- ❌ No jobs complete
- ❌ Worker appears "stuck"

### After Fix
- ✅ Binary files skipped gracefully
- ✅ Jobs complete successfully
- ✅ Clear logging of skipped files
- ✅ Metrics show skipped count
- ✅ Worker processes normally

---

## 🔧 IMPLEMENTATION PRIORITY

**HIGH - This is blocking ALL ingestion**

Without this fix:
- No jobs can complete
- Worker continuously fails
- System appears broken

With this fix:
- Jobs complete (skipping binary files)
- System functional
- Can process text files normally

---

## 📝 VERIFICATION PLAN

1. Implement binary file filtering
2. Restart worker
3. Create test job targeting `/repo/tests`
4. Monitor logs for "Skipping binary file"
5. Verify job completes with skipped count > 0
6. Test RAG query on ingested documents

---

**Status:** Ready to implement  
**Priority:** HIGH  
**Estimated time:** 15 minutes  
**Expected result:** Worker processes jobs successfully, skipping binary files

---

**Investigation Duration:** 5 hours total  
**Root Cause Found:** Hour 5  
**Solution Identified:** Binary file filtering  

🎉 **This will fix the worker!**

