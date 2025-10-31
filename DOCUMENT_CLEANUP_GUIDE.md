**Date:** October 30, 2025  
**Status:** Document Cleanup System Ready  
**Coverage:** Intelligent Cleanup of Existing Documents

---

# Document Cleanup System

## Overview

Clean up **existing documents** in your database using the same intelligent filtering rules that prevent noise during ingestion.

**What it does:**
- 🔍 Analyzes existing 1,854 documents
- 🎯 Identifies low-value files (logs, configs, build artifacts)
- 🧹 Removes them from PostgreSQL + ChromaDB
- 📊 Frees capacity for valuable content

---

## Quick Start

### 1. Check What Can Be Cleaned

```bash
# Get cleanup report
curl http://localhost:8000/api/v1/documents/cleanup/report | jq

# Response:
# {
#   "total_documents": 1854,
#   "latest_versions": 1200,
#   "old_versions": 654,
#   "recommendations": [
#     {
#       "action": "cleanup_low_value",
#       "count": 234,
#       "description": "Remove 234 low-value documents (logs, configs, build artifacts)"
#     },
#     {
#       "action": "cleanup_old_versions",
#       "count": 654,
#       "description": "Remove 654 old document versions (keep only latest)"
#     }
#   ]
# }
```

### 2. Preview What Would Be Deleted (DRY RUN)

```bash
# See what low-value documents would be removed
curl -X POST http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=true | jq

# Response shows:
# - How many documents would be deleted
# - List of files that would be removed
# - Categories and priorities
# - Estimated space freed
```

### 3. Actually Clean Up (After Verifying)

```bash
# Remove low-value documents (logs, configs, build artifacts)
curl -X POST http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=false | jq

# Or remove old versions (keeps only latest)
curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": false}' | jq
```

---

## What Gets Cleaned

### Low-Value Documents (SKIP Priority)

**Automatically identified as cleanup candidates:**

- **Logs:** `.log`, `.out`, `/logs/`
- **Configs:** `.env`, `.ini`, `.cfg`, `.conf`, `config.json`
- **Build artifacts:** `/dist/`, `/build/`, `__pycache__/`, `.pyc`, `.class`
- **Package locks:** `package-lock.json`, `yarn.lock`, `poetry.lock`
- **Virtual envs:** `/venv/`, `/.venv/`, `/env/`
- **Data files:** `.csv`, `.db`, `.sqlite` (large, low RAG value)
- **IDE files:** `.DS_Store`, `/.idea/`, `/.vscode/`

### Old Versions

**Non-latest versions of documents:**
- Same file, older content_hash
- Marked as `is_latest = false`
- Not in ChromaDB (not searchable)
- Taking up PostgreSQL space

---

## API Endpoints

### 1. Get Cleanup Report

**Endpoint:** `GET /api/v1/documents/cleanup/report`

**Description:** Get recommendations for what can be cleaned

**Example:**
```bash
curl http://localhost:8000/api/v1/documents/cleanup/report | jq
```

**Response:**
```json
{
  "success": true,
  "report": {
    "timestamp": "2025-10-30T16:00:00",
    "total_documents": 1854,
    "latest_versions": 1200,
    "old_versions": 654,
    "analysis": {
      "by_priority": {
        "CRITICAL": 5,
        "HIGH": 150,
        "MEDIUM": 800,
        "LOW": 200,
        "SKIP": 699
      },
      "by_category": {
        "documentation": 155,
        "source_code": 800,
        "test": 200,
        "configuration": 234,
        "temporary": 465
      },
      "cleanup_candidates": 699
    },
    "recommendations": [
      {
        "action": "cleanup_low_value",
        "count": 699,
        "description": "Remove 699 low-value documents"
      }
    ]
  }
}
```

---

### 2. Analyze Documents

**Endpoint:** `POST /api/v1/documents/cleanup/analyze`

**Description:** Detailed analysis of cleanup candidates

**Parameters:**
- `include_latest` (bool): Analyze latest versions too
- `min_priority` (string): Minimum priority to keep (CRITICAL, HIGH, MEDIUM, LOW)

**Example:**
```bash
# Analyze everything below MEDIUM priority
curl -X POST "http://localhost:8000/api/v1/documents/cleanup/analyze?min_priority=MEDIUM" | jq
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "total_analyzed": 1854,
    "cleanup_candidates": [
      {
        "id": "abc-123",
        "file_path": "logs/app.log",
        "priority": "SKIP",
        "category": "temporary",
        "reason": "Log file",
        "is_latest": true,
        "has_embedding": true
      },
      ...
    ],
    "keep_documents": [...],
    "statistics": {
      "by_priority": {...},
      "by_category": {...}
    }
  }
}
```

---

### 3. Cleanup Low-Value Documents

**Endpoint:** `POST /api/v1/documents/cleanup/low-value`

**Description:** Quick cleanup of logs, configs, build artifacts

**Parameters:**
- `dry_run` (bool, default: true): Preview mode

