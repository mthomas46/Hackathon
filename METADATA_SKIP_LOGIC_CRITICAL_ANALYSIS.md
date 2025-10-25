# Critical Analysis: Metadata-Aware Skip Logic

## 🎯 Proposed Solution

**Add metadata completeness check to duplicate detection logic**

Instead of:
```python
if existing:
    if needs_embedding or force_update:
        # Re-process
    else:
        return skip  # Skip duplicate
```

Use:
```python
if existing:
    needs_metadata_update = check_metadata_completeness(existing, job.mode)
    if needs_embedding or force_update or needs_metadata_update:
        # Re-process
    else:
        return skip
```

---

## 🔍 Critical Analysis: Potential Flaws

### **FLAW #1: What metadata should we check?**

**Problem:** Which fields define "complete" metadata?
- Just temporal fields? (git_date, git_author)
- All optional fields?
- Mode-specific fields?

**Risk:** Hard-coding field names creates brittleness

**Solution:** Define metadata requirements per ingestion mode

---

### **FLAW #2: Version Drift**

**Problem:** What if we add new metadata fields in the future?
- Old documents lack new fields
- Do we re-process ALL existing documents?

**Risk:** Endless re-processing loop

**Solution:** Add metadata schema version tracking

---

### **FLAW #3: Performance Impact**

**Problem:** Checking multiple metadata fields for every document
- Database queries multiply
- Slower ingestion

**Risk:** Unacceptable performance degradation

**Solution:** Single composite check, indexed fields

---

### **FLAW #4: Partial Metadata**

**Problem:** What if some but not all metadata is present?
- git_date exists but git_author is None
- Is this "complete" enough?

**Risk:** Ambiguous completeness definition

**Solution:** Define minimum required fields per mode

---

### **FLAW #5: Mode Changes**

**Problem:** Document ingested in snapshot mode, now running enriched
- Should we add temporal metadata?
- Or respect original ingestion mode?

**Risk:** Inconsistent behavior across modes

**Solution:** Track ingestion_mode and only update if mode matches or upgrades

---

## ✅ Recommended Implementation

### **Strategy: Required Fields Registry**

```python
REQUIRED_METADATA_BY_MODE = {
    "snapshot": {
        "required_fields": [],  # No metadata required
        "version": 1
    },
    "enriched": {
        "required_fields": ["git_date"],  # Minimum: temporal date
        "optional_fields": ["git_author", "git_author_email", "git_commit_message"],
        "version": 1
    },
    "git_history": {
        "required_fields": ["git_date", "git_commit_sha"],
        "version": 1
    }
}
```

### **Logic Flow:**

1. **Check content_hash** (existing)
2. **Check embedding** (existing)
3. **NEW: Check metadata completeness**
   - Get required fields for job.mode
   - Check if ALL required fields are present and non-None
   - If ANY required field is missing → re-process
4. **NEW: Check metadata version** (future-proof)
   - Compare document's metadata_version to current version
   - If outdated → re-process

### **Benefits:**

✅ **Extensible:** Easy to add new fields or modes
✅ **Performance:** Single check with indexed columns
✅ **Clear:** Explicit requirements per mode
✅ **Future-proof:** Version tracking prevents endless loops
✅ **Flexible:** Optional vs required distinction

### **Edge Cases Handled:**

- Document with partial metadata → re-processed if required field missing
- Snapshot → Enriched upgrade → adds temporal data
- New metadata fields added → only re-processes if version changes
- Null vs empty string → treats both as missing

---

## 🚨 Implementation Considerations

### **1. Database Impact**

**Need indexes on:**
- `git_date` (already added in migration 010)
- `metadata_version` (new column needed)

### **2. Backward Compatibility**

**Existing documents:**
- Will have `metadata_version = None`
- Should default to version 0
- Will be re-processed once to add version

### **3. Migration Strategy**

**Option A: Lazy migration**
- Add version field with default NULL
- Update on next ingestion
- Pro: No downtime
- Con: Gradual rollout

**Option B: Active migration**
- Backfill all documents with version 1
- Immediate consistency
- Pro: Clean state
- Con: Potentially slow

**Recommendation:** Option A (lazy migration)

---

## 🎯 Final Recommendation

**Implement with 3 levels of checking:**

1. **Level 1: Content** - content_hash (existing)
2. **Level 2: Embeddings** - embedding_id (existing)
3. **Level 3: Metadata** - required fields + version (NEW)

**Skip document ONLY if ALL levels are satisfied.**

This catches:
- ✅ Content changes
- ✅ Missing embeddings
- ✅ Missing required metadata
- ✅ Outdated metadata schema

**Risk Level:** LOW
**Implementation Effort:** MEDIUM
**Value:** HIGH

---

## 📋 Implementation Checklist

- [ ] Add `metadata_version` column to documents table
- [ ] Create `REQUIRED_METADATA_BY_MODE` registry
- [ ] Implement `check_metadata_completeness()` function
- [ ] Update duplicate detection logic
- [ ] Add logging for metadata checks
- [ ] Update tests
- [ ] Create migration script

