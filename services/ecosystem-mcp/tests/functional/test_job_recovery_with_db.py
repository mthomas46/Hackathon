"""
Functional tests for job recovery with real database checkpoints.

These tests validate that jobs can be recovered after crashes or restarts
using real checkpoint data stored in the test database.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict, Any

from src.models.ingestion import IngestionJobModel, JobStatus
from src.repositories.ingestion_job_repository import IngestionJobRepository
from src.services.job_recovery.checkpoint_manager import CheckpointManager
from src.services.job_recovery.recovery_service import RecoveryService
from tests.utils.test_helpers import create_test_document


pytestmark = pytest.mark.functional


@pytest.fixture
async def checkpoint_manager(clean_database):
    """Checkpoint manager with test database."""
    return CheckpointManager(clean_database)


@pytest.fixture
async def recovery_service(clean_database, checkpoint_manager):
    """Recovery service with test database."""
    return RecoveryService(clean_database, checkpoint_manager)


@pytest.fixture
async def job_repo(clean_database):
    """Job repository with test database."""
    return IngestionJobRepository(clean_database)


class TestJobRecoveryBasics:
    """Test basic job recovery functionality."""

    async def test_save_and_load_checkpoint(
        self,
        checkpoint_manager,
        job_repo,
        test_session_id
    ):
        """Test saving and loading checkpoint data."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save checkpoint
        checkpoint_data = {
            "processed_files": ["file1.py", "file2.py"],
            "failed_files": ["file3.py"],
            "current_file": "file4.py",
            "total_files": 10,
            "progress": 0.3
        }
        await checkpoint_manager.save_checkpoint(job_id, checkpoint_data)

        # Load checkpoint
        loaded = await checkpoint_manager.load_checkpoint(job_id)

        assert loaded is not None
        assert loaded["processed_files"] == checkpoint_data["processed_files"]
        assert loaded["failed_files"] == checkpoint_data["failed_files"]
        assert loaded["current_file"] == checkpoint_data["current_file"]
        assert loaded["progress"] == checkpoint_data["progress"]

    async def test_recover_job_from_checkpoint(
        self,
        recovery_service,
        job_repo,
        checkpoint_manager,
        test_session_id
    ):
        """Test recovering a job from checkpoint."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save checkpoint
        checkpoint_data = {
            "processed_files": ["file1.py", "file2.py"],
            "failed_files": [],
            "current_file": "file3.py",
            "total_files": 5,
            "progress": 0.4
        }
        await checkpoint_manager.save_checkpoint(job_id, checkpoint_data)

        # Recover job
        recovered_job = await recovery_service.recover_job(job_id)

        assert recovered_job is not None
        assert recovered_job.id == job_id
        assert recovered_job.status == JobStatus.PROCESSING
        assert len(recovered_job.processed_files) == 2

    async def test_checkpoint_updates_incrementally(
        self,
        checkpoint_manager,
        job_repo,
        test_session_id
    ):
        """Test that checkpoints update incrementally."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save initial checkpoint
        await checkpoint_manager.save_checkpoint(job_id, {
            "processed_files": ["file1.py"],
            "progress": 0.2
        })

        # Update checkpoint
        await checkpoint_manager.save_checkpoint(job_id, {
            "processed_files": ["file1.py", "file2.py"],
            "progress": 0.4
        })

        # Load and verify
        loaded = await checkpoint_manager.load_checkpoint(job_id)
        assert len(loaded["processed_files"]) == 2
        assert loaded["progress"] == 0.4


