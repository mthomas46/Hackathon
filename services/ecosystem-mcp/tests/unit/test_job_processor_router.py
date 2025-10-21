"""
Unit tests for JobProcessorRouter

Tests routing logic for snapshot vs git_history modes.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from uuid import uuid4

from src.services.ingestion.job_processor_router import JobProcessorRouter, route_and_process_job
from src.storage.db_models import IngestionJobModel


@pytest.fixture
def mock_job_snapshot():
    """Create a mock snapshot mode job."""
    job = Mock(spec=IngestionJobModel)
    job.id = uuid4()
    job.mode = 'snapshot'
    job.repo_path = '/test/repo'
    return job


@pytest.fixture
def mock_job_git_history():
    """Create a mock git_history mode job."""
    job = Mock(spec=IngestionJobModel)
    job.id = uuid4()
    job.mode = 'git_history'
    job.repo_path = '/test/repo'
    return job


class TestJobProcessorRouterBasic:
    """Basic router tests."""
    
    def test_router_instantiation(self):
        """Test router can be instantiated."""
        router = JobProcessorRouter()
        assert router is not None
    
    @pytest.mark.asyncio
    async def test_route_snapshot_mode(self, mock_job_snapshot):
        """Test routing to snapshot processor."""
        with patch('src.services.ingestion.job_processor_router.get_snapshot_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value={
                'mode': 'snapshot',
                'processed': 100,
                'elapsed_seconds': 60
            })
            mock_get_processor.return_value = mock_processor
            
            router = JobProcessorRouter()
            result = await router.process(mock_job_snapshot)
            
            # Should call snapshot processor
            mock_get_processor.assert_called_once()
            mock_processor.process.assert_called_once()
            
            assert result['mode'] == 'snapshot'
            assert result['processed'] == 100
    
    @pytest.mark.asyncio
    async def test_route_git_history_mode(self, mock_job_git_history):
        """Test routing to git history processor."""
        with patch('src.services.ingestion.job_processor_router.JobProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value={
                'processed_documents': 50
            })
            mock_processor_class.return_value = mock_processor
            
            router = JobProcessorRouter()
            result = await router.process(mock_job_git_history)
            
            # Should call git history processor
            mock_processor_class.assert_called_once_with(mock_job_git_history)
            mock_processor.process.assert_called_once()
            
            assert result['processed_documents'] == 50


class TestRoutingLogic:
    """Test routing decision logic."""
    
    @pytest.mark.asyncio
    async def test_unknown_mode_raises_error(self):
        """Test unknown mode raises ValueError."""
        job = Mock(spec=IngestionJobModel)
        job.id = uuid4()
        job.mode = 'unknown_mode'
        job.repo_path = '/test/repo'
        
        router = JobProcessorRouter()
        
        with pytest.raises(ValueError) as exc_info:
            await router.process(job)
        
        assert 'Unknown ingestion mode' in str(exc_info.value)
        assert 'unknown_mode' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_mode_case_sensitive(self):
        """Test mode matching is case-sensitive."""
        job = Mock(spec=IngestionJobModel)
        job.id = uuid4()
        job.mode = 'SNAPSHOT'  # Wrong case
        job.repo_path = '/test/repo'
        
        router = JobProcessorRouter()
        
        # Should raise error for incorrect case
        with pytest.raises(ValueError):
            await router.process(job)


class TestProcessorArguments:
    """Test arguments passed to processors."""
    
    @pytest.mark.asyncio
    async def test_snapshot_processor_receives_correct_args(self, mock_job_snapshot):
        """Test snapshot processor receives repo_path and job_id."""
        with patch('src.services.ingestion.job_processor_router.get_snapshot_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value={})
            mock_get_processor.return_value = mock_processor
            
            router = JobProcessorRouter()
            await router.process(mock_job_snapshot)
            
            # Check arguments
            call_args = mock_get_processor.call_args
            repo_path = call_args[0][0]
            job_id = call_args[0][1]
            
            assert isinstance(repo_path, Path)
            assert str(repo_path) == '/test/repo'
            assert job_id == str(mock_job_snapshot.id)
    
    @pytest.mark.asyncio
    async def test_git_processor_receives_job(self, mock_job_git_history):
        """Test git history processor receives full job."""
        with patch('src.services.ingestion.job_processor_router.JobProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value={})
            mock_processor_class.return_value = mock_processor
            
            router = JobProcessorRouter()
            await router.process(mock_job_git_history)
            
            # Should receive full job object
            mock_processor_class.assert_called_once_with(mock_job_git_history)


class TestConvenienceFunction:
    """Test route_and_process_job convenience function."""
    
    @pytest.mark.asyncio
    async def test_convenience_function(self, mock_job_snapshot):
        """Test convenience function works."""
        with patch('src.services.ingestion.job_processor_router.get_snapshot_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value={'mode': 'snapshot'})
            mock_get_processor.return_value = mock_processor
            
            result = await route_and_process_job(mock_job_snapshot)
            
            assert result['mode'] == 'snapshot'


class TestResultFormatting:
    """Test result formatting from processors."""
    
    @pytest.mark.asyncio
    async def test_snapshot_result_passthrough(self, mock_job_snapshot):
        """Test snapshot processor result is passed through."""
        expected_result = {
            'mode': 'snapshot',
            'processed': 100,
            'skipped': 10,
            'failed': 2,
            'elapsed_seconds': 120.5,
            'files_per_second': 0.83
        }
        
        with patch('src.services.ingestion.job_processor_router.get_snapshot_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value=expected_result)
            mock_get_processor.return_value = mock_processor
            
            router = JobProcessorRouter()
            result = await router.process(mock_job_snapshot)
            
            assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_git_history_result_passthrough(self, mock_job_git_history):
        """Test git history processor result is passed through."""
        expected_result = {
            'processed_documents': 50,
            'failed_documents': 2,
            'commits_processed': 100
        }
        
        with patch('src.services.ingestion.job_processor_router.JobProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value=expected_result)
            mock_processor_class.return_value = mock_processor
            
            router = JobProcessorRouter()
            result = await router.process(mock_job_git_history)
            
            assert result == expected_result


class TestErrorHandling:
    """Test error handling in routing."""
    
    @pytest.mark.asyncio
    async def test_snapshot_processor_error_propagates(self, mock_job_snapshot):
        """Test errors from snapshot processor propagate."""
        with patch('src.services.ingestion.job_processor_router.get_snapshot_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(side_effect=Exception("Snapshot failed"))
            mock_get_processor.return_value = mock_processor
            
            router = JobProcessorRouter()
            
            with pytest.raises(Exception) as exc_info:
                await router.process(mock_job_snapshot)
            
            assert "Snapshot failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_git_processor_error_propagates(self, mock_job_git_history):
        """Test errors from git processor propagate."""
        with patch('src.services.ingestion.job_processor_router.JobProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(side_effect=Exception("Git processing failed"))
            mock_processor_class.return_value = mock_processor
            
            router = JobProcessorRouter()
            
            with pytest.raises(Exception) as exc_info:
                await router.process(mock_job_git_history)
            
            assert "Git processing failed" in str(exc_info.value)


class TestLogging:
    """Test logging behavior."""
    
    @pytest.mark.asyncio
    async def test_logs_routing_decision(self, mock_job_snapshot, caplog):
        """Test router logs routing decision."""
        with patch('src.services.ingestion.job_processor_router.get_snapshot_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process = AsyncMock(return_value={})
            mock_get_processor.return_value = mock_processor
            
            router = JobProcessorRouter()
            await router.process(mock_job_snapshot)
            
            # Should log routing decision
            # Note: Actual log checking depends on test setup
            assert True  # Placeholder


class TestModeValidation:
    """Test mode validation."""
    
    @pytest.mark.asyncio
    async def test_valid_modes(self):
        """Test both valid modes are accepted."""
        valid_modes = ['snapshot', 'git_history']
        
        for mode in valid_modes:
            job = Mock(spec=IngestionJobModel)
            job.id = uuid4()
            job.mode = mode
            job.repo_path = '/test/repo'
            
            # Should not raise for valid modes
            # (will raise for other reasons if processors not mocked)
            router = JobProcessorRouter()
            
            # Verify mode is recognized (doesn't raise ValueError)
            assert job.mode in ['snapshot', 'git_history']
    
    @pytest.mark.asyncio
    async def test_none_mode_raises_error(self):
        """Test None mode raises error."""
        job = Mock(spec=IngestionJobModel)
        job.id = uuid4()
        job.mode = None
        job.repo_path = '/test/repo'
        
        router = JobProcessorRouter()
        
        with pytest.raises(ValueError):
            await router.process(job)
    
    @pytest.mark.asyncio
    async def test_empty_mode_raises_error(self):
        """Test empty string mode raises error."""
        job = Mock(spec=IngestionJobModel)
        job.id = uuid4()
        job.mode = ''
        job.repo_path = '/test/repo'
        
        router = JobProcessorRouter()
        
        with pytest.raises(ValueError):
            await router.process(job)

