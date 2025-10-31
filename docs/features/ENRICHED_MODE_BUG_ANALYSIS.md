**Date:** October 25, 2025  
**Status:** Critical Bug - Enriched Mode Blocked  
**Severity:** High (blocks Temporal RAG timeline creation)  

---

# Enriched Mode Foreign Key Constraint Bug

## Executive Summary

Enriched mode ingestion is **currently broken** due to a foreign key constraint violation. The feature attempts to reference git commit SHAs that don't exist in the database, causing all enriched ingestions to fail silently (0 documents processed).

---

## Bug Details

### Error Message
```
insert or update on table "documents" violates foreign key constraint 
"documents_git_commit_sha_fkey"

DETAIL: Key (git_commit_sha)=(6d39a3e760e5f59626a845fc0711f2c3ba188ee5) 
is not present in table "git_commits".
```

### Root Cause
1. **Enriched mode** fetches the last commit SHA for each file using `git log`
2. It tries to insert a `Document` record with `git_commit_sha = <sha>`
3. The database has a foreign key constraint: `documents.git_commit_sha` → `git_commits.sha`
4. **The commit record doesn't exist** in `git_commits` table
5. PostgreSQL rejects the insert → **Foreign Key Violation**

### Observed Behavior
- Job status: "processing" (forever)
- Documents processed: 0
- Embeddings generated: 0
- Duration: Hangs indefinitely
- Logs: Repeated foreign key violation errors

---

## Database Schema

### Foreign Key Constraint
```sql
ALTER TABLE documents 
  ADD CONSTRAINT documents_git_commit_sha_fkey 
  FOREIGN KEY (git_commit_sha) 
  REFERENCES git_commits(sha);
```

### Missing Step
The enriched mode code path does:
1. ✅ Read files from filesystem
2. ✅ Get last commit SHA for each file
3. ❌ **MISSING:** Insert commit into `git_commits` table
4. ❌ **FAILS:** Insert document with commit SHA reference

---

## Code Path Analysis

### Current Implementation (Broken)
```python
# In enriched mode ingestion
for file in files:
    last_commit_sha = get_last_commit_for_file(file)
    
    # ❌ This fails because git_commit_sha doesn't exist
    document = Document(
        path=file,
        content=read_file(file),
        git_commit_sha=last_commit_sha,  # Foreign key violation!
        ...
    )
    session.add(document)
```

### Required Fix
```python
# In enriched mode ingestion
for file in files:
    last_commit_sha = get_last_commit_for_file(file)
    commit_info = get_commit_info(last_commit_sha)
    
    # ✅ First, ensure commit exists in database
    git_commit = await ensure_git_commit_exists(
        session,
        sha=last_commit_sha,
        author=commit_info.author,
        date=commit_info.date,
        message=commit_info.message
    )
    
    # ✅ Then insert document (foreign key satisfied)
    document = Document(
        path=file,
        content=read_file(file),
        git_commit_sha=last_commit_sha,
        ...
    )
    session.add(document)
```

---

## Impact

### Blocked Features
1. ❌ **Enriched Mode Ingestion** - Completely broken
2. ❌ **Timeline Creation** - Requires git commit metadata
3. ❌ **Temporal RAG Evolution Queries** - Need timelines
4. ❌ **Git History Context** - Documents missing commit links

### Working Features
1. ✅ **Snapshot Mode** - Works (no git metadata)
2. ✅ **Full History Mode** - Works (creates commits properly)
3. ✅ **Incremental Mode** - Works (creates commits properly)

---

## Test Results

### Job: 339b9ef1-50e2-4f36-8940-f4e60000f473
- **Mode:** enriched
- **Status:** completed (but failed silently)
- **Processed:** 0 documents
- **Duration:** ~1 second
- **Error:** Foreign key violation (not surfaced to user)

### Job: 2296e974-1df1-42db-9c5c-7ac0a95e016d
- **Mode:** enriched
- **Status:** processing (hanging)
- **Processed:** 0 documents
- **Duration:** 194+ seconds
- **Error:** Repeated foreign key violations

---

## Fix Requirements

### 1. Add Git Commit Creation
**File:** `services/ecosystem-mcp/src/services/ingestion/ingestion_worker.py`  
**Location:** `_process_enriched_snapshot()` method

