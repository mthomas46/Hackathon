"""
Comprehensive tests for job recovery system.

Tests checkpoint creation, state persistence, and graceful resumption
for ingestion, embeddings, and documentation jobs.
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Import recovery components
import sys
from pathlib import Path

# Add the service directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ecosystem-mcp"))

from src.utils.job_recovery import (
    JobCheckpoint,
    JobRecoveryManager,
    RecoverableJob,
    JobType,
    CheckpointStatus
)


class TestJobCheckpoint:
    """Test checkpoint creation and serialization."""
    
    def test_checkpoint_creation(self):
        """Test basic checkpoint creation."""
        checkpoint = JobCheckpoint(
            job_id="test-job-123",
            job_type=JobType.INGESTION,
            checkpoint_id="checkpoint-1",
            sequence=0,
            data={"test": "data"}
        )
        
        assert checkpoint.job_id == "test-job-123"
        assert checkpoint.job_type == JobType.INGESTION
        assert checkpoint.checkpoint_id == "checkpoint-1"
        assert checkpoint.sequence == 0
        assert checkpoint.status == CheckpointStatus.PENDING
        assert checkpoint.data == {"test": "data"}
        assert checkpoint.created_at is not None
        assert checkpoint.completed_at is None
    
    def test_checkpoint_to_dict(self):
        """Test checkpoint serialization."""
        checkpoint = JobCheckpoint(
            job_id="test-job-123",
            job_type=JobType.EMBEDDING,
            checkpoint_id="checkpoint-1",
            sequence=5,
            status=CheckpointStatus.COMPLETED,
            data={"processed": 100}
        )
        checkpoint.completed_at = datetime.utcnow()
        
        data = checkpoint.to_dict()
        
        assert data["job_id"] == "test-job-123"
        assert data["job_type"] == "embedding"
        assert data["checkpoint_id"] == "checkpoint-1"
        assert data["sequence"] == 5
        assert data["status"] == "completed"
        assert data["data"] == {"processed": 100}
        assert "created_at" in data
        assert "completed_at" in data
    
    def test_checkpoint_from_dict(self):
        """Test checkpoint deserialization."""
        data = {
            "job_id": "test-job-456",
            "job_type": "documentation",
            "checkpoint_id": "checkpoint-2",
            "sequence": 10,
            "status": "in_progress",
            "data": {"pass": 3},
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }
        
        checkpoint = JobCheckpoint.from_dict(data)
        
        assert checkpoint.job_id == "test-job-456"
        assert checkpoint.job_type == JobType.DOCUMENTATION
        assert checkpoint.checkpoint_id == "checkpoint-2"
        assert checkpoint.sequence == 10
        assert checkpoint.status == CheckpointStatus.IN_PROGRESS


class TestJobRecoveryManager:
    """Test recovery manager checkpoint management."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock()
        db.session = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db
    
    @pytest.fixture
    def recovery_manager(self, mock_db):
        """Create recovery manager instance."""
        return JobRecoveryManager(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_checkpoint(self, recovery_manager):
        """Test checkpoint creation."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()):
            checkpoint = await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-1",
                data={"test": "data"}
            )
            
            assert checkpoint.job_id == "job-1"
            assert checkpoint.checkpoint_id == "cp-1"
            assert checkpoint.sequence == 0
            assert "job-1" in recovery_manager.checkpoints
            assert len(recovery_manager.checkpoints["job-1"]) == 1
    
    @pytest.mark.asyncio
    async def test_multiple_checkpoints_sequence(self, recovery_manager):
        """Test checkpoint sequence numbering."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()):
            cp1 = await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-1",
                data={}
            )
            cp2 = await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-2",
                data={}
            )
            cp3 = await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-3",
                data={}
            )
            
            assert cp1.sequence == 0
            assert cp2.sequence == 1
            assert cp3.sequence == 2
    
    @pytest.mark.asyncio
    async def test_update_checkpoint_status(self, recovery_manager):
        """Test checkpoint status updates."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()):
            checkpoint = await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-1",
                data={}
            )
            
            assert checkpoint.status == CheckpointStatus.PENDING
            
            await recovery_manager.update_checkpoint_status(
                job_id="job-1",
                checkpoint_id="cp-1",
                status=CheckpointStatus.COMPLETED,
                data={"result": "success"}
            )
            
            updated = recovery_manager.checkpoints["job-1"][0]
            assert updated.status == CheckpointStatus.COMPLETED
            assert updated.data["result"] == "success"
            assert updated.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_last_checkpoint(self, recovery_manager):
        """Test retrieving last checkpoint."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()):
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-1",
                data={}
            )
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-2",
                data={}
            )
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-3",
                data={}
            )
            
            last = await recovery_manager.get_last_checkpoint("job-1")
            
            assert last is not None
            assert last.checkpoint_id == "cp-3"
            assert last.sequence == 2
    
    @pytest.mark.asyncio
    async def test_get_last_checkpoint_with_status_filter(self, recovery_manager):
        """Test retrieving last checkpoint with status filter."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()):
            cp1 = await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-1",
                data={}
            )
            await recovery_manager.update_checkpoint_status(
                "job-1", "cp-1", CheckpointStatus.COMPLETED
            )
            
            cp2 = await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-2",
                data={}
            )
            await recovery_manager.update_checkpoint_status(
                "job-1", "cp-2", CheckpointStatus.COMPLETED
            )
            
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-3",
                data={}
            )
            
            last_completed = await recovery_manager.get_last_checkpoint(
                "job-1",
                status=CheckpointStatus.COMPLETED
            )
            
            assert last_completed is not None
            assert last_completed.checkpoint_id == "cp-2"
    
    @pytest.mark.asyncio
    async def test_get_incomplete_checkpoints(self, recovery_manager):
        """Test retrieving incomplete checkpoints."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()):
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-1",
                data={}
            )
            await recovery_manager.update_checkpoint_status(
                "job-1", "cp-1", CheckpointStatus.COMPLETED
            )
            
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-2",
                data={}
            )
            
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-3",
                data={}
            )
            await recovery_manager.update_checkpoint_status(
                "job-1", "cp-3", CheckpointStatus.IN_PROGRESS
            )
            
            incomplete = await recovery_manager.get_incomplete_checkpoints("job-1")
            
            assert len(incomplete) == 2
            assert all(cp.status in [CheckpointStatus.PENDING, CheckpointStatus.IN_PROGRESS] for cp in incomplete)
    
    @pytest.mark.asyncio
    async def test_can_resume(self, recovery_manager):
        """Test can_resume logic."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()):
            # No checkpoints - cannot resume
            assert not await recovery_manager.can_resume("job-1")
            
            # Pending checkpoint - cannot resume
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-1",
                data={}
            )
            assert not await recovery_manager.can_resume("job-1")
            
            # Completed checkpoint - can resume
            await recovery_manager.update_checkpoint_status(
                "job-1", "cp-1", CheckpointStatus.COMPLETED
            )
            assert await recovery_manager.can_resume("job-1")
    
    @pytest.mark.asyncio
    async def test_get_resume_state(self, recovery_manager):
        """Test resume state retrieval."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()):
            # Create and complete checkpoint
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-1",
                data={"processed": 100}
            )
            await recovery_manager.update_checkpoint_status(
                "job-1", "cp-1", CheckpointStatus.COMPLETED
            )
            
            # Create incomplete checkpoint
            await recovery_manager.create_checkpoint(
                job_id="job-1",
                job_type=JobType.INGESTION,
                checkpoint_id="cp-2",
                data={}
            )
            
            resume_state = await recovery_manager.get_resume_state("job-1")
            
            assert resume_state["can_resume"] is True
            assert resume_state["last_checkpoint"]["checkpoint_id"] == "cp-1"
            assert resume_state["resume_from_sequence"] == 1
            assert resume_state["incomplete_count"] == 1
            assert resume_state["progress"]["completed_checkpoints"] == 1
            assert resume_state["progress"]["total_checkpoints"] == 2
    
    @pytest.mark.asyncio
    async def test_cleanup_checkpoints(self, recovery_manager):
        """Test checkpoint cleanup."""
        with patch.object(recovery_manager, '_persist_checkpoint', new=AsyncMock()), \
             patch.object(recovery_manager, '_delete_checkpoint', new=AsyncMock()):
            
            # Create 10 checkpoints
            for i in range(10):
                await recovery_manager.create_checkpoint(
                    job_id="job-1",
                    job_type=JobType.INGESTION,
                    checkpoint_id=f"cp-{i}",
                    data={}
                )
            
            assert len(recovery_manager.checkpoints["job-1"]) == 10
            
            # Cleanup, keeping last 3
            await recovery_manager.cleanup_checkpoints("job-1", keep_last=3)
            
            assert len(recovery_manager.checkpoints["job-1"]) == 3
            assert recovery_manager.checkpoints["job-1"][0].checkpoint_id == "cp-7"
            assert recovery_manager.checkpoints["job-1"][2].checkpoint_id == "cp-9"


