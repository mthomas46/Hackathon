**Date:** October 25, 2025  
**Status:** 🔍 Debug Session in Progress  
**Focus:** Methodical Tracing of Enriched Mode Temporal Data  

---

# Temporal RAG: Debug Session Log

## 🎯 **Objective**

Methodically trace why temporal data (`git_date`, `git_author`, etc.) is not populating during enriched mode ingestion.

---

## 🔄 **Reset Steps Completed**

### **Step 1: Clear Redis**
```bash
✅ Redis stream deleted
✅ Consumer groups reset
```

### **Step 2: Reset Database Jobs**
```sql
✅ All queued/processing jobs marked as failed
✅ Clean slate for new jobs
```

### **Step 3: Restart Service**
```bash
✅ Service restarted
✅ Workers reset
✅ Fresh consumer initialized
```

---

## 🔍 **Debug Logging Added**

### **Phase 2 Entry Point** (Line ~1523)
```python
logger.info(f"🔍 [PHASE2-START] Extracting temporal metadata")
logger.info(f"🔍 [PHASE2-CHECK] git_metadata exists: {git_metadata is not None}")
logger.info(f"🔍 [PHASE2-CHECK] job.mode: {job.mode}")
```

**Purpose:** Verify Phase 2 code is reached

---

### **Git Metadata Extraction** (Line ~1529)
```python
if git_metadata:
    logger.info(f"🔍 [PHASE2-META] git_metadata keys: {list(git_metadata.keys())}")
    logger.info(f"🔍 [PHASE2-META] metadata_source: {git_metadata.get('metadata_source')}")
```

**Purpose:** Verify git_metadata structure and source

---

### **Git Date Parsing** (Line ~1533)
```python
logger.info(f"🔍 [PHASE2-GIT] Checking last_commit_date: {git_metadata.get('last_commit_date')}")
if git_metadata.get("last_commit_date"):
    git_date_value = datetime.fromisoformat(...)
    logger.info(f"✅ [PHASE2-GIT] Parsed git_date: {git_date_value}")
```

**Purpose:** Trace git date parsing

---

### **Fallback 1: file_mtime** (Line ~1545)
```python
if not git_date_value and git_metadata.get("file_mtime"):
    logger.info(f"🔍 [PHASE2-FALLBACK1] Using file_mtime: {git_metadata.get('file_mtime')}")
    git_date_value = datetime.fromisoformat(git_metadata["file_mtime"])
    logger.info(f"✅ [PHASE2-FALLBACK1] Parsed mtime: {git_date_value}")
```

**Purpose:** Trace first fallback

---

### **Fallback 2: Direct Filesystem** (Line ~1548)
```python
if not git_date_value and job.mode == "enriched":
    logger.info(f"🔍 [PHASE2-FALLBACK2] git_date still None, trying filesystem")
    full_path = os.path.join(job.repo_path, file_path)
    logger.info(f"🔍 [PHASE2-FALLBACK2] Full path: {full_path}")
    if os.path.exists(full_path):
        mtime = os.path.getmtime(full_path)
        git_date_value = datetime.fromtimestamp(mtime)
        logger.info(f"✅ [PHASE2-FALLBACK2] Using file mtime: {git_date_value}")
```

**Purpose:** Trace final fallback

---

### **Final State** (Line ~1560)
```python
logger.info(f"🔍 [PHASE2-FINAL] Final values:")
logger.info(f"   git_date_value: {git_date_value}")
logger.info(f"   git_author_value: {git_author_value}")
logger.info(f"   git_commit_sha: {git_commit_sha}")
```

**Purpose:** Verify values before DocumentModel creation

---

## 📊 **Test Execution**

### **Test Job Details**
```yaml
Job ID: [from test]
Service Name: debug-temporal-test
Mode: enriched
Repo Path: /repo
```

### **Expected Log Pattern**
```
🔍 [ENRICH-1] Starting enriched metadata extraction
🔍 [ENRICH-2] Checking GitService initialization
...
🔍 [PHASE2-START] Extracting temporal metadata
🔍 [PHASE2-CHECK] git_metadata exists: True/False
🔍 [PHASE2-META] git_metadata keys: [...]
🔍 [PHASE2-GIT] Checking last_commit_date: ...
✅ [PHASE2-GIT] Parsed git_date: ...
🔍 [PHASE2-FINAL] Final values: git_date_value=...
```

---

## 🔍 **Diagnostic Questions**

