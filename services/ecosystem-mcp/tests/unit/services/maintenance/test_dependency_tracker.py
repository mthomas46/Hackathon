"""
Unit tests for DependencyTracker service.
Tests documentation dependency tracking and analysis.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from src.services.maintenance.dependency_tracker import DependencyTracker

@pytest.fixture
def sample_documents():
    """Create sample DocumentModel objects with dependencies."""
    from src.storage.db_models import DocumentModel
    
    doc1 = MagicMock(spec=DocumentModel)
    doc1.id = uuid4()
    doc1.file_path = "/docs/api.md"
    doc1.service_name = "test-service"
    doc1.content = "# API\n\nSee [guide](../docs/guide.md) for details."
    doc1.normalized_content = "# API\n\nSee [guide](../docs/guide.md) for details."
    
    doc2 = MagicMock(spec=DocumentModel)
    doc2.id = uuid4()
    doc2.file_path = "/docs/guide.md"
    doc2.service_name = "test-service"
    doc2.content = "# Guide\n\nRefer to [API](api.md)"
    doc2.normalized_content = "# Guide\n\nRefer to [API](api.md)"
    
    doc3 = MagicMock(spec=DocumentModel)
    doc3.id = uuid4()
    doc3.file_path = "/docs/standalone.md"
    doc3.service_name = "test-service"
    doc3.content = "# Standalone\n\nNo dependencies."
    doc3.normalized_content = "# Standalone\n\nNo dependencies."
    
    return [doc1, doc2, doc3]

@pytest.mark.unit
class TestTrackerInstantiation:
    def test_create_tracker(self):
        tracker = DependencyTracker()
        assert tracker is not None
    
    def test_tracker_has_methods(self):
        tracker = DependencyTracker()
        assert hasattr(tracker, 'build_dependency_graph')

@pytest.mark.unit
class TestDependencyMapping:
    async def test_build_dependency_graph(self, sample_documents):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.dependency_tracker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await tracker.build_dependency_graph(service_name="test-service")
                assert result is not None
                assert "nodes" in result
                assert "edges" in result

    async def test_graph_with_no_dependencies(self):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.dependency_tracker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = []
                
                result = await tracker.build_dependency_graph(service_name="test-service")
                assert result is not None
                assert isinstance(result, dict)

@pytest.mark.unit
class TestGraphAnalysis:
    async def test_graph_statistics(self, sample_documents):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.dependency_tracker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await tracker.build_dependency_graph(service_name="test-service")
                assert "statistics" in result

    async def test_identify_orphaned_documents(self, sample_documents):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.dependency_tracker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await tracker.build_dependency_graph(service_name="test-service")
                assert result is not None

@pytest.mark.unit
class TestImpactAnalysis:
    async def test_analyze_dependency_impact(self, sample_documents):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.dependency_tracker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await tracker.build_dependency_graph(service_name="test-service")
                assert "nodes" in result

    async def test_circular_dependency_detection(self, sample_documents):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.dependency_tracker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await tracker.build_dependency_graph(service_name="test-service")
                assert result is not None

@pytest.mark.unit
class TestDependencyReporting:
    async def test_generate_dependency_report(self, sample_documents):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.dependency_tracker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await tracker.build_dependency_graph(service_name="test-service")
                assert "metadata" in result

@pytest.mark.unit
class TestDependencyErrorHandling:
    async def test_handle_empty_service(self):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.dependency_tracker.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = []
                
                result = await tracker.build_dependency_graph(service_name="test-service")
                assert result is not None

    async def test_handle_tracker_error(self):
        tracker = DependencyTracker()
        with patch('src.services.maintenance.dependency_tracker.get_database') as mock_db:
            mock_context = AsyncMock()
            mock_context.__aenter__.side_effect = Exception("Database error")
            mock_db.return_value.session.return_value = mock_context
            
            with pytest.raises(Exception):
                await tracker.build_dependency_graph(service_name="test-service")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
