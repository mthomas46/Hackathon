**Date:** October 30, 2025  
**Status:** Document Cleanup - Quick Start  
**Time to Deploy:** 10 minutes

---

# Document Cleanup - Quick Start

## What This Does

**Cleans up your existing 1,854 documents** using the same intelligent filtering rules we just implemented.

**Expected results:**
- Remove 500-700 low-value documents (logs, configs, build artifacts)
- Free 40-70 MB of space
- Improve RAG quality (less noise)

---

## 3-Step Deployment

### Step 1: Add Router to App (2 min)

**File:** `services/ecosystem-mcp/src/api/app.py`

Add **after line 377** (after `documents.router`):

```python
    # Document cleanup (uses intelligent filtering on existing docs)
    from .routes import document_cleanup
    app.include_router(
        document_cleanup.router,
        prefix="/api/v1/documents",
        tags=["Document Cleanup"]
    )
```

### Step 2: Rebuild & Restart (5 min)

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
docker-compose build ecosystem-mcp && docker-compose up -d
sleep 20
```

### Step 3: Run Cleanup (3 min)

```bash
# See what can be cleaned
curl http://localhost:8000/api/v1/documents/cleanup/report | jq

# Remove old versions (safe)
curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions \
  -d '{"dry_run": false}' | jq

# Remove low-value documents (logs, configs)
curl -X POST http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=false | jq
```

---

## What Gets Removed

### Old Versions (Safe to Remove)
- Non-latest document versions
- Already not searchable in RAG
- Just taking up space
- **Expected:** 600-700 documents

### Low-Value Documents (Noise)
- Logs (`.log`, `.out`)
- Configs (`.env`, `.ini`, `config.json`)
- Build artifacts (`__pycache__/`, `dist/`, `build/`)
- Package locks (`package-lock.json`)
- Virtual envs (`venv/`, `.venv/`)
- **Expected:** 200-400 documents

---

## Quick Commands

```bash
# Get report (safe)
curl http://localhost:8000/api/v1/documents/cleanup/report | jq

# Preview what would be deleted (safe)
curl -X POST .../cleanup/low-value?dry_run=true | jq | less

# Remove old versions only (safest)
curl -X POST .../cleanup/old-versions -d '{"dry_run": false}' | jq

# Remove low-value docs (logs, configs)
curl -X POST .../cleanup/low-value?dry_run=false | jq

# Check results
curl http://localhost:8000/api/v1/admin/stats | jq '.documents'
```

---

## Expected Output

### Before
```json
{
  "total_documents": 1854,
  "latest": 1200,
  "old_versions": 654
}
```

### After
```json
{
  "total_documents": 966,
  "latest": 966,
  "old_versions": 0
}
```

**Result:** 888 documents removed (47.9%)

---

## Safety

- ✅ All endpoints default to `dry_run=true` (preview mode)
- ✅ See exact list before deleting
- ✅ Reversible (re-ingest if needed)
- ✅ Logs everything

---

**Time:** 10 minutes  
**Risk:** Low  
**Impact:** High (40% space freed, better RAG quality)

