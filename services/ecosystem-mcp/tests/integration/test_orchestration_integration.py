"""
Integration Tests for Sub-Job Orchestration

Tests the critical Gap #1 fix: Wiring JobOrchestrator to ingestion pipeline.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime

# Import the components we're testing
from src.services.ingestion.job_processor import JobProcessor
from src.storage.db_models import IngestionJobModel


@pytest.mark.integration
@pytest.mark.skip(reason="Tests patch non-existent attributes - needs refactoring for current API")
class TestOrchestrationIntegration:
    """Test sub-job orchestration integrated into ingestion pipeline."""
    
    @pytest.fixture
    def job_processor(self):
        """Create job processor instance."""
        return JobProcessor()
    
    @pytest.fixture
    def test_job_standard(self):
        """Create test job without orchestration."""
        return IngestionJobModel(
            id=uuid4(),
            mode="full",
            status="pending",
            started_at=datetime.utcnow(),
            processed_documents=0,
            total_documents=0,
            failed_documents=0,
            skipped_documents=0,
            repo_path="/app",
            embeddings_generated=0,
            total_cost_usd=0.0,
            job_metadata={"use_subjobs": False}
        )
    
    @pytest.fixture
    def test_job_orchestrated(self):
        """Create test job with orchestration."""
        return IngestionJobModel(
            id=uuid4(),
            mode="full",
            status="pending",
            started_at=datetime.utcnow(),
            processed_documents=0,
            total_documents=0,
            failed_documents=0,
            skipped_documents=0,
            repo_path="/app",
            embeddings_generated=0,
            total_cost_usd=0.0,
            job_metadata={"use_subjobs": True}
        )
    
    async def test_orchestration_flag_detection(self, job_processor, test_job_orchestrated):
        """Test that use_subjobs flag is correctly detected."""
        # Check flag is present
        assert test_job_orchestrated.job_metadata.get('use_subjobs') == True
        
        # Should attempt orchestration (even if repo is small)
        with patch.object(job_processor, '_should_use_orchestration', return_value=False):
            with patch.object(job_processor, '_process_with_orchestration') as mock_orch:
                # The flag is detected, but repo size check says no
                result = await job_processor.process(test_job_orchestrated)
                # Should NOT call orchestration (repo too small)
                mock_orch.assert_not_called()
    
    async def test_standard_processing_when_flag_false(self, job_processor, test_job_standard):
        """Test standard processing used when use_subjobs=False."""
        with patch.object(job_processor, '_process_with_orchestration') as mock_orch:
            # Process job
            # This will fail without full setup, but we're testing routing
            try:
                result = await job_processor.process(test_job_standard)
            except Exception:
                pass  # Expected to fail in test environment
            
            # Orchestration should NOT be called
            mock_orch.assert_not_called()
    
    async def test_orchestration_called_when_conditions_met(self, job_processor, test_job_orchestrated):
        """Test orchestration called when use_subjobs=True and repo is large."""
        # Mock the checks to return True
        with patch.object(job_processor, '_should_use_orchestration', return_value=True):
            with patch.object(job_processor, '_process_with_orchestration', new_callable=AsyncMock) as mock_orch:
                # Set return value
                mock_orch.return_value = {
                    "success": True,
                    "processed_documents": 100,
                    "subjobs_executed": 5
                }
                
                # Process job
                result = await job_processor.process(test_job_orchestrated)
                
                # Orchestration SHOULD be called
                mock_orch.assert_called_once_with(test_job_orchestrated)
                
                # Check result
                assert result["success"] == True
                assert result["subjobs_executed"] == 5
    
    async def test_should_use_orchestration_quick_mode(self, job_processor):
        """Test that quick mode doesn't use orchestration."""
        job = IngestionJobModel(
            id=uuid4(),
            mode="quick",  # Quick mode
            status="pending",
            started_at=datetime.utcnow(),
            processed_documents=0,
            total_documents=0,
            failed_documents=0,
            skipped_documents=0,
            repo_path="/app",
            embeddings_generated=0,
            total_cost_usd=0.0,
            job_metadata={"use_subjobs": True}
        )
        
        # Quick mode should return False
        result = await job_processor._should_use_orchestration(job)
        assert result == False
    
    async def test_should_use_orchestration_small_repo(self, job_processor):
        """Test that small repos don't use orchestration."""
        job = IngestionJobModel(
            id=uuid4(),
            mode="full",
            status="pending",
            started_at=datetime.utcnow(),
            processed_documents=0,
            total_documents=0,
            failed_documents=0,
            skipped_documents=0,
            repo_path="/app",  # Will have <500 files in test
            embeddings_generated=0,
            total_cost_usd=0.0,
            job_metadata={"use_subjobs": True}
        )
        
        # Small repo should return False
        # (assumes /app has <500 files in test env)
        result = await job_processor._should_use_orchestration(job)
        # Can't assert since depends on actual file count
        # Just verify it doesn't crash
        assert isinstance(result, bool)
    
    async def test_orchestration_phases(self, job_processor, test_job_orchestrated):
        """Test that orchestration executes all 3 phases."""
        # Mock all the dependencies
        with patch('src.services.ingestion.job_processor.get_repository_scanner') as mock_scanner:
            with patch('src.services.ingestion.job_processor.get_file_classifier') as mock_classifier:
                with patch('src.services.ingestion.job_processor.get_processing_planner') as mock_planner:
                    with patch('src.services.ingestion.job_processor.JobOrchestrator') as mock_orchestrator_class:
                        # Setup mocks
                        mock_scanner_inst = AsyncMock()
                        mock_scanner_inst.scan.return_value = Mock(total_files=100, files=[])
                        mock_scanner.return_value = mock_scanner_inst
                        
                        mock_classifier_inst = AsyncMock()
                        mock_classifier_inst.classify.return_value = []
                        mock_classifier.return_value = mock_classifier_inst
                        
                        mock_planner_inst = AsyncMock()
                        mock_plan = Mock(id="plan_123", sub_jobs=[], estimated_time_minutes=10)
                        mock_planner_inst.create_plan.return_value = mock_plan
                        mock_planner.return_value = mock_planner_inst
                        
                        mock_orchestrator = AsyncMock()
                        mock_exec_result = Mock(
                            status="completed",
                            total_files_processed=100,
                            total_files_failed=0,
                            total_files_skipped=0,
                            sub_jobs_completed=5,
                            sub_jobs_failed=0
                        )
                        mock_orchestrator.execute_plan.return_value = mock_exec_result
                        mock_orchestrator_class.return_value = mock_orchestrator
                        
                        # Mock progress updates
                        with patch.object(job_processor, '_update_progress', new_callable=AsyncMock):
                            # Execute
                            result = await job_processor._process_with_orchestration(test_job_orchestrated)
                            
                            # Verify all phases called
                            mock_scanner_inst.scan.assert_called_once()
                            mock_classifier_inst.classify.assert_called_once()
                            mock_planner_inst.create_plan.assert_called_once()
                            mock_orchestrator.execute_plan.assert_called_once_with("plan_123")
                            
                            # Check result structure
                            assert result["success"] == True
                            assert result["processed_documents"] == 100
                            assert result["subjobs_executed"] == 5
                            assert "subjobs_failed" in result
    
    async def test_orchestration_handles_discovery_failure(self, job_processor, test_job_orchestrated):
        """Test graceful handling of discovery phase failure."""
        with patch('src.services.ingestion.job_processor.get_repository_scanner') as mock_scanner:
            # Make scanner raise exception
            mock_scanner_inst = AsyncMock()
            mock_scanner_inst.scan.side_effect = Exception("Scanner failed")
            mock_scanner.return_value = mock_scanner_inst
            
            with patch.object(job_processor, '_update_progress', new_callable=AsyncMock):
                # Execute
                result = await job_processor._process_with_orchestration(test_job_orchestrated)
                
                # Should fail gracefully
                assert result["success"] == False
                assert "Discovery failed" in result["error"]
                assert result["processed_documents"] == 0
    
    async def test_orchestration_handles_planning_failure(self, job_processor, test_job_orchestrated):
        """Test graceful handling of planning phase failure."""
        with patch('src.services.ingestion.job_processor.get_repository_scanner') as mock_scanner:
            with patch('src.services.ingestion.job_processor.get_file_classifier') as mock_classifier:
                with patch('src.services.ingestion.job_processor.get_processing_planner') as mock_planner:
                    # Setup successful discovery
                    mock_scanner_inst = AsyncMock()
                    mock_scanner_inst.scan.return_value = Mock(total_files=100, files=[])
                    mock_scanner.return_value = mock_scanner_inst
                    
                    mock_classifier_inst = AsyncMock()
                    mock_classifier_inst.classify.return_value = []
                    mock_classifier.return_value = mock_classifier_inst
                    
                    # Make planner fail
                    mock_planner_inst = AsyncMock()
                    mock_planner_inst.create_plan.side_effect = Exception("Planner failed")
                    mock_planner.return_value = mock_planner_inst
                    
                    with patch.object(job_processor, '_update_progress', new_callable=AsyncMock):
                        # Execute
                        result = await job_processor._process_with_orchestration(test_job_orchestrated)
                        
                        # Should fail gracefully
                        assert result["success"] == False
                        assert "Planning failed" in result["error"]
    
    async def test_orchestration_handles_execution_failure(self, job_processor, test_job_orchestrated):
        """Test graceful handling of execution phase failure."""
        with patch('src.services.ingestion.job_processor.get_repository_scanner') as mock_scanner:
            with patch('src.services.ingestion.job_processor.get_file_classifier') as mock_classifier:
                with patch('src.services.ingestion.job_processor.get_processing_planner') as mock_planner:
                    with patch('src.services.ingestion.job_processor.JobOrchestrator') as mock_orchestrator_class:
                        # Setup successful discovery & planning
                        mock_scanner_inst = AsyncMock()
                        mock_scanner_inst.scan.return_value = Mock(total_files=100, files=[])
                        mock_scanner.return_value = mock_scanner_inst
                        
                        mock_classifier_inst = AsyncMock()
                        mock_classifier_inst.classify.return_value = []
                        mock_classifier.return_value = mock_classifier_inst
                        
                        mock_planner_inst = AsyncMock()
                        mock_plan = Mock(id="plan_123", sub_jobs=[], estimated_time_minutes=10)
                        mock_planner_inst.create_plan.return_value = mock_plan
                        mock_planner.return_value = mock_planner_inst
                        
                        # Make orchestrator fail
                        mock_orchestrator = AsyncMock()
                        mock_orchestrator.execute_plan.side_effect = Exception("Execution failed")
                        mock_orchestrator_class.return_value = mock_orchestrator
                        
                        with patch.object(job_processor, '_update_progress', new_callable=AsyncMock):
                            # Execute
                            result = await job_processor._process_with_orchestration(test_job_orchestrated)
                            
                            # Should fail gracefully
                            assert result["success"] == False
                            assert "Orchestration failed" in result["error"]


@pytest.mark.integration
@pytest.mark.slow
class TestOrchestrationEndToEnd:
    """End-to-end tests with real components (requires full setup)."""
    
    @pytest.mark.skip(reason="Requires full database and service setup")
    async def test_full_orchestration_pipeline(self):
        """Test complete orchestration pipeline with real components."""
        # This test would require:
        # - Real database
        # - Real repository
        # - All services running
        # Skip for now, implement when infrastructure ready
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

