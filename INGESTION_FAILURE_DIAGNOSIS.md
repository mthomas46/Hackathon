# 🔍 Ingestion Job Failure Diagnosis

**Job ID:** `90048d17-9426-4e9f-8121-5b6eca88e701`  
**Status:** Completed (but with 100% failures)  
**Date:** October 14, 2025

---

## 📊 Job Metrics

```
Processed: 0 / 319 documents
Failed: 319 (100%)
Skipped: 0
Embeddings: 0
Status: completed (no error_message)
```

---

## 🐛 Problem Analysis

### What Happened
The job shows as "completed" but ALL 319 files failed to process. This is unusual because:

1. **No error_message:** The job record has no `error_message` field populated
2. **100% failure rate:** Every single file failed
3. **Status = "completed":** Job didn't crash, it ran to completion
4. **Silent failures:** No exceptions logged in container logs

### How Failures Are Tracked

From `job_processor.py` line 256-259:
```python
if file_result["success"]:
    result["processed"] += 1
elif file_result.get("skipped"):
    result["skipped"] += 1  # Duplicates
else:
    result["failed"] += 1  # Actual errors
```

**A file is marked as "failed" when:**
- `success = False` (exception occurred in `_process_file`)
- NOT marked as `skipped` (not a duplicate)

---

## 🔍 Possible Causes (Most Likely First)

### 1. ❌ Git Repository Issue (MOST LIKELY)
**Symptoms match perfectly:**
- Worker can't read /app as git repo
- Every file fails at git content retrieval
- No error_message (exception caught at file level, not job level)

**Evidence from logs:**
```
InvalidGitRepositoryError: /app
```

**Why this causes 100% failure:**
- `git_service.get_file_content_at_commit()` fails for EVERY file
- Exception caught per-file, so job "completes"
- No job-level error because git check passes initially

**Fix:**
```bash
docker exec ecosystem-mcp-service git init /app
docker exec ecosystem-mcp-service git add -A
docker exec ecosystem-mcp-service git commit -m "Initial commit"
```

### 2. Database Connection Lost During Processing
- PostgreSQL connection dropped mid-job
- Each file fails at document save
- Worker kept trying all files

### 3. ChromaDB Connection Issue
- ChromaDB became unreachable
- Failures at embedding storage
- But this shouldn't fail the entire file (only sets `embedding_failed`)

### 4. Normalizer/Parser Errors
- All files of certain type(s)
- Parser crashed for specific format
- Less likely (would expect some diversity in file types)

---

## 🔬 Verification Steps

### Check Git Repository Status
```bash
# Is /app a valid git repo?
docker exec ecosystem-mcp-service git -C /app status

# Are there commits?
docker exec ecosystem-mcp-service git -C /app log --oneline -5
```

**Expected:** Should show commits
**If broken:** Shows `fatal: not a git repository`

### Check Recent Processing
```bash
# Check if other jobs succeeded
curl http://localhost:8000/api/v1/admin/ingest/status

# Look for pattern: 
# - Jobs before 90048d17: success
# - Jobs after: also failing?
```

### Check Worker Logs (if available)
```bash
# Get detailed logs for this job
docker logs ecosystem-mcp-service 2>&1 | grep -C 20 "90048d17"
```

### Check Database Connectivity
```bash
# Can worker reach PostgreSQL?
docker exec ecosystem-mcp-service wget -qO- http://ecosystem-mcp-postgres:5432 2>&1
```

---

## ✅ Immediate Fix

Based on the evidence, the most likely issue is `/app` not being a git repository:

### Step 1: Reinitialize Git Repo in Container
```bash
docker exec ecosystem-mcp-service git init /app
docker exec ecosystem-mcp-service git config user.email "worker@ecosystem-mcp"
docker exec ecosystem-mcp-service git config user.name "Ecosystem Worker"
docker exec ecosystem-mcp-service git -C /app add -A
docker exec ecosystem-mcp-service git -C /app commit -m "Reinitialize for ingestion"
```

### Step 2: Verify Git is Working
```bash
docker exec ecosystem-mcp-service git -C /app log --oneline -1
```

Should show:
```
<commit-hash> Reinitialize for ingestion
```