**Example (DRY RUN):**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=true" | jq
```

**Example (ACTUAL DELETE):**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=false" | jq
```

**Response:**
```json
{
  "success": true,
  "result": {
    "dry_run": false,
    "deleted": 699,
    "embeddings_deleted": 234,
    "statistics": {
      "by_category": {
        "temporary": 465,
        "configuration": 234
      }
    }
  }
}
```

---

### 4. Cleanup Old Versions

**Endpoint:** `POST /api/v1/documents/cleanup/old-versions`

**Description:** Remove old document versions (keep only latest)

**Body:**
```json
{
  "dry_run": true,
  "older_than_days": 90  // Optional: only delete versions older than N days
}
```

**Example (DRY RUN):**
```bash
curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": true}' | jq
```

**Example (DELETE all old versions):**
```bash
curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": false}' | jq
```

**Response:**
```json
{
  "success": true,
  "result": {
    "dry_run": false,
    "deleted": 654,
    "embeddings_deleted": 0
  }
}
```

---

### 5. Cleanup By Category

**Endpoint:** `POST /api/v1/documents/cleanup/by-category`

**Description:** Clean up specific categories

**Categories:**
- `temporary`: Logs, temp files
- `configuration`: Config files
- `build_artifact`: Build outputs
- `test`: Test files
- `data`: Data files

**Body:**
```json
{
  "categories": ["temporary", "configuration"],
  "dry_run": true
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/documents/cleanup/by-category \
  -H 'Content-Type: application/json' \
  -d '{"categories": ["temporary", "configuration"], "dry_run": false}' | jq
```

---

### 6. Advanced Cleanup

**Endpoint:** `POST /api/v1/documents/cleanup/execute`

**Description:** Full control over cleanup

**Body:**
```json
{
  "dry_run": true,
  "include_latest": false,
  "categories_to_remove": ["temporary"],
  "min_priority": "LOW"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/documents/cleanup/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "dry_run": false,
    "include_latest": true,
    "min_priority": "MEDIUM"
  }' | jq
```

---

## Common Scenarios

### Scenario 1: Free Up Space Quickly

**Goal:** Remove obvious noise (logs, configs)

```bash
# 1. Check what would be removed
curl -X POST "http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=true" | jq

# 2. Review the list (check candidates)

# 3. Actually remove
curl -X POST "http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=false" | jq
```

**Expected Result:**
- 400-700 documents removed
- 50-150 MB freed
- Only low-value files deleted
- Source code and docs untouched

---

### Scenario 2: Remove Old Versions Only

**Goal:** Keep latest, remove history (safe cleanup)

```bash
# 1. See how many old versions exist
curl http://localhost:8000/api/v1/documents/cleanup/report | jq '.report.old_versions'

# 2. Preview deletion
curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions \
  -d '{"dry_run": true}' | jq

# 3. Delete old versions
curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions \
  -d '{"dry_run": false}' | jq
```

