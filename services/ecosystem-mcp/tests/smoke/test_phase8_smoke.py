"""
Smoke tests for Phase 8: Git-Optional Ingestion

Quick validation that Phase 8 features are accessible and functional.
"""

import pytest
from pathlib import Path


@pytest.mark.smoke
class TestPhase8Imports:
    """Test all Phase 8 modules can be imported."""
    
    def test_import_snapshot_processor(self):
        """Test SnapshotProcessor can be imported."""
        from src.services.ingestion.snapshot_processor import SnapshotProcessor
        assert SnapshotProcessor is not None
    
    def test_import_job_processor_router(self):
        """Test JobProcessorRouter can be imported."""
        from src.services.ingestion.job_processor_router import JobProcessorRouter
        assert JobProcessorRouter is not None
    
    def test_import_ingestion_models(self):
        """Test new API models can be imported."""
        from src.api.models.ingestion_models import (
            IngestionMode,
            IngestRequest,
            IngestionJobResponse,
            IngestionStatsResponse,
            ModeComparisonResponse
        )
        assert IngestionMode is not None
        assert IngestRequest is not None
        assert IngestionJobResponse is not None
        assert IngestionStatsResponse is not None
        assert ModeComparisonResponse is not None
    
    def test_import_updated_db_models(self):
        """Test updated database models can be imported."""
        from src.storage.db_models import DocumentModel, IngestionJobModel
        assert DocumentModel is not None
        assert IngestionJobModel is not None


@pytest.mark.smoke
class TestPhase8Models:
    """Test Phase 8 models are correctly configured."""
    
    def test_ingestion_mode_enum(self):
        """Test IngestionMode enum has correct values."""
        from src.api.models.ingestion_models import IngestionMode
        
        assert hasattr(IngestionMode, 'SNAPSHOT')
        assert hasattr(IngestionMode, 'GIT_HISTORY')
        assert IngestionMode.SNAPSHOT.value == "snapshot"
        assert IngestionMode.GIT_HISTORY.value == "git_history"
    
    def test_ingest_request_defaults(self):
        """Test IngestRequest has correct defaults."""
        from src.api.models.ingestion_models import IngestRequest, IngestionMode
        
        request = IngestRequest(repo_path="/app")
        
        assert request.repo_path == "/app"
        assert request.mode == IngestionMode.GIT_HISTORY  # Default
        assert request.include_patterns is None
        assert request.exclude_patterns is None
    
    def test_document_model_has_new_fields(self):
        """Test DocumentModel has Phase 8 fields."""
        from src.storage.db_models import DocumentModel
        from sqlalchemy import inspect
        
        mapper = inspect(DocumentModel)
        columns = {c.key for c in mapper.columns}
        
        # Phase 8 fields
        assert 'ingestion_mode' in columns
        assert 'version' in columns
        assert 'content_hash' in columns
        assert 'git_commit_sha' in columns


@pytest.mark.smoke
class TestPhase8Components:
    """Test Phase 8 components can be instantiated."""
    
    def test_snapshot_processor_instantiation(self):
        """Test SnapshotProcessor can be instantiated."""
        from src.services.ingestion.snapshot_processor import SnapshotProcessor
        
        processor = SnapshotProcessor(Path("/test"), "job123")
        
        assert processor is not None
        assert processor.repo_path == Path("/test")
        assert processor.job_id == "job123"
    
    def test_job_processor_router_instantiation(self):
        """Test JobProcessorRouter can be instantiated."""
        from src.services.ingestion.job_processor_router import JobProcessorRouter
        
        router = JobProcessorRouter()
        
        assert router is not None
    
    def test_ingest_request_validation(self):
        """Test IngestRequest validates correctly."""
        from src.api.models.ingestion_models import IngestRequest
        
        # Valid request
        request = IngestRequest(
            repo_path="/app",
            mode="snapshot",
            include_patterns=["*.py", "*.md"]
        )
        
        assert request.repo_path == "/app"
        assert request.mode == "snapshot"
        assert len(request.include_patterns) == 2


@pytest.mark.smoke
class TestPhase8Routing:
    """Test Phase 8 routing logic."""
    
    @pytest.mark.asyncio
    async def test_router_handles_snapshot_mode(self):
        """Test router can route snapshot mode."""
        from src.services.ingestion.job_processor_router import JobProcessorRouter
        from src.storage.db_models import IngestionJobModel
        from unittest.mock import Mock, AsyncMock, patch
        from uuid import uuid4
        
        job = Mock(spec=IngestionJobModel)
        job.id = uuid4()
        job.mode = 'snapshot'
        job.repo_path = '/test'
        
        with patch('src.services.ingestion.job_processor_router.get_snapshot_processor') as mock:
            processor = Mock()
            processor.process = AsyncMock(return_value={'mode': 'snapshot'})
            mock.return_value = processor
            
            router = JobProcessorRouter()
            result = await router.process(job)
            
            assert result['mode'] == 'snapshot'
    
    @pytest.mark.asyncio
    async def test_router_handles_git_history_mode(self):
        """Test router can route git_history mode."""
        from src.services.ingestion.job_processor_router import JobProcessorRouter
        from src.storage.db_models import IngestionJobModel
        from unittest.mock import Mock, AsyncMock, patch
        from uuid import uuid4
        
        job = Mock(spec=IngestionJobModel)
        job.id = uuid4()
        job.mode = 'git_history'
        job.repo_path = '/test'
        
        with patch('src.services.ingestion.job_processor_router.JobProcessor') as mock:
            processor = Mock()
            processor.process = AsyncMock(return_value={'processed_documents': 10})
            mock.return_value = processor
            
            router = JobProcessorRouter()
            result = await router.process(job)
            
            assert 'processed_documents' in result


