"""Unit tests for log statistics calculation functionality."""

import pytest
from modules.log_stats import calculate_log_statistics


class TestLogStatistics:
    """Test suite for log statistics calculation functions."""

    def test_empty_logs(self):
        """Test statistics calculation with empty log list."""
        stats = calculate_log_statistics([])

        expected = {
            "count": 0,
            "by_level": {},
            "by_service": {},
            "errors_by_service": {},
            "top_services": []
        }

        assert stats == expected

    def test_single_log(self):
        """Test statistics with a single log entry."""
        logs = [
            {
                "service": "api-gateway",
                "level": "INFO",
                "message": "Request processed",
                "timestamp": "2024-01-15T10:30:45.123456+00:00"
            }
        ]

        stats = calculate_log_statistics(logs)

        assert stats["count"] == 1
        assert stats["by_level"] == {"info": 1}
        assert stats["by_service"] == {"api-gateway": 1}
        assert stats["errors_by_service"] == {}
        assert stats["top_services"] == [("api-gateway", 1)]

    def test_multiple_logs_different_levels(self):
        """Test statistics with logs of different levels."""
        logs = [
            {"service": "api", "level": "INFO", "message": "Request 1"},
            {"service": "api", "level": "ERROR", "message": "Error occurred"},
            {"service": "api", "level": "DEBUG", "message": "Debug info"},
            {"service": "api", "level": "INFO", "message": "Request 2"},
            {"service": "api", "level": "WARN", "message": "Warning issued"},
        ]

        stats = calculate_log_statistics(logs)

        assert stats["count"] == 5
        assert stats["by_level"] == {
            "info": 2,
            "error": 1,
            "debug": 1,
            "warn": 1
        }
        assert stats["by_service"] == {"api": 5}
        assert stats["errors_by_service"] == {"api": 1}  # Only ERROR level

    def test_multiple_services(self):
        """Test statistics across multiple services."""
        logs = [
            {"service": "api-gateway", "level": "INFO", "message": "API call"},
            {"service": "api-gateway", "level": "ERROR", "message": "API error"},
            {"service": "database", "level": "INFO", "message": "DB query"},
            {"service": "database", "level": "INFO", "message": "DB query 2"},
            {"service": "database", "level": "ERROR", "message": "DB connection failed"},
            {"service": "cache", "level": "INFO", "message": "Cache hit"},
        ]

        stats = calculate_log_statistics(logs)

        assert stats["count"] == 6
        assert stats["by_level"] == {"info": 4, "error": 2}
        assert stats["by_service"] == {
            "api-gateway": 2,
            "database": 3,
            "cache": 1
        }
        assert stats["errors_by_service"] == {
            "api-gateway": 1,
            "database": 1
        }

        # Check top services (should be sorted by count descending)
        expected_top = [
            ("database", 3),
            ("api-gateway", 2),
            ("cache", 1)
        ]
        assert stats["top_services"] == expected_top

    def test_case_insensitive_levels(self):
        """Test that log levels are handled case-insensitively."""
        logs = [
            {"service": "test", "level": "info", "message": "Lowercase"},
            {"service": "test", "level": "INFO", "message": "Uppercase"},
            {"service": "test", "level": "Info", "message": "Mixed case"},
            {"service": "test", "level": "ERROR", "message": "Error case"},
            {"service": "test", "level": "error", "message": "Error lowercase"},
        ]

        stats = calculate_log_statistics(logs)

        assert stats["by_level"] == {"info": 3, "error": 2}
        assert stats["errors_by_service"] == {"test": 2}

    def test_missing_fields(self):
        """Test handling of logs with missing fields."""
        logs = [
            {"service": "service1", "level": "INFO"},  # Missing message
            {"service": "service1", "message": "No level"},  # Missing level
            {"level": "INFO", "message": "No service"},  # Missing service
            {"service": "service2", "level": "ERROR", "message": "Complete"},  # Complete
        ]

        stats = calculate_log_statistics(logs)

        assert stats["count"] == 4
        assert stats["by_level"] == {"info": 2, "": 1, "error": 1}  # Empty string for missing level
        assert stats["by_service"] == {"service1": 2, "": 1, "service2": 1}  # Empty string for missing service
        assert stats["errors_by_service"] == {"service2": 1}  # Only actual errors

    def test_fatal_level_treated_as_error(self):
        """Test that FATAL level is treated as an error."""
        logs = [
            {"service": "critical-service", "level": "FATAL", "message": "System crash"},
            {"service": "normal-service", "level": "ERROR", "message": "Normal error"},
            {"service": "normal-service", "level": "INFO", "message": "Normal info"},
        ]

        stats = calculate_log_statistics(logs)

        assert stats["by_level"] == {"fatal": 1, "error": 1, "info": 1}
        assert stats["errors_by_service"] == {
            "critical-service": 1,  # FATAL counts as error
            "normal-service": 1     # ERROR counts as error
        }

    def test_top_services_limit(self):
        """Test that top services is limited to 5 services."""
        # Create logs for 7 different services
        logs = []
        for i in range(7):
            for j in range(i + 1):  # service0: 1 log, service1: 2 logs, etc.
                logs.append({
                    "service": f"service{i}",
                    "level": "INFO",
                    "message": f"Message {j} for service {i}"
                })

        stats = calculate_log_statistics(logs)

        # Should have top 5 services only
        assert len(stats["top_services"]) == 5

        # Should be sorted by count descending
        expected_counts = [7, 6, 5, 4, 3]  # Top 5 services by log count
        actual_counts = [count for _, count in stats["top_services"]]
        assert actual_counts == expected_counts

        # Should include services 6, 5, 4, 3, 2 (highest counts)
        expected_services = ["service6", "service5", "service4", "service3", "service2"]
        actual_services = [service for service, _ in stats["top_services"]]
        assert actual_services == expected_services

    def test_large_dataset(self):
        """Test performance and correctness with a larger dataset."""
        # Generate 1000 logs across 10 services with various levels
        import random

        services = [f"service{i}" for i in range(10)]
        levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]

        logs = []
        for i in range(1000):
            logs.append({
                "service": random.choice(services),
                "level": random.choice(levels),
                "message": f"Log message {i}",
                "timestamp": f"2024-01-15T10:30:{i:04d}.000000+00:00"
            })

        stats = calculate_log_statistics(logs)

        # Basic validations
        assert stats["count"] == 1000
        assert len(stats["by_level"]) <= 5  # Should have all levels we used
        assert len(stats["by_service"]) == 10  # All 10 services
        assert sum(stats["by_level"].values()) == 1000
        assert sum(stats["by_service"].values()) == 1000
        assert len(stats["top_services"]) == 5  # Limited to top 5
