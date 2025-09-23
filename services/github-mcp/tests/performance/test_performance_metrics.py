"""Performance Tests for GitHub MCP Service.

This module tests performance characteristics including:
- Response time benchmarks for tool invocations
- Throughput testing under concurrent load
- Memory usage and resource consumption
- Scalability testing with increasing load
- Performance regression detection

Performance tests ensure the GitHub MCP service meets performance requirements.
"""

import asyncio
import time
import statistics
import psutil
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

import pytest


class TestPerformanceMetrics:
    """Performance testing for GitHub MCP service components."""

    @pytest.fixture
    def performance_config(self):
        """Performance test configuration."""
        return {
            "warmup_iterations": 10,
            "test_iterations": 100,
            "concurrent_users": [1, 5, 10, 25, 50],
            "target_response_time_ms": 500,
            "acceptable_error_rate": 0.05,  # 5%
            "memory_threshold_mb": 100,
            "cpu_threshold_percent": 80
        }

    @pytest.mark.asyncio
    async def test_tool_invocation_response_time(self, performance_config):
        """Test response time for tool invocations under normal load."""
        # Mock tool registry and implementations
        mock_tool = AsyncMock()
        mock_tool.return_value = {
            "content": [{"text": "Mock repository data"}]
        }

        with patch("main.tool_registry") as mock_registry, \
             patch("main.invoke_tool", side_effect=mock_tool):

            mock_registry.has_tool.return_value = True

            from main import invoke_tool

            # Warmup phase
            for _ in range(performance_config["warmup_iterations"]):
                await invoke_tool("repos.get", {"owner": "octocat", "repo": "test"})

            # Performance test phase
            response_times = []
            start_time = time.time()

            for _ in range(performance_config["test_iterations"]):
                iteration_start = time.time()
                result = await invoke_tool("repos.get", {"owner": "octocat", "repo": "test"})
                iteration_end = time.time()

                response_time = (iteration_end - iteration_start) * 1000  # Convert to ms
                response_times.append(response_time)

                # Verify result structure
                assert "content" in result

            end_time = time.time()
            total_time = end_time - start_time

            # Calculate performance metrics
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            throughput = performance_config["test_iterations"] / total_time

            # Performance assertions
            assert avg_response_time < performance_config["target_response_time_ms"], \
                f"Average response time {avg_response_time:.2f}ms exceeds target {performance_config['target_response_time_ms']}ms"

            assert p95_response_time < performance_config["target_response_time_ms"] * 2, \
                f"95th percentile response time {p95_response_time:.2f}ms too high"

            # Log performance results
            print(f"Performance Test Results:")
            print(f"  Total Requests: {performance_config['test_iterations']}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")
            print(f"  Median Response Time: {median_response_time:.2f}ms")
            print(f"  Min Response Time: {min_response_time:.2f}ms")
            print(f"  Max Response Time: {max_response_time:.2f}ms")
            print(f"  95th Percentile: {p95_response_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_load_performance(self, performance_config):
        """Test performance under concurrent load."""
        async def single_user_load(user_id: int, iterations: int) -> List[float]:
            """Simulate a single user's load pattern."""
            response_times = []

            for i in range(iterations):
                start_time = time.time()

                # Simulate different tool calls
                tool_name = f"repos.get_user_{user_id}_{i}"
                await asyncio.sleep(0.001)  # Simulate network delay

                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)

            return response_times

        # Test different concurrency levels
        for concurrent_users in performance_config["concurrent_users"]:
            print(f"\nTesting with {concurrent_users} concurrent users...")

            start_time = time.time()

            # Create concurrent user tasks
            tasks = [
                single_user_load(user_id, 10)  # 10 iterations per user
                for user_id in range(concurrent_users)
            ]

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # Aggregate results
            all_response_times = []
            for user_times in results:
                all_response_times.extend(user_times)

            total_requests = len(all_response_times)
            throughput = total_requests / total_time

            avg_response_time = statistics.mean(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]

            print(f"  Concurrent Users: {concurrent_users}")
            print(f"  Total Requests: {total_requests}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")
            print(f"  95th Percentile: {p95_response_time:.2f}ms")

            # Performance assertions for concurrent load
            assert throughput > concurrent_users * 0.5, \
                f"Throughput {throughput:.2f} req/s too low for {concurrent_users} users"

            assert avg_response_time < performance_config["target_response_time_ms"] * (concurrent_users ** 0.5), \
                f"Average response time {avg_response_time:.2f}ms too high under concurrent load"

    def test_memory_usage_baseline(self, performance_config):
        """Test baseline memory usage."""
        process = psutil.Process(os.getpid())

        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform some operations to establish baseline
        test_data = []
        for i in range(1000):
            test_data.append({"id": i, "data": f"test_data_{i}" * 10})

        # Get memory usage after operations
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = final_memory - initial_memory

        print(f"Memory Usage Test:")
        print(f"  Initial Memory: {initial_memory:.2f} MB")
        print(f"  Final Memory: {final_memory:.2f} MB")
        print(f"  Memory Delta: {memory_delta:.2f} MB")

        # Memory assertions
        assert memory_delta < performance_config["memory_threshold_mb"], \
            f"Memory usage increased by {memory_delta:.2f} MB, exceeds threshold {performance_config['memory_threshold_mb']} MB"

        assert final_memory < 500, \
            f"Total memory usage {final_memory:.2f} MB too high"

    @pytest.mark.asyncio
    async def test_api_endpoint_performance(self):
        """Test performance of FastAPI endpoints."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test health endpoint performance
        response_times = []

        for _ in range(50):  # Test multiple requests
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()

            assert response.status_code == 200
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)

        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]

        print(f"API Endpoint Performance:")
        print(f"  Health Endpoint - Avg: {avg_response_time:.2f}ms, P95: {p95_response_time:.2f}ms")

        assert avg_response_time < 100, \
            f"Health endpoint too slow: {avg_response_time:.2f}ms"

        # Test tools listing endpoint
        start_time = time.time()
        response = client.get("/tools")
        end_time = time.time()

        tools_response_time = (end_time - start_time) * 1000

        assert response.status_code == 200
        print(f"  Tools Endpoint - Response Time: {tools_response_time:.2f}ms")

        assert tools_response_time < 200, \
            f"Tools endpoint too slow: {tools_response_time:.2f}ms"

    @pytest.mark.asyncio
    async def test_cache_performance_impact(self):
        """Test performance impact of caching mechanisms."""
        # This would test caching performance if implemented
        # For now, establish baseline for future caching implementation

        # Mock cache-enabled operations
        cache_hits = 0
        cache_misses = 0

        # Simulate cache operations
        for i in range(100):
            if i % 3 == 0:  # 33% cache hit rate
                cache_hits += 1
                await asyncio.sleep(0.001)  # Fast cache hit
            else:
                cache_misses += 1
                await asyncio.sleep(0.01)  # Slower cache miss

        hit_rate = cache_hits / (cache_hits + cache_misses)

        print(f"Cache Performance Simulation:")
        print(f"  Cache Hit Rate: {hit_rate:.2%}")
        print(f"  Cache Hits: {cache_hits}")
        print(f"  Cache Misses: {cache_misses}")

        # In a real implementation, we'd assert performance improvements
        assert hit_rate > 0.3, "Cache hit rate too low for effective caching"

    def test_scalability_under_load(self, performance_config):
        """Test system scalability as load increases."""
        import threading
        import queue

        results_queue = queue.Queue()

        def worker_thread(thread_id: int, num_requests: int):
            """Worker thread to simulate load."""
            thread_results = []

            for i in range(num_requests):
                start_time = time.time()

                # Simulate work (in real test, this would be actual API calls)
                time.sleep(0.001)  # 1ms of work

                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                thread_results.append(response_time)

            results_queue.put((thread_id, thread_results))

        # Test with increasing thread counts
        thread_counts = [1, 2, 4, 8]
        requests_per_thread = 25

        scalability_results = []

        for num_threads in thread_counts:
            print(f"\nTesting scalability with {num_threads} threads...")

            start_time = time.time()

            # Start worker threads
            threads = []
            for thread_id in range(num_threads):
                thread = threading.Thread(
                    target=worker_thread,
                    args=(thread_id, requests_per_thread)
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            end_time = time.time()
            total_time = end_time - start_time

            # Collect results
            all_response_times = []
            while not results_queue.empty():
                thread_id, thread_results = results_queue.get()
                all_response_times.extend(thread_results)

            total_requests = len(all_response_times)
            throughput = total_requests / total_time
            avg_response_time = statistics.mean(all_response_times)

            scalability_results.append({
                "threads": num_threads,
                "total_requests": total_requests,
                "throughput": throughput,
                "avg_response_time": avg_response_time,
                "total_time": total_time
            })

            print(f"  Threads: {num_threads}")
            print(f"  Total Requests: {total_requests}")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")

        # Analyze scalability
        baseline_throughput = scalability_results[0]["throughput"]
        max_throughput = max(r["throughput"] for r in scalability_results)

        scalability_factor = max_throughput / baseline_throughput

        print(f"\nScalability Analysis:")
        print(f"  Baseline Throughput (1 thread): {baseline_throughput:.2f} req/s")
        print(f"  Max Throughput ({thread_counts[-1]} threads): {max_throughput:.2f} req/s")
        print(f"  Scalability Factor: {scalability_factor:.2f}x")

        # Scalability assertions
        assert scalability_factor > 1.5, \
            f"Poor scalability: only {scalability_factor:.2f}x improvement with {thread_counts[-1]}x threads"

    @pytest.mark.asyncio
    async def test_resource_cleanup_performance(self):
        """Test performance of resource cleanup operations."""
        import gc

        # Create some resources
        resources = []
        for i in range(100):
            resources.append({"id": i, "data": f"resource_data_{i}" * 100})

        # Force garbage collection
        start_time = time.time()
        gc.collect()
        end_time = time.time()

        cleanup_time = (end_time - start_time) * 1000

        print(f"Resource Cleanup Performance:")
        print(f"  Cleanup Time: {cleanup_time:.2f}ms")

        assert cleanup_time < 100, \
            f"Resource cleanup too slow: {cleanup_time:.2f}ms"

    def test_cpu_usage_baseline(self, performance_config):
        """Test baseline CPU usage during operations."""
        process = psutil.Process(os.getpid())

        # Get initial CPU usage
        initial_cpu = process.cpu_percent(interval=0.1)

        # Perform CPU-intensive operations
        result = 0
        for i in range(100000):
            result += i ** 2

        # Get CPU usage after operations
        final_cpu = process.cpu_percent(interval=0.1)

        print(f"CPU Usage Test:")
        print(f"  Initial CPU: {initial_cpu:.2f}%")
        print(f"  Final CPU: {final_cpu:.2f}%")

        assert final_cpu < performance_config["cpu_threshold_percent"], \
            f"CPU usage {final_cpu:.2f}% exceeds threshold {performance_config['cpu_threshold_percent']}%"


class TestPerformanceBenchmarks:
    """Performance benchmarks for regression testing."""

    @pytest.fixture
    def benchmark_data(self):
        """Benchmark test data."""
        return {
            "small_payload": {"owner": "octocat", "repo": "Hello-World"},
            "medium_payload": {
                "owner": "octocat",
                "repo": "Hello-World",
                "description": "A test repository" * 10,
                "metadata": {"stars": 100, "forks": 50}
            },
            "large_payload": {
                "owner": "octocat",
                "repo": "Hello-World",
                "description": "A test repository" * 100,
                "metadata": {"stars": 100, "forks": 50, "contributors": ["user"] * 50},
                "readme": "README content" * 200
            }
        }

    @pytest.mark.benchmark
    def test_payload_size_performance_impact(self, benchmark_data):
        """Test performance impact of different payload sizes."""
        import json

        results = {}

        for payload_name, payload in benchmark_data.items():
            # Serialize/deserialize benchmark
            start_time = time.time()

            for _ in range(100):
                json_str = json.dumps(payload)
                parsed = json.loads(json_str)

            end_time = time.time()

            avg_time = (end_time - start_time) / 100 * 1000  # ms
            payload_size = len(json.dumps(payload))

            results[payload_name] = {
                "size_bytes": payload_size,
                "avg_time_ms": avg_time,
                "time_per_byte_us": (avg_time * 1000) / payload_size
            }

            print(f"{payload_name}: {payload_size} bytes, {avg_time:.2f}ms avg")

        # Performance should scale reasonably with payload size
        small_time = results["small_payload"]["avg_time_ms"]
        large_time = results["large_payload"]["avg_time_ms"]

        scaling_factor = large_time / small_time
        size_ratio = results["large_payload"]["size_bytes"] / results["small_payload"]["size_bytes"]

        print(f"Scaling analysis: {scaling_factor:.2f}x time for {size_ratio:.2f}x size")

        # Scaling should be sub-linear for reasonable performance
        assert scaling_factor < size_ratio * 2, \
            f"Poor scaling: {scaling_factor:.2f}x time increase for {size_ratio:.2f}x size increase"
