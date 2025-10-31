**Date:** October 24, 2025  
**Status:** ✅ LIVE - Quick start guide  
**Coverage:** User-friendly guide for enriched mode

# Enriched Mode Quick Start

## 🎯 **TL;DR**

**Enriched mode = Snapshot speed + Git metadata**

- ⚡ **8x faster** than full mode
- 🔖 Captures last commit info per file
- 📊 Works with timeline operations
- ✅ **Now the default recommendation**

---

## 🚀 **HOW TO USE (3 STEPS)**

### Option 1: Dashboard (Easiest)

**Step 1:** Open http://localhost:8501

**Step 2:** Click "📥 Ingestion Manager" → "🚀 Start Ingestion"

**Step 3:** 
- **Ingestion Type:** Select "enriched" (it's the default!)
- **Path:** Enter your repo path
- Click "🚀 Start Ingestion"

**Done!** ✅

### Option 2: API (Advanced)

```bash
# Start enriched ingestion
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/repo",
    "mode": "enriched"
  }' | jq

# Get job ID from response, then monitor:
JOB_ID="<your-job-id>"
watch -n 5 "curl -s http://localhost:8000/api/v1/admin/ingest/$JOB_ID | jq '{status, processed, total}'"
```

---

## 📊 **WHAT YOU GET**

### Git Metadata Per File

✅ **Last Commit SHA:** `a1b2c3d4...`  
✅ **Author:** `John Doe`  
✅ **Email:** `john@example.com`  
✅ **Date:** `2025-10-24T12:30:00`  
✅ **Message:** `"Updated installation docs"`

### Full Document Content

✅ **Complete text** (no truncation)  
✅ **Embeddings** (768D vectors)  
✅ **Metadata** (in ChromaDB)  
✅ **Timeline** (placement works)

---

## ⏱️ **PERFORMANCE**

| Files | Enriched | Snapshot | Full |
|-------|----------|----------|------|
| 1,000 | ~2 min | ~1 min | ~20 min |
| 5,000 | ~10 min | ~5 min | ~2 hours |
| 10,000 | ~30 min | ~15 min | ~4 hours |

**Enriched is 8x faster than full mode!**

---

## 🎯 **USE CASES**

### Perfect For:

✅ **Documentation RAG:**
- "Who last updated this doc?"
- "Which docs are stale?"
- "Show recent changes"

✅ **Code Analysis:**
- "Who owns this file?"
- "Find unmaintained files"
- "Track recent activity"

✅ **Ownership Tracking:**
- Author per file
- Staleness detection
- Activity analysis

### Not Suitable For:

❌ **Full version history** (use full mode)  
❌ **Version comparisons** (use full mode)  
❌ **Line-level blame** (use git blame)

---

## ❓ **FAQ**

### Q: When should I use enriched vs snapshot?

**Use enriched when:**
- ✅ You want git metadata (author, date)
- ✅ You care about ownership/staleness
- ✅ You want timeline operations
- ✅ Speed is important

**Use snapshot when:**
- ✅ Maximum speed is critical
- ✅ You don't need git metadata
- ✅ Non-git repositories

### Q: When should I use enriched vs full?

**Use enriched when:**
- ✅ You need git context but not full history
- ✅ You want 8x faster ingestion
- ✅ You care about current state + metadata
- ✅ 90% of use cases!

**Use full when:**
- ✅ You need complete version history
- ✅ You need version comparisons
- ✅ Compliance requires audit trail

### Q: Does enriched work with timeline?

**Yes!** ✅ 
- As-of-date queries
- Staleness detection
- Author tracking
- Timeline placement

### Q: What if git fails for a file?

**Graceful fallback!** ✅
- File still gets ingested
- Warning logged
- Continues with next file
- No metadata for that file

---

## 🔍 **VERIFY IT WORKS**

### Check Git Metadata

```bash
# Search for a document
curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "README", "n_results": 1}' \
  | jq '.results[0].metadata'
```

**Should show:**
```json
{
  "file_path": "docs/README.md",
  "git_commit_sha": "a1b2c3d4",
  "git_author": "John Doe",
  "git_date": "2025-10-24T12:30:00",
  "ingestion_mode": "enriched"
}
```

### Check Timeline

```bash
# Query timeline
curl -s -X POST http://localhost:8000/api/v1/versioning/as-of \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-10-01"}' \
  | jq '.documents[0] | {file_path, git_commit_sha}'
```

**Should return enriched documents!**

---

## 📚 **MORE INFO**

**Detailed Guides:**
- `ENRICHED_MODE_FEATURE.md` - Complete feature guide
- `ENRICHED_MODE_TIMELINE_COMPATIBILITY.md` - Timeline details
- `ENRICHED_MODE_COMPLETE.md` - Implementation summary
- `ENRICHED_MODE_DEPLOYMENT_SUMMARY.md` - Deployment details

**API Docs:**
- http://localhost:8000/docs

**Dashboard:**
- http://localhost:8501

---

**Status:** ✅ LIVE  
**Recommendation:** Use enriched for 90% of use cases  
**Performance:** 8x faster than full mode  

🚀 **Enjoy enriched mode!**

