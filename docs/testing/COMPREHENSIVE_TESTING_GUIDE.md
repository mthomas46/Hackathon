# Comprehensive Testing Guide

**Purpose:** Document testing strategy for all protection systems.

**Status:** Test infrastructure documented, ready for implementation.

---

## 📋 **Testing Overview**

### **Test Categories**

1. **Unit Tests** - Test individual functions/classes
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Test full workflows
4. **Performance Tests** - Test under load

### **Coverage Goals**

- **Unit Tests:** 80%+ coverage
- **Integration Tests:** All critical paths
- **E2E Tests:** All user workflows
- **Performance Tests:** Key bottlenecks

---

## 🧪 **Unit Tests**

### **1. JSONB Validation Tests**

**File:** `tests/unit/test_jsonb_validator.py`

**Test Cases:**

```python
import pytest
from src.utils.jsonb_validator import JsonbFieldValidator

class TestJsonbValidator:
    """Test JSONB field validation."""
    
    def test_detect_direct_assignment(self):
        """Should detect obj.field = value without flag_modified."""
        code = '''
        job.job_metadata = metadata
        await session.commit()
        '''
        validator = JsonbFieldValidator()
        violations = validator.validate_string(code)
        
        assert len(violations) == 1
        assert violations[0].severity == 'error'
        assert 'flag_modified' in violations[0].message
    
    def test_detect_inplace_modification(self):
        """Should detect obj.field.update() without flag_modified."""
        code = '''
        job.job_metadata.update({'key': 'value'})
        await session.commit()
        '''
        validator = JsonbFieldValidator()
        violations = validator.validate_string(code)
        
        assert len(violations) == 1
        assert 'update()' in violations[0].message
    
    def test_no_false_positive_with_flag_modified(self):
        """Should NOT flag code that uses flag_modified correctly."""
        code = '''
        metadata = job.job_metadata.copy()
        metadata['key'] = 'value'
        job.job_metadata = metadata
        flag_modified(job, 'job_metadata')
        await session.commit()
        '''
        validator = JsonbFieldValidator()
        violations = validator.validate_string(code)
        
        assert len(violations) == 0
    
    def test_detect_item_assignment(self):
        """Should detect obj.field['key'] = value."""
        code = '''
        job.job_metadata['status'] = 'done'
        '''
        validator = JsonbFieldValidator()
        violations = validator.validate_string(code)
        
        assert len(violations) == 1
        assert violations[0].severity == 'warning'
    
    def test_multiple_violations_in_function(self):
        """Should detect multiple violations in same function."""
        code = '''
        async def update_job(job):
            job.job_metadata = {}
            job.job_metadata['key1'] = 'value1'
            job.job_metadata.update({'key2': 'value2'})
        '''
        validator = JsonbFieldValidator()
        violations = validator.validate_string(code)
        
        assert len(violations) >= 3
    
    def test_validator_handles_syntax_errors(self):
        """Should gracefully handle syntax errors."""
        code = '''
        def broken( 
        '''
        validator = JsonbFieldValidator()
        violations = validator.validate_string(code)
        
        # Should not crash, may return empty or skip file
        assert isinstance(violations, list)
```

**Run Tests:**
```bash
pytest tests/unit/test_jsonb_validator.py -v
```

---

### **2. Checkpoint Manager Tests**

**File:** `tests/unit/test_checkpoint_manager.py`

**Test Cases:**