### Step 3: Start New Test Job
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/app", "mode": "quick"}'
```

### Step 4: Monitor Progress
- Go to: http://localhost:8501 → Ingestion Manager
- Enable auto-refresh
- Watch for successful processing

---

## 📋 Expected Behavior After Fix

**Before (Broken):**
```
Job: 90048d17...
Status: completed
Processed: 0 / 319
Failed: 319
```

**After (Fixed):**
```
Job: <new-job-id>
Status: processing → completed
Processed: 300+ / 319
Failed: 0-10 (expected failures for large/binary files)
Skipped: 0-100 (duplicates from previous runs)
```

---

## 🎯 Root Cause

**Most Likely:** The `/app` directory lost its git initialization after a container restart/rebuild.

**Why it happened:**
1. Git repo is initialized in `/app` (inside container)
2. Container gets recreated (`docker-compose down && up`)
3. Volume mount brings back files but NOT the `.git` directory (if .git is in .gitignore or not mounted)
4. Worker tries to run but can't read git history
5. Every file fails at `git_service.get_file_content_at_commit()`

**Long-term fix:**
- Ensure `.git` directory persists across restarts
- Or reinitialize on container startup
- Or use a Docker volume for `/app/.git`

---

## 🚨 Why No error_message?

The job has no `error_message` because:

1. **File-level exceptions** are caught in `_process_file`:
   ```python
   except Exception as e:
       result["error"] = str(e)  # ← Only in file result
   ```

2. **Job-level success** is still True:
   ```python
   result["success"] = True  # ← Job completes even if all files fail
   ```

3. **Error message only set on job-level failure:**
   ```python
   if not result["success"]:
       job.error_message = result.get("error")  # ← Only if job crashes
   ```

**This is actually correct behavior:**
- Job runs to completion (doesn't crash)
- Individual files fail (tracked in metrics)
- Job.error_message is for catastrophic failures (e.g., git repo not found at job start)

---

## 🔮 Future Improvements

### Better Error Tracking
- Store failed file paths and errors in job_metadata
- Add endpoint to view failed file details
- Surface common failure reasons in dashboard

### Better Error Messages
- If >50% files fail with same error, set job.error_message
- Add "dominant_error" field to job results
- Show in dashboard: "319 files failed with: InvalidGitRepositoryError"

### Preemptive Checks
- Before starting job, verify git repo is valid
- Check database connectivity
- Check ChromaDB connectivity
- Fail fast if infrastructure is broken

---

## 📚 Related Files

- `services/ecosystem-mcp/src/services/ingestion/job_processor.py` (lines 376-547)
  - `_process_file` method
  - Error handling logic
  
- `services/ecosystem-mcp/src/services/ingestion/ingestion_worker.py` (lines 149-217)
  - Job processing orchestration
  - Job status updates

- `services/ecosystem-mcp/src/services/git/git_service.py`
  - Git operations
  - File content retrieval

---

## ✅ Next Steps

1. **Reinitialize /app as git repo** (most likely fix)
2. **Start new test job** to verify
3. **Monitor for success** in dashboard
4. **If still failing:** Check database/ChromaDB connectivity
5. **Consider:** Adding pre-job validation checks

---

*Last Updated: October 14, 2025*

---

## 🔬 Investigation Results

### Git Status: ✅ WORKING
```bash
$ docker exec ecosystem-mcp-service git -C /app status
On branch master
...working correctly...

$ docker exec ecosystem-mcp-service git -C /app log --oneline -5
a9542a2 Init

$ docker exec ecosystem-mcp-service git -C /app ls-tree -r --name-only a9542a2 | wc -l
541 files
```

### File Retrieval Test: ✅ WORKING
```
Total files found: 541
Testing file: .deployment_state.json
✅ Success! Content length: 133
```

### 🎯 New Analysis

**Job processed 319 files but found 541 total:**
- Total files in commit: 541
- Files after filtering: 319 (filtered by `_filter_files`)
- Files processed: 0
- Files failed: 319
- Files skipped: 0

**This means:**
1. Git is working fine
2. File content retrieval is working
3. Filtering is working (541 → 319)
4. **Something AFTER git retrieval is failing**

### Possible Failure Points (Ordered by Likelihood)

####  1. ❌ Database Connection Issue (NEW #1)
**Most likely given symptoms:**
- Job "completed" (didn't crash at job level)
- Every file failed (100% failure)
- No error_message on job
- Happened during processing

**What probably happened:**
- PostgreSQL connection was lost/broken mid-job
- Each file fails at `doc_repo.create(document)`
- Exception caught per-file
- Job continues to process all files
- All fail with same error

**How to verify:**
```bash
# Check PostgreSQL logs for disconnections around 21:27-21:31
docker logs ecosystem-mcp-postgres 2>&1 | grep -E "21:2[7-9]|21:3[0-1]"