### **Q1: Is Phase 2 code reached?**
**Look for:** `[PHASE2-START]` in logs

- ✅ If found: Code is executing
- ❌ If not found: Code path issue

---

### **Q2: Does git_metadata exist?**
**Look for:** `[PHASE2-CHECK] git_metadata exists: True`

- ✅ If True: Enriched extraction worked
- ❌ If False: Git extraction failed

---

### **Q3: What's in git_metadata?**
**Look for:** `[PHASE2-META] git_metadata keys: [...]`

**Expected keys:**
- `last_commit_sha`
- `last_commit_date`
- `last_commit_author`
- `last_commit_author_email`
- `last_commit_message`
- `metadata_source` (git or filesystem)

---

### **Q4: Is git_date parsed successfully?**
**Look for:** `[PHASE2-GIT] Parsed git_date: ...`

- ✅ If found: Git date extraction working
- ❌ If not found: Check fallbacks

---

### **Q5: Which fallback is used?**
**Look for:**
- `[PHASE2-FALLBACK1]` → Using file_mtime from git_metadata
- `[PHASE2-FALLBACK2]` → Using direct filesystem mtime

---

### **Q6: What are the final values?**
**Look for:** `[PHASE2-FINAL] Final values:`

**Check:**
- `git_date_value` → Should NOT be None
- `git_author_value` → Should have value (if from git)
- `git_commit_sha` → Should have SHA (if from git)

---

## 🎯 **Success Criteria**

### **✅ Complete Success**
```
[PHASE2-START] ← Code reached
[PHASE2-CHECK] git_metadata exists: True ← Metadata extracted
[PHASE2-GIT] Parsed git_date: 2025-10-25... ← Date parsed
[PHASE2-FINAL] git_date_value: 2025-10-25... ← Value set
```

**Result:** Documents should have temporal data

---

### **🟡 Partial Success (Fallback 1)**
```
[PHASE2-START] ← Code reached
[PHASE2-CHECK] git_metadata exists: True
[PHASE2-GIT] last_commit_date: NONE ← No git date
[PHASE2-FALLBACK1] Using file_mtime ← Fallback triggered
[PHASE2-FINAL] git_date_value: 2025-10-25... ← Value set
```

**Result:** Documents should have temporal data (from filesystem)

---

### **🟡 Partial Success (Fallback 2)**
```
[PHASE2-START] ← Code reached
[PHASE2-CHECK] git_metadata exists: False ← No git metadata
[PHASE2-FALLBACK2] Using file mtime ← Final fallback
[PHASE2-FINAL] git_date_value: 2025-10-25... ← Value set
```

**Result:** Documents should have temporal data (from direct filesystem)

---

### **❌ Failure Scenarios**

#### **Scenario 1: Code Not Reached**
```
[No PHASE2- logs at all]
```

**Issue:** Code path not executing

**Fix:** Check if enriched mode uses different function

---

#### **Scenario 2: No git_metadata**
```
[PHASE2-CHECK] git_metadata exists: False
[PHASE2-FALLBACK2] File does not exist
[PHASE2-FINAL] git_date_value: None
```

**Issue:** Both git and filesystem extraction failed

**Fix:** Check paths, permissions, git availability

---

#### **Scenario 3: Parsing Errors**
```
[PHASE2-GIT] last_commit_date: <invalid format>
❌ Failed to parse git_date: ...
[PHASE2-FINAL] git_date_value: None
```

**Issue:** Date format mismatch

**Fix:** Check datetime parsing logic

---

## 📝 **Next Steps After Log Analysis**

### **If Phase 2 logs found:**
1. ✅ Verify git_metadata structure
2. ✅ Verify date parsing
3. ✅ Verify final values
4. ✅ Check database for populated fields

### **If Phase 2 logs NOT found:**
1. ❌ Code path issue
2. 🔍 Check if enriched mode uses different function
3. 🔍 Add logging earlier in process
4. 🔍 Verify git_metadata scope

---

## 🎯 **Expected Outcome**

After this debug session, we should know EXACTLY:

1. ✅ Is Phase 2 code executing?
2. ✅ Is git_metadata being populated?
3. ✅ Are dates being parsed?
4. ✅ Which fallback (if any) is triggered?
5. ✅ What are the final values before DB insert?

**This will pinpoint the exact failure point.**

---

**End of Debug Session Setup**

**Status:** 🔍 Logging Added - Ready for Analysis