```python
import pytest
from src.services.ingestion.checkpoint_manager import CheckpointManager, Checkpoint
from datetime import datetime, timedelta

class TestCheckpointManager:
    """Test checkpoint management functionality."""
    
    @pytest.mark.asyncio
    async def test_save_checkpoint(self):
        """Should save checkpoint to database."""
        manager = CheckpointManager()
        
        success = await manager.save_checkpoint(
            job_id=UUID('...'),
            commit_sha='abc123',
            processed_files=['file1.py', 'file2.py'],
            current_file_index=50,
            total_files=1000,
            processed_count=45,
            skipped_count=3,
            failed_count=2,
            embeddings_count=45
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_load_checkpoint(self):
        """Should load checkpoint from database."""
        manager = CheckpointManager()
        job_id = UUID('...')
        
        # First save
        await manager.save_checkpoint(...)
        
        # Then load
        checkpoint = await manager.load_checkpoint(job_id)
        
        assert checkpoint is not None
        assert checkpoint.current_file_index == 50
        assert len(checkpoint.processed_files) == 50
    
    @pytest.mark.asyncio
    async def test_should_resume_recent_checkpoint(self):
        """Should resume from recent checkpoint."""
        manager = CheckpointManager()
        job_id = UUID('...')
        
        # Save checkpoint
        await manager.save_checkpoint(...)
        
        # Check should resume
        should_resume = await manager.should_resume(job_id)
        
        assert should_resume is True
    
    @pytest.mark.asyncio
    async def test_should_not_resume_old_checkpoint(self):
        """Should NOT resume from checkpoint >24 hours old."""
        manager = CheckpointManager()
        
        # Create old checkpoint (25 hours ago)
        old_checkpoint = Checkpoint(
            checkpoint_time=datetime.utcnow() - timedelta(hours=25),
            ...
        )
        
        # Save to database
        # ...
        
        should_resume = await manager.should_resume(job_id)
        
        assert should_resume is False
    
    @pytest.mark.asyncio
    async def test_should_not_resume_minimal_progress(self):
        """Should NOT resume checkpoint with <10 files processed."""
        manager = CheckpointManager()
        
        # Save checkpoint with only 5 files
        await manager.save_checkpoint(
            current_file_index=5,
            ...
        )
        
        should_resume = await manager.should_resume(job_id)
        
        assert should_resume is False
    
    def test_should_save_checkpoint_at_interval(self):
        """Should return True at checkpoint intervals."""
        manager = CheckpointManager(checkpoint_interval=50)
        
        assert manager.should_save_checkpoint(50) is True
        assert manager.should_save_checkpoint(100) is True
        assert manager.should_save_checkpoint(49) is False
        assert manager.should_save_checkpoint(51) is False
    
    @pytest.mark.asyncio
    async def test_clear_checkpoint(self):
        """Should clear checkpoint from database."""
        manager = CheckpointManager()
        job_id = UUID('...')
        
        # Save checkpoint
        await manager.save_checkpoint(...)
        
        # Clear it
        await manager.clear_checkpoint(job_id)
        
        # Should not load
        checkpoint = await manager.load_checkpoint(job_id)
        assert checkpoint is None
```

**Run Tests:**
```bash
pytest tests/unit/test_checkpoint_manager.py -v
```

---

## 🔗 **Integration Tests**

### **1. Phantom Job Detection Tests**

**File:** `tests/integration/test_phantom_job_detection.py`

**Test Cases:**

```python
import pytest
import asyncio
from uuid import uuid4

class TestPhantomJobDetection:
    """Test phantom job detection and handling."""
    
    @pytest.mark.asyncio
    async def test_job_deleted_during_processing(self):
        """Worker should detect job deletion and stop processing."""
        
        # 1. Create and start job
        job_id = await create_test_job()
        worker = get_ingestion_worker()
        
        # 2. Start processing in background
        task = asyncio.create_task(worker._process_job(job_id))
        
        # 3. Wait for job to start processing
        await asyncio.sleep(2)
        
        # 4. Delete job from database (simulate phantom)
        await delete_job_from_database(job_id)
        
        # 5. Wait for worker to detect and stop
        await asyncio.sleep(15)  # Should check every 10 files
        
        # 6. Verify worker stopped
        assert task.done()
        
        # 7. Verify job marked as failed or skipped remaining files
        # (check logs or database state)
    
    @pytest.mark.asyncio
    async def test_job_marked_failed_during_processing(self):
        """Worker should detect job failure and stop."""
        
        # 1. Create and start job
        job_id = await create_test_job()
        
        # 2. Start processing
        task = asyncio.create_task(process_job(job_id))
        await asyncio.sleep(2)
        
        # 3. Mark job as failed via API
        response = await client.post(f"/api/v1/admin/ingest/{job_id}/fail")
        assert response.status_code == 200
        
        # 4. Wait for worker to detect
        await asyncio.sleep(15)
        
        # 5. Verify worker stopped
        assert task.done()
    
    @pytest.mark.asyncio
    async def test_orphaned_job_detected_on_startup(self):
        """Orphaned jobs should be detected and handled on startup."""
        
        # 1. Create job in 'processing' state
        job_id = await create_job_in_database(status='processing')
        
        # 2. Don't create Redis message (simulate orphan)
        
        # 3. Restart application (trigger startup checks)
        await restart_application()
        
        # 4. Verify job was detected as orphaned
        job = await get_job_from_database(job_id)
        assert job.status == 'failed'
        assert 'orphaned' in job.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_worker_periodic_existence_check(self):
        """Worker should check job existence every 10 files."""
        
        # 1. Create job with 100 files
        job_id = await create_test_job_with_n_files(100)
        
        # 2. Start processing and monitor
        check_count = 0
        async def monitor():
            nonlocal check_count
            # Monitor database queries for job existence checks
            # Should happen at files: 10, 20, 30, ... 100
            # = 10 checks total
        
        # 3. Process job
        await process_job(job_id)
        
        # 4. Verify checks happened at right intervals
        assert check_count == 10
```