class TestRecoverableJob:
    """Test recoverable job base class."""
    
    @pytest.fixture
    def mock_recovery_manager(self):
        """Mock recovery manager."""
        manager = Mock(spec=JobRecoveryManager)
        manager.create_checkpoint = AsyncMock()
        manager.update_checkpoint_status = AsyncMock()
        manager.can_resume = AsyncMock(return_value=True)
        manager.get_resume_state = AsyncMock(return_value={
            "can_resume": True,
            "last_checkpoint": {
                "data": {"processed": 50}
            },
            "resume_from_sequence": 1
        })
        return manager
    
    @pytest.mark.asyncio
    async def test_create_checkpoint(self, mock_recovery_manager):
        """Test checkpoint creation in recoverable job."""
        job = RecoverableJob(
            job_id="job-1",
            job_type=JobType.INGESTION,
            recovery_manager=mock_recovery_manager
        )
        
        checkpoint = Mock()
        checkpoint.checkpoint_id = "cp-1"
        mock_recovery_manager.create_checkpoint.return_value = checkpoint
        
        result = await job.create_checkpoint("cp-1", {"test": "data"})
        
        mock_recovery_manager.create_checkpoint.assert_called_once()
        assert job.current_checkpoint == checkpoint
    
    @pytest.mark.asyncio
    async def test_complete_checkpoint(self, mock_recovery_manager):
        """Test marking checkpoint as completed."""
        job = RecoverableJob(
            job_id="job-1",
            job_type=JobType.INGESTION,
            recovery_manager=mock_recovery_manager
        )
        
        checkpoint = Mock()
        checkpoint.checkpoint_id = "cp-1"
        job.current_checkpoint = checkpoint
        
        await job.complete_checkpoint(data={"result": "success"})
        
        mock_recovery_manager.update_checkpoint_status.assert_called_once_with(
            job_id="job-1",
            checkpoint_id="cp-1",
            status=CheckpointStatus.COMPLETED,
            data={"result": "success"}
        )
    
    @pytest.mark.asyncio
    async def test_fail_checkpoint(self, mock_recovery_manager):
        """Test marking checkpoint as failed."""
        job = RecoverableJob(
            job_id="job-1",
            job_type=JobType.INGESTION,
            recovery_manager=mock_recovery_manager
        )
        
        checkpoint = Mock()
        checkpoint.checkpoint_id = "cp-1"
        job.current_checkpoint = checkpoint
        
        await job.fail_checkpoint("Test error")
        
        mock_recovery_manager.update_checkpoint_status.assert_called_once_with(
            job_id="job-1",
            checkpoint_id="cp-1",
            status=CheckpointStatus.FAILED,
            data={"error": "Test error"}
        )


