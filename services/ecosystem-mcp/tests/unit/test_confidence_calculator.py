"""
Unit tests for TemporalConfidenceCalculator.

Tests confidence calculation logic, pre-flight checks, and upgrade suggestions.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from src.services.timeline.confidence_calculator import TemporalConfidenceCalculator
from src.models.timeline import TemporalConfidence


class TestConfidenceCalculation:
    """Test confidence level calculation."""
    
    @pytest.mark.asyncio
    async def test_high_confidence_calculation(self):
        """Test HIGH confidence (90%+ git_history)."""
        # Mock database session
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 95
        mock_row.snapshot = 5
        mock_result.first.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        metadata = await calculator.calculate_confidence(service_name="test-service")
        
        assert metadata.total_documents == 100
        assert metadata.git_history_documents == 95
        assert metadata.snapshot_documents == 5
        assert metadata.git_percentage == 95.0
        assert metadata.can_show_evolution is True
        assert metadata.can_detect_drift is True
        assert metadata.can_show_timeline is True
        assert metadata.can_compare_periods is True
        assert metadata.fallback_strategy == "minimal_fallback"
        assert len(metadata.warnings) == 0
    
    @pytest.mark.asyncio
    async def test_medium_confidence_calculation(self):
        """Test MEDIUM confidence (50-90% git_history)."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 70
        mock_row.snapshot = 30
        mock_result.first.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        metadata = await calculator.calculate_confidence(service_name="test-service")
        
        assert metadata.git_percentage == 70.0
        assert metadata.can_show_evolution is True  # Partial
        assert metadata.can_detect_drift is True    # Partial
        assert metadata.fallback_strategy == "hybrid_with_warnings"
        assert len(metadata.warnings) > 0
        assert "70.0%" in metadata.warnings[0]
    
    @pytest.mark.asyncio
    async def test_low_confidence_calculation(self):
        """Test LOW confidence (1-50% git_history)."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 25
        mock_row.snapshot = 75
        mock_result.first.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        metadata = await calculator.calculate_confidence(service_name="test-service")
        
        assert metadata.git_percentage == 25.0
        assert metadata.can_show_evolution is False
        assert metadata.can_detect_drift is False
        assert metadata.can_show_timeline is True  # Content-based only
        assert metadata.fallback_strategy == "content_based_fallback"
        assert len(metadata.warnings) > 0
        assert "severely limited" in metadata.warnings[1].lower()
    
    @pytest.mark.asyncio
    async def test_none_confidence_calculation(self):
        """Test NONE confidence (0% git_history)."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 0
        mock_row.snapshot = 100
        mock_result.first.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        metadata = await calculator.calculate_confidence(service_name="test-service")
        
        assert metadata.git_percentage == 0.0
        assert metadata.can_show_evolution is False
        assert metadata.can_detect_drift is False
        assert metadata.can_show_timeline is False
        assert metadata.can_compare_periods is False
        assert metadata.fallback_strategy == "no_temporal_features"
        assert len(metadata.warnings) > 0
        assert "not possible" in metadata.warnings[1].lower()
    
    @pytest.mark.asyncio
    async def test_empty_document_set(self):
        """Test with no documents."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 0
        mock_row.git_history = 0
        mock_row.snapshot = 0
        mock_result.first.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        metadata = await calculator.calculate_confidence(service_name="test-service")
        
        assert metadata.total_documents == 0
        assert metadata.git_percentage == 0.0
        assert metadata.can_show_evolution is False
    
    @pytest.mark.asyncio
    async def test_confidence_at_boundaries(self):
        """Test confidence calculation at exact boundaries."""
        calculator = TemporalConfidenceCalculator(Mock())
        
        # Test at 90% boundary (HIGH)
        result = calculator._determine_confidence(100, 90, 10)
        assert result.git_percentage == 90.0
        assert result.fallback_strategy == "minimal_fallback"
        
        # Test at 89.9% (MEDIUM)
        result = calculator._determine_confidence(100, 89, 11)
        assert result.git_percentage == 89.0
        assert result.fallback_strategy == "hybrid_with_warnings"
        
        # Test at 50% boundary (MEDIUM)
        result = calculator._determine_confidence(100, 50, 50)
        assert result.git_percentage == 50.0
        assert result.fallback_strategy == "hybrid_with_warnings"
        
        # Test at 49.9% (LOW)
        result = calculator._determine_confidence(100, 49, 51)
        assert result.git_percentage == 49.0
        assert result.fallback_strategy == "content_based_fallback"


class TestPreFlightCheck:
    """Test pre-flight validation."""
    
    @pytest.mark.asyncio
    async def test_preflight_passes_high_confidence(self):
        """Test pre-flight passes with HIGH confidence."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 95
        mock_row.snapshot = 5
        mock_result.first.return_value = mock_row  # HIGH
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        result = await calculator.check_pre_flight(
            service_name="test-service",
            minimum_confidence=TemporalConfidence.MEDIUM
        )
        
        assert result["can_proceed"] is True
        assert result["actual_confidence"] == "HIGH"
        assert result["required_confidence"] == "MEDIUM"
        assert "✅" in result["recommendation"]
    
    @pytest.mark.asyncio
    async def test_preflight_fails_low_confidence(self):
        """Test pre-flight fails with insufficient confidence."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 25
        mock_row.snapshot = 75
        mock_result.first.return_value = mock_row  # LOW
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        result = await calculator.check_pre_flight(
            service_name="test-service",
            minimum_confidence=TemporalConfidence.MEDIUM
        )
        
        assert result["can_proceed"] is False
        assert result["actual_confidence"] == "LOW"
        assert result["required_confidence"] == "MEDIUM"
        assert "⚠️" in result["recommendation"]
        assert "re-ingesting" in result["recommendation"].lower()
    
    @pytest.mark.asyncio
    async def test_preflight_with_none_confidence(self):
        """Test pre-flight with NONE confidence."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 0
        mock_row.snapshot = 100
        mock_result.first.return_value = mock_row  # NONE
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        result = await calculator.check_pre_flight(
            service_name="test-service",
            minimum_confidence=TemporalConfidence.LOW
        )
        
        # With auto_adjust=True (default), NONE confidence now allows timeline creation with warnings
        assert result["can_proceed"] is True
        assert result["actual_confidence"] == "NONE"
        assert "recommendation" in result
        assert "snapshot-only" in result["recommendation"].lower() or "limited" in result["recommendation"].lower()