**Run Tests:**
```bash
pytest tests/integration/test_phantom_job_detection.py -v
```

---

### **2. Graceful Shutdown Tests**

**File:** `tests/integration/test_graceful_shutdown.py`

**Test Cases:**

```python
import pytest
import signal
import os

class TestGracefulShutdown:
    """Test graceful shutdown behavior."""
    
    @pytest.mark.asyncio
    async def test_sigterm_triggers_graceful_shutdown(self):
        """SIGTERM should trigger graceful shutdown."""
        
        # 1. Start worker
        worker = get_ingestion_worker()
        await worker.start()
        
        # 2. Start processing job
        job_id = await create_test_job()
        
        # 3. Send SIGTERM
        os.kill(os.getpid(), signal.SIGTERM)
        
        # 4. Wait for shutdown
        await asyncio.sleep(5)
        
        # 5. Verify checkpoint was saved
        checkpoint = await load_checkpoint(job_id)
        assert checkpoint is not None
        
        # 6. Verify worker stopped
        assert worker.running is False
    
    @pytest.mark.asyncio
    async def test_shutdown_completes_current_file(self):
        """Shutdown should wait for current file to complete."""
        
        # 1. Start processing
        job_id = await start_slow_job()  # Files take 2s each
        
        # 2. Wait until processing file
        await asyncio.sleep(1)
        
        # 3. Send SIGTERM
        os.kill(os.getpid(), signal.SIGTERM)
        
        # 4. Measure shutdown time
        start = time.time()
        await wait_for_shutdown()
        elapsed = time.time() - start
        
        # 5. Should wait for file to complete (~2s + overhead)
        assert 2 <= elapsed <= 5
    
    @pytest.mark.asyncio
    async def test_shutdown_timeout_forces_exit(self):
        """Shutdown should force exit after timeout."""
        
        # 1. Set short timeout (5s)
        handler = GracefulShutdownHandler(max_shutdown_time=5)
        
        # 2. Start processing very slow job
        job_id = await start_job_with_slow_files()  # Files take 10s
        
        # 3. Send SIGTERM
        os.kill(os.getpid(), signal.SIGTERM)
        
        # 4. Measure shutdown time
        start = time.time()
        await wait_for_shutdown()
        elapsed = time.time() - start
        
        # 5. Should force exit after timeout
        assert 5 <= elapsed <= 7  # ~5s + overhead
```

---

### **3. Checkpoint Recovery Tests**

**File:** `tests/integration/test_checkpoint_recovery.py`

**Test Cases:**

