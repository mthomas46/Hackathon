"""
Unit tests for metrics calculator.

Tests metric calculation functions.
"""

import pytest
from datetime import datetime, timezone

from data.models import LogEntry
from metrics.calculator import (
    calculate_metrics,
    aggregate_by_service,
    calculate_error_rate,
    calculate_avg_duration,
    calculate_operations_per_service,
    calculate_operations_per_type,
    calculate_status_code_distribution,
    calculate_percentile,
    calculate_duration_percentiles,
    calculate_min_max_duration
)


# ============================================================================
# Basic Calculation Tests
# ============================================================================

@pytest.mark.unit
class TestBasicCalculations:
    """Tests for basic metric calculations."""
    
    def test_calculate_metrics_with_valid_logs(self, sample_log_entries):
        """Test calculate_metrics with valid log entries."""
        metrics = calculate_metrics(sample_log_entries)
        
        assert metrics.total_operations == 2
        assert metrics.successful_operations == 1
        assert metrics.failed_operations == 1
        assert metrics.error_rate == 50.0
        assert metrics.avg_duration_ms > 0
    
    def test_calculate_metrics_with_empty_list(self):
        """Test calculate_metrics with empty list."""
        metrics = calculate_metrics([])
        
        assert metrics.total_operations == 0
        assert metrics.successful_operations == 0
        assert metrics.failed_operations == 0
        assert metrics.error_rate == 0.0
        assert metrics.avg_duration_ms == 0.0
    
    def test_calculate_error_rate(self, sample_log_entries):
        """Test error rate calculation."""
        error_rate = calculate_error_rate(sample_log_entries)
        
        assert error_rate == 50.0  # 1 failed out of 2
    
    def test_calculate_error_rate_all_successful(self, sample_log_entry):
        """Test error rate with all successful operations."""
        logs = [sample_log_entry, sample_log_entry]
        error_rate = calculate_error_rate(logs)
        
        assert error_rate == 0.0
    
    def test_calculate_error_rate_all_failed(self, failed_log_entry):
        """Test error rate with all failed operations."""
        logs = [failed_log_entry, failed_log_entry]
        error_rate = calculate_error_rate(logs)
        
        assert error_rate == 100.0
    
    def test_calculate_avg_duration(self, sample_log_entries):
        """Test average duration calculation."""
        avg = calculate_avg_duration(sample_log_entries)
        
        # (15.5 + 125.5) / 2 = 70.5
        assert avg == 70.5
    
    def test_calculate_avg_duration_with_none_values(self, sample_timestamp):
        """Test average duration with None values (should be ignored)."""
        logs = [
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=10.0),
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=None),
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=20.0)
        ]
        
        avg = calculate_avg_duration(logs)
        assert avg == 15.0  # (10 + 20) / 2


# ============================================================================
# Aggregation Tests
# ============================================================================

@pytest.mark.unit
class TestAggregations:
    """Tests for aggregation functions."""
    
    def test_calculate_operations_per_service(self, sample_log_entries):
        """Test operations per service calculation."""
        ops = calculate_operations_per_service(sample_log_entries)
        
        assert ops["doc_store"] == 1
        assert ops["prompt_store"] == 1
    
    def test_calculate_operations_per_type(self, sample_log_entries):
        """Test operations per type calculation."""
        ops = calculate_operations_per_type(sample_log_entries)
        
        assert ops["CREATE"] == 2
    
    def test_calculate_status_code_distribution(self, sample_log_entries):
        """Test status code distribution."""
        distribution = calculate_status_code_distribution(sample_log_entries)
        
        assert distribution[201] == 1
        assert distribution[500] == 1
    
    def test_aggregate_by_service(self, sample_log_entries):
        """Test aggregating metrics by service."""
        metrics_by_service = aggregate_by_service(sample_log_entries)
        
        assert "doc_store" in metrics_by_service
        assert "prompt_store" in metrics_by_service
        
        doc_metrics = metrics_by_service["doc_store"]
        assert doc_metrics.total_operations == 1
        assert doc_metrics.error_rate == 0.0
        
        prompt_metrics = metrics_by_service["prompt_store"]
        assert prompt_metrics.total_operations == 1
        assert prompt_metrics.error_rate == 100.0