**Changes:**
```python
async def _process_enriched_snapshot(self, ...):
    # ...existing file discovery...
    
    for file in files:
        try:
            # Get last commit for file
            last_commit = repo.git.log(
                "-1", 
                "--pretty=format:%H|%an|%ae|%ad|%s",
                "--date=iso",
                "--", file_path
            )
            
            if last_commit:
                sha, author, email, date, message = last_commit.split("|", 4)
                
                # ✅ NEW: Ensure commit exists in database
                from ...storage.repositories import GitCommitRepository
                git_repo = GitCommitRepository(session)
                
                commit_exists = await git_repo.get_by_sha(sha)
                if not commit_exists:
                    await git_repo.create(
                        sha=sha,
                        author=author,
                        author_email=email,
                        commit_date=parse_iso_date(date),
                        message=message,
                        repo_path=str(repo.working_dir)
                    )
                
                # ✅ Now document insert will succeed
                document = Document(
                    git_commit_sha=sha,
                    ...
                )
        except Exception as e:
            logger.error(f"Failed to process {file}: {e}")
            continue
```

### 2. Improve Error Handling
**Current:** Silent failure, job shows "completed" with 0 docs  
**Required:** Surface foreign key violations to user, mark job as "failed"

```python
try:
    await session.add(document)
    await session.flush()
except ForeignKeyViolationError as e:
    if "git_commit_sha_fkey" in str(e):
        logger.error(
            f"Missing git commit in database: {git_commit_sha}. "
            f"Enriched mode requires commits to be created first."
        )
        # Mark job as failed with clear error message
        await self._fail_job(
            job_id,
            error="Foreign key violation: git commit not found. "
                  "This is a bug in enriched mode implementation."
        )
        raise
```

### 3. Add Integration Test
**File:** `services/ecosystem-mcp/tests/integration/test_enriched_ingestion.py`

```python
async def test_enriched_mode_creates_git_commits():
    """Test that enriched mode properly creates git commit records."""
    # Start enriched ingestion
    job_id = await start_ingestion(mode="enriched", repo_path="/test/repo")
    
    # Wait for completion
    job = await wait_for_job(job_id)
    
    # Verify commits were created
    async with db.session() as session:
        git_repo = GitCommitRepository(session)
        commits = await git_repo.get_all()
        
        assert len(commits) > 0, "No git commits created"
        
        # Verify documents reference valid commits
        doc_repo = DocumentRepository(session)
        docs = await doc_repo.get_by_job_id(job_id)
        
        for doc in docs:
            if doc.git_commit_sha:
                commit = await git_repo.get_by_sha(doc.git_commit_sha)
                assert commit is not None, f"Document references non-existent commit: {doc.git_commit_sha}"
```

---

## Workarounds

### Option 1: Use Snapshot Mode
```bash
curl -X POST "http://localhost:8000/api/v1/admin/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/repo/services/ecosystem-mcp",
    "mode": "snapshot"
  }'
```

**Pros:** Works immediately, processes all files  
**Cons:** No git history, no timeline data

### Option 2: Use Full History Mode
```bash
curl -X POST "http://localhost:8000/api/v1/admin/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/repo/services/ecosystem-mcp",
    "mode": "git_history"
  }'
```

**Pros:** Creates commits properly, full timeline  
**Cons:** Slow (processes 1,811 commits)

### Option 3: Fix and Rebuild
1. Implement commit creation logic
2. Add error handling
3. Add integration tests
4. Rebuild service
5. Rerun enriched ingestion

---

## Recommendation

**Immediate:** Use **snapshot** or **full history** mode for Temporal RAG validation  
**Short-term:** Fix enriched mode foreign key handling  
**Long-term:** Add comprehensive integration tests for all ingestion modes

---

## Related Issues

- Enriched mode was introduced to provide a faster alternative to full history
- It's meant to give "best of both worlds": snapshot speed + git metadata
- This bug makes it completely unusable
- No user-facing error - job appears to succeed but does nothing

---

## Priority

**Critical** - This bug blocks a key differentiating feature (enriched mode with git context)

**Estimated Fix Time:** 2-4 hours (implementation + testing)

---

## Files To Modify

1. `services/ecosystem-mcp/src/services/ingestion/ingestion_worker.py`
   - Add `ensure_git_commit_exists()` helper
   - Call it before creating documents in enriched mode

2. `services/ecosystem-mcp/src/storage/repositories/git_commit_repository.py`
   - Ensure `get_or_create()` method exists
   - Add bulk insert optimization for multiple commits

3. `services/ecosystem-mcp/tests/integration/test_enriched_ingestion.py`
   - New file with integration tests

4. `services/ecosystem-mcp/src/services/ingestion/error_handling.py`
   - Catch and properly surface foreign key violations

---

## Next Steps

1. Decide: Fix enriched mode OR use workaround?
2. If fixing: Implement commit creation logic
3. If workaround: Use snapshot/full history for validation
4. Document limitation in user-facing docs

