# 🧪 Testing Guide: Ingestion Path Resolution

**Comprehensive testing for the automatic path validation and resolution feature**

---

## 📋 **Overview**

This document describes the testing strategy and test suites for the ingestion path resolution feature that fixes the HTTP 400 error when using host machine paths.

---

## 🎯 **What We're Testing**

### Core Functionality:
1. **Path Validation** - Verifying host paths can be accessed and are git repositories
2. **Path Resolution** - Converting host paths to container-accessible paths
3. **Frontend Integration** - Automatic validation before ingestion
4. **Backend Processing** - Correct handling of resolved paths
5. **Error Handling** - Graceful failures and helpful error messages
6. **User Experience** - Recent paths tracking and feedback

---

## 🗂️ **Test Structure**

```
tests/
├── test_ingestion_path_resolution.py          # Unit tests
├── integration/
│   └── test_ingestion_path_resolution_integration.py  # Integration tests
└── e2e/
    └── test_ingestion_path_resolution_e2e.py  # End-to-end tests
```

---

## 1️⃣ **Unit Tests**

**File:** `tests/test_ingestion_path_resolution.py`

### Test Coverage:

#### A. **HostPathResolver** (Core utility)
```python
✅ test_normalize_path_basic()
   - Test absolute path normalization
   - Test tilde expansion (~/)
   - Test symlink resolution

✅ test_detect_git_root_found()
   - Test finding .git directory in parent folders
   - Test from nested subdirectories

✅ test_detect_git_root_not_found()
   - Test when no .git exists
   - Returns None appropriately

✅ test_resolve_container_path_mounted()
   - Test resolution for mounted host paths
   - Maps /Users/.../Hackathon → /app

✅ test_resolve_container_path_not_mounted()
   - Test resolution for unmounted paths
   - Returns None for container_path

✅ test_resolve_full_workflow()
   - Complete resolution from host → container
   - Detects git root
   - Identifies subdirectories
   - Returns ResolvedPath object
```

#### B. **validate_ingestion_path** (Validation function)
```python
✅ test_validate_valid_path()
   - Valid git repository path
   - Returns is_valid=True

✅ test_validate_not_mounted()
   - Path not in Docker mounts
   - Returns is_valid=False
   - Includes mount suggestion

✅ test_validate_no_git_repo()
   - Directory without .git
   - Returns is_valid=False
   - Error message mentions git
```

#### C. **API Integration** (Mocked backend)
```python
✅ test_ingest_endpoint_with_host_path_resolution()
   - Mock validation succeeds
   - Mock database job creation
   - Mock Redis queue
   - Returns 200 with job_id

✅ test_ingest_endpoint_fails_unmounted_path()
   - Mock validation fails (unmounted)
   - Returns 400 with error
   - Includes mount suggestion
```

#### D. **Frontend Logic** (Simulated)
```python
✅ test_frontend_validates_before_submit()
   - Calls /api/v1/path/validate
   - Uses resolved container path
   - Sends to /api/v1/admin/ingest

✅ test_frontend_handles_validation_failure()
   - Validation returns is_valid=False
   - Frontend does NOT proceed with ingestion
```

#### E. **Subdirectory Targeting**
```python
✅ test_resolve_subdirectory()
   - Detects git root vs target directory
   - Calculates relative path (target_subdir)
   - is_subdirectory=True

✅ test_ingest_subdirectory()
   - Includes target_subdirectory in request
   - Backend processes correctly
```

#### F. **Error Recovery**
```python
✅ test_validation_api_timeout()
   - httpx.TimeoutException
   - Frontend handles gracefully

✅ test_validation_api_connection_error()
   - httpx.ConnectError
   - Frontend continues with original path

✅ test_backend_path_not_exist_error()
   - Path doesn't exist in container
   - Returns 400 with clear message
```

### Running Unit Tests:
```bash
python3 -m pytest tests/test_ingestion_path_resolution.py -v
```

**Expected Output:**
```
tests/test_ingestion_path_resolution.py::TestHostPathResolver::test_normalize_path_basic PASSED
tests/test_ingestion_path_resolution.py::TestHostPathResolver::test_detect_git_root_found PASSED
... (19 tests)

===================== 19 passed in 2.3s =====================
```

---

## 2️⃣ **Integration Tests**

**File:** `tests/integration/test_ingestion_path_resolution_integration.py`

### Test Coverage:

