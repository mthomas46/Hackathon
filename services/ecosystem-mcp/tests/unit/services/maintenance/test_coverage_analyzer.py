"""
Unit tests for CoverageAnalyzer service.

Tests documentation coverage analysis and gap identification.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.maintenance.coverage_analyzer import CoverageAnalyzer


@pytest.fixture
def sample_documents():
    """Create sample DocumentModel objects for coverage analysis."""
    from uuid import uuid4
    from src.storage.db_models import DocumentModel
    
    doc1 = MagicMock(spec=DocumentModel)
    doc1.id = uuid4()
    doc1.file_path = "/src/api.py"
    doc1.service_name = "test-service"
    
    doc2 = MagicMock(spec=DocumentModel)
    doc2.id = uuid4()
    doc2.file_path = "/src/utils.py"
    doc2.service_name = "test-service"
    
    doc3 = MagicMock(spec=DocumentModel)
    doc3.id = uuid4()
    doc3.file_path = "/docs/api.md"
    doc3.service_name = "test-service"
    
    return [doc1, doc2, doc3]


@pytest.mark.unit
class TestCoverageAnalyzerInstantiation:
    """Test CoverageAnalyzer instantiation."""
    
    def test_create_analyzer(self):
        """Test creating a CoverageAnalyzer instance."""
        analyzer = CoverageAnalyzer()
        assert analyzer is not None
    
    def test_analyzer_has_methods(self):
        """Test that CoverageAnalyzer has required methods."""
        analyzer = CoverageAnalyzer()
        assert hasattr(analyzer, 'analyze_coverage')


@pytest.mark.unit
class TestCoverageAnalysis:
    """Test coverage analysis functionality."""
    
    async def test_analyze_service_coverage(self, sample_documents):
        """Test analyzing documentation coverage for a service."""
        analyzer = CoverageAnalyzer()
        
        with patch('src.services.maintenance.coverage_analyzer.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.coverage_analyzer.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await analyzer.analyze_coverage(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)
                assert "overall_coverage" in result
                assert "metadata" in result
    
    async def test_coverage_with_no_documentation(self):
        """Test coverage analysis when no documentation exists."""
        analyzer = CoverageAnalyzer()
        
        with patch('src.services.maintenance.coverage_analyzer.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.coverage_analyzer.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = []
                
                result = await analyzer.analyze_coverage(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)
                assert result["metadata"]["total_documents"] == 0


@pytest.mark.unit
class TestCoverageMetrics:
    """Test coverage metric calculations."""
    
    async def test_get_coverage_metrics(self, sample_documents):
        """Test retrieving coverage metrics."""
        analyzer = CoverageAnalyzer()
        
        with patch('src.services.maintenance.coverage_analyzer.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.coverage_analyzer.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await analyzer.analyze_coverage(service_name="test-service")
                
                assert "overall_coverage" in result
                assert isinstance(result["overall_coverage"], dict)
    
    async def test_coverage_with_zero_files(self):
        """Test coverage calculation with zero files."""
        analyzer = CoverageAnalyzer()
        
        with patch('src.services.maintenance.coverage_analyzer.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.coverage_analyzer.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = []
                
                result = await analyzer.analyze_coverage(service_name="test-service")
                
                assert result["metadata"]["total_documents"] == 0


@pytest.mark.unit
class TestGapIdentification:
    """Test identifying documentation gaps."""
    
    async def test_identify_undocumented_files(self, sample_documents):
        """Test identifying files without documentation."""
        analyzer = CoverageAnalyzer()
        
        with patch('src.services.maintenance.coverage_analyzer.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.coverage_analyzer.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await analyzer.analyze_coverage(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)
                assert "recommendations" in result


@pytest.mark.unit
class TestCoverageReporting:
    """Test coverage reporting functionality."""
    
    async def test_generate_coverage_report(self, sample_documents):
        """Test generating a coverage report."""
        analyzer = CoverageAnalyzer()
        
        with patch('src.services.maintenance.coverage_analyzer.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.coverage_analyzer.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await analyzer.analyze_coverage(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)
                assert "file_coverage" in result
                assert "service_coverage" in result


@pytest.mark.unit
class TestCoverageErrorHandling:
    """Test error handling in coverage analysis."""
    
    async def test_handle_empty_service(self):
        """Test handling service with no files."""
        analyzer = CoverageAnalyzer()
        
        with patch('src.services.maintenance.coverage_analyzer.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.coverage_analyzer.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = []
                
                result = await analyzer.analyze_coverage(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)
                assert result["metadata"]["total_documents"] == 0
    
    async def test_handle_analysis_error(self):
        """Test handling errors during analysis."""
        analyzer = CoverageAnalyzer()
        
        with patch('src.services.maintenance.coverage_analyzer.get_database') as mock_db:
            mock_context = AsyncMock()
            mock_context.__aenter__.side_effect = Exception("Database error")
            mock_db.return_value.session.return_value = mock_context
            
            with pytest.raises(Exception):
                await analyzer.analyze_coverage(service_name="test-service")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

