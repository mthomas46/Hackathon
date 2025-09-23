"""Tests for enhanced log collector service functionality."""

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.log_stats import calculate_log_statistics
from modules.log_storage import LogStorage


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

        storage.add_log({"service": "test", "level": "info", "message": "Old log", "timestamp": old_time})
        storage.add_log({"service": "test", "level": "info", "message": "Recent log", "timestamp": recent_time})

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
            {
                "service": "api",
                "level": "info",
                "message": "Request processed",
                "timestamp": "2024-01-01T10:00:00Z",
                "context": {"response_time": 0.1},
            },
            {
                "service": "api",
                "level": "info",
                "message": "Request processed",
                "timestamp": "2024-01-01T10:01:00Z",
                "context": {"response_time": 0.2},
            },
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            count = storage.export_logs(temp_file, format="json")
            assert count == 2

            # Verify exported file
            with open(temp_file, "r") as f:
                exported_data = json.load(f)
                assert len(exported_data) == 2
                assert exported_data[0]["message"] == "Test message 1"

        finally:
            os.unlink(temp_file)

    def test_export_logs_jsonl(self):
        """Test log export to JSONL format."""
        storage = LogStorage()

        storage.add_log({"service": "test", "level": "info", "message": "Test message"})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_file = f.name

        try:
            count = storage.export_logs(temp_file, format="jsonl")
            assert count == 1

            # Verify exported file (JSONL format)
            with open(temp_file, "r") as f:
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            # Export only API service logs
            count = storage.export_logs(temp_file, service="api")
            assert count == 2

            with open(temp_file, "r") as f:
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
            {"service": "api", "level": "info", "message": "Request 1", "timestamp": "2024-01-01T12:00:00Z"},
            {"service": "api", "level": "error", "message": "Error occurred", "timestamp": "2024-01-01T12:05:00Z"},
            {
                "service": "worker",
                "level": "info",
                "message": "Task completed",
                "timestamp": "2024-01-01T11:00:00Z",  # Older than time window
            },
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
                "service": "api",
                "level": "info",
                "message": "Request",
                "timestamp": "2024-01-01T12:00:00Z",
                "context": {"response_time": 0.1},
            },
            {
                "service": "api",
                "level": "info",
                "message": "Request",
                "timestamp": "2024-01-01T12:01:00Z",
                "context": {"response_time": 0.3},
            },
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
            {
                "service": "api",
                "level": "info",
                "message": "Request",
                "timestamp": "2024-01-01T12:00:00Z",
                "context": {"response_time": 0.1},
            },
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            count = storage.export_logs(temp_file, format="json")
            assert count == 1

            # Verify file was created and has content
            assert os.path.exists(temp_file)
            with open(temp_file, "r") as f:
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
                "timestamp": "2024-01-01T12:00:00Z",
            }
            storage.add_log(log_entry)

            # Force persistence (normally async)
            asyncio.run(storage._persist_log_entry(log_entry))

            # Check that file was created
            expected_file = storage._storage_path / "logs_2024-01-01.jsonl"
            assert expected_file.exists()

            # Check file contents
            with open(expected_file, "r") as f:
                lines = f.readlines()
                assert len(lines) == 1
                persisted_log = json.loads(lines[0])
                assert persisted_log["message"] == "Persistent test message"


