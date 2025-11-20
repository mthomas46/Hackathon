**Date:** November 20, 2025  
**Status:** Foreign Key Constraint Issue Resolved  
**Impact:** Documentation Run Creation Now Working  

# Foreign Key Constraint Fix - HTTP 500 Error Resolved

## 🐛 Issue

When trying to create a documentation run via the `/api/v1/documentation/runs` endpoint, users encountered an **HTTP 500 error**:

```
insert or update on table "documentation_runs" violates foreign key constraint "documentation_runs_repo_id_fkey"
DETAIL:  Key (repo_id)=(/Users/mykalthomas/Documents/work/adminservice) is not present in table "repository_contexts".
```

---

## 🔍 Root Cause

### The Problem

1. The `documentation_runs` table has a foreign key constraint: `repo_id` → `repository_contexts.repo_id`
2. The `run_manager.py` was setting `repo_id = repo_path` (full file path)
3. The `repository_contexts` table was **empty** (0 rows)
4. PostgreSQL rejected the insert because the referenced `repo_id` didn't exist

### Code Location

**File:** `src/services/documentation/run_manager.py`  
**Line:** 78

```python
# OLD CODE (BROKEN)
repo_id = repo_path  # Use repo_path as repo_id
```

This would set `repo_id` to something like `/Users/mykalthomas/Documents/work/adminservice`, which doesn't exist in the `repository_contexts` table.

---

## ✅ Solution

### The Fix

Since `repo_id` in the `DocumentationRunModel` is **nullable** (`nullable=True`), we can set it to `None` when the repository context doesn't exist in the database.

**Updated Code:**

```python
# Check if repo_id exists in repository_contexts, otherwise set to None
# repo_id has a foreign key constraint but is nullable
from ...storage.models_analysis import RepositoryContextModel
from sqlalchemy import select

query = select(RepositoryContextModel.repo_id).filter(
    RepositoryContextModel.repo_id == repo_path
)
result = await self.session.execute(query)
existing_repo = result.scalar_one_or_none()

repo_id = existing_repo if existing_repo else None
if not existing_repo:
    logger.warning(f"Repository context not found for path '{repo_path}', setting repo_id to None")
```

### How It Works

1. **Query the database** to check if the `repo_path` exists in `repository_contexts`
2. **If it exists**: Use the existing `repo_id`
3. **If it doesn't exist**: Set `repo_id` to `None` (which is valid since the field is nullable)
4. **Log a warning** so we know when this happens

---

## 📊 Test Results

### Before Fix

```bash
curl -X POST http://localhost:8000/api/v1/documentation/runs \
  -H "Content-Type: application/json" \
  -d '{"source_directory": "/Users/mykalthomas/Documents/work/adminservice", ...}'

❌ HTTP 500: Foreign key constraint violation
```

### After Fix

```bash
curl -X POST http://localhost:8000/api/v1/documentation/runs \
  -H "Content-Type: application/json" \
  -d '{"source_directory": "/Users/mykalthomas/Documents/work/adminservice", ...}'

✅ HTTP 200: {
  "run_id": "c5ea6c03-9790-43ca-a544-927a4aa4c5b3",
  "name": "Test Run",
  "status": "pending",
  "message": "Documentation run 'Test Run' created successfully"
}
```

---

## 🔧 Technical Details

### Database Schema

#### `documentation_runs` Table

```sql
CREATE TABLE documentation_runs (
    id UUID PRIMARY KEY,
    plan_id VARCHAR(500),
    repo_id VARCHAR(500),  -- NULLABLE, references repository_contexts.repo_id
    ...
    FOREIGN KEY (repo_id) REFERENCES repository_contexts(repo_id) ON DELETE CASCADE
);
```

#### `repository_contexts` Table

```sql
CREATE TABLE repository_contexts (
    id UUID PRIMARY KEY,
    repo_id VARCHAR(500) UNIQUE NOT NULL,
    repo_name VARCHAR(500),
    languages JSON,
    frameworks JSON,
    ...
);
```

### Why repo_id Is Nullable

The `repo_id` field is nullable because:
1. **Documentation runs can exist without full repository analysis** (e.g., quick generations)
2. **Repository contexts are created separately** during ingestion/analysis
3. **Flexibility for different workflows** (some users may not have full repo context)

