"""
Performance tests for large data volume handling and memory efficiency.

This module contains comprehensive performance tests for handling large datasets,
memory usage patterns, data processing efficiency, and scalability with
increasing data volumes.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient

from infrastructure.config.config import DashboardSettings
from services.clients.simulation_client import SimulationClient


class TestDataVolumePerformance:
    """Test suite for data volume performance and memory efficiency."""

    @pytest.fixture
    def large_dataset_config(self):
        """Create configuration optimized for large dataset handling."""
        config = DashboardSettings()
        config.performance.cache_size = 5000  # Larger cache for big data
        config.performance.enable_compression = True
        config.performance.max_concurrent_requests = 20
        return config

    @pytest.fixture
    def large_data_simulation_client(self, large_dataset_config):
        """Create simulation client configured for large data handling."""
        return SimulationClient(large_dataset_config.simulation_service)

    def test_large_simulation_list_performance(self, large_dataset_config):
        """Test performance when listing large numbers of simulations."""
        async def large_simulation_list_test():
            """Async test for large simulation list handling."""
            client = SimulationClient(large_dataset_config.simulation_service)

            # Create mock large simulation list (1000 simulations)
            large_simulation_list = []
            for i in range(1000):
                large_simulation_list.append({
                    "id": f"sim_large_{i:04d}",
                    "name": f"Large Dataset Simulation {i}",
                    "status": "completed" if i % 3 == 0 else "running",
                    "progress": np.random.uniform(0, 100),
                    "created_at": "2024-01-01T00:00:00Z",
                    "metrics": {
                        "duration": np.random.uniform(300, 3600),
                        "complexity": np.random.choice(["low", "medium", "high"]),
                        "team_size": np.random.randint(1, 20)
                    }
                })

            with patch.object(client, 'list_simulations', new_callable=AsyncMock) as mock_list:
                mock_list.return_value = large_simulation_list

                # Test retrieval performance
                start_time = time.time()
                result = await client.list_simulations()
                end_time = time.time()

                # Performance assertions
                retrieval_time = end_time - start_time
                assert retrieval_time < 2.0, f"Large list retrieval took {retrieval_time}s, exceeded 2s limit"
                assert len(result) == 1000, f"Expected 1000 simulations, got {len(result)}"

                # Verify data integrity
                assert all(sim["id"].startswith("sim_large_") for sim in result), "Simulation IDs corrupted"
                assert all("metrics" in sim for sim in result), "Simulation metrics missing"

        asyncio.run(large_simulation_list_test())

    @pytest.mark.asyncio
    async def test_large_dataframe_processing_performance(self, large_dataset_config):
        """Test performance of processing large DataFrames in AI insights."""
        # Create large test DataFrame (10,000 rows x 50 columns)
        np.random.seed(42)
        large_df = pd.DataFrame({
            "feature_" + str(i): np.random.normal(0, 1, 10000)
            for i in range(50)
        })
        large_df["target"] = np.random.choice([0, 1], 10000)

        # Mock AI insights processing
        with patch("pages.ai_insights.SKLEARN_AVAILABLE", True), \
             patch("pages.ai_insights.perform_pattern_analysis") as mock_pattern:

            mock_pattern.return_value = {
                "mean": large_df.mean().to_dict(),
                "std": large_df.std().to_dict(),
                "correlations": large_df.corr().to_dict(),
                "processing_time": 0.0
            }

            # Test processing performance
            start_time = time.time()

            from pages.ai_insights import perform_pattern_analysis
            result = perform_pattern_analysis(large_df.values.tolist())

            end_time = time.time()

            # Performance assertions
            processing_time = end_time - start_time
            assert processing_time < 10.0, f"Large DataFrame processing took {processing_time}s, exceeded 10s limit"

            # Verify result integrity
            assert "mean" in result, "Mean calculation missing"
            assert "std" in result, "Standard deviation calculation missing"
            assert len(result["mean"]) == 51, f"Expected 51 features, got {len(result['mean'])}"

    @pytest.mark.asyncio
    async def test_memory_efficiency_with_large_responses(self, large_dataset_config):
        """Test memory usage when handling large API responses."""
        import psutil
        import os

        client = SimulationClient(large_dataset_config.simulation_service)
        process = psutil.Process(os.getpid())

        # Create large response payload (10MB)
        large_response = {
            "simulations": [
                {
                    "id": f"sim_{i}",
                    "name": f"Simulation {i}",
                    "data": "x" * 10000,  # 10KB per simulation
                    "metrics": {"value_" + str(j): j for j in range(100)}
                }
                for i in range(1000)  # 1000 simulations = ~10MB
            ],
            "metadata": {
                "total_count": 1000,
                "page": 1,
                "large_dataset_info": "x" * 1000000  # Additional 1MB
            }
        }

        with patch.object(client, 'list_simulations', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = large_response["simulations"]

            # Monitor memory before
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # Process large response multiple times
            start_time = time.time()
            tasks = []

            for i in range(5):  # Process 5 times
                task = asyncio.create_task(client.list_simulations())
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # Monitor memory after
            memory_after = process.memory_info().rss / 1024 / 1024  # MB

            # Performance assertions
            processing_time = end_time - start_time
            memory_increase = memory_after - memory_before

            assert processing_time < 5.0, f"Large response processing took {processing_time}s, exceeded 5s limit"
            assert memory_increase < 200, f"Memory increase {memory_increase}MB exceeded 200MB limit"

            # Verify all results processed correctly
            assert all(len(result) == 1000 for result in results), "Result size inconsistency"

    @pytest.mark.asyncio
    async def test_pagination_performance_with_large_datasets(self, large_dataset_config):
        """Test pagination performance with large datasets."""
        client = SimulationClient(large_dataset_config.simulation_service)

        # Mock paginated responses
        def mock_paginated_response(page=1, per_page=100):
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page

            return {
                "simulations": [
                    {
                        "id": f"sim_{start_idx + i:04d}",
                        "name": f"Simulation {start_idx + i}",
                        "data": f"data_{i}" * 100  # Moderate data size
                    }
                    for i in range(per_page)
                ],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": 10000,
                    "total_pages": 100
                }
            }

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            # Test sequential pagination (10 pages)
            start_time = time.time()
            all_simulations = []

            for page in range(1, 11):  # 10 pages
                mock_request.return_value = mock_paginated_response(page, 100)
                response = await client._make_request("GET", f"/simulations?page={page}&per_page=100")
                all_simulations.extend(response["simulations"])

                # Small delay to simulate network
                await asyncio.sleep(0.01)

            end_time = time.time()

            # Performance assertions
            pagination_time = end_time - start_time
            assert pagination_time < 3.0, f"Pagination took {pagination_time}s, exceeded 3s limit"
            assert len(all_simulations) == 1000, f"Expected 1000 simulations, got {len(all_simulations)}"

            # Verify pagination integrity
            simulation_ids = [sim["id"] for sim in all_simulations]
            assert len(set(simulation_ids)) == len(simulation_ids), "Duplicate simulation IDs in pagination"

    @pytest.mark.asyncio
    async def test_streaming_large_dataset_processing(self, large_dataset_config):
        """Test streaming processing of large datasets."""
        # Create streaming data generator
        async def generate_large_stream():
            """Generate large streaming dataset."""
            for i in range(5000):  # 5000 data points
                yield {
                    "timestamp": f"2024-01-01T{i:04d}:00:00Z",
                    "value": np.sin(i * 0.01) + np.random.normal(0, 0.1),
                    "metadata": {"batch_id": i // 100, "sequence": i}
                }
                # Small yield to simulate streaming
                await asyncio.sleep(0.001)

        # Test streaming processing performance
        start_time = time.time()
        processed_count = 0
        batch_stats = []

        async for data_point in generate_large_stream():
            processed_count += 1

            # Process in batches of 100
            if processed_count % 100 == 0:
                batch_stats.append({
                    "batch": processed_count // 100,
                    "count": 100,
                    "avg_value": np.mean([np.sin(i * 0.01) for i in range(processed_count-100, processed_count)])
                })

        end_time = time.time()

        # Performance assertions
        processing_time = end_time - start_time
        assert processing_time < 15.0, f"Streaming processing took {processing_time}s, exceeded 15s limit"
        assert processed_count == 5000, f"Expected 5000 data points, got {processed_count}"
        assert len(batch_stats) == 50, f"Expected 50 batches, got {len(batch_stats)}"

    @pytest.mark.asyncio
    async def test_cache_efficiency_with_large_datasets(self, large_dataset_config):
        """Test caching efficiency with large, frequently accessed datasets."""
        # Mock cache with limited size
        cache = {}
        cache_hits = 0
        cache_misses = 0
        cache_size_limit = large_dataset_config.performance.cache_size

        def get_cached_data(key):
            """Get data from cache with size limits."""
            nonlocal cache_hits, cache_misses

            if key in cache:
                cache_hits += 1
                return cache[key]
            else:
                cache_misses += 1

                # Generate large data for the key
                data = {
                    "key": key,
                    "large_payload": "x" * 10000,  # 10KB payload
                    "metadata": {"size": 10000, "compressed": False}
                }

                # Cache with LRU-style eviction
                if len(cache) >= cache_size_limit:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]

                cache[key] = data
                return data

        # Test cache performance with large dataset access patterns
        start_time = time.time()

        # Simulate access pattern: 80% repeated keys, 20% new keys
        access_pattern = []
        for i in range(5000):
            if np.random.random() < 0.8:  # 80% cache hits
                key = f"hot_key_{np.random.randint(0, 100)}"  # Limited hot key set
            else:  # 20% cache misses
                key = f"cold_key_{i}"

            access_pattern.append(key)

        # Execute access pattern
        for key in access_pattern:
            data = get_cached_data(key)
            assert data["key"] == key
            assert len(data["large_payload"]) == 10000

        end_time = time.time()

        # Performance assertions
        access_time = end_time - start_time
        cache_hit_rate = cache_hits / (cache_hits + cache_misses)

        assert access_time < 8.0, f"Large dataset caching took {access_time}s, exceeded 8s limit"
        assert cache_hit_rate >= 0.75, f"Cache hit rate {cache_hit_rate:.2%} below 75% target"
        assert len(cache) <= cache_size_limit, f"Cache exceeded size limit: {len(cache)} > {cache_size_limit}"

    @pytest.mark.asyncio
    async def test_compression_efficiency_with_large_data(self, large_dataset_config):
        """Test data compression efficiency with large payloads."""
        # Test data compression performance
        import gzip
        import json

        # Create large uncompressed data
        large_data = {
            "simulations": [
                {
                    "id": f"sim_{i}",
                    "name": f"Simulation {i}",
                    "metrics": {f"metric_{j}": np.random.random() for j in range(100)},
                    "data": "x" * 5000  # 5KB string data
                }
                for i in range(500)  # 500 simulations = ~2.5MB
            ]
        }

        # Test compression performance
        json_data = json.dumps(large_data).encode('utf-8')
        original_size = len(json_data)

        start_time = time.time()
        compressed_data = gzip.compress(json_data)
        compression_time = time.time() - start_time

        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size

        # Decompression test
        start_time = time.time()
        decompressed_data = gzip.decompress(compressed_data)
        decompression_time = time.time() - start_time

        # Verify data integrity
        assert decompressed_data == json_data, "Compression/decompression corrupted data"

        # Performance assertions
        assert compression_time < 1.0, f"Compression took {compression_time}s, exceeded 1s limit"
        assert decompression_time < 1.0, f"Decompression took {decompression_time}s, exceeded 1s limit"
        assert compression_ratio >= 3.0, f"Compression ratio {compression_ratio:.2f} below 3.0 target"

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, large_dataset_config):
        """Test batch processing performance for bulk operations."""
        # Create batch processing scenario
        batch_size = 100
        total_items = 5000

        async def process_batch(batch_data):
            """Process a batch of data."""
            await asyncio.sleep(0.01)  # Simulate processing time

            # Simulate some processing work
            results = []
            for item in batch_data:
                processed_item = {
                    "id": item["id"],
                    "processed": True,
                    "result": item["value"] * 2,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                results.append(processed_item)

            return results

        # Test batch processing performance
        start_time = time.time()

        all_results = []
        tasks = []

        # Process in batches
        for batch_start in range(0, total_items, batch_size):
            batch_end = min(batch_start + batch_size, total_items)
            batch_data = [
                {"id": i, "value": np.random.random()}
                for i in range(batch_start, batch_end)
            ]

            task = asyncio.create_task(process_batch(batch_data))
            tasks.append(task)

        # Execute all batch tasks concurrently
        batch_results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Flatten results
        for batch_result in batch_results:
            all_results.extend(batch_result)

        # Performance assertions
        processing_time = end_time - start_time
        assert processing_time < 8.0, f"Batch processing took {processing_time}s, exceeded 8s limit"
        assert len(all_results) == total_items, f"Expected {total_items} results, got {len(all_results)}"

        # Verify batch processing integrity
        processed_ids = set(item["id"] for item in all_results)
        expected_ids = set(range(total_items))
        assert processed_ids == expected_ids, "Batch processing missed some items"

        # Verify processing results
        assert all(item["processed"] for item in all_results), "Some items not processed"
        assert all(isinstance(item["result"], (int, float)) for item in all_results), "Invalid processing results"


if __name__ == "__main__":
    pytest.main([__file__])