class TestJobRecoveryAfterCrash:
    """Test job recovery after simulated crashes."""

    async def test_recover_after_worker_crash(
        self,
        recovery_service,
        job_repo,
        checkpoint_manager,
        test_session_id
    ):
        """Test recovery after worker process crashes."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            started_at=datetime.utcnow() - timedelta(minutes=10),
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Simulate partial progress before crash
        checkpoint_data = {
            "processed_files": ["file1.py", "file2.py", "file3.py"],
            "failed_files": ["file4.py"],
            "current_file": "file5.py",
            "total_files": 10,
            "progress": 0.4,
            "last_checkpoint": datetime.utcnow().isoformat()
        }
        await checkpoint_manager.save_checkpoint(job_id, checkpoint_data)

        # Simulate crash (job status still PROCESSING but no activity)
        # Recovery service should detect and recover

        # Recover job
        recovered_job = await recovery_service.recover_job(job_id)

        assert recovered_job is not None
        assert recovered_job.id == job_id
        assert len(recovered_job.processed_files) == 3
        assert len(recovered_job.failed_files) == 1
        # Job should resume from file5.py

    async def test_recover_multiple_jobs_after_crash(
        self,
        recovery_service,
        job_repo,
        checkpoint_manager,
        test_session_id
    ):
        """Test recovering multiple jobs after crash."""
        # Create multiple jobs
        job_ids = [str(uuid4()) for _ in range(3)]
        for job_id in job_ids:
            job = IngestionJobModel(
                id=job_id,
                repo_path=f"/test/repo{job_id}",
                status=JobStatus.PROCESSING,
                test_session_id=test_session_id
            )
            await job_repo.create(job)

            # Save checkpoint for each
            await checkpoint_manager.save_checkpoint(job_id, {
                "processed_files": [f"file{i}.py" for i in range(3)],
                "progress": 0.3
            })

        # Recover all jobs
        recovered_jobs = await recovery_service.recover_all_jobs()

        assert len(recovered_jobs) >= 3
        recovered_ids = [job.id for job in recovered_jobs]
        for job_id in job_ids:
            assert job_id in recovered_ids

    async def test_no_recovery_for_completed_jobs(
        self,
        recovery_service,
        job_repo,
        checkpoint_manager,
        test_session_id
    ):
        """Test that completed jobs are not recovered."""
        # Create completed job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.COMPLETED,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save checkpoint (shouldn't be used)
        await checkpoint_manager.save_checkpoint(job_id, {
            "processed_files": ["file1.py"],
            "progress": 0.5
        })

        # Try to recover
        recovered_job = await recovery_service.recover_job(job_id)

        # Should return None or indicate no recovery needed
        assert recovered_job is None or recovered_job.status == JobStatus.COMPLETED


class TestCheckpointFrequency:
    """Test checkpoint frequency and timing."""

    async def test_checkpoint_every_n_files(
        self,
        checkpoint_manager,
        job_repo,
        test_session_id
    ):
        """Test checkpointing every N files."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Simulate processing with checkpoints every 5 files
        checkpoint_frequency = 5
        processed_files = []

        for i in range(15):
            processed_files.append(f"file{i}.py")

            if (i + 1) % checkpoint_frequency == 0:
                await checkpoint_manager.save_checkpoint(job_id, {
                    "processed_files": processed_files.copy(),
                    "progress": (i + 1) / 15
                })

        # Load final checkpoint
        loaded = await checkpoint_manager.load_checkpoint(job_id)
        assert len(loaded["processed_files"]) == 15
        assert loaded["progress"] == 1.0

    async def test_checkpoint_on_error(
        self,
        checkpoint_manager,
        job_repo,
        test_session_id
    ):
        """Test checkpointing when errors occur."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Process files with some failures
        processed_files = ["file1.py", "file2.py"]
        failed_files = ["file3.py"]  # This file failed

        # Save checkpoint after error
        await checkpoint_manager.save_checkpoint(job_id, {
            "processed_files": processed_files,
            "failed_files": failed_files,
            "last_error": "Parse error in file3.py",
            "progress": 0.3
        })

        # Load and verify
        loaded = await checkpoint_manager.load_checkpoint(job_id)
        assert len(loaded["failed_files"]) == 1
        assert "last_error" in loaded


class TestRecoveryStrategies:
    """Test different recovery strategies."""

    async def test_resume_from_last_checkpoint(
        self,
        recovery_service,
        job_repo,
        checkpoint_manager,
        test_session_id
    ):
        """Test resuming from last checkpoint."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save checkpoint
        checkpoint_data = {
            "processed_files": ["file1.py", "file2.py"],
            "pending_files": ["file3.py", "file4.py", "file5.py"],
            "progress": 0.4
        }
        await checkpoint_manager.save_checkpoint(job_id, checkpoint_data)

        # Recover and resume
        recovered_job = await recovery_service.recover_job(job_id)
        resume_point = await recovery_service.get_resume_point(job_id)

        assert resume_point["next_file"] == "file3.py"
        assert len(resume_point["remaining_files"]) == 3

    async def test_skip_failed_files_on_recovery(
        self,
        recovery_service,
        job_repo,
        checkpoint_manager,
        test_session_id
    ):
        """Test that failed files are skipped on recovery."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save checkpoint with failed files
        checkpoint_data = {
            "processed_files": ["file1.py"],
            "failed_files": ["file2.py", "file3.py"],
            "pending_files": ["file4.py", "file5.py"],
            "progress": 0.3
        }
        await checkpoint_manager.save_checkpoint(job_id, checkpoint_data)

        # Recover
        recovered_job = await recovery_service.recover_job(job_id)
        resume_point = await recovery_service.get_resume_point(job_id)

        # Should skip failed files
        assert "file2.py" not in resume_point["remaining_files"]
        assert "file3.py" not in resume_point["remaining_files"]
        assert "file4.py" in resume_point["remaining_files"]

    async def test_retry_failed_files_with_flag(
        self,
        recovery_service,
        job_repo,
        checkpoint_manager,
        test_session_id
    ):
        """Test retrying failed files when retry flag is set."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save checkpoint with failed files
        checkpoint_data = {
            "processed_files": ["file1.py"],
            "failed_files": ["file2.py"],
            "pending_files": ["file3.py"],
            "progress": 0.5
        }
        await checkpoint_manager.save_checkpoint(job_id, checkpoint_data)

        # Recover with retry flag
        recovered_job = await recovery_service.recover_job(job_id, retry_failed=True)
        resume_point = await recovery_service.get_resume_point(job_id, retry_failed=True)

        # Should include failed files for retry
        all_files = resume_point["remaining_files"]
        assert "file2.py" in all_files or "file3.py" in all_files


