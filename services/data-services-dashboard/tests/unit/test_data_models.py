"""
Unit tests for data models.

Tests Pydantic models: LogEntry, MetricsSummary, DashboardFilter.
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from data.models import LogEntry, MetricsSummary, DashboardFilter


# ============================================================================
# LogEntry Tests
# ============================================================================

@pytest.mark.unit
class TestLogEntry:
    """Tests for LogEntry model."""
    
    def test_create_valid_log_entry(self, sample_timestamp):
        """Test creating a valid log entry."""
        log = LogEntry(
            timestamp=sample_timestamp,
            service="doc_store",
            level="INFO",
            message="Test message",
            operation_type="CREATE",
            method="POST",
            path="/api/v1/test",
            status_code=201,
            duration_ms=15.5,
            success=True,
            phase="complete",
            workflow_id="wf_123"
        )
        
        assert log.service == "doc_store"
        assert log.level == "INFO"
        assert log.operation_type == "CREATE"
        assert log.status_code == 201
        assert log.duration_ms == 15.5
        assert log.success is True
    
    def test_log_entry_with_defaults(self, sample_timestamp):
        """Test log entry with default values."""
        log = LogEntry(
            timestamp=sample_timestamp,
            service="test_service"
        )
        
        assert log.level == "INFO"
        assert log.message == ""
        assert log.operation_type == "unknown"
        assert log.method == ""
        assert log.status_code is None
        assert log.duration_ms is None
    
    def test_log_entry_duration_validation(self, sample_timestamp):
        """Test duration validation (must be < 5 minutes)."""
        # Valid duration
        log = LogEntry(
            timestamp=sample_timestamp,
            service="test",
            duration_ms=1000.0
        )
        assert log.duration_ms == 1000.0
        
        # Invalid duration (> 5 minutes = 300,000ms)
        with pytest.raises(ValidationError) as exc_info:
            LogEntry(
                timestamp=sample_timestamp,
                service="test",
                duration_ms=400000.0
            )
        assert "Duration too large" in str(exc_info.value)
    
    def test_log_entry_status_code_validation(self, sample_timestamp):
        """Test status code validation (100-599)."""
        # Valid status codes
        for code in [200, 201, 404, 500]:
            log = LogEntry(timestamp=sample_timestamp, service="test", status_code=code)
            assert log.status_code == code
        
        # Invalid status codes
        with pytest.raises(ValidationError):
            LogEntry(timestamp=sample_timestamp, service="test", status_code=99)
        
        with pytest.raises(ValidationError):
            LogEntry(timestamp=sample_timestamp, service="test", status_code=600)
    
    def test_log_entry_service_validation(self, sample_timestamp):
        """Test service name validation."""
        # Valid service
        log = LogEntry(timestamp=sample_timestamp, service="valid_service")
        assert log.service == "valid_service"
        
        # Empty service (invalid)
        with pytest.raises(ValidationError):
            LogEntry(timestamp=sample_timestamp, service="")
        
        # Too long service (> 100 chars)
        with pytest.raises(ValidationError):
            LogEntry(timestamp=sample_timestamp, service="x" * 101)


# ============================================================================
# MetricsSummary Tests
# ============================================================================

@pytest.mark.unit
class TestMetricsSummary:
    """Tests for MetricsSummary model."""
    
    def test_create_valid_metrics(self):
        """Test creating valid metrics."""
        metrics = MetricsSummary(
            total_operations=100,
            successful_operations=95,
            failed_operations=5,
            avg_duration_ms=12.5,
            error_rate=5.0,
            operations_per_service={"doc_store": 50, "prompt_store": 50}
        )
        
        assert metrics.total_operations == 100
        assert metrics.successful_operations == 95
        assert metrics.failed_operations == 5
        assert metrics.avg_duration_ms == 12.5
        assert metrics.error_rate == 5.0
    
    def test_metrics_with_defaults(self):
        """Test metrics with default values."""
        metrics = MetricsSummary()
        
        assert metrics.total_operations == 0
        assert metrics.successful_operations == 0
        assert metrics.failed_operations == 0
        assert metrics.avg_duration_ms == 0.0
        assert metrics.error_rate == 0.0
        assert metrics.operations_per_service == {}
    
    def test_error_rate_validation(self):
        """Test error rate validation (0-100)."""
        # Valid error rates
        for rate in [0.0, 50.0, 100.0]:
            metrics = MetricsSummary(error_rate=rate)
            assert 0.0 <= metrics.error_rate <= 100.0
        
        # Invalid error rates (should be clamped)
        metrics = MetricsSummary(error_rate=-5.0)
        assert metrics.error_rate == 0.0
        
        metrics = MetricsSummary(error_rate=150.0)
        assert metrics.error_rate == 100.0
    
    def test_negative_operations_validation(self):
        """Test that operation counts must be non-negative."""
        # Valid counts
        metrics = MetricsSummary(total_operations=10)
        assert metrics.total_operations == 10
        
        # Invalid counts
        with pytest.raises(ValidationError):
            MetricsSummary(total_operations=-1)


# ============================================================================
# DashboardFilter Tests
# ============================================================================

@pytest.mark.unit
class TestDashboardFilter:
    """Tests for DashboardFilter model."""
    
    def test_create_valid_filter(self):
        """Test creating a valid filter."""
        filter_obj = DashboardFilter(
            service="doc_store",
            time_range="Last 500 operations",
            operation_type="CREATE"
        )
        
        assert filter_obj.service == "doc_store"
        assert filter_obj.time_range == "Last 500 operations"
        assert filter_obj.operation_type == "CREATE"
    
    def test_filter_with_defaults(self):
        """Test filter with default values."""
        filter_obj = DashboardFilter()
        
        assert filter_obj.service is None
        assert filter_obj.time_range == "Last 100 operations"
        assert filter_obj.operation_type is None
    
    def test_time_range_validation(self):
        """Test time range validation."""
        # Valid time ranges
        for time_range in ["Last 100 operations", "Last 500 operations", "Last 1000 operations"]:
            filter_obj = DashboardFilter(time_range=time_range)
            assert filter_obj.time_range == time_range
        
        # Invalid time range (should default to "Last 100 operations")
        filter_obj = DashboardFilter(time_range="Last 999 operations")
        assert filter_obj.time_range == "Last 100 operations"
    
    def test_service_max_length(self):
        """Test service name max length validation."""
        # Valid service
        filter_obj = DashboardFilter(service="valid_service")
        assert filter_obj.service == "valid_service"
        
        # Too long service (> 100 chars)
        with pytest.raises(ValidationError):
            DashboardFilter(service="x" * 101)
    
    def test_filter_optional_fields(self):
        """Test that service and operation_type are optional."""
        filter_obj = DashboardFilter(time_range="Last 500 operations")
        
        assert filter_obj.service is None
        assert filter_obj.operation_type is None
        assert filter_obj.time_range == "Last 500 operations"


# ============================================================================
# Model Serialization Tests
# ============================================================================

@pytest.mark.unit
class TestModelSerialization:
    """Tests for model serialization (to/from dict, JSON)."""
    
    def test_log_entry_to_dict(self, sample_log_entry):
        """Test LogEntry serialization to dict."""
        data = sample_log_entry.model_dump()
        
        assert isinstance(data, dict)
        assert data["service"] == "doc_store"
        assert data["operation_type"] == "CREATE"
        assert data["status_code"] == 201
    
    def test_metrics_to_dict(self, sample_metrics):
        """Test MetricsSummary serialization to dict."""
        data = sample_metrics.model_dump()
        
        assert isinstance(data, dict)
        assert data["total_operations"] == 100
        assert data["error_rate"] == 5.0
    
    def test_filter_to_dict(self, sample_dashboard_filter):
        """Test DashboardFilter serialization to dict."""
        data = sample_dashboard_filter.model_dump()
        
        assert isinstance(data, dict)
        assert data["service"] == "doc_store"
        assert data["time_range"] == "Last 500 operations"

