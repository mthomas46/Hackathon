"""
Integration tests for optimized ingestion pipeline.

Tests the full ingestion flow with commit-level and batch optimizations.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
from services.ecosystem_mcp.src.storage.db_models import IngestionJobModel, DocumentModel
from services.ecosystem_mcp.src.models.git_commit import GitCommit


@pytest.fixture
def mock_git_service():
    """Create a mock GitService."""
    service = Mock()
    service.repo_path = Path("/test/repo")
    
    # Mock get_commit_files to return file list
    service.get_commit_files = AsyncMock(return_value=[
        "test/file1.py",
        "test/file2.py",
        "test/file3.md"
    ])
    
    # Mock get_file_content_at_commit
    async def mock_get_content(commit_sha, file_path):
        return f"Content of {file_path} at {commit_sha}"
    
    service.get_file_content_at_commit = mock_get_content
    
    return service


@pytest.fixture
def mock_commit():
    """Create a mock GitCommit."""
    return GitCommit(
        sha="abc123def456789",
        message="Test commit message",
        author="Test Author <test@example.com>",
        date=datetime.utcnow(),
        metadata={}
    )


@pytest.fixture
def test_job():
    """Create a test ingestion job."""
    job = IngestionJobModel(
        id=uuid4(),
        repo_path="/test/repo",
        mode="quick",
        status="queued",
        created_at=datetime.utcnow(),
        job_metadata={}
    )
    return job


@pytest.mark.asyncio
@pytest.mark.integration
async def test_commit_level_skip(mock_git_service, mock_commit, test_job):
    """Test that already-ingested commits are skipped entirely."""
    processor = JobProcessor(worker_id="test")
    processor.git_service = mock_git_service
    
    # Mock the commit optimizer to say commit is already ingested
    with patch.object(processor.commit_optimizer, 'check_commit_already_ingested') as mock_check:
        mock_check.return_value = {
            "already_ingested": True,
            "document_count": 10,
            "ingested_at": datetime.utcnow()
        }
        
        result = await processor._process_commit(mock_commit, test_job)
        
        # Should skip all files
        assert result["skipped"] == 10
        assert result["processed"] == 0
        assert result["failed"] == 0
        
        # Should not call get_commit_files (optimization worked)
        mock_git_service.get_commit_files.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_batch_duplicate_detection(mock_git_service, mock_commit, test_job):
    """Test that batch duplicate checking works correctly."""
    processor = JobProcessor(worker_id="test")
    processor.git_service = mock_git_service
    
    # Mock commit optimizer to allow processing
    with patch.object(processor.commit_optimizer, 'check_commit_already_ingested') as mock_commit_check:
        mock_commit_check.return_value = {
            "already_ingested": False,
            "document_count": 0,
            "ingested_at": None
        }
        
        # Mock batch_check_content_hashes to find some duplicates
        with patch.object(processor.commit_optimizer, 'batch_check_content_hashes') as mock_batch:
            # Return 2 out of 3 hashes as existing (duplicates)
            async def mock_batch_check(hashes):
                return {hashes[0], hashes[1]} if len(hashes) >= 2 else set()
            
            mock_batch.side_effect = mock_batch_check
            
            result = await processor._process_commit(mock_commit, test_job)
            
            # Should detect 2 duplicates via batch check
            assert result["skipped"] >= 2
            
            # Batch check should have been called
            mock_batch.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_optimization_performance():
    """Test that optimizations improve performance significantly."""
    # Create a processor
    processor = JobProcessor(worker_id="test")
    
    # Test batch checking 100 hashes
    test_hashes = [f"hash{i}" for i in range(100)]
    
    start_time = datetime.utcnow()
    existing = await processor.commit_optimizer.batch_check_content_hashes(test_hashes)
    elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    # Batch check should complete quickly (< 100ms for 100 hashes)
    assert elapsed_ms < 100
    assert isinstance(existing, set)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mixed_new_and_duplicate_files(mock_git_service, mock_commit, test_job):
    """Test processing a mix of new files and duplicates."""
    processor = JobProcessor(worker_id="test")
    processor.git_service = mock_git_service
    
    # Mock to allow commit processing
    with patch.object(processor.commit_optimizer, 'check_commit_already_ingested') as mock_commit_check:
        mock_commit_check.return_value = {
            "already_ingested": False,
            "document_count": 0,
            "ingested_at": None
        }
        
        # Mock batch check to return specific files as duplicates
        with patch.object(processor.commit_optimizer, 'batch_check_content_hashes') as mock_batch:
            # Simulate: file1 and file2 are duplicates, file3 is new
            async def mock_batch_check(hashes):
                # Return first 2 hashes as existing
                return {hashes[0], hashes[1]} if len(hashes) >= 2 else set()
            
            mock_batch.side_effect = mock_batch_check
            
            result = await processor._process_commit(mock_commit, test_job)
            
            # Should identify duplicates correctly
            assert result["skipped"] >= 2  # At least 2 duplicates detected


@pytest.mark.asyncio
@pytest.mark.integration
async def test_empty_commit_handling(mock_git_service, mock_commit, test_job):
    """Test handling of commits with no files."""
    processor = JobProcessor(worker_id="test")
    processor.git_service = mock_git_service
    
    # Mock get_commit_files to return empty list
    mock_git_service.get_commit_files.return_value = []
    
    with patch.object(processor.commit_optimizer, 'check_commit_already_ingested') as mock_check:
        mock_check.return_value = {
            "already_ingested": False,
            "document_count": 0,
            "ingested_at": None
        }
        
        result = await processor._process_commit(mock_commit, test_job)
        
        # Should handle gracefully
        assert result["processed"] == 0
        assert result["skipped"] == 0
        assert result["failed"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_large_file_batch_optimization():
    """Test batch optimization with large number of files."""
    processor = JobProcessor(worker_id="test")
    
    # Create 1000 test hashes
    test_hashes = [f"hash{i}" for i in range(1000)]
    
    start_time = datetime.utcnow()
    
    # Batch check all 1000 hashes at once
    existing = await processor.commit_optimizer.batch_check_content_hashes(test_hashes)
    
    elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    # Should complete in reasonable time (< 500ms for 1000 hashes)
    assert elapsed_ms < 500
    
    # Should return a set
    assert isinstance(existing, set)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_optimization_statistics():
    """Test that optimization statistics are tracked correctly."""
    processor = JobProcessor(worker_id="test")
    
    # Get commit statistics
    stats = await processor.commit_optimizer.get_commit_statistics()
    
    assert "unique_commits" in stats
    assert "total_documents" in stats
    assert "last_ingestion" in stats
    assert stats["unique_commits"] >= 0
    assert stats["total_documents"] >= 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_batch_checks():
    """Test that multiple batch checks can run concurrently."""
    processor = JobProcessor(worker_id="test")
    
    # Create multiple batches
    batch1 = [f"hash1_{i}" for i in range(100)]
    batch2 = [f"hash2_{i}" for i in range(100)]
    batch3 = [f"hash3_{i}" for i in range(100)]
    
    # Run all batch checks concurrently
    results = await asyncio.gather(
        processor.commit_optimizer.batch_check_content_hashes(batch1),
        processor.commit_optimizer.batch_check_content_hashes(batch2),
        processor.commit_optimizer.batch_check_content_hashes(batch3)
    )
    
    # All should complete successfully
    assert len(results) == 3
    assert all(isinstance(r, set) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

