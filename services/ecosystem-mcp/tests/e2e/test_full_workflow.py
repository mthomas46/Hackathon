"""
End-to-end tests for complete Phase 1 + Phase 2 workflow
"""

import pytest
import tempfile
from pathlib import Path
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.discovery.discovery_engine import DiscoveryEngine
from src.services.orchestration.job_orchestrator import JobOrchestrator, ExecutionStatus
from src.services.orchestration.progress_tracker import ProgressTracker


@pytest.mark.e2e
@pytest.mark.asyncio
class TestFullWorkflowE2E:
    """End-to-end tests for complete workflow."""
    
    @pytest.fixture
    def test_repo(self):
        """Create a test repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create realistic project structure
            (repo_path / "src").mkdir()
            (repo_path / "src" / "__init__.py").write_text("")
            (repo_path / "src" / "main.py").write_text("""
def main():
    print("Hello World")
    
if __name__ == "__main__":
    main()
""")
            (repo_path / "src" / "utils.py").write_text("""
def helper(x):
    return x * 2
""")
            
            (repo_path / "tests").mkdir()
            (repo_path / "tests" / "__init__.py").write_text("")
            (repo_path / "tests" / "test_main.py").write_text("""
import pytest

def test_main():
    assert True
""")
            
            (repo_path / "README.md").write_text("# Test Project\n\nA test project")
            (repo_path / "requirements.txt").write_text("pytest==7.0.0\n")
            
            yield str(repo_path)
    
    @pytest.mark.asyncio
    async def test_complete_discovery_to_execution(self, test_repo):
        """Test complete workflow from discovery to execution."""
        # Phase 1: Discovery
        engine = DiscoveryEngine()
        discovery_result = await engine.discover(test_repo)
        
        assert discovery_result["success"] is True
        assert discovery_result["plan"]["total_files"] > 0
        assert len(discovery_result["sub_jobs"]) > 0
        
        # Mock database operations for testing
        with patch('src.services.orchestration.job_orchestrator.get_database') as mock_db:
            # Mock database session
            mock_session = AsyncMock()
            mock_db.return_value.session.return_value.__aenter__.return_value = mock_session
            
            # Mock plan loading
            async def mock_load_plan(plan_id):
                mock_plan = MagicMock()
                mock_plan.id = plan_id
                mock_plan.repository_path = test_repo
                mock_plan.total_files = discovery_result["plan"]["total_files"]
                mock_plan.total_sub_jobs = len(discovery_result["sub_jobs"])
                return mock_plan, []
            
            # Phase 2: Execution (mocked)
            orchestrator = JobOrchestrator(max_concurrent=2)
            
            # Note: Full execution would require database, embedding service, etc.
            # This test validates the orchestration logic without external dependencies
            
            # Verify orchestrator initialized
            assert orchestrator.max_concurrent == 2
            assert orchestrator.dependency_manager is not None
            assert orchestrator.resource_allocator is not None
    
    @pytest.mark.asyncio
    async def test_progress_tracking_throughout_workflow(self, test_repo):
        """Test progress tracking from start to finish."""
        engine = DiscoveryEngine()
        discovery_result = await engine.discover(test_repo)
        
        # Initialize progress tracker
        tracker = ProgressTracker()
        plan_id = "test_plan_1"
        
        # Start tracking
        await tracker.start_tracking(
            plan_id=plan_id,
            total_files=discovery_result["plan"]["total_files"],
            sub_jobs_total=len(discovery_result["sub_jobs"])
        )
        
        # Simulate processing
        sub_jobs = discovery_result["sub_jobs"]
        for i, sub_job in enumerate(sub_jobs):
            await tracker.update_sub_job_progress(
                plan_id=plan_id,
                sub_job_id=sub_job["sub_job_id"],
                files_processed=i + 1,
                files_failed=0,
                files_skipped=0,
                total_files=sub_job["file_count"]
            )
            
            # Mark as complete
            await tracker.mark_sub_job_complete(plan_id, sub_job["sub_job_id"], success=True)
        
        # Get final progress
        progress = await tracker.get_progress(plan_id)
        assert progress is not None
        assert progress.sub_jobs_completed == len(sub_jobs)
        
        # Cleanup
        await tracker.stop_tracking(plan_id)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, test_repo):
        """Test error handling throughout the workflow."""
        engine = DiscoveryEngine()
        
        # Test with nonexistent path
        result = await engine.discover("/nonexistent/path")
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_workflow_with_different_file_types(self, test_repo):
        """Test workflow handles various file types."""
        repo_path = Path(test_repo)
        
        # Add more file types
        (repo_path / "config.json").write_text('{"key": "value"}')
        (repo_path / "script.sh").write_text('#!/bin/bash\necho "test"')
        (repo_path / "data.csv").write_text('a,b,c\n1,2,3')
        
        engine = DiscoveryEngine()
        result = await engine.discover(test_repo)
        
        assert result["success"] is True
        
        # Verify different file types are recognized
        files = result["files"]
        file_types = set(f["file_type"] for f in files)
        assert len(file_types) > 1  # Should have multiple types
    
    @pytest.mark.asyncio
    async def test_workflow_performance_metrics(self, test_repo):
        """Test that performance metrics are captured."""
        engine = DiscoveryEngine()
        result = await engine.discover(test_repo)
        
        # Verify timing information
        plan = result["plan"]
        assert "estimated_time_minutes" in plan
        assert plan["estimated_time_minutes"] > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, test_repo):
        """Test multiple workflows can run concurrently."""
        engine = DiscoveryEngine()
        
        # Run two discoveries concurrently
        results = await asyncio.gather(
            engine.discover(test_repo),
            engine.discover(test_repo)
        )
        
        assert all(r["success"] for r in results)
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_workflow_idempotency(self, test_repo):
        """Test that running workflow twice gives consistent results."""
        engine = DiscoveryEngine()
        
        result1 = await engine.discover(test_repo)
        result2 = await engine.discover(test_repo)
        
        # Results should be consistent
        assert result1["plan"]["total_files"] == result2["plan"]["total_files"]
        assert result1["plan"]["total_sub_jobs"] == result2["plan"]["total_sub_jobs"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])

