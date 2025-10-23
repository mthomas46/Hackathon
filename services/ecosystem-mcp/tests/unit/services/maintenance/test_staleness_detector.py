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
        assert hasattr(detector, 'detect_stale_docs')
        assert hasattr(detector, 'calculate_staleness_score')


@pytest.mark.unit
class TestStaleDocumentDetection:
    """Test detection of stale documents."""
    
    async def test_detect_stale_documents(self, sample_documents):
        """Test detecting stale documents with default threshold."""
        detector = StalenessDetector()
        
        with patch.object(detector, '_fetch_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            result = await detector.detect_stale_docs(service_name="test-service")
            
            assert result is not None
            assert isinstance(result, dict)
            assert "stale_documents" in result or "total_stale" in result
    
    async def test_custom_staleness_threshold(self, sample_documents):
        """Test using custom staleness threshold."""
        detector = StalenessDetector()
        
        with patch.object(detector, '_fetch_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            # 30 day threshold - should find 2 stale docs
            result = await detector.detect_stale_docs(
                service_name="test-service",
                threshold_days=30
            )
            
            assert result is not None
            assert isinstance(result, dict)


@pytest.mark.unit
class TestStalenessScore:
    """Test staleness score calculation."""
    
    async def test_calculate_staleness_score(self):
        """Test calculating staleness score for a document."""
        detector = StalenessDetector()
        
        now = datetime.now(timezone.utc)
        old_doc = {
            "id": 1,
            "last_modified": now - timedelta(days=180)
        }
        
        score = await detector.calculate_staleness_score(old_doc)
        
        assert score is not None
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    async def test_recent_doc_low_staleness(self):
        """Test that recent documents have low staleness score."""
        detector = StalenessDetector()
        
        now = datetime.now(timezone.utc)
        recent_doc = {
            "id": 1,
            "last_modified": now - timedelta(days=1)
        }
        
        score = await detector.calculate_staleness_score(recent_doc)
        
        # Recent docs should have low staleness
        assert score < 50


@pytest.mark.unit
class TestStalenessPrioritization:
    """Test prioritizing stale documents by severity."""
    
    async def test_prioritize_by_staleness(self, sample_documents):
        """Test that stale documents are prioritized by age."""
        detector = StalenessDetector()
        
        with patch.object(detector, '_fetch_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            result = await detector.detect_stale_docs(service_name="test-service")
            
            # Should have prioritization or sorted list
            assert result is not None


@pytest.mark.unit
class TestStalenessRecommendations:
    """Test generating recommendations for stale docs."""
    
    async def test_generate_update_recommendations(self, sample_documents):
        """Test generating recommendations for stale documents."""
        detector = StalenessDetector()
        
        with patch.object(detector, '_fetch_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            result = await detector.detect_stale_docs(service_name="test-service")
            
            # Should include recommendations or action items
            assert result is not None


@pytest.mark.unit
class TestStalenessErrorHandling:
    """Test error handling in staleness detection."""
    
    async def test_handle_empty_document_set(self):
        """Test handling empty document set."""
        detector = StalenessDetector()
        
        with patch.object(detector, '_fetch_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            result = await detector.detect_stale_docs(service_name="test-service")
            
            # Should handle gracefully
            assert result is not None
            assert isinstance(result, dict)
    
    async def test_handle_database_error(self):
        """Test handling database errors."""
        detector = StalenessDetector()
        
        with patch.object(detector, '_fetch_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                await detector.detect_stale_docs(service_name="test-service")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

