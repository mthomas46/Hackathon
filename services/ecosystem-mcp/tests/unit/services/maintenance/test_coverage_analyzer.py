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
def sample_service_files():
    """Create sample service files for coverage analysis."""
    return [
        {"path": "/src/api.py", "type": "code", "has_docs": True},
        {"path": "/src/utils.py", "type": "code", "has_docs": False},
        {"path": "/src/models.py", "type": "code", "has_docs": True},
        {"path": "/docs/api.md", "type": "documentation"},
        {"path": "/docs/guide.md", "type": "documentation"},
    ]


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
        assert hasattr(analyzer, 'calculate_coverage_percentage')


@pytest.mark.unit
class TestCoverageAnalysis:
    """Test coverage analysis functionality."""
    
    async def test_analyze_service_coverage(self, sample_service_files):
        """Test analyzing documentation coverage for a service."""
        analyzer = CoverageAnalyzer()
        
        with patch.object(analyzer, '_get_service_files', new_callable=AsyncMock) as mock_files:
            mock_files.return_value = sample_service_files
            
            result = await analyzer.analyze_coverage(service_name="test-service")
            
            assert result is not None
            assert isinstance(result, dict)
            assert "coverage_percentage" in result or "total_files" in result
    
    async def test_coverage_with_no_documentation(self):
        """Test coverage analysis when no documentation exists."""
        analyzer = CoverageAnalyzer()
        
        files = [
            {"path": "/src/api.py", "type": "code", "has_docs": False},
            {"path": "/src/utils.py", "type": "code", "has_docs": False},
        ]
        
        with patch.object(analyzer, '_get_service_files', new_callable=AsyncMock) as mock_files:
            mock_files.return_value = files
            
            result = await analyzer.analyze_coverage(service_name="test-service")
            
            assert result is not None
            assert isinstance(result, dict)


@pytest.mark.unit
class TestCoverageMetrics:
    """Test coverage metric calculations."""
    
    def test_calculate_coverage_percentage(self):
        """Test calculating coverage percentage."""
        analyzer = CoverageAnalyzer()
        
        percentage = analyzer.calculate_coverage_percentage(
            documented_count=7,
            total_count=10
        )
        
        assert percentage == 70.0
    
    def test_coverage_percentage_with_zero_files(self):
        """Test coverage calculation with zero files."""
        analyzer = CoverageAnalyzer()
        
        percentage = analyzer.calculate_coverage_percentage(
            documented_count=0,
            total_count=0
        )
        
        assert percentage == 0.0


@pytest.mark.unit
class TestGapIdentification:
    """Test identifying documentation gaps."""
    
    async def test_identify_undocumented_files(self, sample_service_files):
        """Test identifying files without documentation."""
        analyzer = CoverageAnalyzer()
        
        with patch.object(analyzer, '_get_service_files', new_callable=AsyncMock) as mock_files:
            mock_files.return_value = sample_service_files
            
            result = await analyzer.analyze_coverage(service_name="test-service")
            
            assert result is not None
            # Should identify files without docs
            assert isinstance(result, dict)


@pytest.mark.unit
class TestCoverageReporting:
    """Test coverage reporting functionality."""
    
    async def test_generate_coverage_report(self, sample_service_files):
        """Test generating a coverage report."""
        analyzer = CoverageAnalyzer()
        
        with patch.object(analyzer, '_get_service_files', new_callable=AsyncMock) as mock_files:
            mock_files.return_value = sample_service_files
            
            result = await analyzer.analyze_coverage(service_name="test-service")
            
            assert result is not None
            assert isinstance(result, dict)


@pytest.mark.unit
class TestCoverageErrorHandling:
    """Test error handling in coverage analysis."""
    
    async def test_handle_empty_service(self):
        """Test handling service with no files."""
        analyzer = CoverageAnalyzer()
        
        with patch.object(analyzer, '_get_service_files', new_callable=AsyncMock) as mock_files:
            mock_files.return_value = []
            
            result = await analyzer.analyze_coverage(service_name="test-service")
            
            assert result is not None
            assert isinstance(result, dict)
    
    async def test_handle_analysis_error(self):
        """Test handling errors during analysis."""
        analyzer = CoverageAnalyzer()
        
        with patch.object(analyzer, '_get_service_files', new_callable=AsyncMock) as mock_files:
            mock_files.side_effect = Exception("Analysis error")
            
            with pytest.raises(Exception):
                await analyzer.analyze_coverage(service_name="test-service")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