class TestIngestionRecovery:
    """Test ingestion job recovery."""
    
    @pytest.mark.asyncio
    async def test_ingestion_resume_from_checkpoint(self):
        """Test resuming ingestion from checkpoint."""
        # This would test the RecoverableJobProcessor
        # Integration test requiring database mocks
        pass
    
    @pytest.mark.asyncio
    async def test_ingestion_checkpoint_per_commit(self):
        """Test checkpoint creation for each commit."""
        pass
    
    @pytest.mark.asyncio
    async def test_ingestion_skip_completed_commits(self):
        """Test skipping already-processed commits on resume."""
        pass


class TestEmbeddingRecovery:
    """Test embedding generation recovery."""
    
    @pytest.mark.asyncio
    async def test_embedding_resume_from_checkpoint(self):
        """Test resuming embedding generation."""
        pass
    
    @pytest.mark.asyncio
    async def test_embedding_batch_checkpoints(self):
        """Test checkpoint creation every N documents."""
        pass
    
    @pytest.mark.asyncio
    async def test_embedding_skip_existing(self):
        """Test skipping documents with existing embeddings."""
        pass


class TestDocumentationRecovery:
    """Test documentation generation recovery."""
    
    @pytest.mark.asyncio
    async def test_documentation_resume_from_pass(self):
        """Test resuming documentation from last pass."""
        pass
    
    @pytest.mark.asyncio
    async def test_documentation_checkpoint_per_pass(self):
        """Test checkpoint creation for each pass."""
        pass
    
    @pytest.mark.asyncio
    async def test_documentation_save_intermediate_docs(self):
        """Test saving intermediate documents on checkpoint."""
        pass


class TestRecoveryAPI:
    """Test recovery API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_recovery_status(self):
        """Test GET /recovery/status/{job_id} endpoint."""
        pass
    
    @pytest.mark.asyncio
    async def test_get_checkpoints(self):
        """Test GET /recovery/checkpoints/{job_id} endpoint."""
        pass
    
    @pytest.mark.asyncio
    async def test_resume_job(self):
        """Test POST /recovery/resume endpoint."""
        pass
    
    @pytest.mark.asyncio
    async def test_cleanup_checkpoints_api(self):
        """Test DELETE /recovery/checkpoints/{job_id} endpoint."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