```python
class TestCheckpointRecovery:
    """Test checkpoint-based recovery."""
    
    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(self):
        """Should resume job from saved checkpoint."""
        
        # 1. Start job that will be interrupted
        job_id = await create_test_job_with_n_files(100)
        
        # 2. Process 50 files (checkpoint saved at 50)
        await process_files_until(job_id, file_index=50)
        
        # 3. Simulate interruption (stop worker)
        await stop_worker()
        
        # 4. Restart and resume
        await start_worker()
        result = await process_job(job_id)
        
        # 5. Verify resumed from file 50
        assert result['resumed_from_checkpoint'] is True
        assert result['skipped_files'] == 50
        assert result['processed_files'] == 50  # Only 50-100
    
    @pytest.mark.asyncio
    async def test_no_resume_for_fresh_job(self):
        """Fresh job should not attempt resume."""
        
        # 1. Create new job (no checkpoint)
        job_id = await create_test_job()
        
        # 2. Process
        result = await process_job(job_id)
        
        # 3. Verify no resume attempt
        assert result['resumed_from_checkpoint'] is False
        assert result['skipped_files'] == 0
    
    @pytest.mark.asyncio
    async def test_checkpoint_cleared_on_completion(self):
        """Checkpoint should be cleared after successful completion."""
        
        # 1. Create and process job
        job_id = await create_test_job()
        await process_job(job_id)
        
        # 2. Verify checkpoint cleared
        checkpoint = await load_checkpoint(job_id)
        assert checkpoint is None
```

---

## 📊 **Test Infrastructure**

### **Test Fixtures**

**File:** `tests/conftest.py`

```python
import pytest
from src.storage import get_database
from src.utils.redis_client import get_redis_client

@pytest.fixture
async def test_database():
    """Provide test database connection."""
    db = get_database()
    async with db.session() as session:
        yield session
        await session.rollback()  # Rollback after test

@pytest.fixture
async def test_redis():
    """Provide test Redis connection."""
    redis = get_redis_client()
    yield redis
    # Cleanup test data
    await redis.client.flushdb()

@pytest.fixture
async def test_job():
    """Create test ingestion job."""
    job_id = await create_test_job()
    yield job_id
    # Cleanup
    await delete_test_job(job_id)

@pytest.fixture
def mock_git_service():
    """Mock Git service for testing."""
    with patch('src.services.git.git_service.GitService') as mock:
        yield mock
```

### **Test Utilities**

**File:** `tests/utils/test_helpers.py`

```python
async def create_test_job(**kwargs):
    """Create test ingestion job."""
    pass

async def create_test_job_with_n_files(n: int):
    """Create job with specific number of files."""
    pass

async def delete_test_job(job_id):
    """Clean up test job."""
    pass

async def wait_for_job_status(job_id, status, timeout=30):
    """Wait for job to reach status."""
    pass
```

---

## 🚀 **Running Tests**

### **All Tests**
```bash
pytest tests/ -v
```

### **Unit Tests Only**
```bash
pytest tests/unit/ -v
```

### **Integration Tests Only**
```bash
pytest tests/integration/ -v
```

### **With Coverage**
```bash
pytest tests/ --cov=src --cov-report=html
```

### **Specific Test File**
```bash
pytest tests/unit/test_jsonb_validator.py -v
```

### **Specific Test Case**
```bash
pytest tests/unit/test_jsonb_validator.py::TestJsonbValidator::test_detect_direct_assignment -v
```

---

## 📋 **Test Checklist**

### **Unit Tests**
- [ ] JSONB validator (8 test cases)
- [ ] Checkpoint manager (8 test cases)
- [ ] Graceful shutdown handler
- [ ] Database update monitor
- [ ] Redis queue health checker
- [ ] Orphaned job detector

### **Integration Tests**
- [ ] Phantom job detection (4 test cases)
- [ ] Graceful shutdown (3 test cases)
- [ ] Checkpoint recovery (3 test cases)
- [ ] Queue health check
- [ ] Database monitoring
- [ ] End-to-end ingestion

### **Coverage Goals**
- [ ] Unit test coverage >80%
- [ ] Integration test for all critical paths
- [ ] E2E test for main workflows

---

## ✅ **Summary**

**Test Strategy:**
1. **Unit Tests** - Fast, isolated, high coverage
2. **Integration Tests** - Component interactions
3. **E2E Tests** - Full workflows

**Priority:**
1. JSONB validation (prevent regressions)
2. Phantom job detection (critical for reliability)
3. Checkpoint recovery (data preservation)
4. Graceful shutdown (clean operations)

**Status:**
- Test cases documented ✅
- Test infrastructure outlined ✅
- Ready for implementation 📋

**Next Steps:**
1. Implement unit tests
2. Implement integration tests
3. Run full test suite
4. Achieve 80%+ coverage

---

**All critical test scenarios documented and ready for implementation!** 🧪