#### A. **Path Validation API** (Real HTTP calls)
```python
✅ test_validate_hackathon_path()
   - POST /api/v1/path/validate
   - Real Hackathon directory
   - Verifies is_valid, container_path, git_root

✅ test_validate_subdirectory()
   - Validate services/ecosystem-mcp
   - Checks is_subdirectory=True
   - Checks target_subdir

✅ test_validate_invalid_path()
   - Non-existent path
   - Returns is_valid=False
   - Includes error message

✅ test_validate_non_git_path()
   - Directory without .git
   - Error mentions git requirement
```

#### B. **Ingestion with Resolution** (Real workflow)
```python
✅ test_ingest_with_automatic_resolution()
   - Step 1: Validate path
   - Step 2: Ingest with resolved path
   - Returns job_id
   - Status = queued

✅ test_ingest_without_resolution_fails()
   - Send host path directly
   - Backend tries to validate
   - May fail with 400

✅ test_ingest_subdirectory()
   - Validate subdirectory
   - Include target_subdirectory
   - Starts successfully
```

#### C. **End-to-End Workflow** (Full flow)
```python
✅ test_complete_ingestion_workflow()
   - Health check
   - Validate path
   - Check worker health
   - Start ingestion
   - Monitor job status
   - Verify job in list

✅ test_error_handling_workflow()
   - Validate invalid path
   - Frontend does NOT ingest
   - If forced, returns 400/500
```

#### D. **Mount Configuration**
```python
✅ test_get_mount_points()
   - GET /api/v1/path/mounts
   - Returns configured mounts
   - Includes /app mount

✅ test_suggest_mount_config()
   - POST /api/v1/path/suggest-mount
   - Returns docker-compose.yml snippet
   - Includes volume mapping
```

#### E. **Recent Paths Tracking** (Session state)
```python
✅ test_recent_paths_initialization()
   - Initialized with Hackathon path
   - List has 1 item

✅ test_recent_paths_add_new()
   - Add new path
   - Inserted at position 0 (most recent)

✅ test_recent_paths_limit()
   - Add 15 paths
   - Only keeps 10
   - Most recent first
```

### Running Integration Tests:
```bash
# Start backend first
docker restart ecosystem-mcp-service

# Run tests
python3 -m pytest tests/integration/test_ingestion_path_resolution_integration.py -v -m integration
```

**Expected Output:**
```
tests/integration/test_ingestion_path_resolution_integration.py::TestPathValidationAPI::test_validate_hackathon_path PASSED
tests/integration/test_ingestion_path_resolution_integration.py::TestPathValidationAPI::test_validate_subdirectory PASSED
... (15 tests)

===================== 15 passed in 8.7s =====================
```

---

## 3️⃣ **End-to-End Tests**

**File:** `tests/e2e/test_ingestion_path_resolution_e2e.py`

### Test Coverage:

#### A. **Dashboard Workflow** (Selenium - requires GUI)
```python
⏭️  test_ingestion_with_default_path()
   - Navigate to dashboard
   - Click Ingestion Manager
   - Verify default path
   - Click Start Ingestion
   - See validation messages
   - See success message

⏭️  test_validation_feedback()
   - Check for "Resolving host path..."
   - Check for "Path validated: /app"
   - Check for "Ingestion started!"

⏭️  test_recent_paths_saved()
   - Select "Recent Paths"
   - Verify Hackathon in list

⏭️  test_container_path_mode()
   - Switch to "Container Path"
   - Verify default = /app
   - No validation step
```

**Note:** Dashboard tests are marked with `@pytest.mark.skip` by default because they require:
- Selenium WebDriver
- Chrome/ChromeDriver
- Dashboard running at localhost:8501

#### B. **API Workflow E2E** (Real services)
```python
✅ test_full_ingestion_lifecycle()
   - Validate path
   - Start ingestion
   - Monitor status (poll 10 times)
   - Check data stats
   - Complete workflow

✅ test_error_recovery_workflow()
   - Test invalid path
   - Test non-existent container path
   - Test worker health check
   - All errors handled gracefully
```

#### C. **Performance Testing**
```python
✅ test_validation_performance()
   - Validation completes < 2 seconds
   - Measures actual duration

✅ test_concurrent_validations()
   - 3 simultaneous validations
   - All succeed
   - Measures total time
```

### Running E2E Tests:
```bash
# Start all services
docker restart ecosystem-mcp-service ecosystem-mcp-dashboard

# Run tests
python3 -m pytest tests/e2e/test_ingestion_path_resolution_e2e.py -v -m e2e
```