class TestUpgradePath:
    """Test upgrade path suggestions."""
    
    @pytest.mark.asyncio
    async def test_upgrade_path_from_none(self):
        """Test upgrade suggestions from NONE confidence."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 0
        mock_row.snapshot = 100
        mock_result.first.return_value = mock_row  # NONE
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        suggestions = await calculator.suggest_upgrade_path("test-service")
        
        assert suggestions["current_confidence"] == 0.0
        assert suggestions["estimated_documents_to_reingest"] == 100
        assert len(suggestions["suggestions"]) > 0
        
        first_suggestion = suggestions["suggestions"][0]
        assert first_suggestion["action"] == "re_ingest_with_git_history"
        assert first_suggestion["expected_confidence"] == "HIGH"
        assert len(first_suggestion["benefits"]) > 0
    
    @pytest.mark.asyncio
    async def test_upgrade_path_from_low(self):
        """Test upgrade suggestions from LOW confidence."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 40
        mock_row.snapshot = 60
        mock_result.first.return_value = mock_row  # LOW
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        suggestions = await calculator.suggest_upgrade_path("test-service")
        
        assert suggestions["current_confidence"] == 40.0
        assert suggestions["estimated_documents_to_reingest"] == 60
        
        first_suggestion = suggestions["suggestions"][0]
        assert first_suggestion["action"] == "re_ingest_snapshot_documents"
        assert "60 snapshot documents" in first_suggestion["description"]
    
    @pytest.mark.asyncio
    async def test_upgrade_path_from_medium(self):
        """Test upgrade suggestions from MEDIUM confidence."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 80
        mock_row.snapshot = 20
        mock_result.first.return_value = mock_row  # MEDIUM
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        suggestions = await calculator.suggest_upgrade_path("test-service")
        
        assert suggestions["current_confidence"] == 80.0
        assert suggestions["estimated_documents_to_reingest"] == 20
        
        first_suggestion = suggestions["suggestions"][0]
        assert first_suggestion["action"] == "complete_git_history"
        assert "remaining 20 documents" in first_suggestion["description"]
    
    @pytest.mark.asyncio
    async def test_upgrade_path_already_high(self):
        """Test upgrade path when already HIGH confidence."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 100
        mock_row.git_history = 95
        mock_row.snapshot = 5
        mock_result.first.return_value = mock_row  # HIGH
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        suggestions = await calculator.suggest_upgrade_path("test-service")
        
        assert suggestions["current_confidence"] == 95.0
        
        first_suggestion = suggestions["suggestions"][0]
        assert first_suggestion["action"] == "no_action_needed"
        assert "already has HIGH confidence" in first_suggestion["description"]


class TestConfidenceWithFilters:
    """Test confidence calculation with various filters."""
    
    @pytest.mark.asyncio
    async def test_confidence_with_document_ids(self):
        """Test confidence calculation for specific documents."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 10
        mock_row.git_history = 9
        mock_row.snapshot = 1
        mock_result.first.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        doc_ids = [uuid4() for _ in range(10)]
        
        metadata = await calculator.calculate_confidence(document_ids=doc_ids)
        
        assert metadata.total_documents == 10
        assert metadata.git_percentage == 90.0
    
    @pytest.mark.asyncio
    async def test_confidence_with_repo_path(self):
        """Test confidence calculation for specific repo path."""
        mock_session = Mock()
        mock_result = Mock()
        mock_row = Mock()
        mock_row.total = 50
        mock_row.git_history = 40
        mock_row.snapshot = 10
        mock_result.first.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        metadata = await calculator.calculate_confidence(repo_path="/path/to/repo")
        
        assert metadata.total_documents == 50
        assert metadata.git_percentage == 80.0


class TestErrorHandling:
    """Test error handling in confidence calculator."""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test handling of database errors."""
        mock_session = Mock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
        
        calculator = TemporalConfidenceCalculator(mock_session)
        
        with pytest.raises(Exception, match="Database error"):
            await calculator.calculate_confidence(service_name="test-service")
    
    @pytest.mark.asyncio
    async def test_none_result_handling(self):
        """Test handling of None result from database."""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        calculator = TemporalConfidenceCalculator(mock_session)
        metadata = await calculator.calculate_confidence(service_name="test-service")
        
        # Should return NONE confidence
        assert metadata.total_documents == 0
        assert metadata.git_percentage == 0.0

