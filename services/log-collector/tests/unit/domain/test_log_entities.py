"""Unit tests for log-collector domain entities."""

import pytest
from datetime import datetime, timezone, timedelta
from enum import Enum

from services.log_collector.domain.entities import LogEntry, LogStatistics, LogLevel


class TestLogEntry:
    """Test cases for LogEntry entity."""

    def test_log_entry_creation(self):
        """Test basic LogEntry creation."""
        entry = LogEntry(
            id="log-123",
            service_name="api-gateway",
            level=LogLevel.INFO,
            message="User authentication successful",
            timestamp=datetime.now(timezone.utc)
        )

        assert entry.id == "log-123"
        assert entry.service_name == "api-gateway"
        assert entry.level == LogLevel.INFO
        assert entry.message == "User authentication successful"
        assert isinstance(entry.timestamp, datetime)

    def test_log_entry_with_metadata(self):
        """Test LogEntry with additional metadata."""
        metadata = {
            "user_id": "user-456",
            "request_id": "req-789",
            "endpoint": "/api/auth",
            "response_time_ms": 150
        }

        entry = LogEntry(
            id="log-meta",
            service_name="api-gateway",
            level=LogLevel.INFO,
            message="Authentication completed",
            metadata=metadata
        )

        assert entry.metadata["user_id"] == "user-456"
        assert entry.metadata["response_time_ms"] == 150

    def test_log_entry_validation(self):
        """Test LogEntry validation rules."""
        # Valid entry
        valid_entry = LogEntry(
            id="valid-log",
            service_name="test-service",
            level=LogLevel.ERROR,
            message="Database connection failed"
        )
        assert valid_entry.id == "valid-log"

        # Empty message should raise error
        with pytest.raises(ValueError):
            LogEntry(
                id="invalid-log",
                service_name="test-service",
                level=LogLevel.INFO,
                message=""
            )

    def test_log_entry_level_operations(self):
        """Test log level specific operations."""
        # Error level
        error_entry = LogEntry(
            id="error-log",
            service_name="service-1",
            level=LogLevel.ERROR,
            message="Critical error occurred"
        )
        assert error_entry.is_error_level()
        assert error_entry.is_critical()

        # Warning level
        warn_entry = LogEntry(
            id="warn-log",
            service_name="service-1",
            level=LogLevel.WARNING,
            message="Performance degradation"
        )
        assert warn_entry.is_warning_level()
        assert not warn_entry.is_critical()

        # Info level
        info_entry = LogEntry(
            id="info-log",
            service_name="service-1",
            level=LogLevel.INFO,
            message="Service started successfully"
        )
        assert info_entry.is_info_level()
        assert not info_entry.is_error_level()

    def test_log_entry_serialization(self):
        """Test log entry serialization."""
        entry = LogEntry(
            id="serialize-log",
            service_name="test-service",
            level=LogLevel.DEBUG,
            message="Debug information",
            metadata={"key": "value"}
        )

        data = entry.to_dict()
        assert data["id"] == "serialize-log"
        assert data["service_name"] == "test-service"
        assert data["level"] == "debug"
        assert data["message"] == "Debug information"
        assert data["metadata"]["key"] == "value"

    def test_log_entry_time_operations(self):
        """Test log entry time-based operations."""
        base_time = datetime.now(timezone.utc)

        recent_entry = LogEntry(
            id="recent",
            service_name="service-1",
            level=LogLevel.INFO,
            message="Recent log",
            timestamp=base_time - timedelta(minutes=30)
        )

        old_entry = LogEntry(
            id="old",
            service_name="service-1",
            level=LogLevel.INFO,
            message="Old log",
            timestamp=base_time - timedelta(hours=2)
        )

        assert recent_entry.is_recent(hours=1)
        assert not old_entry.is_recent(hours=1)

    def test_log_entry_content_search(self):
        """Test log entry content search capabilities."""
        entry = LogEntry(
            id="search-test",
            service_name="api-gateway",
            level=LogLevel.ERROR,
            message="Database connection timeout for user authentication",
            metadata={"error_code": "DB_TIMEOUT"}
        )

        # Test message search
        assert entry.contains_text("database")
        assert entry.contains_text("timeout")
        assert entry.contains_text("authentication")
        assert not entry.contains_text("network")

        # Test metadata search
        assert entry.contains_in_metadata("DB_TIMEOUT")
        assert entry.contains_in_metadata("error_code")


