"""
Load and stress tests for service integration.

Tests service behavior under various load conditions:
- Light load (10-50 concurrent)
- Medium load (50-200 concurrent)
- Heavy load (200-1000 concurrent)
- Stress testing to find breaking points
"""

import pytest
import asyncio
import time
import uuid
from typing import List, Dict, Any
from datetime import datetime
from statistics import mean, median, stdev

from common.clients import PerformanceStoreClient, MCPStoreClient


# ============================================================================
# Test Configuration
# ============================================================================

LIGHT_LOAD = 50
MEDIUM_LOAD = 200
HEAVY_LOAD = 1000


# ============================================================================
# Load Test Helpers
# ============================================================================

class LoadTestMetrics:
    """Collect and analyze load test metrics."""
    
    def __init__(self):
        self.durations: List[float] = []
        self.successes: int = 0
        self.failures: int = 0
        self.start_time: float = 0
        self.end_time: float = 0
    
    def record_success(self, duration_ms: float):
        """Record successful request."""
        self.durations.append(duration_ms)
        self.successes += 1
    
    def record_failure(self):
        """Record failed request."""
        self.failures += 1
    
    def start(self):
        """Start timer."""
        self.start_time = time.time()
    
    def end(self):
        """End timer."""
        self.end_time = time.time()
    
    def get_report(self) -> Dict[str, Any]:
        """Generate load test report."""
        total = self.successes + self.failures
        success_rate = (self.successes / total * 100) if total > 0 else 0
        
        report = {
            "total_requests": total,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": success_rate,
            "total_duration_sec": self.end_time - self.start_time,
        }
        
        if self.durations:
            report.update({
                "avg_duration_ms": mean(self.durations),
                "median_duration_ms": median(self.durations),
                "min_duration_ms": min(self.durations),
                "max_duration_ms": max(self.durations),
                "stdev_duration_ms": stdev(self.durations) if len(self.durations) > 1 else 0,
            })
        
        if report["total_duration_sec"] > 0:
            report["requests_per_second"] = total / report["total_duration_sec"]
        
        return report


# ============================================================================
# Performance Store Load Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.load
async def test_performance_store_light_load():
    """Test Performance Store under light load (50 concurrent requests)."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store not available")
        
        metrics = LoadTestMetrics()
        metrics.start()
        
        # Create tasks
        tasks = []
        for i in range(LIGHT_LOAD):
            task = _execute_perf_request(client, f"light-{i}", metrics)
            tasks.append(task)
        
        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end()
        report = metrics.get_report()
        
        # Print report
        print("\n" + "=" * 70)
        print("Performance Store - Light Load Test (50 concurrent)")
        print("=" * 70)
        print(f"Total requests: {report['total_requests']}")
        print(f"Successes: {report['successes']}")
        print(f"Failures: {report['failures']}")
        print(f"Success rate: {report['success_rate']:.2f}%")
        print(f"Total duration: {report['total_duration_sec']:.2f}s")
        
        if "avg_duration_ms" in report:
            print(f"Avg duration: {report['avg_duration_ms']:.2f}ms")
            print(f"Median duration: {report['median_duration_ms']:.2f}ms")
            print(f"Min duration: {report['min_duration_ms']:.2f}ms")
            print(f"Max duration: {report['max_duration_ms']:.2f}ms")
            print(f"Stdev duration: {report['stdev_duration_ms']:.2f}ms")
        
        if "requests_per_second" in report:
            print(f"Throughput: {report['requests_per_second']:.2f} req/s")
        
        print("=" * 70)
        
        # Assertions
        assert report["success_rate"] >= 80, f"Success rate too low: {report['success_rate']:.2f}%"
    
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.load
async def test_performance_store_medium_load():
    """Test Performance Store under medium load (200 concurrent requests)."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store not available")
        
        metrics = LoadTestMetrics()
        metrics.start()
        
        # Create tasks
        tasks = []
        for i in range(MEDIUM_LOAD):
            task = _execute_perf_request(client, f"medium-{i}", metrics)
            tasks.append(task)
        
        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end()
        report = metrics.get_report()
        
        # Print report
        print("\n" + "=" * 70)
        print("Performance Store - Medium Load Test (200 concurrent)")
        print("=" * 70)
        print(f"Total requests: {report['total_requests']}")
        print(f"Successes: {report['successes']}")
        print(f"Failures: {report['failures']}")
        print(f"Success rate: {report['success_rate']:.2f}%")
        print(f"Total duration: {report['total_duration_sec']:.2f}s")
        
        if "avg_duration_ms" in report:
            print(f"Avg duration: {report['avg_duration_ms']:.2f}ms")
            print(f"Median duration: {report['median_duration_ms']:.2f}ms")
            print(f"Throughput: {report.get('requests_per_second', 0):.2f} req/s")
        
        print("=" * 70)
        
        # Expect some degradation but still good success rate
        assert report["success_rate"] >= 70, f"Success rate too low: {report['success_rate']:.2f}%"
    
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.load
@pytest.mark.stress
async def test_performance_store_heavy_load():
    """Test Performance Store under heavy load (1000 concurrent requests)."""
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store not available")
        
        metrics = LoadTestMetrics()
        metrics.start()
        
        # Create tasks
        tasks = []
        for i in range(HEAVY_LOAD):
            task = _execute_perf_request(client, f"heavy-{i}", metrics)
            tasks.append(task)
        
        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end()
        report = metrics.get_report()
        
        # Print report
        print("\n" + "=" * 70)
        print("Performance Store - Heavy Load Test (1000 concurrent)")
        print("=" * 70)
        print(f"Total requests: {report['total_requests']}")
        print(f"Successes: {report['successes']}")
        print(f"Failures: {report['failures']}")
        print(f"Success rate: {report['success_rate']:.2f}%")
        print(f"Total duration: {report['total_duration_sec']:.2f}s")
        
        if "avg_duration_ms" in report:
            print(f"Avg duration: {report['avg_duration_ms']:.2f}ms")
            print(f"Median duration: {report['median_duration_ms']:.2f}ms")
            print(f"Throughput: {report.get('requests_per_second', 0):.2f} req/s")
        
        print("=" * 70)
        
        # Under heavy load, expect degradation but should not completely fail
        assert report["success_rate"] >= 50, f"Success rate too low: {report['success_rate']:.2f}%"
    
    finally:
        await client.close()


