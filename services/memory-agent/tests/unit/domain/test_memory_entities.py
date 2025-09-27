"""Unit tests for memory agent domain entities."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from services.memory_agent.domain.entities import MemoryMetrics, MemoryAnalysis, OptimizationRecommendation


class TestMemoryMetrics:
    """Test cases for MemoryMetrics entity."""

    def test_memory_metrics_creation(self):
        """Test basic MemoryMetrics creation."""
        metrics = MemoryMetrics(
            total_memory_mb=8192,
            used_memory_mb=4096,
            available_memory_mb=4096,
            memory_usage_percent=50.0,
            swap_total_mb=2048,
            swap_used_mb=512,
            swap_usage_percent=25.0
        )

        assert metrics.total_memory_mb == 8192
        assert metrics.used_memory_mb == 4096
        assert metrics.memory_usage_percent == 50.0
        assert isinstance(metrics.timestamp, datetime)

    def test_memory_metrics_calculations(self):
        """Test memory metrics calculations."""
        metrics = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=6000,
            available_memory_mb=2000,
            memory_usage_percent=75.0
        )

        assert metrics.memory_usage_percent == 75.0
        assert metrics.is_high_usage() is True
        assert metrics.is_low_usage() is False

    def test_memory_pressure_detection(self):
        """Test memory pressure detection."""
        # High pressure
        high_pressure = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=7200,  # 90% usage
            available_memory_mb=800,
            memory_usage_percent=90.0
        )
        assert high_pressure.get_pressure_level() == "critical"

        # Medium pressure
        medium_pressure = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=5600,  # 70% usage
            available_memory_mb=2400,
            memory_usage_percent=70.0
        )
        assert medium_pressure.get_pressure_level() == "high"

        # Normal pressure
        normal_pressure = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=3200,  # 40% usage
            available_memory_mb=4800,
            memory_usage_percent=40.0
        )
        assert normal_pressure.get_pressure_level() == "normal"


class TestMemoryAnalysis:
    """Test cases for MemoryAnalysis entity."""

    def test_memory_analysis_creation(self):
        """Test basic MemoryAnalysis creation."""
        analysis = MemoryAnalysis(
            analysis_id="test-analysis-001",
            service_name="test-service",
            analysis_type="comprehensive",
            time_window_minutes=60
        )

        assert analysis.analysis_id == "test-analysis-001"
        assert analysis.service_name == "test-service"
        assert analysis.analysis_type == "comprehensive"
        assert analysis.time_window_minutes == 60
        assert isinstance(analysis.start_time, datetime)
        assert analysis.status == "pending"

    def test_memory_analysis_with_metrics(self):
        """Test MemoryAnalysis with metrics data."""
        metrics = [
            MemoryMetrics(total_memory_mb=8000, used_memory_mb=4000, available_memory_mb=4000, memory_usage_percent=50.0),
            MemoryMetrics(total_memory_mb=8000, used_memory_mb=4800, available_memory_mb=3200, memory_usage_percent=60.0)
        ]

        analysis = MemoryAnalysis(
            analysis_id="test-analysis-002",
            service_name="test-service",
            metrics_history=metrics
        )

        assert len(analysis.metrics_history) == 2
        assert analysis.average_memory_usage() == 55.0  # (50 + 60) / 2
        assert analysis.peak_memory_usage() == 60.0

    def test_memory_analysis_insights(self):
        """Test memory analysis insights generation."""
        # Create analysis with memory leak pattern
        metrics = []
        base_usage = 1000
        for i in range(10):
            # Simulate memory leak - gradual increase
            usage = base_usage + (i * 50)  # 1000, 1050, 1100, ...
            metrics.append(MemoryMetrics(
                total_memory_mb=8000,
                used_memory_mb=usage,
                available_memory_mb=8000 - usage,
                memory_usage_percent=(usage / 8000) * 100
            ))

        analysis = MemoryAnalysis(
            analysis_id="leak-analysis",
            service_name="test-service",
            metrics_history=metrics
        )

        insights = analysis.generate_insights()
        assert "potential_memory_leak" in insights
        assert insights["potential_memory_leak"] is True

    def test_memory_analysis_trends(self):
        """Test memory usage trend analysis."""
        # Stable usage
        stable_metrics = [
            MemoryMetrics(total_memory_mb=8000, used_memory_mb=4000, available_memory_mb=4000, memory_usage_percent=50.0)
            for _ in range(5)
        ]

        stable_analysis = MemoryAnalysis(
            analysis_id="stable-analysis",
            service_name="test-service",
            metrics_history=stable_metrics
        )

        assert stable_analysis.get_usage_trend() == "stable"

        # Increasing usage
        increasing_metrics = [
            MemoryMetrics(total_memory_mb=8000, used_memory_mb=4000 + i*200, available_memory_mb=4000 - i*200, memory_usage_percent=50.0 + i*2.5)
            for i in range(5)
        ]

        increasing_analysis = MemoryAnalysis(
            analysis_id="increasing-analysis",
            service_name="test-service",
            metrics_history=increasing_metrics
        )

        assert increasing_analysis.get_usage_trend() == "increasing"


class TestOptimizationRecommendation:
    """Test cases for OptimizationRecommendation entity."""

    def test_optimization_recommendation_creation(self):
        """Test basic OptimizationRecommendation creation."""
        recommendation = OptimizationRecommendation(
            recommendation_id="opt-rec-001",
            service_name="test-service",
            recommendation_type="memory_optimization",
            priority="high",
            description="Reduce memory usage by implementing object pooling"
        )

        assert recommendation.recommendation_id == "opt-rec-001"
        assert recommendation.service_name == "test-service"
        assert recommendation.recommendation_type == "memory_optimization"
        assert recommendation.priority == "high"
        assert recommendation.status == "pending"

    def test_recommendation_with_metrics(self):
        """Test recommendation with expected impact metrics."""
        recommendation = OptimizationRecommendation(
            recommendation_id="opt-rec-002",
            service_name="test-service",
            recommendation_type="garbage_collection",
            expected_memory_savings_mb=500,
            expected_performance_improvement_percent=15.0,
            implementation_effort_hours=4
        )

        assert recommendation.expected_memory_savings_mb == 500
        assert recommendation.expected_performance_improvement_percent == 15.0
        assert recommendation.implementation_effort_hours == 4

    def test_recommendation_lifecycle(self):
        """Test recommendation status lifecycle."""
        recommendation = OptimizationRecommendation(
            recommendation_id="lifecycle-test",
            service_name="test-service",
            recommendation_type="caching"
        )

        # Initial state
        assert recommendation.status == "pending"
        assert recommendation.implemented_at is None

        # Mark as implemented
        recommendation.mark_implemented()
        assert recommendation.status == "implemented"
        assert recommendation.implemented_at is not None

        # Mark as evaluated
        recommendation.mark_evaluated(actual_savings_mb=300, success=True)
        assert recommendation.status == "evaluated"
        assert recommendation.actual_memory_savings_mb == 300
        assert recommendation.success is True

    def test_recommendation_priority_scoring(self):
        """Test recommendation priority scoring."""
        high_priority = OptimizationRecommendation(
            recommendation_id="high-pri",
            service_name="test-service",
            priority="high",
            expected_memory_savings_mb=1000,
            implementation_effort_hours=2
        )

        medium_priority = OptimizationRecommendation(
            recommendation_id="med-pri",
            service_name="test-service",
            priority="medium",
            expected_memory_savings_mb=500,
            implementation_effort_hours=8
        )

        # High priority should have higher impact score
        assert high_priority.get_impact_score() > medium_priority.get_impact_score()

    def test_recommendation_cost_benefit_analysis(self):
        """Test cost-benefit analysis for recommendations."""
        recommendation = OptimizationRecommendation(
            recommendation_id="cost-benefit-test",
            service_name="test-service",
            expected_memory_savings_mb=1000,
            expected_performance_improvement_percent=20.0,
            implementation_effort_hours=8
        )

        # Assuming some cost per hour, calculate ROI
        hourly_cost = 50  # $50/hour
        implementation_cost = recommendation.implementation_effort_hours * hourly_cost

        # Memory savings over a year (rough estimate)
        annual_memory_cost_savings = recommendation.expected_memory_savings_mb * 0.01  # $0.01 per MB per year

        assert implementation_cost > 0
        assert annual_memory_cost_savings > 0
