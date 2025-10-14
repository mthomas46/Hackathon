# 🚀 Ingestion System - Quick Reference

**Last Updated:** October 14, 2025

---

## ⚡ Quick Start

### Start Ingestion (Dashboard)
```
1. Open: http://localhost:8501
2. Go to: Ingestion Manager
3. Tab: Start Ingestion
4. Set path: /app (or custom path)
5. Mode: quick/full/incremental
6. Click: Start Ingestion
```

### Start Ingestion (API)
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/app", "mode": "quick"}'
```

### Check Status
```bash
curl http://localhost:8000/api/v1/admin/ingest/status
```

---

## 📊 Understanding Metrics

### Processed ✅
**New documents successfully ingested**
- Content parsed and normalized
- Embedding generated
- Stored in PostgreSQL + ChromaDB

### Skipped ⏭️
**Duplicates (NOT errors!)**
- Identical content already exists
- May have enriched existing metadata
- This is NORMAL and GOOD

### Failed ❌
**Actual errors**
- Parse errors
- Validation failures
- Database errors
- These need attention

### Embeddings 🧬
**Vector embeddings generated**
- Should match "Processed" count
- Used for semantic search
- Stored in ChromaDB

---

## 🎯 Common Scenarios

### Scenario 1: High Skip Rate
```
Processed: 3
Skipped: 316
Failed: 0

✅ NORMAL! Most files were already ingested
```

### Scenario 2: High Failure Rate
```
Processed: 10
Skipped: 50
Failed: 100

⚠️ INVESTIGATE! Check error logs
```

### Scenario 3: All New
```
Processed: 2,367
Skipped: 0
Failed: 0

✅ GREAT! First ingestion or fresh data
```

### Scenario 4: All Skipped
```
Processed: 0
Skipped: 319
Failed: 0

✅ NORMAL! Re-ingesting same data
```

---

## 🔧 Troubleshooting

### Problem: Job stuck at "processing"
**Solution:**
1. Check logs: `docker logs ecosystem-mcp-service`
2. Verify worker is running (it's embedded in main service)
3. Check for errors in logs
4. Restart service: `docker restart ecosystem-mcp-service`

### Problem: High failure rate
**Solution:**
1. Check error messages in job details
2. Common causes:
   - Invalid file formats
   - Permission issues
   - Missing dependencies
   - Git repository issues
3. Fix root cause and re-run

### Problem: No embeddings despite processed docs
**Solution:**
1. Check ChromaDB logs
2. Verify ChromaDB path is writable
3. Check for ChromaDB errors in main service logs
4. Retry mechanism will attempt 3 times automatically

### Problem: ChromaDB connection errors
**Solution:**
✅ **AUTO-FIXED!** System will:
1. Detect connection loss
2. Attempt to restart client
3. Retry operation up to 3 times
4. Only fail if all retries exhausted

---

## 📁 Key Files

### Backend
```
src/storage/chromadb_client.py       - ChromaDB with auto-restart
src/services/ingestion/job_processor.py  - Main processing logic
src/services/ingestion/ingestion_worker.py  - Background worker
src/api/routes/admin.py              - Admin endpoints
```

### Frontend
```
dashboard_views/ingestion_manager.py - Ingestion dashboard
```

### Data
```
/app/data/chroma_db/          - ChromaDB persistent storage
PostgreSQL: ingestion_jobs    - Job status table
PostgreSQL: documents         - Document storage
```

---

## 🔑 Key Concepts

### Duplicate Detection
**How it works:**
1. Hash document content (SHA-256)
2. Check if hash exists in database
3. If exists → Skip (may enrich metadata)
4. If new → Process and store

**Why it's good:**
- Prevents redundant data
- Saves storage space
- Avoids duplicate embeddings
- Maintains data integrity

### Metadata Enrichment
**What it does:**
- Finds missing fields in existing document
- Adds data from duplicate document
- Merges arrays (tags, categories)
- Never overwrites existing data

**Example:**
```
Existing: {author: "Alice", tags: ["python"]}
Duplicate: {tags: ["api"], description: "API docs"}
Result: {author: "Alice", tags: ["python", "api"], description: "API docs"}
```

### Retry Logic
**Strategy:**
1. First attempt: Immediate
2. Second attempt: After 1 second
3. Third attempt: After 2 seconds
4. Give up: After 4 more seconds

**When used:**
- ChromaDB operations
- Embedding storage
- Transient failures

---

## 📞 API Endpoints

### Start Ingestion
```
POST /api/v1/admin/ingest
Body: {"repo_path": "/app", "mode": "quick"}
```

### Get All Jobs
```
GET /api/v1/admin/ingest/status
```

### Get Job Details
```
GET /api/v1/admin/ingest/{job_id}
```

### Clear Data
```
DELETE /api/v1/admin/data/postgres
DELETE /api/v1/admin/data/chromadb
```

### Get Statistics
```
GET /api/v1/admin/data/stats
```

---

## 🎓 Best Practices

### 1. Use Appropriate Mode
```
quick: Last 10 commits (fast, < 1 min)
full: All commits (slow, may take hours)
incremental: Since last ingestion (planned)
```

### 2. Monitor Logs
```bash
# Follow logs
docker logs -f ecosystem-mcp-service

# Search for errors
docker logs ecosystem-mcp-service 2>&1 | grep -i error
```

### 3. Start Fresh When Needed
```
1. Clear data (Dashboard → Ingestion Manager → Clear Data)
2. Confirm deletion
3. Run fresh ingestion
4. Monitor progress
```

### 4. Understand Skip Rate
```
First ingestion: 0% skip rate
Subsequent runs: 90%+ skip rate is normal
Re-running same data: 100% skip rate is normal
```

---

## ⚙️ Configuration

### ChromaDB Settings
```python
# In config.py
chroma_path: ./data/chroma_db
chroma_collection_name: ecosystem_docs
```

### Retry Settings
```python
# In chromadb_client.py
max_retries: 3
backoff: exponential (1s, 2s, 4s)
```

### Worker Settings
```python
# In ingestion_worker.py
poll_interval: 5 seconds
error_backoff: 10 seconds
```

---

## 🚨 When to Contact Support

### Critical Issues
- Service won't start
- Database connection failures
- Persistent ChromaDB errors
- Data corruption

### Non-Critical Issues
- High skip rate (normal)
- Slow ingestion (depends on data)
- Minor transient errors (retry handles)

---

## ✅ Health Checks

### System Healthy
```
✅ Service: Up and responding
✅ Database: Connected
✅ ChromaDB: Accessible
✅ Worker: Running (embedded)
✅ Jobs: Processing normally
```

### Check Health
```bash
curl http://localhost:8000/health
```

### Expected Response
```json
{
  "status": "healthy",
  "database": {"status": "connected"},
  "chromadb": {"status": "accessible"}
}
```

---

## 📊 Performance Expectations

### Quick Mode (10 commits)
```
Duration: < 5 minutes
Documents: 100-500
Embeddings: 100-500
```

### Full Mode (all commits)
```
Duration: 30-60 minutes
Documents: 2,000-5,000
Embeddings: 2,000-5,000
```

### Re-ingestion (duplicates)
```
Duration: < 1 minute
Documents: 0 (all skipped)
Embeddings: 0
```

---

**Quick Reference Created:** October 14, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅

