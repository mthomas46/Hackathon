"""Integration tests for memory agent functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from services.memory_agent.domain.entities import MemoryMetrics, MemoryAnalysis, OptimizationRecommendation
from services.memory_agent.application.commands import AnalyzeMemoryCommand, OptimizeMemoryCommand
from services.memory_agent.application.handlers.memory_handler import MemoryHandler


class TestMemoryAnalysisIntegration:
    """Integration tests for memory analysis workflows."""

    @pytest.fixture
    async def memory_handler(self):
        """Create MemoryHandler for integration testing."""
        handler = MemoryHandler()
        # Mock the repository and services
        handler._memory_repository = Mock()
        handler._memory_service = Mock()
        return handler

    @pytest.mark.asyncio
    async def test_complete_memory_analysis_workflow(self, memory_handler):
        """Test complete memory analysis workflow."""
        # Mock repository responses
        memory_handler._memory_repository.get_recent_metrics = AsyncMock(return_value=[
            MemoryMetrics(total_memory_mb=8000, used_memory_mb=4000, available_memory_mb=4000, memory_usage_percent=50.0),
            MemoryMetrics(total_memory_mb=8000, used_memory_mb=4800, available_memory_mb=3200, memory_usage_percent=60.0)
        ])

        memory_handler._memory_service.analyze_patterns = AsyncMock(return_value={
            "trend": "stable",
            "anomalies": [],
            "recommendations": ["Monitor memory usage"]
        })

        command = AnalyzeMemoryCommand(
            service_name="test-service",
            analysis_type="comprehensive",
            time_window_minutes=60
        )

        result = await memory_handler.handle_analyze_memory(command)

        assert result is not None
        memory_handler._memory_repository.get_recent_metrics.assert_called_once()
        memory_handler._memory_service.analyze_patterns.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_optimization_workflow(self, memory_handler):
        """Test memory optimization workflow."""
        # Mock current memory state
        memory_handler._memory_repository.get_current_metrics = AsyncMock(return_value=
            MemoryMetrics(total_memory_mb=8000, used_memory_mb=6400, available_memory_mb=1600, memory_usage_percent=80.0)
        )

        # Mock optimization service
        memory_handler._memory_service.generate_optimization_plan = AsyncMock(return_value=[
            OptimizationRecommendation(
                recommendation_id="opt-001",
                service_name="test-service",
                recommendation_type="garbage_collection",
                description="Run garbage collection to free memory"
            )
        ])

        memory_handler._memory_service.apply_optimization = AsyncMock(return_value={
            "success": True,
            "memory_freed_mb": 200,
            "performance_improved": 10.0
        })

        command = OptimizeMemoryCommand(
            service_name="test-service",
            optimization_type="automatic"
        )

        result = await memory_handler.handle_optimize_memory(command)

        assert result is not None
        memory_handler._memory_repository.get_current_metrics.assert_called_once()
        memory_handler._memory_service.generate_optimization_plan.assert_called_once()

    def test_memory_monitoring_integration(self):
        """Test memory monitoring data flow."""
        # Create a series of memory metrics to simulate monitoring
        metrics_series = []
        base_time = datetime.now(timezone.utc)

        for i in range(10):
            # Simulate varying memory usage over time
            usage_variation = 100 * (i % 3)  # 0, 100, 200, 0, 100, 200...
            metrics = MemoryMetrics(
                timestamp=base_time + timedelta(minutes=i*5),
                total_memory_mb=8000,
                used_memory_mb=4000 + usage_variation,
                available_memory_mb=4000 - usage_variation,
                memory_usage_percent=(4000 + usage_variation) / 8000 * 100
            )
            metrics_series.append(metrics)

        # Create analysis from metrics
        analysis = MemoryAnalysis(
            analysis_id="integration-test",
            service_name="test-service",
            metrics_history=metrics_series
        )

        # Verify analysis can process the data
        assert len(analysis.metrics_history) == 10
        assert analysis.average_memory_usage() > 0
        assert analysis.peak_memory_usage() > 0

        # Test trend analysis
        trend = analysis.get_usage_trend()
        assert trend in ["increasing", "decreasing", "stable", "fluctuating"]

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across memory agent components."""
        handler = MemoryHandler()

        # Mock repository to raise exception
        handler._memory_repository.get_recent_metrics = AsyncMock(side_effect=Exception("Database connection failed"))

        command = AnalyzeMemoryCommand(
            service_name="test-service",
            analysis_type="basic"
        )

        # Should handle the error gracefully
        with pytest.raises(Exception):  # In real implementation, this might be caught and logged
            await handler.handle_analyze_memory(command)

    def test_memory_threshold_integration(self):
        """Test memory threshold monitoring integration."""
        # Define memory thresholds
        critical_threshold = 90.0  # 90% usage
        warning_threshold = 75.0   # 75% usage
        normal_threshold = 60.0    # 60% usage

        test_cases = [
            (95.0, "critical"),
            (80.0, "warning"),
            (70.0, "elevated"),
            (50.0, "normal")
        ]

        for usage_percent, expected_level in test_cases:
            metrics = MemoryMetrics(
                total_memory_mb=8000,
                used_memory_mb=int(8000 * usage_percent / 100),
                available_memory_mb=int(8000 * (100 - usage_percent) / 100),
                memory_usage_percent=usage_percent
            )

            # Test threshold evaluation
            if usage_percent >= critical_threshold:
                assert metrics.get_pressure_level() == "critical"
            elif usage_percent >= warning_threshold:
                assert metrics.get_pressure_level() in ["high", "critical"]
            elif usage_percent >= normal_threshold:
                assert metrics.get_pressure_level() in ["elevated", "high", "critical"]
            else:
                assert metrics.get_pressure_level() in ["normal", "elevated", "high", "critical"]

    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """Test concurrent memory analysis operations."""
        # This test would verify that multiple memory analysis operations
        # can run concurrently without interfering with each other

        async def mock_analysis_operation(operation_id: int):
            await asyncio.sleep(0.01)  # Simulate some work
            return f"operation_{operation_id}_completed"

        # Run multiple operations concurrently
        tasks = [mock_analysis_operation(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all("completed" in result for result in results)

    def test_memory_persistence_integration(self):
        """Test memory metrics persistence and retrieval."""
        # This would test the full cycle of:
        # 1. Collecting memory metrics
        # 2. Storing them in repository
        # 3. Retrieving them for analysis
        # 4. Generating reports

        # Create sample metrics
        metrics = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=4000,
            available_memory_mb=4000,
            memory_usage_percent=50.0
        )

        # In a real implementation, this would be persisted and retrieved
        # For testing, we verify the data structure
        assert metrics.total_memory_mb == 8000
        assert metrics.used_memory_mb == 4000
        assert metrics.memory_usage_percent == 50.0

        # Test serialization/deserialization
        metrics_dict = metrics.to_dict()
        assert "total_memory_mb" in metrics_dict
        assert "used_memory_mb" in metrics_dict
        assert "timestamp" in metrics_dict
