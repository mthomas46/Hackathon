# Artifact Saving Investigation

**Date:** November 20, 2025  
**Run ID:** 433da983-8524-411f-9aff-f18f7f95f0d6  
**Issue:** Run completed successfully but generated 0 artifacts  
**Status:** 🟡 PARTIALLY RESOLVED (artifacts save, totals don't update)

---

## 🎯 Current Status

### What's Working ✅
1. **Artifacts ARE being saved** - Confirmed via direct database query
2. **Artifact content IS correct** - word_count matches (651 words)
3. **ORM updates ARE executing** - Logs show `artifacts=1, words=651`
4. **session.commit() IS being called** - No exceptions thrown
5. **Repository method IS working** - No errors in artifact creation

### What's NOT Working ❌
1. **Run totals don't persist** - `total_artifacts` and `total_words` remain `0` in database
2. **API returns incorrect counts** - Shows `total_documents: 0` despite 1 artifact existing

---

## 🔍 Investigation Timeline

### Attempt 1: Use DocumentationRunManager ❌
**Issue:** Manager requires `session` parameter  
**Error:** `DocumentationRunManager.__init__() missing 1 required positional argument: 'session'`  
**Commit:** `a4e95eda`

### Attempt 2: Fix session instantiation ❌
**Issue:** Still didn't work after passing session  
**Commit:** `b6a71307`

### Attempt 3: Use DocumentationRunRepository directly ❌
**Issue:** SQL UPDATE with class attributes didn't persist  
**Commit:** `8e858a06` - Added `func.coalesce()` for NULL handling

### Attempt 4: ORM-based update (Current) ⚠️
**Approach:** Fetch run object, modify directly, let ORM track changes  
**Result:** Logs show correct values but database doesn't persist  
**Commits:** `36d2be4b`, `d563b341`

---

## 📊 Evidence

### Database Verification
```sql
-- Artifact EXISTS
SELECT id, run_id, title, word_count 
FROM documentation_artifacts 
WHERE run_id = 'f67cae76-99d9-4ca7-8531-cda0436509c2';

 id                                  | run_id                              | title                        | word_count 
-------------------------------------+-------------------------------------+------------------------------+------------
 37978168-cf01-4c78-94be-b5c33dae22c1| f67cae76-99d9-4ca7-8531-cda0436509c2| adminService - api_reference | 651
```

```sql
-- But run totals are ZERO
SELECT total_artifacts, total_words 
FROM documentation_runs 
WHERE id = 'f67cae76-99d9-4ca7-8531-cda0436509c2';

 total_artifacts | total_words 
-----------------+-------------
               0 |           0
```

### Log Evidence
```
Updating run f67cae76-99d9-4ca7-8531-cda0436509c2 totals: +1 artifact, +651 words
✅ Run totals updated: artifacts=1, words=651
✅ Saved artifact: adminService - api_reference
✅ Run totals automatically updated: 1 artifact, 651 words
```

---

## 🔬 Root Cause Analysis

### Theory 1: Transaction Isolation ❓
- **Hypothesis:** Artifact and run update in different transactions
- **Evidence:** Artifact persists, run update doesn't
- **Counter:** Both use same session in same context

### Theory 2: Session Commit Issue ❓
- **Hypothesis:** `session.commit()` not actually committing
- **Evidence:** No exceptions, but changes don't persist
- **Test:** Added logging around commit (pending)

### Theory 3: ORM Session Expiry ❓
- **Hypothesis:** Run object expires before commit
- **Evidence:** `expire_on_commit=False` in session config
- **Counter:** Should prevent expiry

### Theory 4: PostgreSQL Transaction Issue ❓
- **Hypothesis:** Database-level transaction problem
- **Evidence:** One table updates, another doesn't
- **Test Needed:** Check PostgreSQL logs

---

## 💻 Current Code Flow

### orchestrator.py (Phase 5)
```python
async with get_database().session() as session:
    repository = DocumentationRunRepository(session)
    
    artifact = await repository.add_artifact(
        run_id=run_id,
        # ... parameters
    )
    
    logger.info("🔄 About to commit transaction...")
    await session.commit()
    logger.info("✅ Transaction committed successfully")
```

### repository.py (add_artifact)
```python
# Save artifact
self.session.add(artifact)
await self.session.flush()

# Update run totals (ORM-based)
result = await self.session.execute(
    select(DocumentationRunModel).where(DocumentationRunModel.id == run_id)
)
run = result.scalar_one_or_none()

if run:
    run.total_artifacts = (run.total_artifacts or 0) + 1
    run.total_words = (run.total_words or 0) + word_count
    await self.session.flush()
    logger.info(f"✅ Run totals updated: artifacts={run.total_artifacts}, words={run.total_words}")

return artifact
```

---

## 🧪 Tests Performed

| Test | Artifact Saved | Totals Updated | Notes |
|------|---------------|----------------|-------|
| SQL UPDATE with expressions | ✅ | ❌ | UPDATE affected 1 row but didn't persist |
| SQL UPDATE with func.coalesce | ✅ | ❌ | Same result |
| ORM direct modification | ✅ | ❌ | Logs show correct values |

---

## 🔧 Next Steps

### Immediate (In Progress)
1. ✅ Add commit logging
2. ⏳ Test with commit logging
3. ⏳ Check if commit actually executes

### If Still Failing
1. Try explicit `session.refresh(run)` after update
2. Try separate transaction for run update
3. Check PostgreSQL transaction logs
4. Try raw SQL UPDATE outside ORM
5. Check for database triggers or constraints

### Alternative Approaches
1. **Post-commit update:** Update totals after artifact is committed
2. **Separate endpoint:** Add `/update-totals` endpoint to fix existing runs
3. **Database trigger:** PostgreSQL trigger to auto-update totals
4. **Async task:** Update totals in background worker

---

## 📈 Impact

### User Experience
- ✅ Artifacts ARE generated and accessible via `/artifacts` endpoint
- ❌ Run listing shows `0 documents` (incorrect)
- ❌ Metrics/analytics incorrect
- ⚠️ Workaround: Can still view artifacts directly

### System Integrity
- Database inconsistency between `documentation_artifacts` and `documentation_runs`
- Run totals (total_artifacts, total_words) don't reflect reality
- Potential issues with pagination, filtering, or sorting by document count

---

## 📝 Commits

| Commit | Description | Result |
|--------|-------------|--------|
| `a4e95eda` | Initial fix attempt | Failed - missing session |
| `b6a71307` | Fix session instantiation | Failed - totals still 0 |
| `8e858a06` | Add func.coalesce() | Failed - UPDATE didn't persist |
| `36d2be4b` | Switch to ORM update | Failed - totals still 0 |
| `f1718f58` | Add debug logging | Helped diagnose |
| `d563b341` | Add commit logging | Testing in progress |

---

## 🎯 Success Criteria

- [ ] `total_artifacts` increments correctly
- [ ] `total_words` increments correctly  
- [ ] API returns correct `total_documents`
- [ ] Database shows consistent state
- [ ] No manual intervention needed

---

**Last Updated:** 2025-11-20 20:15 UTC  
**Next Action:** Test with commit logging, investigate transaction isolation

