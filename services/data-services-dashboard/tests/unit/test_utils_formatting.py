"""
Unit tests for formatting utilities.

Tests formatting functions for display.
"""

import pytest
from datetime import datetime

from utils.formatting import (
    format_duration,
    truncate_workflow_id,
    format_timestamp,
    format_percentage,
    format_service_name,
    format_status_code,
    format_count,
    format_uptime
)


# ============================================================================
# Duration Formatting Tests
# ============================================================================

@pytest.mark.unit
class TestDurationFormatting:
    """Tests for duration formatting."""
    
    def test_format_duration_milliseconds(self):
        """Test formatting durations in milliseconds."""
        assert format_duration(150.5) == "150.5ms"
        assert format_duration(999.9) == "999.9ms"
    
    def test_format_duration_seconds(self):
        """Test formatting durations in seconds."""
        assert format_duration(1500.0) == "1.50s"
        assert format_duration(5000.0) == "5.00s"
    
    def test_format_duration_minutes(self):
        """Test formatting durations in minutes."""
        assert format_duration(60000.0) == "1m 0.0s"
        assert format_duration(125000.0) == "2m 5.0s"
    
    def test_format_duration_none(self):
        """Test formatting None duration."""
        assert format_duration(None) == "N/A"
    
    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "0ms"


# ============================================================================
# Workflow ID Formatting Tests
# ============================================================================

@pytest.mark.unit
class TestWorkflowIdFormatting:
    """Tests for workflow ID truncation."""
    
    def test_truncate_short_workflow_id(self):
        """Test truncating a short workflow ID (no truncation needed)."""
        wf_id = "short123"
        assert truncate_workflow_id(wf_id, max_length=12) == "short123"
    
    def test_truncate_long_workflow_id(self):
        """Test truncating a long workflow ID."""
        wf_id = "very_long_workflow_id_that_needs_truncation"
        result = truncate_workflow_id(wf_id, max_length=12)
        
        assert len(result) == 12
        assert result.endswith("...")
        assert result == "very_long_w..."
    
    def test_truncate_none_workflow_id(self):
        """Test truncating None workflow ID."""
        assert truncate_workflow_id(None) == "N/A"
    
    def test_truncate_empty_workflow_id(self):
        """Test truncating empty workflow ID."""
        assert truncate_workflow_id("") == "N/A"


# ============================================================================
# Timestamp Formatting Tests
# ============================================================================

@pytest.mark.unit
class TestTimestampFormatting:
    """Tests for timestamp formatting."""
    
    def test_format_timestamp(self):
        """Test formatting a timestamp."""
        dt = datetime(2025, 10, 9, 12, 30, 45)
        assert format_timestamp(dt) == "2025-10-09 12:30:45"
    
    def test_format_timestamp_midnight(self):
        """Test formatting midnight timestamp."""
        dt = datetime(2025, 10, 9, 0, 0, 0)
        assert format_timestamp(dt) == "2025-10-09 00:00:00"


# ============================================================================
# Percentage Formatting Tests
# ============================================================================

@pytest.mark.unit
class TestPercentageFormatting:
    """Tests for percentage formatting."""
    
    def test_format_percentage_default(self):
        """Test formatting percentage with default decimals."""
        assert format_percentage(12.5) == "12.5%"
        assert format_percentage(0.0) == "0.0%"
        assert format_percentage(100.0) == "100.0%"
    
    def test_format_percentage_custom_decimals(self):
        """Test formatting percentage with custom decimals."""
        assert format_percentage(12.5678, decimals=2) == "12.57%"
        assert format_percentage(12.5, decimals=0) == "12%"


# ============================================================================
# Service Name Formatting Tests
# ============================================================================

@pytest.mark.unit
class TestServiceNameFormatting:
    """Tests for service name formatting."""
    
    def test_format_service_name_underscores(self):
        """Test formatting service name with underscores."""
        assert format_service_name("doc_store") == "Doc Store"
        assert format_service_name("memory_agent") == "Memory Agent"
    
    def test_format_service_name_dashes(self):
        """Test formatting service name with dashes."""
        assert format_service_name("external-service-store") == "External Service Store"
    
    def test_format_service_name_mixed(self):
        """Test formatting service name with mixed separators."""
        assert format_service_name("my_service-name") == "My Service Name"


# ============================================================================
# Status Code Formatting Tests
# ============================================================================

@pytest.mark.unit
class TestStatusCodeFormatting:
    """Tests for HTTP status code formatting."""
    
    def test_format_success_status_codes(self):
        """Test formatting successful status codes (< 400)."""
        assert format_status_code(200) == "✅ 200"
        assert format_status_code(201) == "✅ 201"
        assert format_status_code(204) == "✅ 204"
    
    def test_format_error_status_codes(self):
        """Test formatting error status codes (>= 400)."""
        assert format_status_code(400) == "❌ 400"
        assert format_status_code(404) == "❌ 404"
        assert format_status_code(500) == "❌ 500"
    
    def test_format_none_status_code(self):
        """Test formatting None status code."""
        assert format_status_code(None) == "N/A"


# ============================================================================
# Count Formatting Tests
# ============================================================================

@pytest.mark.unit
class TestCountFormatting:
    """Tests for count formatting (singular/plural)."""
    
    def test_format_count_singular(self):
        """Test formatting count with singular form."""
        assert format_count(1, "operation") == "1 operation"
        assert format_count(1, "error") == "1 error"
    
    def test_format_count_plural(self):
        """Test formatting count with plural form."""
        assert format_count(0, "operation") == "0 operations"
        assert format_count(2, "operation") == "2 operations"
        assert format_count(100, "operation") == "100 operations"
    
    def test_format_count_custom_plural(self):
        """Test formatting count with custom plural form."""
        assert format_count(1, "category", "categories") == "1 category"
        assert format_count(2, "category", "categories") == "2 categories"


# ============================================================================
# Uptime Formatting Tests
# ============================================================================

@pytest.mark.unit
class TestUptimeFormatting:
    """Tests for uptime formatting."""
    
    def test_format_uptime_seconds(self):
        """Test formatting uptime in seconds."""
        assert format_uptime(30) == "30s"
        assert format_uptime(59) == "59s"
    
    def test_format_uptime_minutes(self):
        """Test formatting uptime in minutes."""
        assert format_uptime(60) == "1m 0s"
        assert format_uptime(125) == "2m 5s"
        assert format_uptime(3599) == "59m 59s"
    
    def test_format_uptime_hours(self):
        """Test formatting uptime in hours."""
        assert format_uptime(3600) == "1h 0m"
        assert format_uptime(7265) == "2h 1m"
    
    def test_format_uptime_days(self):
        """Test formatting uptime in days."""
        assert format_uptime(86400) == "1d 0h"
        assert format_uptime(90000) == "1d 1h"
        assert format_uptime(172800) == "2d 0h"

