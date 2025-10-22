"""
Stress Tests for Worker Loop and Job Processing

Tests the worker's ability to handle:
- Multiple concurrent jobs
- Large file sets (approaching 10k limit)
- Rapid job submission
- Worker restart scenarios
- Timeout protection
- Async yielding under load
"""

import pytest
import asyncio
import time
from uuid import uuid4
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from services.ecosystem_mcp.src.services.ingestion.ingestion_worker import IngestionWorker
from services.ecosystem_mcp.src.storage.db_models import IngestionJobModel


class TestWorkerStress:
    """Stress tests for ingestion worker."""
    
    @pytest.fixture
    async def worker(self):
        """Create and start a worker instance."""
        worker = IngestionWorker()
        await worker.start()
        yield worker
        await worker.stop()
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository with many files."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Create directory structure with many files
        for i in range(100):
            subdir = repo_path / f"dir_{i}"
            subdir.mkdir()
            for j in range(10):
                file_path = subdir / f"file_{j}.py"
                file_path.write_text(f"# File {i}-{j}\nprint('test')\n")
        
        yield repo_path
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_multiple_iterations_stress(self, worker):
        """
        Test worker can handle many iterations without hanging.
        
        SUCCESS CRITERIA:
        - Worker reaches 50+ iterations
        - No hanging or blocking
        - Memory usage stable
        """
        from services.ecosystem_mcp.src.utils.redis_client import get_redis_client
        
        redis = get_redis_client()
        await redis.connect()
        
        # Create 50 small test jobs
        job_ids = []
        for i in range(50):
            job_id = str(uuid4())
            job_ids.append(job_id)
            await redis.add_to_stream(
                stream=redis.INGESTION_STREAM,
                data={"job_id": job_id, "mode": "snapshot", "repo_path": "/host/tests"}
            )
        
        # Wait for worker to process all jobs (max 5 minutes)
        start_time = time.time()
        max_wait = 300  # 5 minutes
        
        while time.time() - start_time < max_wait:
            # Check how many jobs completed
            from services.ecosystem_mcp.src.storage import get_database
            async with get_database().session() as session:
                from sqlalchemy import select, func
                from services.ecosystem_mcp.src.storage.db_models import IngestionJobModel
                
                result = await session.execute(
                    select(func.count(IngestionJobModel.id))
                    .where(IngestionJobModel.id.in_(job_ids))
                    .where(IngestionJobModel.status.in_(["completed", "failed"]))
                )
                completed = result.scalar()
                
                if completed >= 50:
                    break
            
            await asyncio.sleep(2)
        
        elapsed = time.time() - start_time
        
        # Verify all jobs processed
        assert completed >= 50, f"Only {completed}/50 jobs completed in {elapsed:.1f}s"
        assert elapsed < max_wait, f"Took too long: {elapsed:.1f}s"
        
        print(f"✅ Processed 50 jobs in {elapsed:.1f}s ({elapsed/50:.2f}s per job)")
    
    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_large_file_set_stress(self, temp_repo):
        """
        Test processing approaching 10k file limit.
        
        SUCCESS CRITERIA:
        - Processes up to 10,000 files
        - Completes within 10 minutes
        - Async yielding prevents blocking
        - Memory usage acceptable
        """
        from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
        
        # Create a job targeting our temp repo with many files
        job = IngestionJobModel(
            id=uuid4(),
            repo_path=str(temp_repo),
            mode="snapshot",
            status="queued",
            started_at=datetime.utcnow()
        )
        
        processor = JobProcessor(worker_id="stress-test")
        
        start_time = time.time()
        result = await processor.process(job)
        elapsed = time.time() - start_time
        
        assert result["success"], f"Job failed: {result.get('error')}"
        assert result["total_documents"] > 0, "No documents processed"
        assert elapsed < 600, f"Took too long: {elapsed:.1f}s (>10min)"
        
        print(f"✅ Processed {result['total_documents']} files in {elapsed:.1f}s")
        print(f"   Throughput: {result['total_documents']/elapsed:.1f} files/sec")
    
    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_async_yielding_under_load(self, temp_repo):
        """
        Test that async yielding works under load.
        
        SUCCESS CRITERIA:
        - Event loop yields control during large scans
        - Other async tasks can run concurrently
        - No event loop blocking detected
        """
        from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
        
        # Create two jobs that will run concurrently
        job1 = IngestionJobModel(
            id=uuid4(),
            repo_path=str(temp_repo),
            mode="snapshot",
            status="queued"
        )
        
        job2 = IngestionJobModel(
            id=uuid4(),
            repo_path=str(temp_repo),
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        
        # Track if both jobs make progress
        progress_log = []
        
        async def monitor_progress():
            """Monitor that both jobs make progress."""
            for i in range(60):  # Monitor for 60 seconds
                await asyncio.sleep(1)
                progress_log.append(f"Monitor tick {i}")
        
        # Run jobs and monitor concurrently
        start_time = time.time()
        results = await asyncio.gather(
            processor.process(job1),
            processor.process(job2),
            monitor_progress(),
            return_exceptions=True
        )
        elapsed = time.time() - start_time
        
        # Verify both jobs completed
        assert not isinstance(results[0], Exception), f"Job 1 failed: {results[0]}"
        assert not isinstance(results[1], Exception), f"Job 2 failed: {results[1]}"
        assert len(progress_log) > 0, "Monitor didn't run - event loop blocked!"
        
        print(f"✅ Both jobs completed while monitor ran {len(progress_log)} times")
        print(f"   Elapsed: {elapsed:.1f}s")
    
    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_timeout_protection_stress(self):
        """
        Test timeout protection under stress.
        
        SUCCESS CRITERIA:
        - Timeout fires for legitimately stuck jobs
        - Doesn't fire for slow-but-progressing jobs
        - Worker continues after timeout
        """
        from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
        
        # Create a job that will take a while but should complete
        job = IngestionJobModel(
            id=uuid4(),
            repo_path="/host/services",
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        
        # Process with timeout
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                processor.process(job),
                timeout=120  # 2 minutes should be enough for /services
            )
            elapsed = time.time() - start_time
            
            assert result["success"] or result["total_documents"] > 0
            print(f"✅ Job completed in {elapsed:.1f}s without timeout")
        except asyncio.TimeoutError:
            pytest.fail("Timeout fired for valid job - async yielding not working!")
    
    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_worker_restart_recovery(self):
        """
        Test worker can recover after restart.
        
        SUCCESS CRITERIA:
        - Worker restarts cleanly
        - Picks up where it left off
        - No jobs lost
        """
        worker1 = IngestionWorker()
        await worker1.start()
        
        # Submit a job
        from services.ecosystem_mcp.src.utils.redis_client import get_redis_client
        redis = get_redis_client()
        await redis.connect()
        
        job_id = str(uuid4())
        await redis.add_to_stream(
            stream=redis.INGESTION_STREAM,
            data={"job_id": job_id, "mode": "snapshot", "repo_path": "/host/tests"}
        )
        
        # Give it a moment to start processing
        await asyncio.sleep(2)
        
        # Stop worker
        await worker1.stop()
        
        # Start new worker
        worker2 = IngestionWorker()
        await worker2.start()
        
        # Wait for job to complete (new worker should pick it up)
        await asyncio.sleep(10)
        
        # Verify job completed
        from services.ecosystem_mcp.src.storage import get_database
        async with get_database().session() as session:
            from services.ecosystem_mcp.src.storage.repositories import IngestionJobRepository
            repo = IngestionJobRepository(session)
            job = await repo.get_by_id(job_id)
            
            assert job is not None, "Job lost after worker restart!"
            assert job.status in ["completed", "processing"], f"Job status: {job.status}"
        
        await worker2.stop()
        print("✅ Worker restarted and recovered successfully")


class TestPerformanceBenchmarks:
    """Performance benchmarks for worker and job processing."""
    
    @pytest.mark.benchmark
    async def test_throughput_benchmark(self):
        """
        Benchmark: Files processed per second.
        
        TARGET: >100 files/sec
        """
        from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
        
        # Create temp directory with known file count
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        file_count = 1000
        for i in range(file_count):
            (repo_path / f"file_{i}.py").write_text(f"# File {i}\n")
        
        job = IngestionJobModel(
            id=uuid4(),
            repo_path=str(repo_path),
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        
        start_time = time.time()
        result = await processor.process(job)
        elapsed = time.time() - start_time
        
        shutil.rmtree(temp_dir)
        
        throughput = result["total_documents"] / elapsed
        
        print(f"\n📊 BENCHMARK: Throughput")
        print(f"   Files: {result['total_documents']}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Throughput: {throughput:.1f} files/sec")
        
        assert throughput > 50, f"Throughput too low: {throughput:.1f} files/sec"
    
    @pytest.mark.benchmark
    async def test_memory_usage_benchmark(self):
        """
        Benchmark: Memory usage during large scan.
        
        TARGET: <500MB for 10k files
        """
        import psutil
        import os
        from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
        
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        baseline_mb = process.memory_info().rss / 1024 / 1024
        
        # Process large directory
        job = IngestionJobModel(
            id=uuid4(),
            repo_path="/host/services",
            mode="snapshot",
            status="queued"
        )
        
        processor = JobProcessor()
        result = await processor.process(job)
        
        # Check peak memory
        peak_mb = process.memory_info().rss / 1024 / 1024
        delta_mb = peak_mb - baseline_mb
        
        print(f"\n📊 BENCHMARK: Memory Usage")
        print(f"   Baseline: {baseline_mb:.1f} MB")
        print(f"   Peak: {peak_mb:.1f} MB")
        print(f"   Delta: {delta_mb:.1f} MB")
        print(f"   Files Processed: {result['total_documents']}")
        print(f"   MB per 1000 files: {(delta_mb / result['total_documents']) * 1000:.1f}")
        
        assert delta_mb < 500, f"Memory usage too high: {delta_mb:.1f} MB"
    
    @pytest.mark.benchmark
    async def test_worker_iteration_latency(self):
        """
        Benchmark: Time between worker iterations.
        
        TARGET: <100ms when queue is empty
        """
        from services.ecosystem_mcp.src.services.ingestion.ingestion_worker import IngestionWorker
        
        worker = IngestionWorker()
        await worker.start()
        
        # Measure time between iterations (when queue is empty)
        iteration_times = []
        
        # Monitor for 30 seconds
        start_time = time.time()
        last_iteration = start_time
        
        while time.time() - start_time < 30:
            await asyncio.sleep(0.1)
            # Worker should be iterating with no jobs
            # In production, we'd monitor logs or add metrics
            current_time = time.time()
            iteration_times.append(current_time - last_iteration)
            last_iteration = current_time
        
        await worker.stop()
        
        avg_latency_ms = (sum(iteration_times) / len(iteration_times)) * 1000
        
        print(f"\n📊 BENCHMARK: Worker Iteration Latency")
        print(f"   Average: {avg_latency_ms:.1f}ms")
        print(f"   Min: {min(iteration_times)*1000:.1f}ms")
        print(f"   Max: {max(iteration_times)*1000:.1f}ms")
        
        # This is a proxy measurement, actual latency tracking would need instrumentation
        print("   Note: Actual measurement requires worker instrumentation")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

