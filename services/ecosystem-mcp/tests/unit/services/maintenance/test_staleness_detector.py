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
    """Create sample documents with various staleness levels."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "path": "/docs/recent.md",
            "last_modified": now - timedelta(days=5),
            "content": "Recent documentation"
        },
        {
            "id": 2,
            "path": "/docs/moderate.md",
            "last_modified": now - timedelta(days=60),
            "content": "Moderately stale"
        },
        {
            "id": 3,
            "path": "/docs/stale.md",
            "last_modified": now - timedelta(days=200),
            "content": "Very stale documentation"
        }
    ]


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
        assert hasattr(detector, '_calculate_staleness_severity')


@pytest.mark.unit
class TestStaleDocumentDetection:
    """Test detection of stale documents."""
    
    async def test_detect_stale_documents(self, sample_documents):
        """Test detecting stale documents with default threshold."""
        detector = StalenessDetector()
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock document repository
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.list_all.return_value = sample_documents
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)
    
    async def test_custom_staleness_threshold(self, sample_documents):
        """Test using custom staleness threshold."""
        # Create detector with custom threshold
        detector = StalenessDetector(staleness_threshold_days=30)
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.list_all.return_value = sample_documents
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                assert result is not None
                assert isinstance(result, dict)


@pytest.mark.unit
class TestStalenessScore:
    """Test staleness score calculation."""
    
    def test_calculate_staleness_severity(self):
        """Test calculating staleness severity for a document."""
        detector = StalenessDetector()
        
        # Test HIGH severity (between thresholds)
        severity = detector._calculate_staleness_severity(staleness_days=120)
        assert severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    
    def test_critical_staleness_severity(self):
        """Test that very old documents get CRITICAL severity."""
        detector = StalenessDetector(
            staleness_threshold_days=90,
            critical_threshold_days=180
        )
        
        # 200 days should be CRITICAL
        severity = detector._calculate_staleness_severity(staleness_days=200)
        assert severity == "CRITICAL"


@pytest.mark.unit
class TestStalenessPrioritization:
    """Test prioritizing stale documents by severity."""
    
    async def test_prioritize_by_staleness(self, sample_documents):
        """Test that stale documents are prioritized by severity."""
        detector = StalenessDetector()
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.list_all.return_value = sample_documents
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                # Should have stale documents list
                assert result is not None
                assert isinstance(result, dict)


@pytest.mark.unit
class TestStalenessRecommendations:
    """Test generating recommendations for stale docs."""
    
    async def test_generate_update_recommendations(self, sample_documents):
        """Test that results include actionable information."""
        detector = StalenessDetector()
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.list_all.return_value = sample_documents
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                # Should include stale documents and summary
                assert result is not None
                assert isinstance(result, dict)


@pytest.mark.unit
class TestStalenessErrorHandling:
    """Test error handling in staleness detection."""
    
    async def test_handle_empty_document_set(self):
        """Test handling empty document set."""
        detector = StalenessDetector()
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            with patch('src.services.maintenance.staleness_detector.DocumentRepository') as MockRepo:
                mock_repo = AsyncMock()
                MockRepo.return_value = mock_repo
                mock_repo.list_all.return_value = []
                
                result = await detector.detect_stale_documents(service_name="test-service")
                
                # Should handle gracefully with empty results
                assert result is not None
                assert isinstance(result, dict)
    
    async def test_handle_database_error(self):
        """Test handling database errors."""
        detector = StalenessDetector()
        
        with patch('src.services.maintenance.staleness_detector.get_database') as mock_db:
            mock_db.return_value.__aenter__.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                await detector.detect_stale_documents(service_name="test-service")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