**Expected Result:**
- 500-700 old versions removed
- Latest versions intact
- No functional impact (old versions weren't searchable anyway)

---

### Scenario 3: Targeted Category Cleanup

**Goal:** Remove specific types of files

```bash
# Remove only logs and temp files
curl -X POST http://localhost:8000/api/v1/documents/cleanup/by-category \
  -H 'Content-Type: application/json' \
  -d '{"categories": ["temporary"], "dry_run": false}' | jq

# Remove only configs
curl -X POST http://localhost:8000/api/v1/documents/cleanup/by-category \
  -H 'Content-Type: application/json' \
  -d '{"categories": ["configuration"], "dry_run": false}' | jq
```

---

### Scenario 4: Aggressive Cleanup

**Goal:** Keep only HIGH and CRITICAL priority docs

```bash
# This will remove MEDIUM, LOW, and SKIP priority documents
curl -X POST http://localhost:8000/api/v1/documents/cleanup/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "dry_run": false,
    "include_latest": true,
    "min_priority": "HIGH"
  }' | jq
```

**⚠️ Warning:** This is aggressive! Will remove:
- All source code (MEDIUM)
- All tests (LOW)
- All low-value files (SKIP)

Only use if you want **documentation-only** RAG!

---

## Safety Features

### 1. Dry-Run by Default

All endpoints default to `dry_run=true`:
- See what would be deleted
- Verify before actual deletion
- No accidental data loss

### 2. Detailed Preview

Dry-run shows:
- Exact list of files (first 50)
- Categories and priorities
- Estimated space freed
- Statistics

### 3. Granular Control

Choose what to delete:
- By priority (SKIP only, LOW and below, etc.)
- By category (temporary, configuration, etc.)
- By age (old versions only)
- By latest status

### 4. Logs Everything

All cleanup operations are logged:
- What was analyzed
- What was deleted
- Any errors
- Statistics

---

## Expected Results

### Before Cleanup

```
Total documents:     1,854
├─ Latest versions:  1,200
│  ├─ Documentation:   155 (HIGH)
│  ├─ Source code:     800 (MEDIUM)
│  ├─ Tests:           200 (LOW)
│  └─ Noise:           45  (SKIP)  ← Should be removed
└─ Old versions:     654   ← Should be removed

ChromaDB embeddings: 1,200
PostgreSQL space:    200 MB
```

### After Cleanup (Low-Value + Old Versions)

```
Total documents:     1,155
├─ Latest versions:  1,155
│  ├─ Documentation:   155 (HIGH)
│  ├─ Source code:     800 (MEDIUM)
│  └─ Tests:           200 (LOW)
└─ Old versions:     0    ✅ Removed

Removed:             699 documents (37.7%)
ChromaDB embeddings: 1,155
PostgreSQL space:    150 MB ✅ Freed 50 MB
```

### Space Available

```
Before:
- Documents in RAG: 1,200
- Capacity: 2,000
- Headroom: 800 (40%)

After:
- Documents in RAG: 1,155
- Capacity: 2,000
- Headroom: 845 (42%)
```

---

## Integration with App

Add to `src/api/app.py`:

```python
# Document cleanup
from .routes import document_cleanup

app.include_router(
    document_cleanup.router,
    prefix="/api/v1/documents",
    tags=["Document Cleanup"]
)
```

---

## Monitoring

### Check Cleanup Results

```bash
# Before cleanup
curl http://localhost:8000/api/v1/admin/stats | jq '.documents.total'
# Output: 1854

# After cleanup
curl http://localhost:8000/api/v1/admin/stats | jq '.documents.total'
# Output: 1155

# Difference: 699 documents removed ✅
```

### Check Logs

```bash
docker logs ecosystem-mcp-service | grep "Cleanup\|Deleted"

# Expected output:
# 🧹 Cleaning up categories: ['temporary', 'configuration']
# 📊 Found 699 cleanup candidates
# 🗑️  Deleted embedding for logs/app.log
# ✅ Cleanup complete: Deleted 699 documents, 234 embeddings
```

---

## Troubleshooting

### "No cleanup candidates found"

**Possible reasons:**
1. Your documents are already clean (good!)
2. Intelligent filtering was already used during ingestion
3. Check report to see distribution

**Action:** Run report first
```bash
curl http://localhost:8000/api/v1/documents/cleanup/report | jq
```

---

### "Endpoint not found (404)"

**Reason:** Router not added to app

**Fix:** Add to `src/api/app.py`:
```python
from .routes import document_cleanup
app.include_router(document_cleanup.router, prefix="/api/v1/documents")
```

Then rebuild container.

---

### "Important files being deleted"

**Reason:** Rules might be too aggressive

**Action:** 
1. Always dry-run first
2. Check candidates list
3. Use more specific categories or priorities
4. If a file shouldn't be marked SKIP, add custom rule

---

## Best Practices

### 1. Always Dry-Run First

```bash
# GOOD: Check first
curl -X POST .../cleanup/low-value?dry_run=true
# Review results
curl -X POST .../cleanup/low-value?dry_run=false

# BAD: Delete without checking
curl -X POST .../cleanup/low-value?dry_run=false  # ❌ Don't do this first!
```

### 2. Start Conservative

```bash
# Start with safest cleanup (old versions only)
curl -X POST .../cleanup/old-versions -d '{"dry_run": false}'

# Then remove obvious noise
curl -X POST .../cleanup/low-value?dry_run=false

# Finally, aggressive if needed
curl -X POST .../cleanup/execute -d '{"min_priority": "MEDIUM", "dry_run": false}'
```

### 3. Monitor After Cleanup

```bash
# Check stats before/after
curl http://localhost:8000/api/v1/admin/stats

# Test RAG quality
curl -X POST http://localhost:8000/api/v1/ask \
  -d '{"question": "What is the architecture?"}'

# Verify search still works well
```

### 4. Run Periodically

```bash
# Schedule monthly cleanup (cron)
0 0 1 * * curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions -d '{"dry_run": false}'
```

---

## Summary

### What This Enables

✅ **Retroactive filtering** - Apply intelligent rules to existing docs  
✅ **Capacity recovery** - Free up 30-40% space  
✅ **Quality improvement** - Remove noise from RAG  
✅ **Automated cleanup** - API-based, schedulable  
✅ **Safe operations** - Dry-run, preview, granular control  

### Quick Wins

**5-Minute Cleanup:**
```bash
# 1. Get report (30 seconds)
curl http://localhost:8000/api/v1/documents/cleanup/report | jq

# 2. Preview low-value cleanup (1 minute)
curl -X POST .../cleanup/low-value?dry_run=true | jq | less

# 3. Execute (3 minutes)
curl -X POST .../cleanup/low-value?dry_run=false | jq

# Result: 500-700 documents removed, 40-70 MB freed
```

---

**Status:** Ready to Use  
**Risk:** Low (dry-run default, reversible via re-ingestion)  
**Impact:** High (30-40% space recovery)

