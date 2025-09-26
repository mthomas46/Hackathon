"""API performance and load testing for prompt_store service.

This module provides comprehensive API endpoint performance testing including:
- HTTP endpoint response time benchmarking
- Concurrent API call load testing
- Rate limiting and throughput analysis
- Memory usage during API operations
- Error rate monitoring under load

Run with: python -m pytest tests/performance/test_api_performance.py -v --tb=short
"""

import asyncio
import time
import statistics
import aiohttp
import psutil
from typing import List, Dict, Any, Optional
import pytest
from concurrent.futures import ThreadPoolExecutor
import threading


class APIPerformanceTester:
    """API performance testing client for prompt_store."""

    def __init__(self, base_url: str = "http://localhost:5110"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(self, method: str, endpoint: str,
                          data: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make HTTP request and return timing/response data."""
        if not self.session:
            raise RuntimeError("Use async context manager")

        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json()
                    return {
                        "status_code": response.status,
                        "response_time": response_time,
                        "data": response_data,
                        "success": response.status < 400
                    }
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json()
                    return {
                        "status_code": response.status,
                        "response_time": response_time,
                        "data": response_data,
                        "success": response.status < 400
                    }
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=headers) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json()
                    return {
                        "status_code": response.status,
                        "response_time": response_time,
                        "data": response_data,
                        "success": response.status < 400
                    }
            else:
                raise ValueError(f"Unsupported method: {method}")

        except Exception as e:
            response_time = time.time() - start_time
            return {
                "status_code": 0,
                "response_time": response_time,
                "error": str(e),
                "success": False
            }

    async def create_test_prompt(self) -> Optional[str]:
        """Create a test prompt and return its ID."""
        prompt_data = {
            "name": f"api_perf_test_{int(time.time() * 1000)}",
            "category": "api_performance",
            "content": "This is a test prompt for API performance testing.",
            "created_by": "api_perf_test"
        }

        result = await self.make_request("POST", "/api/v1/prompts", prompt_data)
        if result["success"]:
            return result["data"]["id"]
        return None

    async def get_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Get a prompt by ID."""
        return await self.make_request("GET", f"/api/v1/prompts/{prompt_id}")

    async def update_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Update a prompt."""
        update_data = {
            "content": "Updated content for API performance testing.",
            "updated_by": "api_perf_test"
        }
        return await self.make_request("PUT", f"/api/v1/prompts/{prompt_id}", update_data)

    async def start_refinement(self, prompt_id: str) -> Dict[str, Any]:
        """Start prompt refinement."""
        refinement_data = {
            "refinement_instructions": "Make this prompt more detailed and add error handling",
            "llm_service": "interpreter",
            "user_id": "api_perf_test"
        }
        return await self.make_request("POST", f"/api/v1/prompts/{prompt_id}/refine", refinement_data)

    async def get_health(self) -> Dict[str, Any]:
        """Get service health."""
        return await self.make_request("GET", "/health")


@pytest.mark.performance
class TestAPIEndpointPerformance:
    """Performance tests for individual API endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, benchmark):
        """Benchmark health endpoint response time."""
        async with APIPerformanceTester() as tester:
            result = await benchmark(tester.get_health)
            assert result["success"] is True
            assert result["status_code"] == 200
            # Health endpoint should respond within 100ms
            assert result["response_time"] < 0.1, ".3f"

    @pytest.mark.asyncio
    async def test_prompt_creation_performance(self, benchmark):
        """Benchmark prompt creation endpoint."""
        async with APIPerformanceTester() as tester:
            # Skip if service not running
            health = await tester.get_health()
            if not health["success"]:
                pytest.skip("Prompt store service not available")

            result = await benchmark(tester.create_test_prompt)
            assert result is not None
            # Prompt creation should complete within 500ms
            assert result["response_time"] < 0.5, ".3f"

    @pytest.mark.asyncio
    async def test_prompt_retrieval_performance(self, benchmark):
        """Benchmark prompt retrieval endpoint."""
        async with APIPerformanceTester() as tester:
            # Create test prompt first
            prompt_id = await tester.create_test_prompt()
            if not prompt_id:
                pytest.skip("Could not create test prompt")

            async def retrieve_prompt():
                return await tester.get_prompt(prompt_id)

            result = await benchmark(retrieve_prompt)
            assert result["success"] is True
            assert result["status_code"] == 200
            # Prompt retrieval should complete within 200ms
            assert result["response_time"] < 0.2, ".3f"

    @pytest.mark.asyncio
    async def test_prompt_update_performance(self, benchmark):
        """Benchmark prompt update endpoint."""
        async with APIPerformanceTester() as tester:
            # Create test prompt first
            prompt_id = await tester.create_test_prompt()
            if not prompt_id:
                pytest.skip("Could not create test prompt")

            async def update_prompt():
                return await tester.update_prompt(prompt_id)

            result = await benchmark(update_prompt)
            assert result["success"] is True
            assert result["status_code"] == 200
            # Prompt update should complete within 300ms
            assert result["response_time"] < 0.3, ".3f"


@pytest.mark.load_test
class TestAPIConcurrencyLoad:
    """Load testing for API endpoints under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Test concurrent health endpoint calls."""
        async with APIPerformanceTester() as tester:
            async def health_check():
                return await tester.get_health()

            # Run 20 concurrent health checks
            tasks = [health_check() for _ in range(20)]
            start_time = time.time()

            results = await asyncio.gather(*tasks)

            end_time = time.time()
            duration = end_time - start_time

            successful = sum(1 for r in results if r["success"])
            response_times = [r["response_time"] for r in results if r["success"]]

            print(f"Concurrent health checks: {successful}/20 successful")
            print(".3f")
            if response_times:
                print(".3f")

            assert successful >= 18, f"Too many failed health checks: {successful}/20"
            assert duration < 2.0, f"Concurrent health checks too slow: {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_concurrent_prompt_operations(self):
        """Test concurrent prompt creation and retrieval."""
        async with APIPerformanceTester() as tester:
            # Skip if service not running
            health = await tester.get_health()
            if not health["success"]:
                pytest.skip("Prompt store service not available")

            async def create_and_retrieve():
                # Create prompt
                prompt_id = await tester.create_test_prompt()
                if prompt_id:
                    # Retrieve it
                    result = await tester.get_prompt(prompt_id)
                    return result["success"]
                return False

            # Run 10 concurrent create+retrieve operations
            tasks = [create_and_retrieve() for _ in range(10)]
            start_time = time.time()

            results = await asyncio.gather(*tasks)

            end_time = time.time()
            duration = end_time - start_time

            successful = sum(1 for r in results if r)

            print(f"Concurrent prompt ops: {successful}/10 successful")
            print(".3f")

            assert successful >= 8, f"Too many failed operations: {successful}/10"
            assert duration < 5.0, f"Concurrent operations too slow: {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_api_throughput_analysis(self):
        """Analyze API throughput under sustained load."""
        async with APIPerformanceTester() as tester:
            # Skip if service not running
            health = await tester.get_health()
            if not health["success"]:
                pytest.skip("Prompt store service not available")

            # Perform 50 health checks over 10 seconds
            response_times = []
            start_time = time.time()

            for i in range(50):
                result = await tester.get_health()
                if result["success"]:
                    response_times.append(result["response_time"])
                await asyncio.sleep(0.2)  # 200ms between requests

            end_time = time.time()
            total_duration = end_time - start_time

            if response_times:
                stats = {
                    "total_requests": len(response_times),
                    "successful_requests": len(response_times),
                    "total_duration": total_duration,
                    "requests_per_second": len(response_times) / total_duration,
                    "avg_response_time": statistics.mean(response_times),
                    "95th_percentile": sorted(response_times)[int(len(response_times) * 0.95)]
                }

                print("API Throughput Analysis:")
                print(f"  Requests: {stats['total_requests']}")
                print(".1f")
                print(".3f")
                print(".3f")
                print(".3f")

                # Should handle at least 2 requests per second
                assert stats["requests_per_second"] > 2.0, f"Throughput too low: {stats['requests_per_second']:.1f} req/s"
                # Average response time should be under 200ms
                assert stats["avg_response_time"] < 0.2, f"Average response time too high: {stats['avg_response_time']:.3f}s"
            else:
                pytest.fail("No successful requests recorded")


@pytest.mark.stress_test
class TestAPIStressTesting:
    """Stress testing for API endpoints under extreme conditions."""

    @pytest.mark.asyncio
    async def test_burst_load_health_endpoint(self):
        """Test burst load on health endpoint."""
        async with APIPerformanceTester() as tester:
            # Send 100 rapid health check requests
            tasks = [tester.get_health() for _ in range(100)]
            start_time = time.time()

            results = await asyncio.gather(*tasks)

            end_time = time.time()
            duration = end_time - start_time

            successful = sum(1 for r in results if r["success"])
            response_times = [r["response_time"] for r in results if r["success"]]

            print(f"Burst load health checks: {successful}/100 successful")
            print(".3f")
            if response_times:
                print(".3f")

            assert successful >= 95, f"Too many failed burst requests: {successful}/100"
            assert duration < 10.0, f"Burst load too slow: {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage during API load testing."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        async with APIPerformanceTester() as tester:
            # Skip if service not running
            health = await tester.get_health()
            if not health["success"]:
                pytest.skip("Prompt store service not available")

            # Perform 200 API operations
            tasks = []
            for i in range(50):
                tasks.append(tester.create_test_prompt())
                tasks.append(tester.get_health())

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            duration = end_time - start_time

            successful = sum(1 for r in results if r is not None and (isinstance(r, dict) and r.get("success", False)))

            print(f"Memory usage under load: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
            print(f"Operations: {successful}/100 successful in {duration:.3f}s")

            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100, f"Memory leak detected: {memory_increase:.1f}MB increase"
            # Should complete operations within reasonable time
            assert duration < 30.0, f"Load test too slow: {duration:.3f}s"


# Performance monitoring utilities
def monitor_performance(func):
    """Decorator to monitor function performance."""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = process.cpu_percent()

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            end_cpu = process.cpu_percent()

            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            cpu_usage = (start_cpu + end_cpu) / 2

            print(f"Performance: {func.__name__}")
            print(".3f")
            print(".1f")
            print(".1f")

    return wrapper


# Load testing configuration
LOAD_TEST_CONFIG = {
    "warmup_requests": 10,
    "test_duration_seconds": 60,
    "concurrent_users": 10,
    "request_interval_ms": 100,
    "target_rps": 50
}


if __name__ == "__main__":
    print("Prompt Store API Performance Testing Suite")
    print("=" * 55)
    print("Run individual tests:")
    print("  pytest tests/performance/test_api_performance.py::TestAPIEndpointPerformance -v")
    print("  pytest tests/performance/test_api_performance.py::TestAPIConcurrencyLoad -v")
    print("  pytest tests/performance/test_api_performance.py::TestAPIStressTesting -v")
    print()
    print("Run all performance tests:")
    print("  pytest tests/performance/ -k performance -v")
    print()
    print("Note: These tests require the prompt_store service to be running on localhost:5110")