# Check if there were connection issues
docker logs ecosystem-mcp-postgres 2>&1 | grep -i "connection\|disconnect\|timeout"
```

#### 2. ❌ ChromaDB Embedding Storage Failure
**Possible but less likely:**
- ChromaDB became unreachable
- Each file fails at `chroma.add_embeddings_with_retry`
- But wait... code shows `embedding_failed` flag should be set, not full failure
- Unless retry logic itself crashes?

**From code:**
```python
if not embedding_success:
    logger.error(f"⚠️ Failed to store embedding for {path} after retries, but document saved")
    result["embedding_failed"] = True
    # ← Should NOT fail the file!
```

So this shouldn't cause 100% failure unless the retry logic itself throws an exception.

#### 3. ❌ Embedding Generation Service Failure
**Also possible:**
- Ollama/embedding service became unavailable
- `embedding_service.generate_embedding()` fails for every file
- Exception not caught at embedding level

**How to verify:**
```bash
# Check Ollama status during that time
docker logs ecosystem-mcp-ollama 2>&1 | grep -E "21:2[7-9]|21:3[0-1]"
```

#### 4. ❌ Normalizer Crashes
**Less likely:**
- Would expect some file types to work
- Unless all 319 files are same type that has broken normalizer

### 🔍 The Mystery of the Missing Error

**Why no error_message on job?**

Looking at the code flow:

1. **File-level exception:**
   ```python
   # In _process_file (line 541)
   except Exception as e:
       result["error"] = str(e)  # ← Error only in file result
       # Job continues...
   ```

2. **Job continues:**
   ```python
   # In process (line 148-158)
   for commit in commits:
       commit_result = await self._process_commit(commit, job)
       result["failed_documents"] += commit_result["failed"]
   # After loop:
   result["success"] = True  # ← Job "succeeds"
   ```

3. **Job marked as completed:**
   ```python
   # In ingestion_worker (line 178-188)
   job.status = "completed" if result["success"] else "failed"
   if not result["success"]:
       job.error_message = result.get("error")  # ← Never executed
   ```

**Result:** Job shows "completed" with no error_message, but all files failed.

### 💡 Recommended Investigation Steps

1. **Check Database Connection Pool:**
   ```bash
   # Is PostgreSQL healthy?
   docker exec ecosystem-mcp-postgres pg_isready
   
   # Check active connections
   docker exec ecosystem-mcp-postgres psql -U admin -d ecosystem_mcp -c \
     "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
   ```

2. **Check Embedding Service:**
   ```bash
   # Is Ollama responsive?
   curl -s http://localhost:11434/api/tags | python3 -m json.tool
   ```

3. **Start a NEW test job and monitor logs in real-time:**
   ```bash
   # Terminal 1: Watch logs
   docker logs -f ecosystem-mcp-service
   
   # Terminal 2: Start job
   curl -X POST http://localhost:8000/api/v1/admin/ingest \
     -H "Content-Type: application/json" \
     -d '{"repo_path": "/app", "mode": "quick"}'
   
   # Terminal 3: Monitor progress
   # Dashboard: http://localhost:8501 → Ingestion Manager
   ```

4. **Check for file-specific errors in logs:**
   ```bash
   docker logs ecosystem-mcp-service 2>&1 | grep -E "Error processing file|Failed to process" | tail -20
   ```

### 📊 What to Look For in New Test Job

**Healthy behavior:**
```
Processing commit 1/1: a9542a2
Commit a9542a2: 319/541 files to process
✅ Processed services/api/routes/admin.py
✅ Processed services/config.py
...
✅ Job completed: 300+/319 documents
```

**Broken behavior (same as job 90048d17):**
```
Processing commit 1/1: a9542a2
Commit a9542a2: 319/541 files to process
❌ Error processing file .deployment_state.json: [same error for all]
❌ Error processing file .dockerignore: [same error for all]
...
✅ Job completed: 0/319 documents, 319 failed
```

**Look for the repeated error message!**

---

*Investigation Updated: October 14, 2025*
