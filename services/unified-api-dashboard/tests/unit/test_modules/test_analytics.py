"""
Unit Tests for Analytics Module

Comprehensive unit tests for usage analytics, performance insights,
error tracking, and usage patterns analysis.
"""

from datetime import datetime, timedelta

import pytest

from ....modules.analytics.error_tracking import ErrorTracking
from ....modules.analytics.performance_insights import PerformanceInsights
from ....modules.analytics.usage_analytics import UsageAnalytics
from ....modules.analytics.usage_patterns import UsagePatterns


class TestUsageAnalytics:
    """Test UsageAnalytics functionality."""

    @pytest.fixture
    def usage_analytics(self, mock_discovery_client, mock_health_monitor):
        """Create UsageAnalytics instance for testing."""
        return UsageAnalytics(mock_discovery_client, mock_health_monitor)

    @pytest.mark.asyncio
    async def test_record_api_request(self, usage_analytics):
        """Test API request recording."""
        await usage_analytics.record_api_request(
            {
                "timestamp": datetime.now(),
                "service": "test-service",
                "endpoint": "/api/test",
                "method": "GET",
                "response_time": 150,
                "status_code": 200,
                "user_id": "user123",
            }
        )

        # Check that data was recorded (internal storage)
        assert len(usage_analytics.usage_data) == 1

    @pytest.mark.asyncio
    async def test_get_usage_overview(self, usage_analytics, sample_usage_data):
        """Test usage overview generation."""
        # Populate with sample data
        for record in sample_usage_data:
            await usage_analytics.record_api_request(record)

        overview = await usage_analytics.get_usage_overview()

        assert "total_requests" in overview
        assert "unique_users" in overview
        assert "services_used" in overview
        assert "peak_usage_hour" in overview
        assert overview["total_requests"] == len(sample_usage_data)

    @pytest.mark.asyncio
    async def test_get_performance_insights(self, usage_analytics, sample_usage_data):
        """Test performance insights generation."""
        # Populate with sample data
        for record in sample_usage_data:
            await usage_analytics.record_api_request(record)

        insights = await usage_analytics.get_performance_insights()

        assert "avg_response_time" in insights
        assert "p95_response_time" in insights
        assert "p99_response_time" in insights
        assert "error_rate" in insights
        assert "throughput_rps" in insights

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, usage_analytics, sample_usage_data):
        """Test anomaly detection."""
        # Populate with sample data
        for record in sample_usage_data:
            await usage_analytics.record_api_request(record)

        anomalies = await usage_analytics.detect_anomalies()

        # Should return anomaly information
        assert isinstance(anomalies, list)

    @pytest.mark.asyncio
    async def test_export_analytics_data(self, usage_analytics, sample_usage_data):
        """Test analytics data export."""
        # Populate with sample data
        for record in sample_usage_data:
            await usage_analytics.record_api_request(record)

        export_data = await usage_analytics.export_analytics_data("json")

        assert "usage_data" in export_data
        assert "performance_metrics" in export_data
        assert "anomalies" in export_data
        assert len(export_data["usage_data"]) == len(sample_usage_data)


