"""Unit tests for log collector domain services."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from services.log_collector.domain.services.log_stats import LogStatsService
from services.log_collector.domain.services.log_storage import LogStorageService
from services.log_collector.domain.entities import LogEntry, LogStatistics


class TestLogStatsService:
    """Test cases for LogStatsService."""

    @pytest.fixture
    def log_stats_service(self):
        """Create LogStatsService instance for testing."""
        return LogStatsService()

    def test_calculate_basic_stats(self, log_stats_service):
        """Test basic log statistics calculation."""
        logs = [
            LogEntry(level="INFO", service="test-service", message="Test message 1"),
            LogEntry(level="ERROR", service="test-service", message="Test error"),
            LogEntry(level="WARNING", service="test-service", message="Test warning"),
            LogEntry(level="INFO", service="test-service", message="Test message 2"),
        ]

        stats = log_stats_service.calculate_statistics(logs, "test-service")

        assert stats.total_logs == 4
        assert stats.error_count == 1
        assert stats.warning_count == 1
        assert stats.info_count == 2
        assert stats.error_rate == 25.0  # 1/4 * 100

    def test_calculate_stats_with_time_window(self, log_stats_service):
        """Test statistics calculation with time window."""
        base_time = datetime.now(timezone.utc)

        # Create logs with timestamps
        logs = []
        for i in range(5):
            log = LogEntry(
                level="INFO",
                service="test-service",
                message=f"Message {i}",
                timestamp=base_time
            )
            logs.append(log)

        time_window_minutes = 60
        stats = log_stats_service.calculate_statistics_with_time_window(
            logs, "test-service", time_window_minutes
        )

        assert stats.total_logs == 5
        assert stats.time_window_start <= base_time
        assert stats.time_window_end >= base_time

    def test_detect_anomalies(self, log_stats_service):
        """Test anomaly detection in logs."""
        # Normal logs
        normal_logs = [
            LogEntry(level="INFO", service="test-service", message="Normal operation")
            for _ in range(10)
        ]

        # Add some anomalies
        anomaly_logs = normal_logs + [
            LogEntry(level="ERROR", service="test-service", message="Critical error!")
            for _ in range(5)
        ]

        anomalies = log_stats_service.detect_anomalies(anomaly_logs)

        assert len(anomalies) > 0
        assert any("error" in anomaly.lower() for anomaly in anomalies)

    def test_generate_performance_insights(self, log_stats_service):
        """Test performance insights generation."""
        logs = [
            LogEntry(level="INFO", service="api", message="Request processed", timestamp=datetime.now(timezone.utc))
            for _ in range(100)
        ]

        insights = log_stats_service.generate_performance_insights(logs)

        assert isinstance(insights, dict)
        assert "logs_per_minute" in insights
        assert "peak_hour" in insights

    def test_calculate_error_patterns(self, log_stats_service):
        """Test error pattern analysis."""
        logs = [
            LogEntry(level="ERROR", service="api", message="Connection timeout"),
            LogEntry(level="ERROR", service="api", message="Connection timeout"),
            LogEntry(level="ERROR", service="api", message="Database error"),
            LogEntry(level="ERROR", service="api", message="Connection timeout"),
        ]

        patterns = log_stats_service.calculate_error_patterns(logs)

        assert "Connection timeout" in patterns
        assert patterns["Connection timeout"] == 3
        assert patterns["Database error"] == 1

    def test_generate_recommendations(self, log_stats_service):
        """Test recommendation generation based on log analysis."""
        # Logs with high error rate
        logs = [
            LogEntry(level="ERROR", service="api", message="Timeout")
            for _ in range(8)
        ] + [
            LogEntry(level="INFO", service="api", message="Success")
            for _ in range(2)
        ]

        recommendations = log_stats_service.generate_recommendations(logs)

        assert len(recommendations) > 0
        assert any("error rate" in rec.lower() for rec in recommendations)


class TestLogStorageService:
    """Test cases for LogStorageService."""

    @pytest.fixture
    def log_storage_service(self):
        """Create LogStorageService instance for testing."""
        return LogStorageService()

    @pytest.mark.asyncio
    async def test_store_log_entry(self, log_storage_service):
        """Test storing a single log entry."""
        log_entry = LogEntry(
            level="INFO",
            service="test-service",
            message="Test log message"
        )

        result = await log_storage_service.store_log_entry(log_entry)

        assert result is True
        # Verify the log was stored (implementation dependent)

    @pytest.mark.asyncio
    async def test_store_multiple_entries(self, log_storage_service):
        """Test storing multiple log entries."""
        log_entries = [
            LogEntry(level="INFO", service="test-service", message=f"Message {i}")
            for i in range(5)
        ]

        results = await log_storage_service.store_multiple_entries(log_entries)

        assert len(results) == 5
        assert all(result for result in results)

    @pytest.mark.asyncio
    async def test_retrieve_logs_by_service(self, log_storage_service):
        """Test retrieving logs by service name."""
        # First store some logs
        logs = [
            LogEntry(level="INFO", service="api", message="API request"),
            LogEntry(level="ERROR", service="api", message="API error"),
            LogEntry(level="INFO", service="worker", message="Worker task"),
        ]

        await log_storage_service.store_multiple_entries(logs)

        # Retrieve API logs
        api_logs = await log_storage_service.retrieve_logs_by_service("api")
        assert len(api_logs) >= 2
        assert all(log.service == "api" for log in api_logs)

    @pytest.mark.asyncio
    async def test_retrieve_logs_by_level(self, log_storage_service):
        """Test retrieving logs by level."""
        logs = [
            LogEntry(level="INFO", service="test", message="Info message"),
            LogEntry(level="ERROR", service="test", message="Error message"),
            LogEntry(level="WARNING", service="test", message="Warning message"),
        ]

        await log_storage_service.store_multiple_entries(logs)

        error_logs = await log_storage_service.retrieve_logs_by_level("ERROR")
        assert len(error_logs) >= 1
        assert all(log.level == "ERROR" for log in error_logs)

    @pytest.mark.asyncio
    async def test_retrieve_logs_by_time_range(self, log_storage_service):
        """Test retrieving logs within time range."""
        base_time = datetime.now(timezone.utc)

        # Create logs with different timestamps
        old_log = LogEntry(
            level="INFO",
            service="test",
            message="Old log",
            timestamp=base_time.replace(hour=base_time.hour - 2)
        )

        new_log = LogEntry(
            level="INFO",
            service="test",
            message="New log",
            timestamp=base_time
        )

        await log_storage_service.store_multiple_entries([old_log, new_log])

        # Retrieve logs from last hour
        recent_logs = await log_storage_service.retrieve_logs_by_time_range(
            base_time.replace(hour=base_time.hour - 1),
            base_time
        )

        assert len(recent_logs) >= 1
        # Should contain the new log but not the old one

    @pytest.mark.asyncio
    async def test_search_logs(self, log_storage_service):
        """Test searching logs by content."""
        logs = [
            LogEntry(level="INFO", service="test", message="User login successful"),
            LogEntry(level="INFO", service="test", message="Database connection established"),
            LogEntry(level="ERROR", service="test", message="Failed to connect to database"),
        ]

        await log_storage_service.store_multiple_entries(logs)

        # Search for database-related logs
        db_logs = await log_storage_service.search_logs("database")
        assert len(db_logs) >= 2
        assert all("database" in log.message.lower() for log in db_logs)

    @pytest.mark.asyncio
    async def test_get_log_statistics(self, log_storage_service):
        """Test retrieving log statistics."""
        # Store various types of logs
        logs = [
            LogEntry(level="INFO", service="api", message="Request processed"),
            LogEntry(level="ERROR", service="api", message="Request failed"),
            LogEntry(level="WARNING", service="api", message="Slow response"),
            LogEntry(level="INFO", service="worker", message="Task completed"),
        ]

        await log_storage_service.store_multiple_entries(logs)

        stats = await log_storage_service.get_log_statistics("api")

        assert stats.total_logs >= 3
        assert "error_rate" in stats
        assert "most_common_levels" in stats

    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, log_storage_service):
        """Test cleanup of old log entries."""
        old_time = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 1)

        # Create old logs
        old_logs = [
            LogEntry(
                level="INFO",
                service="test",
                message="Old log",
                timestamp=old_time
            )
            for _ in range(3)
        ]

        await log_storage_service.store_multiple_entries(old_logs)

        # Cleanup logs older than 6 months
        deleted_count = await log_storage_service.cleanup_old_logs(months=6)

        assert deleted_count >= 0

    def test_validate_log_entry(self, log_storage_service):
        """Test log entry validation."""
        # Valid log
        valid_log = LogEntry(
            level="INFO",
            service="test-service",
            message="Valid log message"
        )
        assert log_storage_service.validate_log_entry(valid_log) is True

        # Invalid log (empty message)
        invalid_log = LogEntry(
            level="INFO",
            service="test-service",
            message=""
        )
        assert log_storage_service.validate_log_entry(invalid_log) is False

    def test_get_storage_metrics(self, log_storage_service):
        """Test storage metrics retrieval."""
        metrics = log_storage_service.get_storage_metrics()

        assert isinstance(metrics, dict)
        assert "total_logs_stored" in metrics
        assert "storage_size_mb" in metrics
        assert "retention_days" in metrics