async def _execute_perf_request(
    client: PerformanceStoreClient,
    request_id: str,
    metrics: LoadTestMetrics,
):
    """Execute a single performance store request."""
    start_time = time.time()
    
    try:
        await client.record_execution(
            orchestration_id=f"load-test-{request_id}",
            mcp_id="load-test-mcp",
            pattern_name="chain-of-thought",
            status="success",
            duration_ms=100.0,
            query=f"Load test query {request_id}",
        )
        
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_success(duration_ms)
    
    except Exception as e:
        metrics.record_failure()


# ============================================================================
# MCP Store Load Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.load
async def test_mcp_store_light_load():
    """Test MCP Store under light load (50 concurrent requests)."""
    client = MCPStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("MCP Store not available")
        
        metrics = LoadTestMetrics()
        metrics.start()
        
        # Create tasks (list packages is relatively lightweight)
        tasks = []
        for i in range(LIGHT_LOAD):
            task = _execute_store_request(client, metrics)
            tasks.append(task)
        
        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end()
        report = metrics.get_report()
        
        # Print report
        print("\n" + "=" * 70)
        print("MCP Store - Light Load Test (50 concurrent)")
        print("=" * 70)
        print(f"Total requests: {report['total_requests']}")
        print(f"Successes: {report['successes']}")
        print(f"Failures: {report['failures']}")
        print(f"Success rate: {report['success_rate']:.2f}%")
        print(f"Total duration: {report['total_duration_sec']:.2f}s")
        
        if "avg_duration_ms" in report:
            print(f"Avg duration: {report['avg_duration_ms']:.2f}ms")
            print(f"Throughput: {report.get('requests_per_second', 0):.2f} req/s")
        
        print("=" * 70)
        
        # Assertions
        assert report["success_rate"] >= 80, f"Success rate too low: {report['success_rate']:.2f}%"
    
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.load
async def test_mcp_store_medium_load():
    """Test MCP Store under medium load (200 concurrent requests)."""
    client = MCPStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("MCP Store not available")
        
        metrics = LoadTestMetrics()
        metrics.start()
        
        # Create tasks
        tasks = []
        for i in range(MEDIUM_LOAD):
            task = _execute_store_request(client, metrics)
            tasks.append(task)
        
        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end()
        report = metrics.get_report()
        
        # Print report
        print("\n" + "=" * 70)
        print("MCP Store - Medium Load Test (200 concurrent)")
        print("=" * 70)
        print(f"Total requests: {report['total_requests']}")
        print(f"Successes: {report['successes']}")
        print(f"Failures: {report['failures']}")
        print(f"Success rate: {report['success_rate']:.2f}%")
        print(f"Total duration: {report['total_duration_sec']:.2f}s")
        
        if "avg_duration_ms" in report:
            print(f"Avg duration: {report['avg_duration_ms']:.2f}ms")
            print(f"Throughput: {report.get('requests_per_second', 0):.2f} req/s")
        
        print("=" * 70)
        
        # Expect decent success rate
        assert report["success_rate"] >= 70, f"Success rate too low: {report['success_rate']:.2f}%"
    
    finally:
        await client.close()


