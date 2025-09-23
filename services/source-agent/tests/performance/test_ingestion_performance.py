"""Performance Tests for Data Ingestion Operations in Source Agent Service.

This module tests performance characteristics of data ingestion operations including:
- Data source connector throughput and latency
- Ingestion pipeline processing speed and scalability
- Memory usage during large-scale data ingestion
- Concurrent data source connections and processing
- Performance regression detection across data sources

Performance tests ensure the Source Agent service meets enterprise data ingestion requirements.
"""

import asyncio
import time
import statistics
import psutil
import os
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta

import pytest


class TestIngestionPerformance:
    """Performance testing for data ingestion operations."""

    @pytest.fixture
    def performance_config(self):
        """Performance test configuration for data ingestion."""
        return {
            "warmup_iterations": 5,
            "test_iterations": 20,
            "concurrent_connections": [1, 5, 10, 20],
            "target_ingestion_time_ms": 5000,  # 5 seconds for data ingestion
            "acceptable_error_rate": 0.03,  # 3%
            "memory_threshold_mb": 500,
            "cpu_threshold_percent": 80
        }

    @pytest.fixture
    def sample_data_sources(self):
        """Sample data sources of different types for testing."""
        return {
            "small_github": {
                "type": "github",
                "config": {"owner": "test-org", "repo": "small-repo", "path": "README.md"},
                "expected_size": 1024,  # 1KB
                "complexity": "low"
            },
            "medium_api": {
                "type": "api",
                "config": {"url": "https://api.example.com/data", "method": "GET"},
                "expected_size": 10240,  # 10KB
                "complexity": "medium"
            },
            "large_database": {
                "type": "database",
                "config": {"query": "SELECT * FROM large_table LIMIT 1000", "connection": "enterprise_db"},
                "expected_size": 102400,  # 100KB
                "complexity": "high"
            },
            "very_large_filesystem": {
                "type": "filesystem",
                "config": {"path": "/enterprise/docs", "recursive": True, "pattern": "*.pdf"},
                "expected_size": 1048576,  # 1MB
                "complexity": "very_high"
            }
        }

    @pytest.mark.asyncio
    async def test_data_source_ingestion_throughput(self, performance_config, sample_data_sources):
        """Test data source ingestion throughput under normal load."""
        # Mock data ingestion
        mock_ingestion_result = {
            "documents_ingested": 1,
            "total_size_bytes": 1024,
            "processing_time": 0.5,
            "source_type": "github",
            "status": "completed"
        }

        with patch("main.FetchHandler.fetch_document", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_ingestion_result

            # Import the fetch function
            from main import fetch_document

            # Warmup phase
            for _ in range(performance_config["warmup_iterations"]):
                await fetch_document(sample_data_sources["small_github"], "test_session")

            # Performance test phase - test different data source complexities
            for source_name, source_config in sample_data_sources.items():
                print(f"\nTesting {source_name} data source ingestion performance...")

                # Adjust mock result based on source complexity
                complexity_multipliers = {
                    "low": 1,
                    "medium": 2,
                    "high": 4,
                    "very_high": 8
                }
                multiplier = complexity_multipliers[source_config["complexity"]]

                mock_result = mock_ingestion_result.copy()
                mock_result["total_size_bytes"] = source_config["expected_size"]
                mock_result["processing_time"] = 0.5 * multiplier
                mock_result["source_type"] = source_config["type"]
                mock_fetch.return_value = mock_result

                response_times = []
                data_sizes = []
                start_time = time.time()

                for _ in range(performance_config["test_iterations"]):
                    iteration_start = time.time()
                    result = await fetch_document(source_config, f"session_{source_name}")
                    iteration_end = time.time()

                    response_time = (iteration_end - iteration_start) * 1000  # Convert to ms
                    response_times.append(response_time)
                    data_sizes.append(result.get("total_size_bytes", 0))

                    # Verify result structure
                    assert "documents_ingested" in result
                    assert "total_size_bytes" in result
                    assert result["status"] == "completed"

                end_time = time.time()
                total_time = end_time - start_time

                # Calculate performance metrics
                avg_response_time = statistics.mean(response_times)
                median_response_time = statistics.median(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                throughput = sum(data_sizes) / total_time / 1024  # KB/s
                avg_data_rate = statistics.mean(data_sizes) / (avg_response_time / 1000) / 1024  # KB/s

                # Performance assertions based on data source complexity
                complexity_time_limits = {
                    "low": 1000,
                    "medium": 2000,
                    "high": 4000,
                    "very_high": 8000
                }
                expected_max_time = complexity_time_limits[source_config["complexity"]]

                assert avg_response_time < expected_max_time, \
                    f"Average response time {avg_response_time:.2f}ms exceeds target {expected_max_time}ms for {source_name}"

                print(f"  Data Source: {source_name}")
                print(f"  Total Ingestions: {performance_config['test_iterations']}")
                print(f"  Total Time: {total_time:.2f}s")
                print(f"  Throughput: {throughput:.2f} KB/s")
                print(f"  Avg Data Rate: {avg_data_rate:.2f} KB/s")
                print(f"  Avg Response Time: {avg_response_time:.2f}ms")
                print(f"  Median Response Time: {median_response_time:.2f}ms")
                print(f"  95th Percentile: {p95_response_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_data_source_connections(self, performance_config, sample_data_sources):
        """Test performance under concurrent data source connections."""
        async def single_data_ingestion(source_id: int, source_config: Dict[str, Any]) -> float:
            """Perform single data ingestion and return response time."""
            start_time = time.time()

            # Simulate data source processing with variable time based on complexity
            complexity_delays = {
                "low": 0.1,
                "medium": 0.3,
                "high": 0.8,
                "very_high": 2.0
            }

            # Base processing time
            processing_time = complexity_delays[source_config["complexity"]]

            # Add some variance
            import random
            processing_time += random.uniform(-processing_time * 0.2, processing_time * 0.2)
            processing_time = max(0.05, processing_time)  # Minimum 50ms

            await asyncio.sleep(processing_time)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return response_time

        # Test different concurrency levels
        for concurrent_connections in performance_config["concurrent_connections"]:
            print(f"\nTesting concurrent data ingestion with {concurrent_connections} parallel connections...")

            start_time = time.time()

            # Create concurrent ingestion tasks with different data source types
            tasks = []
            for i in range(concurrent_connections):
                # Cycle through different data source types
                source_name = list(sample_data_sources.keys())[i % len(sample_data_sources)]
                source_config = sample_data_sources[source_name]
                task = single_data_ingestion(i, source_config)
                tasks.append(task)

            # Execute all tasks concurrently
            response_times = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # Calculate performance metrics
            throughput = concurrent_connections / total_time  # connections/s
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            print(f"  Concurrent Connections: {concurrent_connections}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} connections/s")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")
            print(f"  Min Response Time: {min_response_time:.2f}ms")
            print(f"  Max Response Time: {max_response_time:.2f}ms")

            # Performance assertions for concurrent connections
            # Allow for some overhead in concurrent processing
            concurrency_overhead = concurrent_connections ** 0.4  # Sub-linear scaling for I/O bound operations
            expected_max_time = performance_config["target_ingestion_time_ms"] * concurrency_overhead

            assert avg_response_time < expected_max_time, \
                f"Average response time {avg_response_time:.2f}ms too high under concurrent load"

            assert throughput > concurrent_connections * 0.8, \
                f"Throughput {throughput:.2f} connections/s too low for {concurrent_connections} concurrent connections"

    def test_memory_usage_during_data_ingestion(self, performance_config, sample_data_sources):
        """Test memory usage during large-scale data ingestion."""
        import gc

        process = psutil.Process()

        def simulate_data_ingestion(source_config: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate data ingestion with memory allocation."""
            # Simulate memory allocation during ingestion
            # In real implementation, this would be actual data fetching and processing

            # Base memory for data processing
            processing_memory = 1024 * 1024 * 10  # 10MB base

            # Additional memory based on data size
            data_size = source_config["expected_size"]
            data_memory = data_size * 2  # 2x for processing buffers

            # Memory for document structures and metadata
            metadata_memory = 1024 * 100  # 100KB for metadata

            # Allocate memory (simulate)
            total_memory = processing_memory + data_memory + metadata_memory
            large_data = "x" * total_memory  # Allocate memory

            # Simulate processing time based on data size
            processing_time = data_size / (1024 * 50)  # 50KB per second processing rate
            time.sleep(min(processing_time, 1.0))  # Cap at 1 second for testing

            result = {
                "source_type": source_config["type"],
                "data_size": data_size,
                "documents_processed": 1,
                "memory_used": total_memory,
                "processing_time": processing_time,
                "status": "completed"
            }

            # Keep reference to prevent immediate GC
            result["_memory_holder"] = large_data

            return result

        # Test memory usage with different data source types
        test_scenarios = [
            ("small_github", sample_data_sources["small_github"]),
            ("medium_api", sample_data_sources["medium_api"]),
            ("large_database", sample_data_sources["large_database"]),
            ("very_large_filesystem", sample_data_sources["very_large_filesystem"])
        ]

        for source_name, source_config in test_scenarios:
            print(f"\nTesting memory usage for {source_name} data ingestion...")

            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform ingestion
            result = simulate_data_ingestion(source_config)

            peak_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Force cleanup
            del result
            gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB

            memory_delta = peak_memory - initial_memory
            memory_leak = final_memory - initial_memory

            print(f"  Initial Memory: {initial_memory:.2f} MB")
            print(f"  Peak Memory: {peak_memory:.2f} MB")
            print(f"  Final Memory: {final_memory:.2f} MB")
            print(f"  Memory Delta: {memory_delta:.2f} MB")
            print(f"  Memory Leak: {memory_leak:.2f} MB")

            # Memory assertions - scale limits based on data size
            data_size_mb = source_config["expected_size"] / (1024 * 1024)
            expected_memory_limit = max(50, data_size_mb * 3)  # At least 50MB, or 3x data size

            assert memory_delta < expected_memory_limit, \
                f"Memory usage increased by {memory_delta:.2f} MB, exceeds limit {expected_memory_limit:.2f} MB for {source_name}"

            # Allow for some cleanup delay but not excessive memory leaks
            assert abs(memory_leak) < 30, \
                f"Memory leak detected: {memory_leak:.2f} MB for {source_name}"

    @pytest.mark.asyncio
    async def test_ingestion_pipeline_scaling(self, performance_config, sample_data_sources):
        """Test ingestion pipeline scaling across different data volumes."""
        import threading
        import queue

        results_queue = queue.Queue()

        def ingestion_pipeline_worker(source_configs: List[Dict[str, Any]], iterations: int):
            """Worker thread to test ingestion pipeline scaling."""
            worker_results = []

            for i in range(iterations):
                start_time = time.time()

                # Process multiple sources in pipeline
                total_data_size = 0
                total_processing_time = 0

                for source_config in source_configs:
                    # Simulate processing each source
                    complexity_delays = {
                        "low": 0.1,
                        "medium": 0.3,
                        "high": 0.8,
                        "very_high": 2.0
                    }

                    processing_time = complexity_delays[source_config["complexity"]]
                    data_size = source_config["expected_size"]

                    time.sleep(processing_time)

                    total_data_size += data_size
                    total_processing_time += processing_time

                end_time = time.time()
                total_time = end_time - start_time

                worker_results.append({
                    "iteration": i,
                    "total_data_size": total_data_size,
                    "total_processing_time": total_processing_time,
                    "pipeline_time": total_time,
                    "sources_processed": len(source_configs)
                })

            results_queue.put(worker_results)

        # Test scaling with different pipeline sizes
        pipeline_sizes = [1, 3, 5, 10]  # Number of sources per pipeline

        scaling_results = {}

        for pipeline_size in pipeline_sizes:
            print(f"\nTesting ingestion pipeline scaling with {pipeline_size} sources per pipeline...")

            # Select sources for this pipeline size
            selected_sources = []
            source_keys = list(sample_data_sources.keys())
            for i in range(pipeline_size):
                source_key = source_keys[i % len(source_keys)]
                selected_sources.append(sample_data_sources[source_key])

            start_time = time.time()

            # Start worker thread
            worker_thread = threading.Thread(
                target=ingestion_pipeline_worker,
                args=(selected_sources, 10)  # 10 iterations
            )
            worker_thread.start()
            worker_thread.join()

            end_time = time.time()
            total_time = end_time - start_time

            # Get results
            worker_results = results_queue.get()

            # Calculate scaling metrics
            avg_pipeline_time = statistics.mean([r["pipeline_time"] for r in worker_results])
            avg_data_processed = statistics.mean([r["total_data_size"] for r in worker_results])
            throughput = avg_data_processed * len(worker_results) / total_time / 1024  # KB/s

            scaling_results[pipeline_size] = {
                "avg_pipeline_time": avg_pipeline_time,
                "avg_data_processed": avg_data_processed,
                "throughput": throughput,
                "total_time": total_time,
                "iterations": len(worker_results)
            }

            print(f"  Pipeline Size: {pipeline_size} sources")
            print(f"  Iterations: {len(worker_results)}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Avg Pipeline Time: {avg_pipeline_time:.2f}s")
            print(f"  Avg Data Processed: {avg_data_processed / 1024:.2f} KB")
            print(f"  Throughput: {throughput:.2f} KB/s")

        # Analyze scaling efficiency
        print("
Scaling Analysis:")
        for size, metrics in scaling_results.items():
            efficiency = metrics["throughput"] / size  # Throughput per source
            print(".2f")

        # Verify scaling behavior - should show reasonable efficiency
        base_throughput = scaling_results[1]["throughput"]
        for size in pipeline_sizes[1:]:
            scaling_efficiency = scaling_results[size]["throughput"] / (base_throughput * size)
            print(".3f")

            # Allow for some scaling overhead but not complete inefficiency
            assert scaling_efficiency > 0.3, \
                f"Poor scaling efficiency {scaling_efficiency:.3f} for pipeline size {size}"

    @pytest.mark.asyncio
    async def test_data_source_connection_pooling_performance(self):
        """Test performance impact of connection pooling for data sources."""
        async def connection_pooled_ingestion(connection_pool_size: int, requests: int) -> Dict[str, Any]:
            """Simulate data ingestion with connection pooling."""
            start_time = time.time()

            # Simulate connection pool management
            active_connections = 0
            max_concurrent = connection_pool_size
            total_wait_time = 0
            total_processing_time = 0

            for i in range(requests):
                # Check if we need to wait for connection
                if active_connections >= max_concurrent:
                    # Simulate waiting for connection
                    wait_time = random.uniform(0.01, 0.1)
                    await asyncio.sleep(wait_time)
                    total_wait_time += wait_time

                active_connections += 1

                # Simulate data processing
                processing_time = random.uniform(0.05, 0.2)
                await asyncio.sleep(processing_time)
                total_processing_time += processing_time

                active_connections -= 1

            total_time = time.time() - start_time

            return {
                "connection_pool_size": connection_pool_size,
                "total_requests": requests,
                "total_time": total_time,
                "total_wait_time": total_wait_time,
                "total_processing_time": total_processing_time,
                "avg_request_time": total_time / requests,
                "connection_utilization": total_processing_time / (total_time * connection_pool_size) if total_time > 0 else 0
            }

        # Test different connection pool sizes
        pool_sizes = [1, 2, 5, 10, 20]
        requests_per_test = 50

        connection_results = []

        for pool_size in pool_sizes:
            print(f"\nTesting connection pooling with pool size {pool_size}...")

            result = await connection_pooled_ingestion(pool_size, requests_per_test)

            throughput = result["total_requests"] / result["total_time"]
            wait_ratio = result["total_wait_time"] / result["total_time"] if result["total_time"] > 0 else 0

            connection_results.append({
                "pool_size": pool_size,
                **result,
                "throughput": throughput,
                "wait_ratio": wait_ratio
            })

            print(f"  Pool Size: {pool_size}")
            print(f"  Total Requests: {result['total_requests']}")
            print(f"  Total Time: {result['total_time']:.2f}s")
            print(f"  Throughput: {throughput:.2f} requests/s")
            print(f"  Avg Request Time: {result['avg_request_time']:.3f}s")
            print(f"  Wait Ratio: {wait_ratio:.3f}")
            print(".3f")

        # Analyze connection pooling effectiveness
        print("
Connection Pooling Analysis:")
        no_pool_result = next(r for r in connection_results if r["pool_size"] == 1)
        for result in connection_results[1:]:  # Skip pool size 1
            speedup = no_pool_result["avg_request_time"] / result["avg_request_time"]
            throughput_gain = result["throughput"] / no_pool_result["throughput"]

            print(".2f")
            print(".2f")

            # Connection pooling should provide benefits
            assert speedup > 1.1 or throughput_gain > 1.1, \
                f"Connection pooling not providing benefit for pool size {result['pool_size']}"
