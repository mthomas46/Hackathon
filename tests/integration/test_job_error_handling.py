"""
Integration tests for job error handling and timeout protection.

Tests various failure scenarios:
- Git corruption
- Timeouts
- Network errors
- Partial failures
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
from services.ecosystem_mcp.src.services.git.git_error_handler import GitCorruptionError
from services.ecosystem_mcp.src.storage.db_models import IngestionJobModel


@pytest.fixture
def mock_job():
    """Create a mock ingestion job."""
    job = Mock(spec=IngestionJobModel)
    job.id = "test-job-123"
    job.repo_path = "/test/repo"
    job.mode = "quick"
    job.job_metadata = {}
    return job


@pytest.fixture
def mock_commit():
    """Create a mock git commit."""
    commit = Mock()
    commit.sha = "abc123def456"
    commit.author = Mock()
    commit.author.name = "Test Author"
    commit.committed_datetime = datetime.now()
    commit.message = "Test commit"
    return commit


@pytest.mark.asyncio
async def test_git_corruption_handling(mock_job, mock_commit):
    """Test that git corruption errors are handled gracefully."""
    processor = JobProcessor(worker_id="test-worker")
    
    # Mock git service to raise corruption error
    processor.git_service = Mock()
    processor.git_service.get_commit_files = AsyncMock(
        side_effect=IndexError("index out of range")
    )
    
    # Mock commit optimizer
    processor.commit_optimizer = Mock()
    processor.commit_optimizer.check_commit_already_ingested = AsyncMock(
        return_value={"already_ingested": False}
    )
    
    # Process commit - should handle error gracefully
    result = await processor._process_commit_with_batch_optimization(
        mock_commit,
        mock_job,
        batch_size=10
    )
    
    # Verify error was handled
    assert result["processed"] == 0
    assert result["failed"] == 1
    assert "error" in result
    assert "index out of range" in result["error"]


@pytest.mark.asyncio
async def test_commit_timeout_protection(mock_job, mock_commit):
    """Test that commits timeout after configured duration."""
    processor = JobProcessor(worker_id="test-worker")
    processor.commit_timeout_seconds = 1  # 1 second timeout for testing
    
    # Mock a slow commit processing function
    async def slow_process(*args, **kwargs):
        await asyncio.sleep(5)  # Longer than timeout
        return {"processed": 1, "failed": 0, "skipped": 0}
    
    processor._process_commit_with_batch_optimization = slow_process
    
    # Process commit with timeout
    result = await processor._process_commit_parallel(
        mock_commit,
        mock_job,
        commit_num=1,
        total_commits=1
    )
    
    # Verify timeout was triggered
    assert result["failed"] == 1
    assert "Timeout" in result.get("error", "")


@pytest.mark.asyncio
async def test_partial_commit_failure():
    """Test handling of commits where some files fail."""
    processor = JobProcessor(worker_id="test-worker")
    
    # Test with mix of successful and failed files
    # (This would require more complex mocking, showing the pattern)
    
    # Verify that partial failures are tracked correctly
    # and don't stop the entire job
    pass  # Placeholder for actual implementation


@pytest.mark.asyncio
async def test_parallel_commit_processing_with_errors(mock_job):
    """Test that parallel processing continues despite individual commit failures."""
    processor = JobProcessor(worker_id="test-worker", max_concurrent_commits=3)
    
    # Create mix of good and bad commits
    commits = []
    for i in range(5):
        commit = Mock()
        commit.sha = f"commit{i}abc"
        commits.append(commit)
    
    # Mock some commits to fail
    call_count = [0]
    
    async def mock_process_commit(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] in [2, 4]:  # 2nd and 4th commits fail
            raise Exception(f"Test error for commit {call_count[0]}")
        return {"processed": 1, "failed": 0, "skipped": 0, "embeddings": 1, "cost": 0.0}
    
    processor._process_commit_with_batch_optimization = mock_process_commit
    
    # Process all commits
    tasks = [
        processor._process_commit_parallel(commit, mock_job, i+1, len(commits))
        for i, commit in enumerate(commits)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify that 3 succeeded and 2 failed
    successful = sum(1 for r in results if not isinstance(r, Exception) and r.get("processed", 0) > 0)
    failed = sum(1 for r in results if not isinstance(r, Exception) and r.get("failed", 0) > 0)
    
    assert successful == 3
    assert failed == 2


@pytest.mark.asyncio
async def test_error_classification():
    """Test that different error types are classified correctly."""
    from services.ecosystem_mcp.src.services.git.git_error_handler import get_git_error_handler
    
    handler = get_git_error_handler()
    
    # Test corruption error
    error = IndexError("index out of range")
    classification = handler.classify_error(
        error,
        {"commit_sha": "abc123", "operation": "get_files"}
    )
    
    assert classification["category"] == "corruption"
    assert classification["suggested_action"] == "skip_commit"
    assert not classification["recoverable"]
    
    # Test unknown error
    error = ValueError("Some other error")
    classification = handler.classify_error(
        error,
        {"commit_sha": "def456", "operation": "process"}
    )
    
    assert classification["category"] == "unknown"
    assert "ValueError" in classification["error_type"]


@pytest.mark.asyncio
async def test_job_continues_after_corrupt_commit(mock_job):
    """Test that job processing continues even after encountering corrupt commits."""
    processor = JobProcessor(worker_id="test-worker")
    
    # Create multiple commits
    commits = []
    for i in range(3):
        commit = Mock()
        commit.sha = f"commit{i}xyz"
        commits.append(commit)
    
    # Mock git service - first commit corrupted, others OK
    call_count = [0]
    
    async def mock_get_files(commit_sha, *args):
        call_count[0] += 1
        if call_count[0] == 1:
            raise IndexError("index out of range")
        return [f"file{i}.py" for i in range(3)]
    
    processor.git_service = Mock()
    processor.git_service.get_commit_files = mock_get_files
    
    # Mock other dependencies
    processor.commit_optimizer = Mock()
    processor.commit_optimizer.check_commit_already_ingested = AsyncMock(
        return_value={"already_ingested": False}
    )
    
    # Process commits
    results = []
    for commit in commits:
        result = await processor._process_commit_with_batch_optimization(
            commit,
            mock_job,
            batch_size=10
        )
        results.append(result)
    
    # First should have error, others should proceed
    assert results[0]["failed"] == 1
    assert "error" in results[0]
    # (Would need more mocking for full test)


def test_error_summary_tracking():
    """Test that error summary is tracked correctly."""
    from services.ecosystem_mcp.src.services.git.git_error_handler import get_git_error_handler
    
    handler = get_git_error_handler()
    
    # Reset counts
    handler.error_counts = {
        "corruption": 0,
        "bad_object": 0,
        "bad_name": 0,
        "timeout": 0,
        "unknown": 0
    }
    
    # Classify multiple errors
    handler.classify_error(
        IndexError("index out of range"),
        {"commit_sha": "abc"}
    )
    handler.classify_error(
        IndexError("index out of range"),
        {"commit_sha": "def"}
    )
    handler.classify_error(
        ValueError("other error"),
        {"commit_sha": "ghi"}
    )
    
    summary = handler.get_error_summary()
    
    assert summary["corruption"] == 2
    assert summary["unknown"] == 1
    assert summary["bad_object"] == 0


@pytest.mark.asyncio
async def test_progress_tracking_with_errors(mock_job, mock_commit):
    """Test that progress tracking continues even with errors."""
    processor = JobProcessor(worker_id="test-worker")
    
    # Mock Redis progress tracking
    processor.redis_client = AsyncMock()
    processor.current_job_id = "test-job-123"
    
    # Mock git service to fail
    processor.git_service = Mock()
    processor.git_service.get_commit_files = AsyncMock(
        side_effect=IndexError("corruption")
    )
    
    processor.commit_optimizer = Mock()
    processor.commit_optimizer.check_commit_already_ingested = AsyncMock(
        return_value={"already_ingested": False}
    )
    
    # Process commit - should track progress even on error
    result = await processor._process_commit_with_batch_optimization(
        mock_commit,
        mock_job,
        batch_size=10
    )
    
    # Verify progress was attempted to be tracked
    # (Would need to check Redis mock calls in full implementation)
    assert result["failed"] == 1

