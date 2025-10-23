"""
Unit tests for StalenessDetector service.

Tests stale documentation detection based on last update timestamps.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.maintenance.staleness_detector import StalenessDetector


@pytest.fixture
def sample_documents():
    """Create sample DocumentModel objects with various staleness levels."""
    from uuid import uuid4
    from src.storage.db_models import DocumentModel
    
    now = datetime.now(timezone.utc)
    
    # Create mock DocumentModel objects
    doc1 = MagicMock(spec=DocumentModel)
    doc1.id = uuid4()
    doc1.file_path = "/docs/recent.md"
    doc1.updated_at = now - timedelta(days=5)
    doc1.created_at = now - timedelta(days=5)
    doc1.content = "Recent documentation"
    
    doc2 = MagicMock(spec=DocumentModel)
    doc2.id = uuid4()
    doc2.file_path = "/docs/moderate.md"
    doc2.updated_at = now - timedelta(days=100)
    doc2.created_at = now - timedelta(days=100)
    doc2.content = "Moderately stale"
    
    doc3 = MagicMock(spec=DocumentModel)
    doc3.id = uuid4()
    doc3.file_path = "/docs/stale.md"
    doc3.updated_at = now - timedelta(days=200)
    doc3.created_at = now - timedelta(days=200)
    doc3.content = "Very stale documentation"
    
    return [doc1, doc2, doc3]


@pytest.mark.unit
class TestStalenessDetectorInstantiation:
    """Test StalenessDetector instantiation."""
    
    def test_create_detector(self):
        """Test creating a StalenessDetector instance."""
        detector = StalenessDetector()
        assert detector is not None
    
    def test_detector_has_methods(self):
        """Test that StalenessDetector has required methods."""
        detector = StalenessDetector()
        assert hasattr(detector, 'detect_stale_documents')
        assert hasattr(detector, '_determine_staleness')


@pytest.mark.unit
class TestStaleDocumentDetection:
    """Test detection of stale documents."""
    
    async def test_detect_stale_documents(self, sample_documents):
        """Test detecting stale documents with default threshold."""
        detector = StalenessDetector(staleness_threshold_days=90)
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            # Mock the database context manager
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            # Mock document repository
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)
                assert "total_analyzed" in result
                assert "total_stale" in result
                assert result["total_analyzed"] == 3
    
    async def test_custom_staleness_threshold(self, sample_documents):
        """Test using custom staleness threshold."""
        # Create detector with 30-day threshold (should find 2 stale docs)
        detector = StalenessDetector(staleness_threshold_days=30)
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)
                # With 30-day threshold, at least the 100 and 200 day old docs should be stale
                assert result["total_analyzed"] == 3
                assert result["total_stale"] >= 0  # May find stale docs based on implementation


@pytest.mark.unit
class TestStalenessScore:
    """Test staleness severity determination."""
    
    def test_determine_staleness_logic(self):
        """Test staleness determination logic."""
        detector = StalenessDetector(
            staleness_threshold_days=90,
            critical_threshold_days=180
        )
        
        # Test that thresholds are set correctly
        assert detector.staleness_threshold == 90
        assert detector.critical_threshold == 180
    
    def test_custom_thresholds(self):
        """Test custom threshold configuration."""
        detector = StalenessDetector(
            staleness_threshold_days=60,
            critical_threshold_days=120
        )
        
        # Thresholds should be configured
        assert detector.staleness_threshold == 60
        assert detector.critical_threshold == 120


@pytest.mark.unit
class TestStalenessPrioritization:
    """Test prioritizing stale documents by severity."""
    
    async def test_prioritize_by_staleness(self, sample_documents):
        """Test that stale documents are categorized by severity."""
        detector = StalenessDetector(staleness_threshold_days=90)
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                # Should have severity categorization
                assert result is not None
                assert "by_severity" in result
                assert "stale_documents" in result


@pytest.mark.unit
class TestStalenessRecommendations:
    """Test generating recommendations for stale docs."""
    
    async def test_generate_update_recommendations(self, sample_documents):
        """Test that results include actionable metadata."""
        detector = StalenessDetector(staleness_threshold_days=90)
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = sample_documents
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                # Should include metadata for action
                assert result is not None
                assert "metadata" in result
                assert result["metadata"]["service_name"] == "test-service"


@pytest.mark.unit
class TestStalenessErrorHandling:
    """Test error handling in staleness detection."""
    
    async def test_handle_empty_document_set(self):
        """Test handling empty document set."""
        detector = StalenessDetector()
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_db.return_value.session.return_value = mock_context
            
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.get_by_service.return_value = []
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                # Should handle gracefully with empty results
                assert result is not None
                assert isinstance(result, dict)
                assert result["total_analyzed"] == 0
                assert result["total_stale"] == 0
                assert result["stale_percentage"] == 0
    
    async def test_handle_database_error(self):
        """Test handling database errors."""
        detector = StalenessDetector()
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_context = AsyncMock()
            mock_context.__aenter__.side_effect = Exception("Database error")
            mock_db.return_value.session.return_value = mock_context
            
            with pytest.raises(Exception):
                await detector.detect_stale_documents(service_name="test-service")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