---

## 🚀 Deployment

### Files Changed

**File:** `src/services/documentation/run_manager.py`  
**Lines:** 76-93  
**Changes:**
- Added database query to check if `repo_id` exists
- Set `repo_id` to `None` if not found
- Added warning log for debugging

### Deployment Steps

1. ✅ Updated `run_manager.py` with fix
2. ✅ Copied to Docker container
3. ✅ Restarted service
4. ✅ Tested endpoint - working correctly

---

## 📈 Impact

### Immediate Benefits

1. ✅ **Documentation runs can be created** without pre-existing repository contexts
2. ✅ **No more HTTP 500 errors** from foreign key violations
3. ✅ **Graceful handling** of missing repository data
4. ✅ **Better logging** (warnings when repo context missing)

### System Behavior

| Scenario | Before Fix | After Fix |
|----------|------------|-----------|
| Repo context exists | ✅ Works | ✅ Works |
| Repo context missing | ❌ HTTP 500 | ✅ Works (repo_id=None) |
| Database consistency | ⚠️ Constraint violation | ✅ Valid nullable value |

---

## 🔮 Future Enhancements

### Option 1: Auto-Create Repository Context

Instead of setting `repo_id` to `None`, we could automatically create a minimal repository context:

```python
if not existing_repo:
    # Create minimal repository context
    repo_context = RepositoryContextModel(
        repo_id=repo_path,
        repo_name=os.path.basename(repo_path)
    )
    self.session.add(repo_context)
    await self.session.flush()
    repo_id = repo_path
```

**Pros:**
- More complete data model
- Can track all repos that have documentation runs

**Cons:**
- Adds complexity
- May create incomplete repo contexts

### Option 2: Use Service Name Instead of Path

Use the service name (e.g., "adminservice") as the repo_id instead of the full path:

```python
repo_id = os.path.basename(repo_path)  # "adminservice" instead of full path
```

**Pros:**
- More portable (not tied to specific file paths)
- Matches service-oriented architecture

**Cons:**
- Requires schema changes
- May have collisions if multiple services have same name

---

## 📝 Related Issues

### HTTP 500 Error #1 (Resolved Nov 19)

**Issue:** `DocumentationRunManager.create_run() got unexpected keyword argument 'name'`

**Fix:** Restructured API endpoint to correctly bundle request parameters into `config` and `metadata` dictionaries.

**File:** `src/api/routes/documentation_runs.py`

### HTTP 500 Error #2 (Resolved Nov 20) ← This Fix

**Issue:** Foreign key constraint violation on `repo_id`

**Fix:** Set `repo_id` to `None` when repository context doesn't exist.

**File:** `src/services/documentation/run_manager.py`

---

## ✅ Verification Checklist

- [x] Foreign key constraint error resolved
- [x] Documentation runs can be created successfully
- [x] repo_id correctly set to None when context missing
- [x] Warning logged when repo context not found
- [x] Endpoint returns HTTP 200 with valid response
- [x] No database integrity issues
- [x] Service restarted and tested

---

## 🎯 Summary

**Problem:** HTTP 500 error due to foreign key constraint violation  
**Root Cause:** Trying to insert non-existent `repo_id` into `documentation_runs`  
**Solution:** Set `repo_id` to `None` when repository context doesn't exist  
**Result:** ✅ Documentation run creation now works correctly  

**Status:** **RESOLVED ✅**  
**Production Ready:** **YES ✅**

---

## 📞 API Usage

### Create Documentation Run

```bash
curl -X POST http://localhost:8000/api/v1/documentation/runs \
  -H "Content-Type: application/json" \
  -d '{
    "source_directory": "/path/to/service",
    "name": "My Documentation Run",
    "description": "Generate API documentation",
    "output_format": "markdown",
    "response_size": "L",
    "tier": "desktop",
    "num_passes": 2,
    "questions_per_pass": 3,
    "created_by": "user@example.com"
  }'
```

**Expected Response:**

```json
{
  "run_id": "uuid-here",
  "name": "My Documentation Run",
  "status": "pending",
  "message": "Documentation run 'My Documentation Run' created successfully"
}
```

---

**Fix Complete! 🎉**