class TestPerformanceInsights:
    """Test PerformanceInsights functionality."""

    @pytest.fixture
    def performance_insights(self, mock_discovery_client, mock_health_monitor):
        """Create PerformanceInsights instance for testing."""
        return PerformanceInsights(mock_discovery_client, mock_health_monitor)

    @pytest.mark.asyncio
    async def test_analyze_response_times(
        self, performance_insights, sample_usage_data
    ):
        """Test response time analysis."""
        analysis = await performance_insights.analyze_response_times(sample_usage_data)

        assert "avg_response_time" in analysis
        assert "p50_response_time" in analysis
        assert "p95_response_time" in analysis
        assert "p99_response_time" in analysis
        assert "min_response_time" in analysis
        assert "max_response_time" in analysis

    @pytest.mark.asyncio
    async def test_analyze_throughput_patterns(
        self, performance_insights, sample_usage_data
    ):
        """Test throughput pattern analysis."""
        analysis = await performance_insights.analyze_throughput_patterns(
            sample_usage_data
        )

        assert "hourly_throughput" in analysis
        assert "daily_throughput" in analysis
        assert "peak_hour" in analysis
        assert "avg_throughput_per_hour" in analysis

    @pytest.mark.asyncio
    async def test_analyze_resource_utilization(self, performance_insights):
        """Test resource utilization analysis."""
        # Mock resource metrics
        resource_data = [
            {
                "timestamp": datetime.now() - timedelta(hours=i),
                "cpu_percent": 50 + i * 5,
                "memory_percent": 60 + i * 3,
            }
            for i in range(5)
        ]

        analysis = await performance_insights.analyze_resource_utilization(
            resource_data
        )

        assert "cpu_utilization" in analysis
        assert "memory_utilization" in analysis
        assert "avg_cpu_percent" in analysis["cpu_utilization"]
        assert "avg_memory_percent" in analysis["memory_utilization"]

    @pytest.mark.asyncio
    async def test_generate_performance_report(
        self, performance_insights, sample_usage_data
    ):
        """Test performance report generation."""
        report = await performance_insights.generate_performance_report(
            sample_usage_data
        )

        assert "summary" in report
        assert "response_time_analysis" in report
        assert "throughput_analysis" in report
        assert "resource_analysis" in report
        assert "recommendations" in report
        assert "generated_at" in report


class TestErrorTracking:
    """Test ErrorTracking functionality."""

    @pytest.fixture
    def error_tracking(self, mock_discovery_client, mock_health_monitor):
        """Create ErrorTracking instance for testing."""
        return ErrorTracking(mock_discovery_client, mock_health_monitor)

    @pytest.mark.asyncio
    async def test_record_error(self, error_tracking, sample_error_data):
        """Test error recording."""
        for error in sample_error_data:
            await error_tracking.record_error(error)

        assert len(error_tracking.error_data) == len(sample_error_data)

    @pytest.mark.asyncio
    async def test_get_error_overview(self, error_tracking, sample_error_data):
        """Test error overview generation."""
        # Record sample errors
        for error in sample_error_data:
            await error_tracking.record_error(error)

        overview = await error_tracking.get_error_overview()

        assert "total_errors" in overview
        assert "error_rate" in overview
        assert "errors_by_type" in overview
        assert "errors_by_service" in overview
        assert "errors_by_endpoint" in overview
        assert overview["total_errors"] == len(sample_error_data)

    @pytest.mark.asyncio
    async def test_analyze_error_patterns(self, error_tracking, sample_error_data):
        """Test error pattern analysis."""
        # Record sample errors
        for error in sample_error_data:
            await error_tracking.record_error(error)

        patterns = await error_tracking.analyze_error_patterns()

        assert "error_clusters" in patterns
        assert "temporal_patterns" in patterns
        assert "frequent_errors" in patterns
        assert "error_sequences" in patterns

    @pytest.mark.asyncio
    async def test_get_error_alerts(self, error_tracking, sample_error_data):
        """Test error alert generation."""
        # Record sample errors
        for error in sample_error_data:
            await error_tracking.record_error(error)

        alerts = await error_tracking.get_error_alerts()

        assert isinstance(alerts, list)
        # Should generate alerts for high error rates

    @pytest.mark.asyncio
    async def test_generate_error_report(self, error_tracking, sample_error_data):
        """Test error report generation."""
        # Record sample errors
        for error in sample_error_data:
            await error_tracking.record_error(error)

        report = await error_tracking.generate_error_report()

        assert "summary" in report
        assert "error_analysis" in report
        assert "alerts" in report
        assert "recommendations" in report
        assert "generated_at" in report