# ============================================================================
# Percentile Tests
# ============================================================================

@pytest.mark.unit
class TestPercentileCalculations:
    """Tests for percentile calculations."""
    
    def test_calculate_percentile_median(self):
        """Test 50th percentile (median)."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        p50 = calculate_percentile(values, 50)
        
        assert p50 == 3.0
    
    def test_calculate_percentile_p95(self):
        """Test 95th percentile."""
        values = list(range(1, 101))  # 1 to 100
        p95 = calculate_percentile(values, 95)
        
        assert p95 == 95.0
    
    def test_calculate_percentile_empty_list(self):
        """Test percentile with empty list."""
        p50 = calculate_percentile([], 50)
        assert p50 == 0.0
    
    def test_calculate_duration_percentiles(self, sample_timestamp):
        """Test duration percentiles calculation."""
        logs = [
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=float(i))
            for i in range(1, 101)
        ]
        
        percentiles = calculate_duration_percentiles(logs)
        
        assert percentiles["p50"] == 50.0
        assert percentiles["p95"] == 95.0
        assert percentiles["p99"] == 99.0
    
    def test_calculate_duration_percentiles_empty(self):
        """Test duration percentiles with no duration data."""
        percentiles = calculate_duration_percentiles([])
        
        assert percentiles["p50"] == 0.0
        assert percentiles["p95"] == 0.0
        assert percentiles["p99"] == 0.0


# ============================================================================
# Min/Max Tests
# ============================================================================

@pytest.mark.unit
class TestMinMaxCalculations:
    """Tests for min/max calculations."""
    
    def test_calculate_min_max_duration(self, sample_timestamp):
        """Test min/max duration calculation."""
        logs = [
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=10.0),
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=50.0),
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=30.0)
        ]
        
        min_max = calculate_min_max_duration(logs)
        
        assert min_max["min"] == 10.0
        assert min_max["max"] == 50.0
    
    def test_calculate_min_max_duration_empty(self):
        """Test min/max with no duration data."""
        min_max = calculate_min_max_duration([])
        
        assert min_max["min"] == 0.0
        assert min_max["max"] == 0.0
    
    def test_calculate_min_max_duration_with_none(self, sample_timestamp):
        """Test min/max with None values (should be ignored)."""
        logs = [
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=10.0),
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=None),
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=20.0)
        ]
        
        min_max = calculate_min_max_duration(logs)
        
        assert min_max["min"] == 10.0
        assert min_max["max"] == 20.0


# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_all_operations_have_no_duration(self, sample_timestamp):
        """Test metrics when no operations have duration data."""
        logs = [
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=None),
            LogEntry(timestamp=sample_timestamp, service="test", duration_ms=None)
        ]
        
        metrics = calculate_metrics(logs)
        
        assert metrics.avg_duration_ms == 0.0
    
    def test_single_operation(self, sample_log_entry):
        """Test metrics with single operation."""
        metrics = calculate_metrics([sample_log_entry])
        
        assert metrics.total_operations == 1
        assert metrics.successful_operations == 1
        assert metrics.error_rate == 0.0
    
    def test_many_services(self, sample_timestamp):
        """Test aggregation with many services."""
        logs = []
        for i in range(10):
            log = LogEntry(
                timestamp=sample_timestamp,
                service=f"service_{i}",
                duration_ms=10.0
            )
            logs.append(log)
        
        ops_per_service = calculate_operations_per_service(logs)
        
        assert len(ops_per_service) == 10
        for i in range(10):
            assert ops_per_service[f"service_{i}"] == 1