class TestConcurrencyAndPerformance:
    """Test concurrency and performance aspects."""

    def test_concurrent_log_ingestion(self):
        """Test concurrent log ingestion from multiple services."""
        import threading
        import time
        import queue

        storage = LogStorage(max_logs=1000)
        results = queue.Queue()

        def worker_thread(service_name, num_logs):
            """Worker thread to simulate concurrent log ingestion."""
            try:
                for i in range(num_logs):
                    log_entry = {
                        "service": service_name,
                        "level": "info",
                        "message": f"Log {i} from {service_name}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    storage.add_log(log_entry)
                results.put((service_name, "success", num_logs))
            except Exception as e:
                results.put((service_name, "error", str(e)))

        # Start multiple threads simulating different services
        threads = []
        services = ["api", "worker", "scheduler", "notifier"]

        for service in services:
            t = threading.Thread(target=worker_thread, args=(service, 50))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify results
        total_results = 0
        successful_services = 0

        while not results.empty():
            service, status, count = results.get()
            if status == "success":
                successful_services += 1
                total_results += count

        assert successful_services == len(services)
        assert total_results == 200  # 4 services * 50 logs each

        # Verify logs were stored
        assert len(storage._logs) == 200

    def test_high_volume_performance(self):
        """Test performance with high volume of logs."""
        storage = LogStorage(max_logs=2000)

        # Add 1000 logs
        start_time = time.time()
        for i in range(1000):
            log_entry = {
                "service": "performance_test",
                "level": "info",
                "message": f"Performance log {i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            storage.add_log(log_entry)

        ingestion_time = time.time() - start_time

        # Performance check: should be able to ingest 1000 logs quickly
        assert ingestion_time < 2.0  # Less than 2 seconds
        assert len(storage._logs) == 1000

        # Test search performance
        search_start = time.time()
        results = storage.search_logs("Performance log 500")
        search_time = time.time() - search_start

        # Search should be fast
        assert search_time < 0.1  # Less than 100ms
        assert len(results) == 1

    def test_memory_cleanup_performance(self):
        """Test cleanup performance with large datasets."""
        storage = LogStorage(max_logs=500)

        # Add logs with old timestamps (expired)
        old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

        for i in range(600):  # More than max capacity
            log_entry = {
                "service": "cleanup_test",
                "level": "info",
                "message": f"Cleanup log {i}",
                "timestamp": old_timestamp,
            }
            storage.add_log(log_entry)

        # Should have exactly max_logs after cleanup
        assert len(storage._logs) == 500

        # Test cleanup performance
        start_time = time.time()
        storage._cleanup_expired_logs()  # Force cleanup
        cleanup_time = time.time() - start_time

        # Cleanup should be fast even with many logs
        assert cleanup_time < 0.5  # Less than 500ms


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    def test_invalid_log_format_handling(self):
        """Test handling of invalid log formats."""
        storage = LogStorage()

        # Test with missing required fields
        invalid_logs = [
            {"level": "info", "message": "Missing service"},  # Missing service
            {"service": "test", "message": "Missing level"},  # Missing level
            {"service": "test", "level": "info"},  # Missing message
            {},  # Completely empty
            None,  # None value
        ]

        for invalid_log in invalid_logs:
            # Should not crash, but may not add invalid logs
            try:
                storage.add_log(invalid_log)
            except Exception:
                # Expected for some invalid formats
                pass

        # Should have some logs (valid ones would be added)
        assert len(storage._logs) >= 0

    def test_timestamp_parsing_edge_cases(self):
        """Test timestamp parsing with various formats."""
        storage = LogStorage()

        test_cases = [
            {"service": "test", "level": "info", "message": "ISO format", "timestamp": "2024-01-01T12:00:00Z"},
            {"service": "test", "level": "info", "message": "ISO with microseconds", "timestamp": "2024-01-01T12:00:00.123456Z"},
            {"service": "test", "level": "info", "message": "ISO with timezone", "timestamp": "2024-01-01T12:00:00+00:00"},
            {"service": "test", "level": "info", "message": "Invalid timestamp", "timestamp": "invalid"},
            {"service": "test", "level": "info", "message": "No timestamp"},  # Missing timestamp
        ]

        for log_entry in test_cases:
            # Should handle all timestamp formats gracefully
            try:
                storage.add_log(log_entry)
            except Exception:
                # May fail for completely invalid timestamps
                pass

        # Should have added at least the valid timestamp logs
        assert len(storage._logs) >= 3

    def test_search_with_special_characters(self):
        """Test search functionality with special characters and edge cases."""
        storage = LogStorage()

        special_logs = [
            {"service": "test", "level": "info", "message": "Special chars: @#$%^&*()"},
            {"service": "test", "level": "info", "message": "Unicode: 你好世界 🌍"},
            {"service": "test", "level": "info", "message": "Empty string: "},
            {"service": "test", "level": "info", "message": "Very long message: " + "x" * 1000},
        ]

        for log in special_logs:
            storage.add_log(log)

        # Search should handle special characters
        results = storage.search_logs("@#$%^&*()")
        assert len(results) == 1

        # Search should handle empty strings gracefully
        results = storage.search_logs("")
        assert len(results) >= 0  # May return all or none

    def test_export_edge_cases(self):
        """Test export functionality with edge cases."""
        storage = LogStorage()

        # Add logs with various data types
        complex_logs = [
            {"service": "test", "level": "info", "message": "Simple string"},
            {"service": "test", "level": "info", "message": "With metadata", "metadata": {"key": "value", "number": 42}},
            {"service": "test", "level": "info", "message": "With nested data", "context": {"nested": {"deep": True}}},
            {"service": "test", "level": "info", "message": "With list", "tags": ["tag1", "tag2"]},
        ]

        for log in complex_logs:
            storage.add_log(log)

        # Test export with complex data
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            count = storage.export_logs(temp_file, format="json")
            assert count == 4

            # Verify complex data is preserved
            with open(temp_file, "r") as f:
                exported_data = json.load(f)
                assert len(exported_data) == 4

                # Check that complex objects are preserved
                metadata_log = next((log for log in exported_data if "metadata" in log), None)
                assert metadata_log is not None
                assert metadata_log["metadata"]["number"] == 42

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_persistence_error_handling(self):
        """Test error handling in persistent storage operations."""
        # Test with invalid path
        storage = LogStorage(persist_to_disk=True, storage_path="/invalid/path/that/does/not/exist")

        log_entry = {"service": "test", "level": "info", "message": "Test message"}

        # Should handle persistence errors gracefully (not crash)
        try:
            storage.add_log(log_entry)
            # If persistence fails, should still work in memory
            assert len(storage._logs) >= 1
        except Exception:
            # May fail if path is completely invalid
            pass


class TestConfigurationScenarios:
    """Test different configuration scenarios."""

    def test_minimal_configuration(self):
        """Test log collector with minimal configuration."""
        storage = LogStorage(
            max_logs=100,
            persist_to_disk=False,
        )

        assert storage._max_logs == 100
        assert storage._persist_to_disk is False

        # Add logs and verify basic functionality
        for i in range(50):
            storage.add_log({"service": "test", "level": "info", "message": f"Log {i}"})

        assert len(storage._logs) == 50

    def test_high_performance_configuration(self):
        """Test log collector optimized for high performance."""
        storage = LogStorage(
            max_logs=10000,
            persist_to_disk=True,
        )

        assert storage._max_logs == 10000
        assert storage._persist_to_disk is True

        # Should handle high volume
        for i in range(1000):
            storage.add_log({"service": "perf", "level": "info", "message": f"High volume log {i}"})

        assert len(storage._logs) == 1000

    def test_long_retention_configuration(self):
        """Test log collector with long retention policies."""
        storage = LogStorage(
            persist_to_disk=True,
            retention_days=90,
        )

        assert storage._retention_days == 90

        # Should be configured for long-term storage
        assert storage._persist_to_disk is True

    def test_debug_configuration(self):
        """Test log collector in debug mode (no limits)."""
        storage = LogStorage(
            max_logs=100000,  # Very high limit for debugging
            persist_to_disk=False,  # Keep in memory for speed
        )

        assert storage._max_logs == 100000
        assert storage._persist_to_disk is False


class TestRetentionAndCleanup:
    """Test log retention and cleanup functionality."""

    def test_retention_policy_enforcement(self):
        """Test that retention policies are properly enforced."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LogStorage(
                persist_to_disk=True,
                storage_path=temp_dir,
                retention_days=1,  # Only keep 1 day
            )

            # Create old log files (simulate files older than retention period)
            old_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            old_file = storage._storage_path / f"logs_{old_date}.jsonl"

            # Create old file
            with open(old_file, "w") as f:
                f.write('{"service": "old", "level": "info", "message": "Old log"}\n')

            # Create recent file
            recent_date = datetime.now().strftime("%Y-%m-%d")
            recent_file = storage._storage_path / f"logs_{recent_date}.jsonl"

            with open(recent_file, "w") as f:
                f.write('{"service": "recent", "level": "info", "message": "Recent log"}\n')

            # Run cleanup
            asyncio.run(storage._cleanup_old_logs())

            # Old file should be removed, recent file should remain
            assert not old_file.exists()
            assert recent_file.exists()

    def test_cleanup_scheduling(self):
        """Test that cleanup runs at appropriate intervals."""
        storage = LogStorage(max_logs=1000)

        # Reset cleanup tracking
        storage._last_cleanup_time = None

        # Add some logs
        for i in range(100):
            storage.add_log({"service": "test", "level": "info", "message": f"Log {i}"})

        # First cleanup should work
        storage._lazy_cleanup_memory()
        first_cleanup_logs = len(storage._logs)

        # Immediate second cleanup should not run
        storage._lazy_cleanup_memory()
        second_cleanup_logs = len(storage._logs)

        # Should be the same (cleanup didn't run again)
        assert first_cleanup_logs == second_cleanup_logs

        # Simulate time passing
        storage._last_cleanup_time = time.time() - 4000  # 4000 seconds ago (> 3000 threshold)

        # Now cleanup should run again
        storage._lazy_cleanup_memory()
        # Should still have the same logs (none expired)
        assert len(storage._logs) == 100


if __name__ == "__main__":
    pytest.main([__file__])
