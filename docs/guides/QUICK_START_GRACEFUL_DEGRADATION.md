**Date:** October 24, 2025  
**Status:** Quick Start Guide  
**Time to Read:** 2 minutes

# Quick Start: Graceful Degradation

## 🚀 What's New (TL;DR)

Jobs now **gracefully handle failures** instead of losing all work:

- ✅ **Commit Limit:** Default 100 commits (was unlimited)
- ✅ **Partial Success:** 90/100 commits work → 90% success (not "failed")
- ✅ **Task Cancellation:** Hung commits are cancelled automatically
- ✅ **Data Recovery:** Documents from successful commits are always ingested
- ✅ **Clear Reporting:** Know exactly what worked/failed/cancelled

---

## 🎯 Quick Test

**Run an incremental job:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/repo", "mode": "incremental"}'
```

**Check job status:**
```bash
curl http://localhost:8000/api/v1/admin/ingest/<JOB_ID> | jq
```

**Expected (with problematic commits):**
```json
{
  "status": "completed",
  "processed_documents": 450,
  "total_documents": 100,
  "failed_documents": 8,
  "skipped_documents": 2,
  "warning": "Partial success: 90/100 commits succeeded (90.0%). Failed: 8, Cancelled: 0, Skipped: 2"
}
```

---

## 📊 Before vs. After

| Scenario | Before | After |
|----------|--------|-------|
| **98 commits work, 2 hang** | ❌ FAILED<br>0 documents | ✅ SUCCESS<br>490 documents |
| **All commits work** | ✅ SUCCESS<br>~5 min | ✅ SUCCESS<br>~2 min (faster) |
| **Job status** | Binary (pass/fail) | Percentage-based (90% success) |

---

## 🔧 Configuration

### Default (Safe)
- Max commits: 100
- Timeout: 90s per commit
- Graceful degradation: ENABLED

### Custom (if needed)
```python
JobProcessor(
    max_commits_to_process=200,  # Increase limit
    # ... other params
)
```

---

## 📋 Key Changes

### 1. Commit Limiting
**Before:** Full mode = 1000 commits  
**After:** Full mode = 100 commits (configurable)  
**Benefit:** 10× safer, faster

### 2. Partial Success
**Before:** 99% success = "FAILED" (lose all data)  
**After:** 99% success = "SUCCESS with warning" (keep data)  
**Benefit:** Data recovery

### 3. Task Cancellation
**Before:** Hung commits block job forever  
**After:** Hung commits cancelled after 90s  
**Benefit:** Job always completes

---

## ✅ Verification

**Check logs:**
```bash
docker logs ecosystem-mcp-service 2>&1 | grep "JobProcessor initialized"
```

**Expected:**
```
JobProcessor initialized (
  max_commits: 100, 
  graceful_degradation: ✅ ENABLED
)
```

---

## 🎓 Philosophy

> **"Some data is infinitely better than no data."**

- Partial success > total failure
- Transparency > perfection
- User gets value even if some commits fail

---

## 📚 Full Documentation

- `GRACEFUL_DEGRADATION_IMPLEMENTATION.md` - Complete technical details
- `COMPLETE_GRACEFUL_DEGRADATION_DEPLOYMENT.md` - Full deployment summary
- `JOB_MONITORING_20f2bf81.md` - Example job analysis
- `BLACKLIST_EXPANDED_TWO_COMMITS.md` - Blacklist details

---

**Ready to Use:** ✅ All features deployed and active  
**Questions?** Check full documentation above

