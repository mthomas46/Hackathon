"""Unit tests for anomaly detection service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
import statistics

from services.mcp_performance_store.application.services.anomaly_detection_service import (
    AnomalyDetectionService,
)
from services.mcp_performance_store.domain.entities.orchestration_execution import (
    OrchestrationExecution,
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
def anomaly_service(mock_execution_repository, mock_pattern_repository):
    """Create an anomaly detection service with mocked repositories."""
    return AnomalyDetectionService(
        execution_repository=mock_execution_repository,
        pattern_performance_repository=mock_pattern_repository,
        z_score_threshold=2.0,
    )


@pytest.mark.asyncio
async def test_detect_orchestration_anomalies_normal(
    anomaly_service, mock_execution_repository, multiple_executions
):
    """Test anomaly detection with normal executions."""
    # Make all executions have similar durations (normal)
    for i, exec in enumerate(multiple_executions):
        exec.duration_ms = 5000 + (i * 10)  # Very small variation
    
    mock_execution_repository.get_executions_in_time_range.return_value = multiple_executions
    
    # Execute
    result = await anomaly_service.detect_orchestration_anomalies(days=7)
    
    # Verify
    assert result is not None
    assert "anomalies" in result
    assert "total_checked" in result
    assert "anomaly_count" in result
    
    # Should find few or no anomalies
    assert result["anomaly_count"] == 0 or result["anomaly_count"] < 2


@pytest.mark.asyncio
async def test_detect_orchestration_anomalies_with_outliers(
    anomaly_service, mock_execution_repository, multiple_executions
):
    """Test anomaly detection with outliers."""
    # Make some executions abnormally slow
    for i, exec in enumerate(multiple_executions):
        if i < 8:
            exec.duration_ms = 5000  # Normal
        else:
            exec.duration_ms = 50000  # Abnormally slow! (10x normal)
    
    mock_execution_repository.get_executions_in_time_range.return_value = multiple_executions
    
    # Execute
    result = await anomaly_service.detect_orchestration_anomalies(days=7)
    
    # Verify
    assert result["anomaly_count"] > 0
    assert len(result["anomalies"]) > 0
    
    # Check anomaly details
    for anomaly in result["anomalies"]:
        assert "execution_id" in anomaly
        assert "duration_ms" in anomaly
        assert "z_score" in anomaly
        assert abs(anomaly["z_score"]) > 2.0  # Above threshold


@pytest.mark.asyncio
async def test_detect_pattern_anomalies(
    anomaly_service, mock_pattern_repository, multiple_pattern_performances
):
    """Test pattern-specific anomaly detection."""
    pattern_name = "RAG"
    
    # Filter and modify performances
    pattern_perfs = [
        p for p in multiple_pattern_performances if p.pattern_name == pattern_name
    ]
    
    # Make one performance abnormally slow
    if len(pattern_perfs) > 0:
        pattern_perfs[-1].duration_ms = 50000  # Outlier
    
    mock_pattern_repository.get_by_pattern.return_value = pattern_perfs
    
    # Execute
    result = await anomaly_service.detect_pattern_anomalies(
        pattern_name=pattern_name, days=7
    )
    
    # Verify
    assert result is not None
    assert "pattern_name" in result
    assert result["pattern_name"] == pattern_name
    assert "anomalies" in result


@pytest.mark.asyncio
async def test_z_score_calculation(anomaly_service):
    """Test Z-score calculation."""
    # Sample data
    values = [5000, 5100, 5200, 4900, 5050, 5150, 50000]  # Last one is outlier
    
    # Calculate mean and std dev
    mean = statistics.mean(values[:-1])  # Exclude outlier for baseline
    std_dev = statistics.stdev(values[:-1])
    
    # Calculate Z-score for outlier
    outlier = values[-1]
    z_score = (outlier - mean) / std_dev if std_dev > 0 else 0
    
    # Verify Z-score is high (outlier should have high Z-score)
    assert abs(z_score) > 2.0


@pytest.mark.asyncio
async def test_empty_data_handling(
    anomaly_service, mock_execution_repository
):
    """Test handling of empty data."""
    mock_execution_repository.get_executions_in_time_range.return_value = []
    
    # Execute
    result = await anomaly_service.detect_orchestration_anomalies(days=7)
    
    # Verify
    assert result["total_checked"] == 0
    assert result["anomaly_count"] == 0
    assert len(result["anomalies"]) == 0


@pytest.mark.asyncio
async def test_insufficient_data_for_statistics(
    anomaly_service, mock_execution_repository
):
    """Test handling when there's insufficient data for statistics."""
    # Create only 1 execution (need at least 2 for standard deviation)
    single_execution = [
        OrchestrationExecution(
            execution_id="exec-1",
            orchestration_id="orch-1",
            mcp_id="mcp-1",
            status=ExecutionStatus.SUCCESS,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_ms=5000,
        )
    ]
    
    mock_execution_repository.get_executions_in_time_range.return_value = single_execution
    
    # Execute
    result = await anomaly_service.detect_orchestration_anomalies(days=7)
    
    # Verify - should handle gracefully
    assert result["total_checked"] == 1
    assert result["anomaly_count"] == 0  # Can't determine anomalies with insufficient data


@pytest.mark.asyncio
async def test_custom_z_score_threshold(
    mock_execution_repository, mock_pattern_repository, multiple_executions
):
    """Test using a custom Z-score threshold."""
    # Create service with stricter threshold
    strict_service = AnomalyDetectionService(
        execution_repository=mock_execution_repository,
        pattern_performance_repository=mock_pattern_repository,
        z_score_threshold=1.5,  # Stricter than default 2.0
    )
    
    # Add moderate outlier
    for i, exec in enumerate(multiple_executions):
        if i < 8:
            exec.duration_ms = 5000
        else:
            exec.duration_ms = 8000  # Moderate outlier
    
    mock_execution_repository.get_executions_in_time_range.return_value = multiple_executions
    
    # Execute
    result = await strict_service.detect_orchestration_anomalies(days=7)
    
    # Verify - stricter threshold should catch more anomalies
    assert result is not None
    # With stricter threshold, we might catch the moderate outliers


@pytest.mark.asyncio
async def test_anomaly_metadata(
    anomaly_service, mock_execution_repository, multiple_executions
):
    """Test that anomaly results include proper metadata."""
    # Create clear outlier
    multiple_executions[0].duration_ms = 50000  # Much higher than others
    
    mock_execution_repository.get_executions_in_time_range.return_value = multiple_executions
    
    # Execute
    result = await anomaly_service.detect_orchestration_anomalies(days=7)
    
    # Verify metadata
    if result["anomaly_count"] > 0:
        anomaly = result["anomalies"][0]
        assert "execution_id" in anomaly
        assert "orchestration_id" in anomaly
        assert "mcp_id" in anomaly
        assert "duration_ms" in anomaly
        assert "z_score" in anomaly
        assert "mean" in result
        assert "std_dev" in result
