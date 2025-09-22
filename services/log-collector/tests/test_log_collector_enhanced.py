"""Tests for enhanced log collector service functionality."""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import sys

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.log_storage import LogStorage, persistent_log_storage
from modules.log_stats import calculate_log_statistics


class TestEnhancedLogStorage:
    """Test enhanced log storage functionality."""

    def test_persistent_storage_initialization(self):
        """Test persistent storage initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LogStorage(persist_to_disk=True, storage_path=temp_dir)

            assert storage._persist_to_disk is True
            assert storage._storage_path.exists()
            assert storage._retention_days == 30

    def test_persistent_storage_disabled(self):
        """Test storage with persistence disabled."""
        storage = LogStorage(persist_to_disk=False)

        assert storage._persist_to_disk is False
        assert storage._storage_path is None

    def test_search_logs_basic(self):
        """Test basic log search functionality."""
        storage = LogStorage()

        # Add test logs
        logs = [
            {"service": "api", "level": "info", "message": "User login successful"},
            {"service": "api", "level": "error", "message": "Database connection failed"},
            {"service": "worker", "level": "info", "message": "Task completed successfully"},
        ]

        for log in logs:
            storage.add_log(log)

        # Search for "successful"
        results = storage.search_logs("successful")
        assert len(results) == 2
        assert all("successful" in log["message"] for log in results)

        # Search for "api" service
        results = storage.search_logs("api", fields=["service"])
        assert len(results) == 2
        assert all(log["service"] == "api" for log in results)

    def test_search_logs_case_insensitive(self):
        """Test case-insensitive search."""
        storage = LogStorage()

        storage.add_log({"service": "API", "level": "info", "message": "User Login"})

        # Search should be case insensitive by default
        results = storage.search_logs("api", fields=["service"])
        assert len(results) == 1

        results = storage.search_logs("user", fields=["message"])
        assert len(results) == 1

    def test_search_logs_case_sensitive(self):
        """Test case-sensitive search."""
        storage = LogStorage()

        storage.add_log({"service": "API", "level": "info", "message": "User Login"})

        # Case-sensitive search
        results = storage.search_logs("api", fields=["service"], case_sensitive=True)
        assert len(results) == 0  # Should not find "API" when searching for "api"

    def test_search_logs_limit(self):
        """Test search results limiting."""
        storage = LogStorage()

        # Add many logs
        for i in range(10):
            storage.add_log({"service": "test", "level": "info", "message": f"Message {i}"})

        # Search with limit
        results = storage.search_logs("Message", limit=3)
        assert len(results) == 3

    def test_time_range_queries(self):
        """Test time-based log queries."""
        storage = LogStorage()

        # Create logs with different timestamps
        now = datetime.now(timezone.utc)
        old_time = (now - timedelta(hours=2)).isoformat()
        recent_time = (now - timedelta(minutes=30)).isoformat()

        storage.add_log({
            "service": "test", "level": "info", "message": "Old log",
            "timestamp": old_time
        })
        storage.add_log({
            "service": "test", "level": "info", "message": "Recent log",
            "timestamp": recent_time
        })

        # Query last hour
        start_time = (now - timedelta(hours=1)).isoformat()
        results = storage.get_logs_by_time_range(start_time=start_time)

        assert len(results) == 1
        assert results[0]["message"] == "Recent log"

    def test_service_metrics_calculation(self):
        """Test detailed service metrics calculation."""
        storage = LogStorage()

        # Add logs for a service
        logs = [
            {"service": "api", "level": "info", "message": "Request processed", "timestamp": "2024-01-01T10:00:00Z",
             "context": {"response_time": 0.1}},
            {"service": "api", "level": "info", "message": "Request processed", "timestamp": "2024-01-01T10:01:00Z",
             "context": {"response_time": 0.2}},
            {"service": "api", "level": "error", "message": "Database error", "timestamp": "2024-01-01T10:02:00Z"},
            {"service": "worker", "level": "info", "message": "Task done", "timestamp": "2024-01-01T10:03:00Z"},
        ]

        for log in logs:
            storage.add_log(log)

        # Get service metrics for "api"
        metrics = storage.get_service_metrics("api", time_window_minutes=120)

        assert metrics["total_logs"] == 3
        assert metrics["performance"]["avg_response_time"] > 0
        assert metrics["performance"]["error_rate"] > 0
        assert metrics["services"]["api"]["error_count"] == 1

    def test_export_logs_json(self):
        """Test log export to JSON format."""
        storage = LogStorage()

        # Add test logs
        logs = [
            {"service": "test", "level": "info", "message": "Test message 1"},
            {"service": "test", "level": "error", "message": "Test error"},
        ]

        for log in logs:
            storage.add_log(log)

        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            count = storage.export_logs(temp_file, format="json")
            assert count == 2

            # Verify exported file
            with open(temp_file, 'r') as f:
                exported_data = json.load(f)
                assert len(exported_data) == 2
                assert exported_data[0]["message"] == "Test message 1"

        finally:
            os.unlink(temp_file)

    def test_export_logs_jsonl(self):
        """Test log export to JSONL format."""
        storage = LogStorage()

        storage.add_log({"service": "test", "level": "info", "message": "Test message"})

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_file = f.name

        try:
            count = storage.export_logs(temp_file, format="jsonl")
            assert count == 1

            # Verify exported file (JSONL format)
            with open(temp_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                log_entry = json.loads(lines[0])
                assert log_entry["message"] == "Test message"

        finally:
            os.unlink(temp_file)

    def test_export_with_filters(self):
        """Test log export with service and level filters."""
        storage = LogStorage()

        logs = [
            {"service": "api", "level": "info", "message": "API request"},
            {"service": "api", "level": "error", "message": "API error"},
            {"service": "worker", "level": "info", "message": "Worker task"},
        ]

        for log in logs:
            storage.add_log(log)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            # Export only API service logs
            count = storage.export_logs(temp_file, service="api")
            assert count == 2

            with open(temp_file, 'r') as f:
                exported_data = json.load(f)
                assert len(exported_data) == 2
                assert all(log["service"] == "api" for log in exported_data)

        finally:
            os.unlink(temp_file)


class TestEnhancedLogStatistics:
    """Test enhanced log statistics calculation."""

    def test_calculate_statistics_with_time_window(self):
        """Test statistics calculation with time window filtering."""
        logs = [
            {
                "service": "api", "level": "info", "message": "Request 1",
                "timestamp": "2024-01-01T12:00:00Z"
            },
            {
                "service": "api", "level": "error", "message": "Error occurred",
                "timestamp": "2024-01-01T12:05:00Z"
            },
            {
                "service": "worker", "level": "info", "message": "Task completed",
                "timestamp": "2024-01-01T11:00:00Z"  # Older than time window
            }
        ]

        # Calculate stats for last 2 hours
        stats = calculate_log_statistics(logs, time_window_hours=2)

        # Should only include logs from last 2 hours (2 out of 3)
        assert stats["total_logs"] == 2
        assert stats["by_level"]["info"] == 1
        assert stats["by_level"]["error"] == 1
        assert stats["by_service"]["api"] == 2

    def test_performance_metrics_calculation(self):
        """Test performance metrics in statistics."""
        logs = [
            {
                "service": "api", "level": "info", "message": "Request",
                "timestamp": "2024-01-01T12:00:00Z",
                "context": {"response_time": 0.1}
            },
            {
                "service": "api", "level": "info", "message": "Request",
                "timestamp": "2024-01-01T12:01:00Z",
                "context": {"response_time": 0.3}
            }
        ]

        stats = calculate_log_statistics(logs)

        assert "performance" in stats
        assert stats["performance"]["avg_response_time"] == 0.2
        assert stats["performance"]["min_response_time"] == 0.1
        assert stats["performance"]["max_response_time"] == 0.3

    def test_service_health_scoring(self):
        """Test service health scoring in statistics."""
        logs = [
            {"service": "api", "level": "info", "message": "Success", "timestamp": "2024-01-01T12:00:00Z"},
            {"service": "api", "level": "info", "message": "Success", "timestamp": "2024-01-01T12:01:00Z"},
            {"service": "api", "level": "error", "message": "Failure", "timestamp": "2024-01-01T12:02:00Z"},
            {"service": "api", "level": "info", "message": "Success", "timestamp": "2024-01-01T12:03:00Z"},
        ]

        stats = calculate_log_statistics(logs)

        assert "service_health" in stats
        api_health = stats["service_health"]["api"]
        assert api_health["total_logs"] == 4
        assert api_health["error_count"] == 1
        assert api_health["health_score"] < 100  # Should be reduced due to error

    def test_time_range_analysis(self):
        """Test time range analysis in statistics."""
        logs = [
            {"service": "api", "level": "info", "message": "Start", "timestamp": "2024-01-01T10:00:00Z"},
            {"service": "api", "level": "info", "message": "Middle", "timestamp": "2024-01-01T11:00:00Z"},
            {"service": "api", "level": "info", "message": "End", "timestamp": "2024-01-01T12:00:00Z"},
        ]

        stats = calculate_log_statistics(logs)

        assert "time_range" in stats
        time_range = stats["time_range"]
        assert "start" in time_range
        assert "end" in time_range
        assert time_range["duration_hours"] == 2.0

    def test_message_pattern_analysis(self):
        """Test message pattern analysis in statistics."""
        logs = [
            {"service": "api", "level": "error", "message": "Database connection failed"},
            {"service": "api", "level": "info", "message": "Request completed successfully"},
            {"service": "api", "level": "error", "message": "Timeout occurred"},
            {"service": "api", "level": "info", "message": "Task started"},
        ]

        stats = calculate_log_statistics(logs)

        assert "message_patterns" in stats
        patterns = stats["message_patterns"]
        assert patterns["error"] >= 2  # "failed" and "occurred" not direct matches
        assert "top_error_patterns" in stats

    def test_hourly_distribution_analysis(self):
        """Test hourly distribution analysis."""
        logs = [
            {"service": "api", "level": "info", "message": "Log 1", "timestamp": "2024-01-01T10:30:00Z"},
            {"service": "api", "level": "info", "message": "Log 2", "timestamp": "2024-01-01T10:45:00Z"},
            {"service": "api", "level": "info", "message": "Log 3", "timestamp": "2024-01-01T11:15:00Z"},
        ]

        stats = calculate_log_statistics(logs)

        assert "hourly_distribution" in stats
        hourly = stats["hourly_distribution"]
        assert hourly["10:00"] == 2  # 10:30 and 10:45
        assert hourly["11:00"] == 1  # 11:15

    def test_summary_statistics(self):
        """Test summary statistics calculation."""
        logs = [
            {"service": "api", "level": "info", "message": "Good", "timestamp": "2024-01-01T10:00:00Z"},
            {"service": "api", "level": "error", "message": "Bad", "timestamp": "2024-01-01T10:01:00Z"},
            {"service": "worker", "level": "info", "message": "Good", "timestamp": "2024-01-01T10:02:00Z"},
            {"service": "worker", "level": "error", "message": "Bad", "timestamp": "2024-01-01T10:03:00Z"},
        ]

        stats = calculate_log_statistics(logs)

        assert "summary" in stats
        summary = stats["summary"]
        assert "healthy_services" in summary
        assert "unhealthy_services" in summary
        assert "total_services" in summary
        assert "avg_health_score" in summary


class TestLogCollectorIntegration:
    """Test log collector service integration."""

    @pytest.mark.asyncio
    async def test_search_endpoint(self):
        """Test search endpoint functionality."""
        # This would test the actual FastAPI endpoint
        # For now, just test the underlying storage search
        storage = LogStorage()

        # Add test logs
        logs = [
            {"service": "api", "level": "info", "message": "User login successful"},
            {"service": "api", "level": "error", "message": "Database connection failed"},
        ]

        for log in logs:
            storage.add_log(log)

        # Test search functionality that would be used by endpoint
        results = storage.search_logs("successful")
        assert len(results) == 1
        assert "login" in results[0]["message"]

    @pytest.mark.asyncio
    async def test_service_metrics_endpoint(self):
        """Test service metrics endpoint functionality."""
        storage = LogStorage()

        # Add test logs
        logs = [
            {"service": "api", "level": "info", "message": "Request", "timestamp": "2024-01-01T12:00:00Z",
             "context": {"response_time": 0.1}},
            {"service": "api", "level": "error", "message": "Error", "timestamp": "2024-01-01T12:01:00Z"},
        ]

        for log in logs:
            storage.add_log(log)

        # Test metrics functionality that would be used by endpoint
        metrics = storage.get_service_metrics("api", time_window_minutes=60)
        assert metrics["total_logs"] == 2
        assert metrics["performance"]["error_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_export_endpoint(self):
        """Test export endpoint functionality."""
        storage = LogStorage()

        storage.add_log({"service": "test", "level": "info", "message": "Test message"})

        # Test export functionality that would be used by endpoint
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            count = storage.export_logs(temp_file, format="json")
            assert count == 1

            # Verify file was created and has content
            assert os.path.exists(temp_file)
            with open(temp_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 1

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestPersistentStorageIntegration:
    """Test persistent storage integration."""

    def test_persistent_storage_creation(self):
        """Test that persistent storage creates necessary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LogStorage(persist_to_disk=True, storage_path=temp_dir)

            # Storage directory should exist
            assert os.path.exists(temp_dir)
            assert os.path.isdir(temp_dir)

    def test_persistent_log_writing(self):
        """Test that logs are written to persistent storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LogStorage(persist_to_disk=True, storage_path=temp_dir)

            # Add a log
            log_entry = {
                "service": "test",
                "level": "info",
                "message": "Persistent test message",
                "timestamp": "2024-01-01T12:00:00Z"
            }
            storage.add_log(log_entry)

            # Force persistence (normally async)
            asyncio.run(storage._persist_log_entry(log_entry))

            # Check that file was created
            expected_file = storage._storage_path / "logs_2024-01-01.jsonl"
            assert expected_file.exists()

            # Check file contents
            with open(expected_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                persisted_log = json.loads(lines[0])
                assert persisted_log["message"] == "Persistent test message"