class TestLogStatistics:
    """Test cases for LogStatistics entity."""

    def test_log_statistics_creation(self):
        """Test basic LogStatistics creation."""
        stats = LogStatistics(
            service_name="api-gateway",
            time_window_start=datetime.now(timezone.utc) - timedelta(hours=1),
            time_window_end=datetime.now(timezone.utc),
            total_entries=150,
            error_count=5,
            warning_count=12,
            info_count=100,
            debug_count=33
        )

        assert stats.service_name == "api-gateway"
        assert stats.total_entries == 150
        assert stats.error_count == 5
        assert stats.warning_count == 12

    def test_log_statistics_calculations(self):
        """Test log statistics calculations."""
        stats = LogStatistics(
            service_name="test-service",
            time_window_start=datetime.now(timezone.utc) - timedelta(hours=1),
            time_window_end=datetime.now(timezone.utc),
            total_entries=200,
            error_count=10,
            warning_count=20,
            info_count=150,
            debug_count=20
        )

        # Test error rate
        assert stats.error_rate == 5.0  # 10/200 * 100

        # Test warning rate
        assert stats.warning_rate == 10.0  # 20/200 * 100

        # Test success rate (non-error logs)
        assert stats.success_rate == 95.0  # (200-10)/200 * 100

    def test_log_statistics_time_window(self):
        """Test log statistics time window operations."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        end_time = datetime.now(timezone.utc)

        stats = LogStatistics(
            service_name="test-service",
            time_window_start=start_time,
            time_window_end=end_time,
            total_entries=100,
            error_count=2,
            warning_count=5,
            info_count=80,
            debug_count=13
        )

        assert stats.window_duration_hours == 2.0
        assert stats.is_within_window(start_time + timedelta(minutes=30))
        assert not stats.is_within_window(start_time - timedelta(minutes=30))

    def test_log_statistics_trends(self):
        """Test log statistics trend analysis."""
        stats = LogStatistics(
            service_name="trending-service",
            time_window_start=datetime.now(timezone.utc) - timedelta(hours=1),
            time_window_end=datetime.now(timezone.utc),
            total_entries=1000,
            error_count=50,
            warning_count=100,
            info_count=800,
            debug_count=50
        )

        # Test severity distribution
        distribution = stats.get_severity_distribution()
        assert distribution["ERROR"] == 50
        assert distribution["WARNING"] == 100
        assert distribution["INFO"] == 800
        assert distribution["DEBUG"] == 50

        # Test health score (lower error rate = higher score)
        health_score = stats.get_health_score()
        assert 0 <= health_score <= 100

    def test_log_statistics_comparison(self):
        """Test log statistics comparison operations."""
        stats1 = LogStatistics(
            service_name="service-a",
            time_window_start=datetime.now(timezone.utc) - timedelta(hours=1),
            time_window_end=datetime.now(timezone.utc),
            total_entries=100,
            error_count=5,
            warning_count=10,
            info_count=75,
            debug_count=10
        )

        stats2 = LogStatistics(
            service_name="service-b",
            time_window_start=datetime.now(timezone.utc) - timedelta(hours=1),
            time_window_end=datetime.now(timezone.utc),
            total_entries=120,
            error_count=8,
            warning_count=15,
            info_count=85,
            debug_count=12
        )

        # Compare error rates
        assert stats1.error_rate < stats2.error_rate

        # Compare total entries
        assert stats1.total_entries < stats2.total_entries

    def test_log_statistics_serialization(self):
        """Test log statistics serialization."""
        stats = LogStatistics(
            service_name="serialize-service",
            time_window_start=datetime.now(timezone.utc) - timedelta(hours=1),
            time_window_end=datetime.now(timezone.utc),
            total_entries=50,
            error_count=2,
            warning_count=5,
            info_count=35,
            debug_count=8
        )

        data = stats.to_dict()
        assert data["service_name"] == "serialize-service"
        assert data["total_entries"] == 50
        assert data["error_count"] == 2
        assert data["warning_count"] == 5
        assert "time_window_start" in data
        assert "time_window_end" in data


class TestLogLevel:
    """Test cases for LogLevel enum."""

    def test_log_level_enum_values(self):
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"

    def test_log_level_from_string(self):
        """Test creating LogLevel from string."""
        assert LogLevel("debug") == LogLevel.DEBUG
        assert LogLevel("error") == LogLevel.ERROR

    def test_log_level_ordering(self):
        """Test log level ordering."""
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR

    def test_log_level_severity(self):
        """Test log level severity operations."""
        # Debug level
        assert LogLevel.DEBUG.is_debug()
        assert not LogLevel.DEBUG.is_error()

        # Error level
        assert LogLevel.ERROR.is_error()
        assert LogLevel.ERROR.is_critical()

        # Warning level
        assert LogLevel.WARNING.is_warning()
        assert LogLevel.WARNING.get_severity_level() == 3

        # Info level
        assert LogLevel.INFO.is_info()
        assert LogLevel.INFO.get_severity_level() == 2


class TestLogEntityIntegration:
    """Integration tests for log entities working together."""

    def test_log_entry_and_statistics_integration(self):
        """Test LogEntry and LogStatistics working together."""
        # Create log entries
        entries = [
            LogEntry(id="log-1", service_name="api-gateway", level=LogLevel.ERROR, message="DB timeout", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="log-2", service_name="api-gateway", level=LogLevel.WARNING, message="High latency", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="log-3", service_name="api-gateway", level=LogLevel.INFO, message="Request processed", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="log-4", service_name="api-gateway", level=LogLevel.INFO, message="Cache hit", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="log-5", service_name="api-gateway", level=LogLevel.DEBUG, message="Cache debug info", timestamp=datetime.now(timezone.utc))
        ]

        # Calculate statistics from entries
        start_time = min(entry.timestamp for entry in entries)
        end_time = max(entry.timestamp for entry in entries)

        error_count = sum(1 for entry in entries if entry.level == LogLevel.ERROR)
        warning_count = sum(1 for entry in entries if entry.level == LogLevel.WARNING)
        info_count = sum(1 for entry in entries if entry.level == LogLevel.INFO)
        debug_count = sum(1 for entry in entries if entry.level == LogLevel.DEBUG)

        stats = LogStatistics(
            service_name="api-gateway",
            time_window_start=start_time,
            time_window_end=end_time,
            total_entries=len(entries),
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            debug_count=debug_count
        )

        # Verify integration
        assert stats.total_entries == 5
        assert stats.error_count == 1
        assert stats.warning_count == 1
        assert stats.info_count == 2
        assert stats.debug_count == 1
        assert stats.error_rate == 20.0  # 1/5 * 100

    def test_log_entity_lifecycle(self):
        """Test complete log entity lifecycle."""
        # Create entry
        entry = LogEntry(
            id="lifecycle-test",
            service_name="test-service",
            level=LogLevel.INFO,
            message="Initial log message",
            metadata={"request_id": "req-123"}
        )

        # Update entry (simulate processing)
        entry.metadata["processed"] = True

        # Create statistics that include this entry
        stats = LogStatistics(
            service_name="test-service",
            time_window_start=datetime.now(timezone.utc) - timedelta(minutes=5),
            time_window_end=datetime.now(timezone.utc),
            total_entries=10,
            error_count=0,
            warning_count=1,
            info_count=8,
            debug_count=1
        )

        # Verify lifecycle consistency
        assert entry.service_name == stats.service_name
        assert entry.level == LogLevel.INFO
        assert stats.info_count > 0
        assert stats.error_rate == 0.0

    def test_log_entity_filtering_and_search(self):
        """Test filtering and search across log entities."""
        entries = [
            LogEntry(id="err-1", service_name="api", level=LogLevel.ERROR, message="DB connection failed", metadata={"db": "postgres"}),
            LogEntry(id="warn-1", service_name="api", level=LogLevel.WARNING, message="High memory usage", metadata={"memory_mb": 850}),
            LogEntry(id="info-1", service_name="api", level=LogLevel.INFO, message="User login successful", metadata={"user_id": "user123"}),
            LogEntry(id="err-2", service_name="worker", level=LogLevel.ERROR, message="Queue processing failed", metadata={"queue": "jobs"})
        ]

        # Filter by service
        api_entries = [e for e in entries if e.service_name == "api"]
        assert len(api_entries) == 3

        # Filter by level
        error_entries = [e for e in entries if e.is_error_level()]
        assert len(error_entries) == 2

        # Search by content
        db_entries = [e for e in entries if e.contains_text("DB") or e.contains_text("db")]
        assert len(db_entries) == 1

        # Search by metadata
        postgres_entries = [e for e in entries if e.contains_in_metadata("postgres")]
        assert len(postgres_entries) == 1
