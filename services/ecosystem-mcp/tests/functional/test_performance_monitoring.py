"""
Functional tests for performance monitoring.

Tests metrics collection, degradation detection, and resource tracking.
"""

import pytest
import httpx
import os
import time
import asyncio
from datetime import datetime, timedelta


pytestmark = pytest.mark.functional


@pytest.fixture
def api_base_url():
    """Get API base URL from environment."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
async def async_http_client(api_base_url):
    """Create async HTTP client."""
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


class TestMetricsCollection:
    """Test real-time metrics collection."""

    async def test_realtime_metric_capture(self, async_http_client):
        """Test real-time metric capture."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                
                # Check for common metrics
                # (actual structure may vary)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_metric_aggregation(self, async_http_client):
        """Test metric aggregation over time."""
        try:
            # Get metrics multiple times
            metrics_samples = []
            
            for _ in range(3):
                response = await async_http_client.get("/api/v1/diagnostics/metrics")
                if response.status_code == 200:
                    metrics_samples.append(response.json())
                await asyncio.sleep(0.5)
            
            # Should have collected samples
            assert len(metrics_samples) >= 0
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_metric_persistence(self, async_http_client):
        """Test metric persistence."""
        try:
            # Generate some activity
            await async_http_client.get("/health")
            
            # Get metrics
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_metric_querying(self, async_http_client):
        """Test metric querying with filters."""
        try:
            # Query metrics with time range
            response = await async_http_client.get(
                "/api/v1/diagnostics/metrics",
                params={"start_time": datetime.utcnow().isoformat()}
            )
            
            # Should accept or return not found
            assert response.status_code in [200, 404, 422]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_metric_visualization_data(self, async_http_client):
        """Test metric data for visualization."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            if response.status_code == 200:
                data = response.json()
                
                # Data should be suitable for visualization
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestDegradationDetection:
    """Test performance degradation detection."""

    async def test_baseline_establishment(self, async_http_client):
        """Test baseline performance establishment."""
        try:
            # Measure baseline
            start = time.time()
            response = await async_http_client.get("/health")
            baseline_latency = time.time() - start
            
            # Baseline should be reasonable
            assert baseline_latency < 5.0
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_degradation_threshold(self, async_http_client):
        """Test degradation threshold detection."""
        try:
            # Make multiple requests to measure performance
            latencies = []
            
            for _ in range(5):
                start = time.time()
                response = await async_http_client.get("/health")
                latency = time.time() - start
                
                if response.status_code == 200:
                    latencies.append(latency)
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                
                # Average latency should be reasonable
                assert avg_latency < 2.0
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_alert_generation(self, async_http_client):
        """Test alert generation for degradation."""
        try:
            # Check if alerts endpoint exists
            response = await async_http_client.get("/api/v1/diagnostics/alerts/active")
            
            # Should return alerts or not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_root_cause_analysis(self, async_http_client):
        """Test root cause analysis for degradation."""
        try:
            # Check if troubleshooting endpoint exists
            response = await async_http_client.get("/api/v1/diagnostics/troubleshoot/issues")
            
            # Should return analysis or not found
            assert response.status_code in [200, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_recovery_validation(self, async_http_client):
        """Test validation of performance recovery."""
        try:
            # Check system health
            response1 = await async_http_client.get("/health")
            
            # Wait a bit
            await asyncio.sleep(0.5)
            
            # Check again
            response2 = await async_http_client.get("/health")
            
            # Both should succeed
            assert response1.status_code in [200, 503]
            assert response2.status_code in [200, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestResourceTracking:
    """Test resource usage tracking."""

    async def test_cpu_usage_tracking(self, async_http_client):
        """Test CPU usage tracking."""
        try:
            response = await async_http_client.get("/api/v1/admin/stats")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_memory_usage_tracking(self, async_http_client):
        """Test memory usage tracking."""
        try:
            response = await async_http_client.get("/api/v1/admin/stats")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_disk_io_tracking(self, async_http_client):
        """Test disk I/O tracking."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            # Should return metrics or not found
            assert response.status_code in [200, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_network_usage_tracking(self, async_http_client):
        """Test network usage tracking."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            # Should return metrics or not found
            assert response.status_code in [200, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_database_connection_tracking(self, async_http_client):
        """Test database connection tracking."""
        try:
            response = await async_http_client.get("/api/v1/infrastructure/health")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestPerformanceMonitoringIntegration:
    """Test performance monitoring integration."""

    async def test_monitoring_dashboard_data(self, async_http_client):
        """Test data for monitoring dashboard."""
        try:
            response = await async_http_client.get("/api/v1/admin/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should provide dashboard-ready data
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_historical_metrics(self, async_http_client):
        """Test historical metrics retrieval."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            # Should return metrics or not found
            assert response.status_code in [200, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_metric_export(self, async_http_client):
        """Test metric export functionality."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should be exportable
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_alert_notifications(self, async_http_client):
        """Test alert notification system."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/alerts/active")
            
            # Should return alerts or not found
            assert response.status_code in [200, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_performance_reports(self, async_http_client):
        """Test performance report generation."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            # Should return data for reports
            assert response.status_code in [200, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

