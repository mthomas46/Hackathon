"""Unit tests for log storage functionality."""

import pytest
from datetime import datetime, timezone
from modules.log_storage import LogStorage


class TestLogStorage:
    """Test suite for LogStorage class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.storage = LogStorage(max_logs=10)

    def teardown_method(self):
        """Clean up after each test method."""
        self.storage.clear_logs()

    def test_initialization(self):
        """Test that LogStorage initializes correctly."""
        assert self.storage.get_count() == 0
        assert self.storage.get_all_logs() == []

    def test_add_single_log(self):
        """Test adding a single log entry."""
        log_entry = {
            "service": "test-service",
            "level": "INFO",
            "message": "Test message",
            "timestamp": "2024-01-15T10:30:45.123456+00:00"
        }

        count = self.storage.add_log(log_entry)
        assert count == 1
        assert self.storage.get_count() == 1

        logs = self.storage.get_all_logs()
        assert len(logs) == 1
        assert logs[0]["service"] == "test-service"
        assert logs[0]["level"] == "INFO"
        assert logs[0]["message"] == "Test message"

    def test_add_log_auto_timestamp(self):
        """Test that timestamp is automatically added if missing."""
        log_entry = {
            "service": "test-service",
            "level": "INFO",
            "message": "Test message"
        }

        self.storage.add_log(log_entry)
        logs = self.storage.get_all_logs()

        assert "timestamp" in logs[0]
        assert logs[0]["timestamp"] is not None
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(logs[0]["timestamp"].replace('Z', '+00:00'))

    def test_add_logs_batch(self):
        """Test adding multiple logs in batch."""
        log_entries = [
            {"service": "service1", "level": "INFO", "message": "Message 1"},
            {"service": "service2", "level": "ERROR", "message": "Message 2"},
            {"service": "service1", "level": "DEBUG", "message": "Message 3"}
        ]

        count = self.storage.add_logs_batch(log_entries)
        assert count == 3
        assert self.storage.get_count() == 3

    def test_capacity_limit(self):
        """Test that storage respects maximum capacity."""
        # Add more logs than the capacity limit
        for i in range(15):
            log_entry = {
                "service": f"service{i}",
                "level": "INFO",
                "message": f"Message {i}"
            }
            self.storage.add_log(log_entry)

        # Should only keep the last 10 logs
        assert self.storage.get_count() == 10

        logs = self.storage.get_all_logs()
        # The first 5 should be removed (oldest), last 10 should remain
        assert len(logs) == 10
        assert logs[0]["service"] == "service5"  # First remaining log
        assert logs[-1]["service"] == "service14"  # Last log

    def test_get_logs_filtering(self):
        """Test filtering logs by service and level."""
        logs = [
            {"service": "api", "level": "INFO", "message": "API call"},
            {"service": "db", "level": "ERROR", "message": "DB error"},
            {"service": "api", "level": "DEBUG", "message": "Debug info"},
            {"service": "cache", "level": "INFO", "message": "Cache hit"}
        ]

        for log in logs:
            self.storage.add_log(log)

        # Filter by service
        api_logs = self.storage.get_logs(service="api")
        assert len(api_logs) == 2
        assert all(log["service"] == "api" for log in api_logs)

        # Filter by level
        error_logs = self.storage.get_logs(level="ERROR")
        assert len(error_logs) == 1
        assert error_logs[0]["level"] == "ERROR"

        # Filter by both
        api_info_logs = self.storage.get_logs(service="api", level="INFO")
        assert len(api_info_logs) == 1
        assert api_info_logs[0]["service"] == "api"
        assert api_info_logs[0]["level"] == "INFO"

    def test_get_logs_limit(self):
        """Test limiting the number of returned logs."""
        # Add 20 logs
        for i in range(20):
            self.storage.add_log({"service": f"service{i}", "level": "INFO", "message": f"Message {i}"})

        # Get all logs (should be limited to capacity of 10)
        all_logs = self.storage.get_logs(limit=0)
        assert len(all_logs) == 10

        # Get limited logs
        limited_logs = self.storage.get_logs(limit=5)
        assert len(limited_logs) == 5

        # Default limit
        default_logs = self.storage.get_logs()
        assert len(default_logs) == 10  # Our default is 100, but we only have 10

    def test_clear_logs(self):
        """Test clearing all logs."""
        # Add some logs
        self.storage.add_logs_batch([
            {"service": "test", "level": "INFO", "message": "msg1"},
            {"service": "test", "level": "INFO", "message": "msg2"}
        ])

        assert self.storage.get_count() == 2

        # Clear logs
        self.storage.clear_logs()
        assert self.storage.get_count() == 0
        assert self.storage.get_all_logs() == []

    def test_thread_safety_concept(self):
        """Test basic thread safety concept (simplified test)."""
        # This is a basic test - in a real scenario you'd use threading
        # For now, just verify the storage handles concurrent-like operations
        import time

        # Simulate some concurrent operations
        for i in range(100):
            self.storage.add_log({
                "service": "concurrent-test",
                "level": "INFO",
                "message": f"Concurrent message {i}",
                "timestamp": f"2024-01-15T10:30:{i:02d}.000000+00:00"
            })

        assert self.storage.get_count() == 10  # Limited by capacity
