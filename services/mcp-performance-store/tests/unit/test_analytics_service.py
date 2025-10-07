"""Unit tests for analytics service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from services.mcp_performance_store.application.services.analytics_service import (
    AnalyticsService,
)
from services.mcp_performance_store.domain.value_objects.execution_status import (
    ExecutionStatus,
)


@pytest.fixture
def mock_execution_repository():
    """Create a mock execution repository."""
    return AsyncMock()


@pytest.fixture
def mock_pattern_repository():
    """Create a mock pattern performance repository."""
    return AsyncMock()


@pytest.fixture
def analytics_service(mock_execution_repository, mock_pattern_repository):
    """Create an analytics service with mocked repositories."""
    return AnalyticsService(
        execution_repository=mock_execution_repository,
        pattern_performance_repository=mock_pattern_repository,
    )


@pytest.mark.asyncio
async def test_calculate_orchestration_trends(
    analytics_service, mock_execution_repository, multiple_executions
):
    """Test orchestration trend calculation."""
    # Setup mock
    mock_execution_repository.get_executions_in_time_range.return_value = multiple_executions
    
    # Execute
    trends = await analytics_service.calculate_orchestration_trends(days=7)
    
    # Verify
    assert trends is not None
    assert "average_duration_ms" in trends
    assert "success_rate" in trends
    assert "total_executions" in trends
    assert "trend" in trends
    
    # Verify repository was called
    mock_execution_repository.get_executions_in_time_range.assert_called_once()


@pytest.mark.asyncio
async def test_calculate_pattern_trends(
    analytics_service, mock_pattern_repository, multiple_pattern_performances
):
    """Test pattern trend calculation."""
    pattern_name = "RAG"
    
    # Filter performances for the pattern
    pattern_perfs = [
        p for p in multiple_pattern_performances if p.pattern_name == pattern_name
    ]
    
    # Setup mock
    mock_pattern_repository.get_by_pattern.return_value = pattern_perfs
    
    # Execute
    trends = await analytics_service.calculate_pattern_trends(pattern_name)
    
    # Verify
    assert trends is not None
    assert trends["pattern_name"] == pattern_name
    assert "average_duration_ms" in trends
    assert "success_rate" in trends
    assert "total_executions" in trends
    
    # Verify repository was called
    mock_pattern_repository.get_by_pattern.assert_called_once_with(
        pattern_name=pattern_name
    )


@pytest.mark.asyncio
async def test_compare_patterns(
    analytics_service, mock_pattern_repository, multiple_pattern_performances
):
    """Test pattern comparison."""
    # Setup mock
    mock_pattern_repository.get_all.return_value = multiple_pattern_performances
    
    # Execute
    comparison = await analytics_service.compare_patterns()
    
    # Verify
    assert comparison is not None
    assert isinstance(comparison, list)
    assert len(comparison) > 0
    
    # Each comparison should have pattern stats
    for pattern_stats in comparison:
        assert "pattern_name" in pattern_stats
        assert "average_duration_ms" in pattern_stats
        assert "success_rate" in pattern_stats
        assert "total_executions" in pattern_stats


@pytest.mark.asyncio
async def test_detect_degradation(
    analytics_service, mock_execution_repository, multiple_executions
):
    """Test performance degradation detection."""
    # Setup mock - simulate degradation by making recent executions slower
    recent_executions = []
    for i, exec in enumerate(multiple_executions):
        if i < 5:
            exec.duration_ms = 5000  # Old: faster
        else:
            exec.duration_ms = 15000  # New: slower (degradation!)
        recent_executions.append(exec)
    
    mock_execution_repository.get_recent.return_value = recent_executions
    
    # Execute
    degradation = await analytics_service.detect_degradation(threshold_percent=20.0)
    
    # Verify
    assert degradation is not None
    assert "is_degraded" in degradation
    assert "old_avg_duration_ms" in degradation
    assert "new_avg_duration_ms" in degradation
    assert "percent_change" in degradation
    
    # Should detect degradation (200% increase)
    assert degradation["is_degraded"] is True
    assert degradation["percent_change"] > 20.0


@pytest.mark.asyncio
async def test_no_degradation_detected(
    analytics_service, mock_execution_repository, multiple_executions
):
    """Test when no degradation is present."""
    # Setup mock - all executions have similar duration
    for exec in multiple_executions:
        exec.duration_ms = 5000  # Consistent performance
    
    mock_execution_repository.get_recent.return_value = multiple_executions
    
    # Execute
    degradation = await analytics_service.detect_degradation(threshold_percent=20.0)
    
    # Verify
    assert degradation["is_degraded"] is False
    assert abs(degradation["percent_change"]) < 20.0


@pytest.mark.asyncio
async def test_calculate_success_rate(analytics_service, multiple_executions):
    """Test success rate calculation."""
    # Count successes
    success_count = sum(
        1 for e in multiple_executions if e.status == ExecutionStatus.SUCCESS
    )
    expected_rate = (success_count / len(multiple_executions)) * 100
    
    # Calculate
    rate = analytics_service._calculate_success_rate(multiple_executions)
    
    # Verify
    assert rate == pytest.approx(expected_rate, rel=0.01)


@pytest.mark.asyncio
async def test_calculate_average_duration(analytics_service, multiple_executions):
    """Test average duration calculation."""
    # Calculate expected average
    total_duration = sum(e.duration_ms for e in multiple_executions)
    expected_avg = total_duration / len(multiple_executions)
    
    # Calculate
    avg = analytics_service._calculate_average_duration(multiple_executions)
    
    # Verify
    assert avg == pytest.approx(expected_avg, rel=0.01)


@pytest.mark.asyncio
async def test_empty_executions_handling(analytics_service):
    """Test handling of empty execution lists."""
    # Success rate should be 0 for empty list
    assert analytics_service._calculate_success_rate([]) == 0.0
    
    # Average duration should be 0 for empty list
    assert analytics_service._calculate_average_duration([]) == 0.0