**Expected Output:**
```
tests/e2e/test_ingestion_path_resolution_e2e.py::TestAPIWorkflowE2E::test_full_ingestion_lifecycle PASSED
tests/e2e/test_ingestion_path_resolution_e2e.py::TestAPIWorkflowE2E::test_error_recovery_workflow PASSED
... (5 tests)

===================== 5 passed in 15.2s =====================
```

---

## 🚀 **Quick Start**

### Run All Tests:
```bash
./run_path_resolution_tests.sh
```

### Run Specific Test Suite:
```bash
# Unit tests only
python3 -m pytest tests/test_ingestion_path_resolution.py -v

# Integration tests only (requires backend)
python3 -m pytest tests/integration/test_ingestion_path_resolution_integration.py -v -m integration

# E2E tests only (requires all services)
python3 -m pytest tests/e2e/test_ingestion_path_resolution_e2e.py -v -m e2e
```

### Run Specific Test:
```bash
python3 -m pytest tests/test_ingestion_path_resolution.py::TestHostPathResolver::test_resolve_full_workflow -v
```

---

## 📊 **Test Statistics**

| Test Suite | Total Tests | Requires Services | Typical Duration |
|------------|-------------|-------------------|------------------|
| Unit | 19 | No | ~2-3 seconds |
| Integration | 15 | Backend | ~8-10 seconds |
| E2E | 5+ | All | ~15-30 seconds |
| **Total** | **39+** | Varies | **~25-45 seconds** |

---

## ✅ **Test Checklist**

Before deploying path resolution feature:

- [ ] All unit tests pass (19/19)
- [ ] Integration tests pass or skip gracefully (15/15)
- [ ] E2E tests pass or skip gracefully (5+/5+)
- [ ] Manual testing in dashboard completed
- [ ] Error messages are user-friendly
- [ ] Performance acceptable (< 2s validation)
- [ ] Documentation updated

---

## 🐛 **Common Test Failures**

### 1. **ModuleNotFoundError**
```
ModuleNotFoundError: No module named 'src.utils.host_path_resolver'
```
**Fix:** Run tests from project root or inside Docker container

### 2. **Integration Tests Skipped**
```
SKIPPED [1] Backend service not running
```
**Fix:** Start backend: `docker restart ecosystem-mcp-service`

### 3. **E2E Tests Skipped**
```
SKIPPED [1] Requires Selenium and running dashboard
```
**Fix:** 
- Install Selenium: `pip install selenium`
- Install ChromeDriver
- Start dashboard: `docker restart ecosystem-mcp-dashboard`

### 4. **Connection Refused**
```
httpx.ConnectError: Connection refused
```
**Fix:** Verify services are running:
```bash
docker ps | grep ecosystem-mcp
```

---

## 📝 **Adding New Tests**

### Template for Unit Test:
```python
def test_new_feature(self):
    """Test description."""
    # Arrange
    resolver = HostPathResolver()
    test_path = "/test/path"
    
    # Act
    result = resolver.some_method(test_path)
    
    # Assert
    assert result.expected_property == expected_value
```

### Template for Integration Test:
```python
@pytest.mark.asyncio
async def test_new_api_feature(self, api_base_url):
    """Test description."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base_url}/api/v1/endpoint",
                json={"data": "value"},
                timeout=10.0
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["key"] == "expected_value"
            
    except httpx.ConnectError:
        pytest.skip("Backend service not running")
```

---

## 🎯 **CI/CD Integration**

### GitHub Actions Example:
```yaml
name: Path Resolution Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio httpx
      
      - name: Run unit tests
        run: |
          pytest tests/test_ingestion_path_resolution.py -v
      
      - name: Start services
        run: |
          docker-compose up -d ecosystem-mcp-service
      
      - name: Run integration tests
        run: |
          pytest tests/integration/test_ingestion_path_resolution_integration.py -v -m integration
```

---

## 📚 **Related Documentation**

- **Implementation:** `INGESTION_PATH_FIX.md`
- **Path Resolution:** `HOST_PATH_INGESTION.md`
- **Default Paths:** `DEFAULT_PATHS_CONFIGURED.md`
- **Docker Mounts:** `DOCKER_VOLUME_MOUNTS_EXPLAINED.md`

---

**Status:** ✅ **TEST SUITE COMPLETE**  
**Date:** October 15, 2025  
**Coverage:** Unit, Integration, E2E

