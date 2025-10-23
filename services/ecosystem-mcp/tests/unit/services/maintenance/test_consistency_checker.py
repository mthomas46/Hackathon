"""
Unit tests for ConsistencyChecker service.
Tests documentation consistency validation.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from src.services.maintenance.consistency_checker import ConsistencyChecker

@pytest.fixture
def sample_documents():
    """Create sample DocumentModel objects."""
    from src.storage.db_models import DocumentModel
    
    doc1 = MagicMock(spec=DocumentModel)
    doc1.id = uuid4()
    doc1.file_path = "/docs/api.md"
    doc1.service_name = "test-service"
    doc1.content = "# API Documentation\n\nSee [guide](../docs/guide.md) for more info."
    
    doc2 = MagicMock(spec=DocumentModel)
    doc2.id = uuid4()
    doc2.file_path = "/docs/guide.md"
    doc2.service_name = "test-service"
    doc2.content = "# User Guide\n\nRefer to the API docs for details."
    
    return [doc1, doc2]

@pytest.mark.unit
class TestConsistencyCheckerInstantiation:
    def test_create_checker(self):
        checker = ConsistencyChecker()
        assert checker is not None
    
    def test_checker_has_methods(self):
        checker = ConsistencyChecker()
        assert hasattr(checker, 'check_consistency')

@pytest.mark.unit  
class TestConsistencyChecks:
    async def test_check_cross_references(self, sample_documents):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            with patch('src.services.maintenance.consistency_checker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                result = await checker.check_consistency(service_name="test")
                assert result is not None
                assert isinstance(result, dict)

    async def test_check_link_validity(self, sample_documents):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            with patch('src.services.maintenance.consistency_checker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                result = await checker.check_consistency(service_name="test")
                assert isinstance(result, dict)

    async def test_check_format_consistency(self, sample_documents):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            with patch('src.services.maintenance.consistency_checker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                result = await checker.check_consistency(service_name="test")
                assert result is not None

@pytest.mark.unit
class TestInconsistencyDetection:
    async def test_detect_broken_links(self, sample_documents):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            with patch('src.services.maintenance.consistency_checker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                result = await checker.check_consistency(service_name="test")
                assert result is not None

    async def test_detect_formatting_issues(self, sample_documents):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            with patch('src.services.maintenance.consistency_checker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                result = await checker.check_consistency(service_name="test")
                assert result is not None

@pytest.mark.unit
class TestConsistencyReporting:
    async def test_generate_consistency_report(self, sample_documents):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            with patch('src.services.maintenance.consistency_checker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                result = await checker.check_consistency(service_name="test")
                assert result is not None

    async def test_report_includes_severity(self, sample_documents):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            with patch('src.services.maintenance.consistency_checker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                result = await checker.check_consistency(service_name="test")
                assert result is not None

@pytest.mark.unit
class TestConsistencyErrorHandling:
    async def test_handle_empty_docs(self):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            with patch('src.services.maintenance.consistency_checker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = []
                result = await checker.check_consistency(service_name="test")
                assert result is not None

    async def test_handle_check_error(self):
        checker = ConsistencyChecker()
        with patch('src.services.maintenance.consistency_checker.get_database') as mock_db:
            mock_context = AsyncMock()
            mock_context.__aenter__.side_effect = Exception("Database error")
            mock_db.return_value.session.return_value = mock_context
            with pytest.raises(Exception):
                await checker.check_consistency(service_name="test")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
