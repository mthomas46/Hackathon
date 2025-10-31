**Date:** October 23, 2025  
**Status:** Phase 1 Test Adaptation - Comprehensive Plan  
**Priority:** HIGH - No Time Constraints  

---

# 🔧 PHASE 1 TEST ADAPTATION PLAN

## **OBJECTIVE**

Adapt all 220 Phase 1 tests to work with the actual codebase implementation, ensuring 100% of tests are functional and passing.

---

## 📋 TEST INVENTORY

### **Functional Tests (70 tests)**
1. `test_job_recovery_with_db.py` - 15 tests
2. `test_documentation_runs.py` - 15 tests
3. `test_temporal_versioning.py` - 10 tests
4. `test_error_recovery_scenarios.py` - 30 tests

### **Integration Tests (150 tests)**
5. `test_admin_routes.py` - 20 tests
6. `test_infrastructure_routes.py` - 25 tests
7. `test_diagnostics_routes.py` - 20 tests
8. `test_cache_analytics_routes.py` - 11 tests
9. `test_job_management_routes.py` - 49 tests
10. `test_reporting_routes.py` - 45 tests

---

## 🔍 ACTUAL IMPLEMENTATION SURVEY

### **Job Recovery System**

**Location:** `src/utils/job_recovery.py`

**Key Classes:**
- `JobType(Enum)`: INGESTION, EMBEDDING, DOCUMENTATION
- `CheckpointStatus(Enum)`: PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED
- `JobCheckpoint`: Checkpoint data structure
- `JobRecoveryManager`: Main recovery manager

**API:**
```python
manager = JobRecoveryManager(db_session)
await manager.create_checkpoint(job_id, job_type, checkpoint_id, data)
await manager.get_latest_checkpoint(job_id)
await manager.resume_job(job_id)
await manager.mark_checkpoint_completed(job_id, checkpoint_id)
await manager.cleanup_checkpoints(job_id)
```

### **Checkpoint Manager (Ingestion-Specific)**

**Location:** `src/services/ingestion/checkpoint_manager.py`

**Key Classes:**
- `Checkpoint`: Ingestion checkpoint data
- `CheckpointManager`: Ingestion checkpoint manager

**API:**
```python
manager = CheckpointManager(checkpoint_interval=5)
await manager.save_checkpoint(job, processed_files, current_index, ...)
checkpoint = await manager.load_checkpoint(job_id)
await manager.should_skip_file(job_id, file_path)
```

### **Documentation Runs**

**Location:** `src/storage/models_documentation.py`

**Key Models:**
- `DocumentationRunModel`: Run metadata
- `DocumentationArtifactModel`: Generated artifacts

**Fields:**
- `status`: String ('pending', 'running', 'completed', 'failed', 'cancelled')
- `plan_id`: String
- `repo_id`: String
- `passes_completed`: Integer
- `total_passes`: Integer

### **Ingestion Models**

**Location:** `src/models/ingestion.py`

**Key Classes:**
- `IngestionJob`: Job model (not IngestionJobModel)
- `IngestionStatus(Enum)`: Status enum (not JobStatus)

### **Repositories**

**Location:** `src/storage/repositories/`

**Available:**
- `IngestionJobRepository`
- `DocumentRepository`
- Various other repositories

---

## 🎯 ADAPTATION STRATEGY

### **Phase 1: Functional Tests (Priority 1)**

#### **File 1: test_job_recovery_with_db.py**

**Issues:**
- ✅ Fixed: `IngestionJobModel` → `IngestionJob`
- ✅ Fixed: `JobStatus` → `IngestionStatus`
- ✅ Fixed: `RecoveryService` → `JobRecoveryManager`
- ⚠️ Need to verify: Fixture setup
- ⚠️ Need to verify: Test logic matches actual API

**Actions:**
1. Verify `JobRecoveryManager` initialization
2. Update test logic to match actual API methods
3. Ensure database session handling is correct
4. Run tests and fix any remaining issues

#### **File 2: test_documentation_runs.py**

**Issues:**
- Need to check: `DocumentationRunModel` import path
- Need to check: `RunStatus` enum (may not exist)
- Need to check: `GeneratedDocumentModel` vs `DocumentationArtifactModel`
- Need to check: Repository imports

**Actions:**
1. Fix model imports
2. Update status handling (string vs enum)
3. Fix repository imports
4. Update test logic to match actual schema

#### **File 3: test_temporal_versioning.py**

**Issues:**
- Need to check: Versioning service imports
- Need to check: Content-addressable storage implementation
- Need to check: Temporal ordering APIs

**Actions:**
1. Survey versioning implementation
2. Fix imports
3. Update test logic
4. Verify database schema matches

#### **File 4: test_error_recovery_scenarios.py**

**Issues:**
- Likely to work with minimal changes
- May need mock adjustments
- May need exception type corrections

**Actions:**
1. Run tests
2. Fix any import errors
3. Adjust mocks as needed
4. Verify error handling logic

### **Phase 2: Integration Tests (Priority 2)**

#### **Files 5-10: API Route Tests**

**Common Issues:**
- Endpoint path corrections
- Request/response model adjustments
- Authentication/authorization handling
- Test client setup

**Actions:**
1. Survey actual API routes
2. Fix endpoint paths
3. Update request/response assertions
4. Run tests and fix issues

---

## 📊 EXECUTION PLAN

### **Step 1: Complete Job Recovery Tests (2-3 hours)**

1. Read full `JobRecoveryManager` API
2. Update all test methods
3. Fix fixtures
4. Run tests
5. Debug and fix failures
6. Verify all 15 tests pass

### **Step 2: Fix Documentation Run Tests (2-3 hours)**

1. Survey documentation models
2. Fix imports
3. Update test logic
4. Run tests
5. Debug and fix failures
6. Verify all 15 tests pass

### **Step 3: Fix Temporal Versioning Tests (2-3 hours)**

1. Survey versioning implementation
2. Fix imports
3. Update test logic
4. Run tests
5. Debug and fix failures
6. Verify all 10 tests pass

### **Step 4: Fix Error Recovery Tests (1-2 hours)**

1. Run tests
2. Fix any issues
3. Verify all 30 tests pass

### **Step 5: Fix Integration Tests (4-6 hours)**

1. Survey API routes
2. Fix imports and paths
3. Run each test file
4. Debug and fix failures
5. Verify all 150 tests pass

---

## 🎯 SUCCESS CRITERIA

### **Per-File Success:**
- All imports resolve
- All fixtures work
- All tests pass
- No skipped tests (unless intentional)

### **Overall Success:**
- 220/220 tests passing
- 100% test execution rate
- Comprehensive coverage validated
- Production-ready test suite

---

## 📝 TRACKING

### **Progress Tracking:**
- Create `PHASE_1_TEST_FIXES_PROGRESS.md`
- Track each file's status
- Document issues and solutions
- Record test pass rates

### **Documentation:**
- Document API differences found
- Note any missing implementations
- Create adaptation guides
- Update test documentation

---

## 🚀 EXECUTION STARTS NOW

Beginning with `test_job_recovery_with_db.py` - reading full implementation and adapting tests systematically.

---

**End of Adaptation Plan**