@pytest.mark.smoke
class TestPhase8Documentation:
    """Test Phase 8 documentation exists."""
    
    def test_snapshot_processor_has_docstrings(self):
        """Test SnapshotProcessor has documentation."""
        from src.services.ingestion.snapshot_processor import SnapshotProcessor
        
        assert SnapshotProcessor.__doc__ is not None
        assert SnapshotProcessor.process.__doc__ is not None
    
    def test_router_has_docstrings(self):
        """Test JobProcessorRouter has documentation."""
        from src.services.ingestion.job_processor_router import JobProcessorRouter
        
        assert JobProcessorRouter.__doc__ is not None
        assert JobProcessorRouter.process.__doc__ is not None
    
    def test_api_models_have_docstrings(self):
        """Test API models have documentation."""
        from src.api.models.ingestion_models import IngestRequest, IngestionMode
        
        assert IngestRequest.__doc__ is not None
        assert IngestionMode.__doc__ is not None


@pytest.mark.smoke
class TestPhase8BackwardCompatibility:
    """Test Phase 8 maintains backward compatibility."""
    
    def test_default_mode_is_git_history(self):
        """Test default ingestion mode is git_history."""
        from src.api.models.ingestion_models import IngestRequest, IngestionMode
        
        request = IngestRequest(repo_path="/app")
        
        assert request.mode == IngestionMode.GIT_HISTORY
    
    def test_document_model_git_commit_nullable(self):
        """Test git_commit_sha is nullable for snapshot mode."""
        from src.storage.db_models import DocumentModel
        from sqlalchemy import inspect
        
        mapper = inspect(DocumentModel)
        git_commit_col = next(c for c in mapper.columns if c.key == 'git_commit_sha')
        
        assert git_commit_col.nullable is True
    
    def test_ingestion_mode_has_default(self):
        """Test ingestion_mode has default value."""
        from src.storage.db_models import DocumentModel
        from sqlalchemy import inspect
        
        mapper = inspect(DocumentModel)
        mode_col = next(c for c in mapper.columns if c.key == 'ingestion_mode')
        
        assert mode_col.default is not None
        assert mode_col.default.arg == 'git_history'


@pytest.mark.smoke
class TestPhase8Statistics:
    """Test Phase 8 code statistics."""
    
    def test_phase8_files_exist(self):
        """Test all Phase 8 files exist."""
        from pathlib import Path
        
        base = Path(__file__).parent.parent.parent
        
        files = [
            base / "src/services/ingestion/snapshot_processor.py",
            base / "src/services/ingestion/job_processor_router.py",
            base / "src/api/models/ingestion_models.py",
            base / "src/storage/migrations/008_add_snapshot_mode.py",
        ]
        
        for file in files:
            assert file.exists(), f"Missing Phase 8 file: {file}"
    
    def test_phase8_tests_exist(self):
        """Test Phase 8 test files exist."""
        from pathlib import Path
        
        base = Path(__file__).parent.parent
        
        test_files = [
            base / "unit/test_snapshot_processor.py",
            base / "unit/test_job_processor_router.py",
            base / "integration/test_phase8_integration.py",
            base / "e2e/test_phase8_e2e.py",
            base / "smoke/test_phase8_smoke.py",
        ]
        
        for file in test_files:
            assert file.exists(), f"Missing Phase 8 test file: {file}"


@pytest.mark.smoke
class TestPhase8QuickValidation:
    """Quick end-to-end validation of Phase 8."""
    
    def test_can_create_snapshot_request(self):
        """Test can create a valid snapshot request."""
        from src.api.models.ingestion_models import IngestRequest
        
        request = IngestRequest(
            repo_path="/app",
            mode="snapshot"
        )
        
        assert request.mode == "snapshot"
    
    def test_can_create_git_history_request(self):
        """Test can create a valid git_history request."""
        from src.api.models.ingestion_models import IngestRequest
        
        request = IngestRequest(
            repo_path="/app",
            mode="git_history"
        )
        
        assert request.mode == "git_history"
    
    @pytest.mark.asyncio
    async def test_router_can_process_both_modes(self):
        """Test router can process both modes."""
        from src.services.ingestion.job_processor_router import JobProcessorRouter
        
        router = JobProcessorRouter()
        
        assert router is not None
        # Actual processing requires mocking in other tests

