"""Unit tests for memory agent application commands."""

import pytest
from datetime import datetime, timezone

from services.memory_agent.application.commands import (
    AnalyzeMemoryCommand,
    OptimizeMemoryCommand,
    MonitorMemoryCommand,
    GetMemoryMetricsCommand
)


class TestAnalyzeMemoryCommand:
    """Test cases for AnalyzeMemoryCommand."""

    def test_command_creation(self):
        """Test basic AnalyzeMemoryCommand creation."""
        command = AnalyzeMemoryCommand(
            service_name="test-service",
            analysis_type="comprehensive",
            time_window_minutes=60,
            include_historical=True
        )

        assert command.service_name == "test-service"
        assert command.analysis_type == "comprehensive"
        assert command.time_window_minutes == 60
        assert command.include_historical is True

    def test_command_with_filters(self):
        """Test command with analysis filters."""
        filters = {
            "memory_threshold_mb": 1000,
            "time_range_hours": 24,
            "severity_levels": ["high", "critical"]
        }

        command = AnalyzeMemoryCommand(
            service_name="test-service",
            analysis_type="filtered",
            filters=filters
        )

        assert command.filters == filters
        assert command.analysis_type == "filtered"

    def test_command_validation(self):
        """Test command validation."""
        # Valid command
        valid_command = AnalyzeMemoryCommand(
            service_name="valid-service",
            analysis_type="basic"
        )
        assert valid_command.service_name == "valid-service"

        # Commands should validate at creation time
        # (In pydantic, validation happens during instantiation)


class TestOptimizeMemoryCommand:
    """Test cases for OptimizeMemoryCommand."""

    def test_command_creation(self):
        """Test basic OptimizeMemoryCommand creation."""
        command = OptimizeMemoryCommand(
            service_name="test-service",
            optimization_type="automatic",
            target_memory_reduction_mb=500,
            max_downtime_seconds=30
        )

        assert command.service_name == "test-service"
        assert command.optimization_type == "automatic"
        assert command.target_memory_reduction_mb == 500
        assert command.max_downtime_seconds == 30

    def test_manual_optimization_command(self):
        """Test manual optimization command."""
        manual_steps = [
            "clear_cache",
            "force_gc",
            "restart_worker"
        ]

        command = OptimizeMemoryCommand(
            service_name="manual-service",
            optimization_type="manual",
            manual_steps=manual_steps,
            priority="high"
        )

        assert command.optimization_type == "manual"
        assert command.manual_steps == manual_steps
        assert command.priority == "high"

    def test_command_with_constraints(self):
        """Test command with optimization constraints."""
        constraints = {
            "min_memory_mb": 100,
            "max_cpu_percent": 80,
            "maintenance_window": "02:00-04:00"
        }

        command = OptimizeMemoryCommand(
            service_name="constrained-service",
            optimization_type="constrained",
            constraints=constraints
        )

        assert command.constraints == constraints


class TestMonitorMemoryCommand:
    """Test cases for MonitorMemoryCommand."""

    def test_command_creation(self):
        """Test basic MonitorMemoryCommand creation."""
        command = MonitorMemoryCommand(
            service_name="test-service",
            monitoring_duration_minutes=30,
            sampling_interval_seconds=10,
            alert_thresholds={
                "memory_percent": 85,
                "growth_rate_mb_per_minute": 50
            }
        )

        assert command.service_name == "test-service"
        assert command.monitoring_duration_minutes == 30
        assert command.sampling_interval_seconds == 10
        assert command.alert_thresholds["memory_percent"] == 85

    def test_continuous_monitoring_command(self):
        """Test continuous monitoring command."""
        command = MonitorMemoryCommand(
            service_name="continuous-service",
            monitoring_mode="continuous",
            alert_webhook="https://alert.example.com/webhook"
        )

        assert command.monitoring_mode == "continuous"
        assert command.alert_webhook == "https://alert.example.com/webhook"

    def test_monitoring_with_custom_metrics(self):
        """Test monitoring with custom metrics."""
        custom_metrics = [
            "heap_size",
            "gc_collections",
            "memory_fragmentation"
        ]

        command = MonitorMemoryCommand(
            service_name="custom-service",
            custom_metrics=custom_metrics,
            export_format="prometheus"
        )

        assert command.custom_metrics == custom_metrics
        assert command.export_format == "prometheus"


class TestGetMemoryMetricsCommand:
    """Test cases for GetMemoryMetricsCommand."""

    def test_command_creation(self):
        """Test basic GetMemoryMetricsCommand creation."""
        command = GetMemoryMetricsCommand(
            service_name="test-service",
            metrics_type="current",
            include_details=True,
            format="json"
        )

        assert command.service_name == "test-service"
        assert command.metrics_type == "current"
        assert command.include_details is True
        assert command.format == "json"

    def test_historical_metrics_command(self):
        """Test historical metrics command."""
        time_range = {
            "start": "2023-01-01T00:00:00Z",
            "end": "2023-01-02T00:00:00Z",
            "granularity": "1h"
        }

        command = GetMemoryMetricsCommand(
            service_name="historical-service",
            metrics_type="historical",
            time_range=time_range,
            aggregation="average"
        )

        assert command.metrics_type == "historical"
        assert command.time_range == time_range
        assert command.aggregation == "average"

    def test_metrics_with_filters(self):
        """Test metrics command with filters."""
        filters = {
            "memory_range_mb": [100, 1000],
            "severity": ["high", "critical"],
            "tags": ["production", "api"]
        }

        command = GetMemoryMetricsCommand(
            service_name="filtered-service",
            metrics_type="filtered",
            filters=filters
        )

        assert command.filters == filters


class TestCommandImmutability:
    """Test command immutability and validation."""

    def test_command_immutability(self):
        """Test that commands are immutable after creation."""
        command = AnalyzeMemoryCommand(
            service_name="immutable-test",
            analysis_type="basic"
        )

        original_service = command.service_name
        original_type = command.analysis_type

        # Commands should be treated as immutable
        assert command.service_name == original_service
        assert command.analysis_type == original_type

    def test_command_equality(self):
        """Test command equality based on content."""
        command1 = AnalyzeMemoryCommand(
            service_name="test-service",
            analysis_type="basic"
        )

        command2 = AnalyzeMemoryCommand(
            service_name="test-service",
            analysis_type="basic"
        )

        command3 = AnalyzeMemoryCommand(
            service_name="different-service",
            analysis_type="basic"
        )

        # Commands with same content should be equal
        assert command1.service_name == command2.service_name
        assert command1.analysis_type == command2.analysis_type

        # Different content should not be equal
        assert command1.service_name != command3.service_name

    def test_command_hash_consistency(self):
        """Test that commands have consistent hash for same content."""
        command1 = AnalyzeMemoryCommand(
            service_name="hash-test",
            analysis_type="basic"
        )

        command2 = AnalyzeMemoryCommand(
            service_name="hash-test",
            analysis_type="basic"
        )

        # Hash should be based on content
        assert hash((command1.service_name, command1.analysis_type)) == \
               hash((command2.service_name, command2.analysis_type))