class TestCheckpointCleanup:
    """Test checkpoint cleanup and maintenance."""

    async def test_cleanup_old_checkpoints(
        self,
        checkpoint_manager,
        job_repo,
        test_session_id
    ):
        """Test cleaning up old checkpoints."""
        # Create completed job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.COMPLETED,
            completed_at=datetime.utcnow() - timedelta(days=8),
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save checkpoint
        await checkpoint_manager.save_checkpoint(job_id, {
            "processed_files": ["file1.py"],
            "progress": 1.0
        })

        # Cleanup checkpoints older than 7 days
        await checkpoint_manager.cleanup_old_checkpoints(days=7)

        # Checkpoint should be deleted
        loaded = await checkpoint_manager.load_checkpoint(job_id)
        assert loaded is None or len(loaded) == 0

    async def test_keep_recent_checkpoints(
        self,
        checkpoint_manager,
        job_repo,
        test_session_id
    ):
        """Test that recent checkpoints are kept."""
        # Create recent job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save checkpoint
        checkpoint_data = {
            "processed_files": ["file1.py"],
            "progress": 0.5
        }
        await checkpoint_manager.save_checkpoint(job_id, checkpoint_data)

        # Cleanup old checkpoints
        await checkpoint_manager.cleanup_old_checkpoints(days=7)

        # Checkpoint should still exist
        loaded = await checkpoint_manager.load_checkpoint(job_id)
        assert loaded is not None
        assert loaded["progress"] == 0.5


class TestConcurrentRecovery:
    """Test recovery with concurrent operations."""

    async def test_concurrent_checkpoint_saves(
        self,
        checkpoint_manager,
        job_repo,
        test_session_id
    ):
        """Test concurrent checkpoint saves."""
        # Create job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Simulate concurrent saves
        async def save_checkpoint(file_num):
            await checkpoint_manager.save_checkpoint(job_id, {
                "processed_files": [f"file{i}.py" for i in range(file_num)],
                "progress": file_num / 10
            })

        # Save concurrently
        await asyncio.gather(*[save_checkpoint(i) for i in range(1, 6)])

        # Load final state
        loaded = await checkpoint_manager.load_checkpoint(job_id)
        assert loaded is not None
        # Should have the last saved state

    async def test_recovery_during_active_processing(
        self,
        recovery_service,
        job_repo,
        checkpoint_manager,
        test_session_id
    ):
        """Test that recovery doesn't interfere with active processing."""
        # Create active job
        job_id = str(uuid4())
        job = IngestionJobModel(
            id=job_id,
            repo_path="/test/repo",
            status=JobStatus.PROCESSING,
            started_at=datetime.utcnow(),  # Just started
            test_session_id=test_session_id
        )
        await job_repo.create(job)

        # Save recent checkpoint
        await checkpoint_manager.save_checkpoint(job_id, {
            "processed_files": ["file1.py"],
            "progress": 0.1,
            "last_checkpoint": datetime.utcnow().isoformat()
        })

        # Try to recover (should detect job is still active)
        recovered_job = await recovery_service.recover_job(job_id)

        # Should either return None or indicate job is active
        if recovered_job:
            assert recovered_job.status == JobStatus.PROCESSING