class TestUsagePatterns:
    """Test UsagePatterns functionality."""

    @pytest.fixture
    def usage_patterns(self, mock_discovery_client, mock_health_monitor):
        """Create UsagePatterns instance for testing."""
        return UsagePatterns(mock_discovery_client, mock_health_monitor)

    @pytest.mark.asyncio
    async def test_record_usage_pattern(self, usage_patterns, sample_usage_data):
        """Test usage pattern recording."""
        for record in sample_usage_data:
            await usage_patterns.record_usage_pattern(record)

        assert len(usage_patterns.patterns_data) == len(sample_usage_data)

    @pytest.mark.asyncio
    async def test_analyze_temporal_patterns(self, usage_patterns, sample_usage_data):
        """Test temporal pattern analysis."""
        # Record sample data
        for record in sample_usage_data:
            await usage_patterns.record_usage_pattern(record)

        patterns = await usage_patterns.analyze_temporal_patterns()

        assert "hourly_patterns" in patterns
        assert "daily_patterns" in patterns
        assert "weekly_patterns" in patterns
        assert "seasonal_trends" in patterns

    @pytest.mark.asyncio
    async def test_analyze_user_behaviors(self, usage_patterns, sample_usage_data):
        """Test user behavior analysis."""
        # Record sample data
        for record in sample_usage_data:
            await usage_patterns.record_usage_pattern(record)

        behaviors = await usage_patterns.analyze_user_behaviors()

        assert "user_segments" in behaviors
        assert "behavior_clusters" in behaviors
        assert "user_journeys" in behaviors
        assert "engagement_metrics" in behaviors

    @pytest.mark.asyncio
    async def test_detect_usage_anomalies(self, usage_patterns, sample_usage_data):
        """Test usage anomaly detection."""
        # Record sample data
        for record in sample_usage_data:
            await usage_patterns.record_usage_pattern(record)

        anomalies = await usage_patterns.detect_usage_anomalies()

        assert isinstance(anomalies, list)
        # Should detect anomalies in usage patterns

    @pytest.mark.asyncio
    async def test_generate_usage_insights_report(
        self, usage_patterns, sample_usage_data
    ):
        """Test usage insights report generation."""
        # Record sample data
        for record in sample_usage_data:
            await usage_patterns.record_usage_pattern(record)

        report = await usage_patterns.generate_usage_insights_report()

        assert "temporal_analysis" in report
        assert "user_behavior_analysis" in report
        assert "anomaly_detection" in report
        assert "recommendations" in report
        assert "generated_at" in report


# Integration tests for analytics modules
class TestAnalyticsIntegration:
    """Integration tests for analytics modules working together."""

    @pytest.fixture
    async def analytics_suite(self, mock_discovery_client, mock_health_monitor):
        """Create full analytics suite for integration testing."""
        return {
            "usage_analytics": UsageAnalytics(
                mock_discovery_client, mock_health_monitor
            ),
            "performance_insights": PerformanceInsights(
                mock_discovery_client, mock_health_monitor
            ),
            "error_tracking": ErrorTracking(mock_discovery_client, mock_health_monitor),
            "usage_patterns": UsagePatterns(mock_discovery_client, mock_health_monitor),
        }

    @pytest.mark.asyncio
    async def test_cross_module_data_flow(self, analytics_suite, sample_usage_data):
        """Test data flow between analytics modules."""
        # Record data in usage analytics
        for record in sample_usage_data:
            await analytics_suite["usage_analytics"].record_api_request(record)

        # Generate insights from different modules
        usage_overview = await analytics_suite["usage_analytics"].get_usage_overview()
        perf_insights = await analytics_suite[
            "performance_insights"
        ].generate_performance_report(sample_usage_data)
        usage_patterns_report = await analytics_suite[
            "usage_patterns"
        ].generate_usage_insights_report()

        # Verify cross-consistency
        assert usage_overview["total_requests"] == len(sample_usage_data)
        assert "response_time_analysis" in perf_insights
        assert "temporal_analysis" in usage_patterns_report

    @pytest.mark.asyncio
    async def test_error_tracking_integration(self, analytics_suite, sample_error_data):
        """Test error tracking integration with other analytics."""
        # Record errors
        for error in sample_error_data:
            await analytics_suite["error_tracking"].record_error(error)

        # Get error overview and usage overview
        error_overview = await analytics_suite["error_tracking"].get_error_overview()
        await analytics_suite["usage_analytics"].get_usage_overview()

        # Verify error metrics are captured
        assert error_overview["total_errors"] == len(sample_error_data)
        assert "error_rate" in error_overview
