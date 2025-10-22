"""
Async Yielding and Event Loop Tests

Tests specifically for the async yielding fix that resolved the
worker loop blocking issue discovered during investigation.

KEY LESSON FROM 7-HOUR DEBUG SESSION:
os.walk() blocks the event loop when scanning 125k+ files,
preventing asyncio.wait_for() timeout from ever firing.

Solution: await asyncio.sleep(0) every 100 files.
"""

import pytest
import asyncio
import time
from pathlib import Path
import tempfile
import shutil
from uuid import uuid4

from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
from services.ecosystem_mcp.src.storage.db_models import IngestionJobModel


class TestAsyncYielding:
    """Tests for async yielding behavior during file scanning."""
    
    @pytest.fixture
    def large_file_tree(self):
        """Create a directory tree with 1000+ files."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Create 1000 files across multiple directories
        for i in range(50):
            subdir = repo_path / f"module_{i}"
            subdir.mkdir()
            for j in range(20):
                file_path = subdir / f"file_{j}.py"
                file_path.write_text(f"# Module {i} File {j}\n")
        
        yield repo_path
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_event_loop_yields_during_scan(self, large_file_tree):
        """
        CRITICAL TEST: Verify event loop yields during os.walk().
        
        This is the fix for the 7-hour bug investigation.
        Without yielding, scanning 125k files blocks for 5-10 minutes.
        
        SUCCESS CRITERIA:
        - Event loop yields control during scan
        - Other tasks can run concurrently
        - Timeout protection can fire
        """
        job = IngestionJobModel(
            id=uuid4(),
            repo_path=str(large_file_tree),
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        
        # Track if event loop is yielding
        yield_count = 0
        
        async def monitor_yields():
            """Monitor that event loop is yielding."""
            nonlocal yield_count
            while True:
                await asyncio.sleep(0.01)  # Check every 10ms
                yield_count += 1
        
        # Run job and monitor concurrently
        monitor_task = asyncio.create_task(monitor_yields())
        
        start_time = time.time()
        result = await processor.process(job)
        elapsed = time.time() - start_time
        
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
        # Verify event loop yielded many times during processing
        expected_yields = int(elapsed / 0.01)  # ~100 per second
        
        print(f"\n✅ Event Loop Yielding Test:")
        print(f"   Processing time: {elapsed:.2f}s")
        print(f"   Yield count: {yield_count}")
        print(f"   Expected yields: ~{expected_yields}")
        print(f"   Yield rate: {yield_count/elapsed:.0f} per second")
        
        # Should have yielded at least 50% of expected (allows for processing overhead)
        assert yield_count > expected_yields * 0.5, \
            f"Event loop not yielding enough! Only {yield_count} yields in {elapsed:.2f}s"
        
        assert result["success"], f"Job failed: {result.get('error')}"
    
    @pytest.mark.asyncio
    async def test_timeout_fires_with_yielding(self, large_file_tree):
        """
        Test that asyncio.wait_for() timeout works with yielding.
        
        Before fix: timeout never fired (event loop blocked)
        After fix: timeout fires correctly
        """
        job = IngestionJobModel(
            id=uuid4(),
            repo_path=str(large_file_tree),
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        
        # Set a very short timeout (should fire)
        start_time = time.time()
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                processor.process(job),
                timeout=0.5  # Half second - should timeout
            )
        elapsed = time.time() - start_time
        
        # Verify timeout fired close to expected time
        assert 0.4 < elapsed < 0.7, \
            f"Timeout fired at {elapsed:.2f}s, expected ~0.5s"
        
        print(f"✅ Timeout fired correctly at {elapsed:.2f}s")
    
    @pytest.mark.asyncio
    async def test_no_blocking_with_large_scan(self):
        """
        Test that large scans don't block event loop.
        
        This was the root cause of the 44-minute hung jobs.
        """
        # Scan a large directory (services directory has many files)
        job = IngestionJobModel(
            id=uuid4(),
            repo_path="/host/services/ecosystem-mcp/src",
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        
        # Track continuous task execution
        task_executions = []
        
        async def continuous_task():
            """Task that runs continuously if event loop not blocked."""
            for i in range(100):
                await asyncio.sleep(0.1)
                task_executions.append(time.time())
        
        # Run both concurrently
        continuous = asyncio.create_task(continuous_task())
        
        start_time = time.time()
        result = await processor.process(job)
        elapsed = time.time() - start_time
        
        # Cancel continuous task
        continuous.cancel()
        try:
            await continuous
        except asyncio.CancelledError:
            pass
        
        # Verify continuous task executed throughout
        execution_count = len(task_executions)
        
        print(f"\n✅ Large Scan Non-Blocking Test:")
        print(f"   Files scanned: {result['total_documents']}")
        print(f"   Scan time: {elapsed:.2f}s")
        print(f"   Continuous task executions: {execution_count}")
        
        # Should have executed at least 50 times in 10+ seconds
        assert execution_count > 50, \
            f"Event loop was blocked! Only {execution_count} executions"
    
    @pytest.mark.asyncio
    async def test_yield_frequency(self, large_file_tree):
        """
        Test that yielding happens at correct frequency.
        
        Implementation: await asyncio.sleep(0) every 100 files
        """
        from unittest.mock import patch
        
        job = IngestionJobModel(
            id=uuid4(),
            repo_path=str(large_file_tree),
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        
        # Track asyncio.sleep(0) calls
        sleep_calls = []
        original_sleep = asyncio.sleep
        
        async def tracked_sleep(delay):
            if delay == 0:
                sleep_calls.append(time.time())
            return await original_sleep(delay)
        
        with patch('asyncio.sleep', side_effect=tracked_sleep):
            result = await processor.process(job)
        
        # Verify yielding frequency
        files_processed = result["total_documents"]
        expected_yields = files_processed // 100  # Every 100 files
        
        print(f"\n✅ Yield Frequency Test:")
        print(f"   Files processed: {files_processed}")
        print(f"   Expected yields: ~{expected_yields}")
        print(f"   Actual yields: {len(sleep_calls)}")
        
        # Should be close to expected (allow 10% margin)
        assert abs(len(sleep_calls) - expected_yields) < expected_yields * 0.1, \
            f"Yield frequency incorrect: {len(sleep_calls)} vs expected ~{expected_yields}"


class TestFileLimit:
    """Tests for the 10,000 file safety limit."""
    
    @pytest.mark.asyncio
    async def test_file_limit_enforced(self):
        """
        Test that 10,000 file limit is enforced.
        
        This prevents runaway processing of 125k+ files.
        """
        # Try to process a very large directory
        job = IngestionJobModel(
            id=uuid4(),
            repo_path="/host",  # Root has 125k+ files
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        
        result = await processor.process(job)
        
        # Should have been limited to 10,000
        assert result["total_documents"] <= 10000, \
            f"File limit not enforced! Processed {result['total_documents']} files"
        
        print(f"✅ File limit enforced: {result['total_documents']}/10,000 files")
    
    @pytest.mark.asyncio
    async def test_warning_logged_when_limited(self, caplog):
        """
        Test that warning is logged when files are limited.
        """
        import logging
        caplog.set_level(logging.WARNING)
        
        job = IngestionJobModel(
            id=uuid4(),
            repo_path="/host",
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        await processor.process(job)
        
        # Check for warning in logs
        warning_found = any(
            "Too many files" in record.message
            for record in caplog.records
            if record.levelno == logging.WARNING
        )
        
        assert warning_found, "No warning logged when file limit hit"
        print("✅ Warning logged when file limit exceeded")


class TestDirectoryExclusions:
    """Tests for enhanced directory exclusions."""
    
    @pytest.mark.asyncio
    async def test_venv_directories_excluded(self):
        """
        Test that venv directories are excluded from scanning.
        
        Before fix: venv directories were scanned (thousands of files)
        After fix: Explicitly excluded
        """
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Create normal files
        (repo_path / "src").mkdir()
        (repo_path / "src" / "main.py").write_text("# main\n")
        
        # Create venv with many files
        venv = repo_path / "venv"
        venv.mkdir()
        (venv / "lib").mkdir(parents=True)
        for i in range(100):
            (venv / "lib" / f"module_{i}.py").write_text(f"# venv {i}\n")
        
        job = IngestionJobModel(
            id=uuid4(),
            repo_path=str(repo_path),
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        result = await processor.process(job)
        
        shutil.rmtree(temp_dir)
        
        # Should only process src files, not venv
        assert result["total_documents"] < 5, \
            f"Venv not excluded! Processed {result['total_documents']} files"
        
        print(f"✅ Venv excluded: only {result['total_documents']} files processed")
    
    @pytest.mark.asyncio
    async def test_all_exclusions(self):
        """
        Test all directory exclusions work.
        
        Exclusions added based on 7-hour debug investigation.
        """
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Create excluded directories
        excluded_dirs = [
            'venv', 'venv_audit', 'venv_hardening', 'logs',
            'node_modules', '__pycache__', 'data', 'redis'
        ]
        
        for dirname in excluded_dirs:
            dir_path = repo_path / dirname
            dir_path.mkdir()
            for i in range(10):
                (dir_path / f"file_{i}.txt").write_text(f"excluded {i}\n")
        
        # Create included directory
        (repo_path / "src").mkdir()
        (repo_path / "src" / "main.py").write_text("# included\n")
        
        job = IngestionJobModel(
            id=uuid4(),
            repo_path=str(repo_path),
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        result = await processor.process(job)
        
        shutil.rmtree(temp_dir)
        
        # Should only process src/main.py
        assert result["total_documents"] <= 2, \
            f"Exclusions not working! Processed {result['total_documents']} files"
        
        print(f"✅ All exclusions working: {result['total_documents']} files processed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