async def _execute_store_request(client: MCPStoreClient, metrics: LoadTestMetrics):
    """Execute a single MCP store request."""
    start_time = time.time()
    
    try:
        # List packages is lightweight and doesn't modify state
        await client.list_packages(limit=10)
        
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_success(duration_ms)
    
    except Exception as e:
        metrics.record_failure()


# ============================================================================
# Combined Workflow Load Test
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.load
async def test_combined_workflow_load():
    """
    Test combined workflow under load.
    
    Simulates realistic usage:
    - Multiple services making requests
    - Mix of read and write operations
    - Concurrent executions
    """
    perf_client = PerformanceStoreClient()
    store_client = MCPStoreClient()
    
    try:
        perf_healthy = await perf_client.health_check()
        store_healthy = await store_client.health_check()
        
        if not perf_healthy or not store_healthy:
            pytest.skip("Required services not available")
        
        metrics = LoadTestMetrics()
        metrics.start()
        
        # Create mixed workload
        tasks = []
        
        # 70% performance store writes (executions)
        for i in range(70):
            task = _execute_perf_request(perf_client, f"combined-{i}", metrics)
            tasks.append(task)
        
        # 30% store reads (list packages)
        for i in range(30):
            task = _execute_store_request(store_client, metrics)
            tasks.append(task)
        
        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end()
        report = metrics.get_report()
        
        # Print report
        print("\n" + "=" * 70)
        print("Combined Workflow - Load Test (100 concurrent)")
        print("=" * 70)
        print(f"Total requests: {report['total_requests']}")
        print(f"Successes: {report['successes']}")
        print(f"Failures: {report['failures']}")
        print(f"Success rate: {report['success_rate']:.2f}%")
        print(f"Total duration: {report['total_duration_sec']:.2f}s")
        
        if "avg_duration_ms" in report:
            print(f"Avg duration: {report['avg_duration_ms']:.2f}ms")
            print(f"Throughput: {report.get('requests_per_second', 0):.2f} req/s")
        
        print("=" * 70)
        
        # Combined workflow should handle load well
        assert report["success_rate"] >= 80, f"Success rate too low: {report['success_rate']:.2f}%"
    
    finally:
        await perf_client.close()
        await store_client.close()


# ============================================================================
# Sustained Load Test
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.load
@pytest.mark.slow
async def test_sustained_load():
    """
    Test sustained load over time (5 minutes).
    
    Simulates continuous production usage to detect:
    - Memory leaks
    - Connection pool exhaustion
    - Performance degradation
    """
    client = PerformanceStoreClient()
    
    try:
        if not await client.health_check():
            pytest.skip("Performance Store not available")
        
        duration_seconds = 300  # 5 minutes
        requests_per_second = 10
        
        print(f"\n{'=' * 70}")
        print(f"Sustained Load Test ({duration_seconds}s @ {requests_per_second} req/s)")
        print(f"{'=' * 70}")
        
        metrics = LoadTestMetrics()
        metrics.start()
        
        end_time = time.time() + duration_seconds
        request_count = 0
        
        while time.time() < end_time:
            batch_start = time.time()
            
            # Execute batch of requests
            tasks = []
            for i in range(requests_per_second):
                task = _execute_perf_request(client, f"sustained-{request_count}-{i}", metrics)
                tasks.append(task)
                request_count += 1
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Wait to maintain target rate
            batch_duration = time.time() - batch_start
            if batch_duration < 1.0:
                await asyncio.sleep(1.0 - batch_duration)
            
            # Print progress every 30 seconds
            if request_count % 300 == 0:
                elapsed = time.time() - metrics.start_time
                print(f"Progress: {elapsed:.0f}s, {request_count} requests, "
                      f"{metrics.successes} successes, {metrics.failures} failures")
        
        metrics.end()
        report = metrics.get_report()
        
        # Print final report
        print(f"\n{'=' * 70}")
        print("Sustained Load Test - Final Report")
        print(f"{'=' * 70}")
        print(f"Total requests: {report['total_requests']}")
        print(f"Successes: {report['successes']}")
        print(f"Failures: {report['failures']}")
        print(f"Success rate: {report['success_rate']:.2f}%")
        print(f"Total duration: {report['total_duration_sec']:.2f}s")
        
        if "avg_duration_ms" in report:
            print(f"Avg duration: {report['avg_duration_ms']:.2f}ms")
            print(f"Throughput: {report.get('requests_per_second', 0):.2f} req/s")
        
        print(f"{'=' * 70}")
        
        # Under sustained load, should maintain good performance
        assert report["success_rate"] >= 85, f"Success rate degraded: {report['success_rate']:.2f}%"
    
    finally:
        await client.close()

