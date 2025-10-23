"""
Functional tests for job recovery with real database checkpoints.

These tests validate that jobs can be recovered after crashes or restarts
using real checkpoint data stored in the test database.

ADAPTED to match actual JobRecoveryManager API.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import List, Dict, Any

from src.utils.job_recovery import JobRecoveryManager, JobType, CheckpointStatus, JobCheckpoint
from src.storage.db_models import IngestionJobModel
from src.storage.repositories import IngestionJobRepository


pytestmark = pytest.mark.functional


@pytest.fixture
async def recovery_manager(clean_database):
    """Job recovery manager with test database."""
    return JobRecoveryManager(clean_database)


@pytest.fixture
async def job_repo(clean_database):
    """Job repository with test database."""
    return IngestionJobRepository(clean_database)


@pytest.fixture
async def test_job(job_repo):
    """Create a test ingestion job."""
    created_job = await job_repo.create_job(
        mode="standard",
        status="running",
        repo_path="/test/repo",
        job_metadata={}
    )
    return created_job


# ============================================================================
# Test 1: Create and Retrieve Checkpoint
# ============================================================================

@pytest.mark.asyncio
async def test_create_checkpoint(recovery_manager, test_job):
    """Test creating a checkpoint and retrieving it."""
    job_id = str(test_job.id)
    
    # Create checkpoint
    checkpoint = await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="checkpoint_1",
        data={
            "processed_files": ["file1.py", "file2.py"],
            "current_index": 2,
            "total_files": 10
        }
    )
    
    # Verify checkpoint was created
    assert checkpoint is not None
    assert checkpoint.job_id == job_id
    assert checkpoint.job_type == JobType.INGESTION
    assert checkpoint.checkpoint_id == "checkpoint_1"
    assert checkpoint.sequence == 0  # First checkpoint
    assert checkpoint.status == CheckpointStatus.PENDING
    assert checkpoint.data["processed_files"] == ["file1.py", "file2.py"]
    
    # Retrieve last checkpoint
    last_checkpoint = await recovery_manager.get_last_checkpoint(job_id)
    assert last_checkpoint is not None
    assert last_checkpoint.checkpoint_id == "checkpoint_1"


# ============================================================================
# Test 2: Multiple Checkpoints with Sequence
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_checkpoints_sequence(recovery_manager, test_job):
    """Test creating multiple checkpoints maintains correct sequence."""
    job_id = str(test_job.id)
    
    # Create multiple checkpoints
    cp1 = await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={"index": 1}
    )
    
    cp2 = await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp2",
        data={"index": 2}
    )
    
    cp3 = await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp3",
        data={"index": 3}
    )
    
    # Verify sequences
    assert cp1.sequence == 0
    assert cp2.sequence == 1
    assert cp3.sequence == 2
    
    # Get last checkpoint
    last = await recovery_manager.get_last_checkpoint(job_id)
    assert last.checkpoint_id == "cp3"
    assert last.sequence == 2


# ============================================================================
# Test 3: Update Checkpoint Status
# ============================================================================

@pytest.mark.asyncio
async def test_update_checkpoint_status(recovery_manager, test_job):
    """Test updating checkpoint status."""
    job_id = str(test_job.id)
    
    # Create checkpoint
    checkpoint = await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={"files": 10}
    )
    
    assert checkpoint.status == CheckpointStatus.PENDING
    assert checkpoint.completed_at is None
    
    # Update to IN_PROGRESS
    await recovery_manager.update_checkpoint_status(
        job_id=job_id,
        checkpoint_id="cp1",
        status=CheckpointStatus.IN_PROGRESS
    )
    
    # Verify update
    last = await recovery_manager.get_last_checkpoint(job_id)
    assert last.status == CheckpointStatus.IN_PROGRESS
    
    # Update to COMPLETED
    await recovery_manager.update_checkpoint_status(
        job_id=job_id,
        checkpoint_id="cp1",
        status=CheckpointStatus.COMPLETED,
        data={"final_count": 15}
    )
    
    # Verify completion
    last = await recovery_manager.get_last_checkpoint(job_id)
    assert last.status == CheckpointStatus.COMPLETED
    assert last.data["final_count"] == 15
    assert last.completed_at is not None


# ============================================================================
# Test 4: Get Incomplete Checkpoints
# ============================================================================

@pytest.mark.asyncio
async def test_get_incomplete_checkpoints(recovery_manager, test_job):
    """Test retrieving incomplete checkpoints."""
    job_id = str(test_job.id)
    
    # Create checkpoints with different statuses
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={}
    )
    await recovery_manager.update_checkpoint_status(
        job_id, "cp1", CheckpointStatus.COMPLETED
    )
    
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp2",
        data={}
    )
    # cp2 stays PENDING
    
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp3",
        data={}
    )
    await recovery_manager.update_checkpoint_status(
        job_id, "cp3", CheckpointStatus.IN_PROGRESS
    )
    
    # Get incomplete checkpoints
    incomplete = await recovery_manager.get_incomplete_checkpoints(job_id)
    
    # Should have cp2 (PENDING) and cp3 (IN_PROGRESS)
    assert len(incomplete) == 2
    checkpoint_ids = [cp.checkpoint_id for cp in incomplete]
    assert "cp2" in checkpoint_ids
    assert "cp3" in checkpoint_ids


# ============================================================================
# Test 5: Can Resume Check
# ============================================================================

@pytest.mark.asyncio
async def test_can_resume(recovery_manager, test_job):
    """Test checking if a job can be resumed."""
    job_id = str(test_job.id)
    
    # No checkpoints - cannot resume
    can_resume = await recovery_manager.can_resume(job_id)
    assert can_resume is False
    
    # Create checkpoint but don't complete it
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={}
    )
    
    # Still cannot resume (no completed checkpoints)
    can_resume = await recovery_manager.can_resume(job_id)
    assert can_resume is False
    
    # Complete the checkpoint
    await recovery_manager.update_checkpoint_status(
        job_id, "cp1", CheckpointStatus.COMPLETED
    )
    
    # Now can resume
    can_resume = await recovery_manager.can_resume(job_id)
    assert can_resume is True


# ============================================================================
# Test 6: Get Resume State
# ============================================================================

@pytest.mark.asyncio
async def test_get_resume_state(recovery_manager, test_job):
    """Test getting resume state for a job."""
    job_id = str(test_job.id)
    
    # No checkpoints
    state = await recovery_manager.get_resume_state(job_id)
    assert state["can_resume"] is False
    assert "reason" in state
    
    # Create and complete checkpoints
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={"processed": 10}
    )
    await recovery_manager.update_checkpoint_status(
        job_id, "cp1", CheckpointStatus.COMPLETED
    )
    
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp2",
        data={"processed": 20}
    )
    await recovery_manager.update_checkpoint_status(
        job_id, "cp2", CheckpointStatus.COMPLETED
    )
    
    # Get resume state
    state = await recovery_manager.get_resume_state(job_id)
    assert state["can_resume"] is True
    assert "last_checkpoint" in state
    assert state["last_checkpoint"]["checkpoint_id"] == "cp2"
    assert state["resume_from_sequence"] == 2  # Next sequence after 1 (cp2 is at sequence 1)
    assert "progress" in state


# ============================================================================
# Test 7: Cleanup Old Checkpoints
# ============================================================================

@pytest.mark.asyncio
async def test_cleanup_checkpoints(recovery_manager, test_job):
    """Test cleaning up old checkpoints."""
    job_id = str(test_job.id)
    
    # Create 10 checkpoints
    for i in range(10):
        await recovery_manager.create_checkpoint(
            job_id=job_id,
            job_type=JobType.INGESTION,
            checkpoint_id=f"cp{i}",
            data={"index": i}
        )
    
    # Verify all 10 exist
    checkpoints = recovery_manager.checkpoints.get(job_id, [])
    assert len(checkpoints) == 10
    
    # Cleanup, keeping last 3
    await recovery_manager.cleanup_checkpoints(job_id, keep_last=3)
    
    # Verify only 3 remain
    checkpoints = recovery_manager.checkpoints.get(job_id, [])
    assert len(checkpoints) == 3
    
    # Verify they are the last 3
    assert checkpoints[0].checkpoint_id == "cp7"
    assert checkpoints[1].checkpoint_id == "cp8"
    assert checkpoints[2].checkpoint_id == "cp9"


# ============================================================================
# Test 8: Filter Checkpoints by Status
# ============================================================================

@pytest.mark.asyncio
async def test_filter_checkpoints_by_status(recovery_manager, test_job):
    """Test filtering checkpoints by status."""
    job_id = str(test_job.id)
    
    # Create checkpoints with different statuses
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={}
    )
    await recovery_manager.update_checkpoint_status(
        job_id, "cp1", CheckpointStatus.COMPLETED
    )
    
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp2",
        data={}
    )
    await recovery_manager.update_checkpoint_status(
        job_id, "cp2", CheckpointStatus.FAILED
    )
    
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp3",
        data={}
    )
    # cp3 stays PENDING
    
    # Get last completed checkpoint
    last_completed = await recovery_manager.get_last_checkpoint(
        job_id, status=CheckpointStatus.COMPLETED
    )
    assert last_completed is not None
    assert last_completed.checkpoint_id == "cp1"
    
    # Get last pending checkpoint
    last_pending = await recovery_manager.get_last_checkpoint(
        job_id, status=CheckpointStatus.PENDING
    )
    assert last_pending is not None
    assert last_pending.checkpoint_id == "cp3"


# ============================================================================
# Test 9: Checkpoint Data Persistence
# ============================================================================

@pytest.mark.asyncio
async def test_checkpoint_data_persistence(recovery_manager, test_job, job_repo):
    """Test that checkpoint data is persisted to database."""
    job_id = str(test_job.id)
    
    # Create checkpoint with data
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={
            "processed_files": ["a.py", "b.py"],
            "metrics": {"count": 100}
        }
    )
    
    # Retrieve job from database
    job = await job_repo.get_by_id(UUID(job_id))
    
    # Verify checkpoint is in metadata
    assert job is not None
    assert job.job_metadata is not None
    assert "checkpoints" in job.job_metadata
    assert len(job.job_metadata["checkpoints"]) == 1
    
    checkpoint_data = job.job_metadata["checkpoints"][0]
    assert checkpoint_data["checkpoint_id"] == "cp1"
    assert checkpoint_data["data"]["processed_files"] == ["a.py", "b.py"]


# ============================================================================
# Test 10: Concurrent Checkpoint Creation
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_checkpoint_creation(recovery_manager, test_job):
    """Test creating checkpoints concurrently."""
    job_id = str(test_job.id)
    
    # Create checkpoints concurrently
    tasks = [
        recovery_manager.create_checkpoint(
            job_id=job_id,
            job_type=JobType.INGESTION,
            checkpoint_id=f"cp{i}",
            data={"index": i}
        )
        for i in range(5)
    ]
    
    checkpoints = await asyncio.gather(*tasks)
    
    # Verify all created
    assert len(checkpoints) == 5
    
    # Verify sequences are unique
    sequences = [cp.sequence for cp in checkpoints]
    assert len(set(sequences)) == 5  # All unique


# ============================================================================
# Test 11: Checkpoint to_dict and from_dict
# ============================================================================

@pytest.mark.asyncio
async def test_checkpoint_serialization(recovery_manager, test_job):
    """Test checkpoint serialization and deserialization."""
    job_id = str(test_job.id)
    
    # Create checkpoint
    original = await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={"test": "data"}
    )
    
    # Serialize
    checkpoint_dict = original.to_dict()
    
    # Verify dict structure
    assert checkpoint_dict["job_id"] == job_id
    assert checkpoint_dict["job_type"] == "ingestion"
    assert checkpoint_dict["checkpoint_id"] == "cp1"
    assert checkpoint_dict["data"]["test"] == "data"
    
    # Deserialize
    restored = JobCheckpoint.from_dict(checkpoint_dict)
    
    # Verify restoration
    assert restored.job_id == original.job_id
    assert restored.job_type == original.job_type
    assert restored.checkpoint_id == original.checkpoint_id
    assert restored.data == original.data


# ============================================================================
# Test 12: Different Job Types
# ============================================================================

@pytest.mark.asyncio
async def test_different_job_types(recovery_manager, test_job):
    """Test checkpoints for different job types."""
    job_id = str(test_job.id)
    
    # Create checkpoints for different job types
    ingestion_cp = await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="ingestion_cp",
        data={}
    )
    
    embedding_cp = await recovery_manager.create_checkpoint(
        job_id=f"{job_id}_embedding",
        job_type=JobType.EMBEDDING,
        checkpoint_id="embedding_cp",
        data={}
    )
    
    doc_cp = await recovery_manager.create_checkpoint(
        job_id=f"{job_id}_doc",
        job_type=JobType.DOCUMENTATION,
        checkpoint_id="doc_cp",
        data={}
    )
    
    # Verify job types
    assert ingestion_cp.job_type == JobType.INGESTION
    assert embedding_cp.job_type == JobType.EMBEDDING
    assert doc_cp.job_type == JobType.DOCUMENTATION


# ============================================================================
# Test 13: Empty Job ID Handling
# ============================================================================

@pytest.mark.asyncio
async def test_empty_job_handling(recovery_manager):
    """Test handling of non-existent job."""
    fake_job_id = str(uuid4())
    
    # Try to get checkpoints for non-existent job
    last = await recovery_manager.get_last_checkpoint(fake_job_id)
    assert last is None
    
    incomplete = await recovery_manager.get_incomplete_checkpoints(fake_job_id)
    assert len(incomplete) == 0
    
    can_resume = await recovery_manager.can_resume(fake_job_id)
    assert can_resume is False


# ============================================================================
# Test 14: Checkpoint Status Transitions
# ============================================================================

@pytest.mark.asyncio
async def test_checkpoint_status_transitions(recovery_manager, test_job):
    """Test valid checkpoint status transitions."""
    job_id = str(test_job.id)
    
    # Create checkpoint
    await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="cp1",
        data={}
    )
    
    # PENDING -> IN_PROGRESS
    await recovery_manager.update_checkpoint_status(
        job_id, "cp1", CheckpointStatus.IN_PROGRESS
    )
    cp = await recovery_manager.get_last_checkpoint(job_id)
    assert cp.status == CheckpointStatus.IN_PROGRESS
    
    # IN_PROGRESS -> COMPLETED
    await recovery_manager.update_checkpoint_status(
        job_id, "cp1", CheckpointStatus.COMPLETED
    )
    cp = await recovery_manager.get_last_checkpoint(job_id)
    assert cp.status == CheckpointStatus.COMPLETED
    assert cp.completed_at is not None


# ============================================================================
# Test 15: Large Checkpoint Data
# ============================================================================

@pytest.mark.asyncio
async def test_large_checkpoint_data(recovery_manager, test_job):
    """Test checkpoint with large data payload."""
    job_id = str(test_job.id)
    
    # Create large data
    large_data = {
        "processed_files": [f"file{i}.py" for i in range(1000)],
        "metrics": {f"metric{i}": i * 100 for i in range(100)},
        "metadata": {"description": "x" * 10000}
    }
    
    # Create checkpoint with large data
    checkpoint = await recovery_manager.create_checkpoint(
        job_id=job_id,
        job_type=JobType.INGESTION,
        checkpoint_id="large_cp",
        data=large_data
    )
    
    # Verify data is preserved
    assert len(checkpoint.data["processed_files"]) == 1000
    assert len(checkpoint.data["metrics"]) == 100
    assert len(checkpoint.data["metadata"]["description"]) == 10000
    
    # Retrieve and verify
    last = await recovery_manager.get_last_checkpoint(job_id)
    assert len(last.data["processed_files"]) == 1000

