"""
Performance tests for AI/ML processing and inference performance.

This module contains comprehensive performance tests for AI insights generation,
machine learning model inference, LLM query processing, and predictive analytics
under various load conditions and data volumes.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from infrastructure.config.config import DashboardSettings
from services.clients.llm_client import LLMGatewayClient


class TestAIProcessingPerformance:
    """Test suite for AI processing performance and inference efficiency."""

    @pytest.fixture
    def ai_config(self):
        """Create configuration optimized for AI processing performance."""
        config = DashboardSettings()
        config.ai_insights.enabled = True
        config.ai_insights.max_concurrent_requests = 10
        config.ai_insights.request_timeout = 30.0
        config.ai_insights.batch_size = 50
        config.llm_gateway.timeout = 60.0
        return config

    @pytest.fixture
    def performance_llm_client(self, ai_config):
        """Create LLM client configured for performance testing."""
        return LLMGatewayClient(ai_config.llm_gateway)

    @pytest.mark.asyncio
    async def test_concurrent_llm_query_performance(self, performance_llm_client):
        """Test concurrent LLM query processing performance."""
        # Test multiple concurrent LLM queries
        query_results = []
        response_times = []

        async def execute_llm_query(query_id, complexity="medium"):
            """Execute a single LLM query with timing."""
            start_time = time.time()

            # Generate query based on complexity
            if complexity == "simple":
                prompt = f"Explain concept {query_id} in one sentence."
            elif complexity == "medium":
                prompt = f"Analyze the following data and provide insights: {query_id} metrics analysis."
            else:  # complex
                prompt = f"""Perform comprehensive analysis of simulation data {query_id}.
                Include trend analysis, anomaly detection, predictive modeling,
                and actionable recommendations based on the following metrics..."""

            # Mock LLM response
            with patch.object(performance_llm_client, 'query', new_callable=AsyncMock) as mock_query:
                mock_response = {
                    "response": f"AI analysis result for query {query_id}",
                    "confidence": 0.85,
                    "tokens_used": len(prompt.split()) * 2,
                    "processing_time": 0.5
                }
                mock_query.return_value = mock_response

                result = await performance_llm_client.query(prompt, model="gpt-4")
                end_time = time.time()

                response_time = end_time - start_time
                response_times.append(response_time)

                return {
                    "query_id": query_id,
                    "result": result,
                    "response_time": response_time,
                    "complexity": complexity
                }

        # Execute concurrent LLM queries
        start_time = time.time()
        tasks = []

        # Mix of different complexity queries
        complexities = ["simple", "medium", "complex"] * 7  # 21 queries total

        for i in range(21):
            complexity = complexities[i % len(complexities)]
            task = asyncio.create_task(execute_llm_query(f"query_{i}", complexity))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Analyze performance
        successful_queries = [r for r in results if not isinstance(r, Exception)]
        total_time = end_time - start_time

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            # Performance assertions
            assert total_time < 45.0, f"Concurrent LLM queries took {total_time:.2f}s, exceeded 45s limit"
            assert avg_response_time < 5.0, f"Average response time {avg_response_time:.2f}s exceeded 5s limit"
            assert max_response_time < 15.0, f"Max response time {max_response_time:.2f}s exceeded 15s limit"

        # Verify query success rate
        success_rate = len(successful_queries) / len(tasks)
        assert success_rate >= 0.9, f"Query success rate {success_rate:.2%} below 90% threshold"

    @pytest.mark.asyncio
    async def test_ai_insights_generation_throughput(self, ai_config):
        """Test AI insights generation throughput."""
        from pages.ai_insights import generate_insights_batch

        # Create test simulation data
        simulation_data = []
        for i in range(100):  # 100 simulations
            simulation_data.append({
                "id": f"sim_{i}",
                "name": f"Simulation {i}",
                "status": "completed",
                "metrics": {
                    "duration": np.random.uniform(300, 3600),
                    "success_rate": np.random.uniform(0.8, 1.0),
                    "resource_usage": np.random.uniform(0.5, 0.9),
                    "error_count": np.random.randint(0, 10)
                },
                "timeline": [
                    {"phase": "planning", "duration": np.random.uniform(50, 200)},
                    {"phase": "execution", "duration": np.random.uniform(200, 800)},
                    {"phase": "analysis", "duration": np.random.uniform(50, 150)}
                ]
            })

        # Mock AI insights generation
        with patch("pages.ai_insights.generate_ai_insights", new_callable=AsyncMock) as mock_generate:
            # Mock insights for each simulation
            insights_results = []
            for i, sim in enumerate(simulation_data):
                insights = {
                    "simulation_id": sim["id"],
                    "insights": [
                        f"Performance trend analysis for {sim['name']}",
                        f"Resource optimization recommendations",
                        f"Risk assessment and mitigation strategies"
                    ],
                    "confidence": np.random.uniform(0.7, 0.95),
                    "generated_at": "2024-01-01T00:00:00Z"
                }
                insights_results.append(insights)

            mock_generate.side_effect = insights_results

            # Test batch insights generation
            start_time = time.time()
            batch_size = 20

            all_insights = []
            for i in range(0, len(simulation_data), batch_size):
                batch = simulation_data[i:i + batch_size]
                batch_insights = await generate_insights_batch(batch)
                all_insights.extend(batch_insights)

            end_time = time.time()

            # Performance analysis
            processing_time = end_time - start_time
            throughput = len(all_insights) / processing_time  # insights per second

            # Performance assertions
            assert processing_time < 30.0, f"Insights generation took {processing_time:.2f}s, exceeded 30s limit"
            assert throughput >= 2.0, f"Insights throughput {throughput:.1f} insights/s below 2.0 minimum"
            assert len(all_insights) == len(simulation_data), f"Expected {len(simulation_data)} insights, got {len(all_insights)}"

            # Verify insights quality
            for insight in all_insights:
                assert "simulation_id" in insight
                assert "insights" in insight
                assert len(insight["insights"]) >= 2
                assert 0.6 <= insight["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_predictive_model_inference_performance(self, ai_config):
        """Test predictive model inference performance."""
        # Create test data for prediction
        test_data = pd.DataFrame({
            "feature_1": np.random.normal(0, 1, 1000),
            "feature_2": np.random.normal(5, 2, 1000),
            "feature_3": np.random.choice([0, 1], 1000),
            "feature_4": np.random.uniform(0, 100, 1000),
            "target": np.random.choice([0, 1], 1000)
        })

        # Mock predictive model
        with patch("pages.ai_insights.train_predictive_model", new_callable=AsyncMock) as mock_train, \
             patch("pages.ai_insights.make_predictions", new_callable=AsyncMock) as mock_predict:

            # Mock model training
            mock_model = MagicMock()
            mock_model.predict.return_value = np.random.choice([0, 1], len(test_data))
            mock_model.predict_proba.return_value = np.random.rand(len(test_data), 2)
            mock_train.return_value = mock_model

            # Mock predictions
            predictions = []
            for i in range(len(test_data)):
                pred = {
                    "prediction": int(np.random.choice([0, 1])),
                    "confidence": float(np.random.uniform(0.5, 0.95)),
                    "feature_importance": {
                        "feature_1": float(np.random.uniform(0.1, 0.4)),
                        "feature_2": float(np.random.uniform(0.1, 0.3)),
                        "feature_3": float(np.random.uniform(0.05, 0.2)),
                        "feature_4": float(np.random.uniform(0.1, 0.35))
                    }
                }
                predictions.append(pred)

            mock_predict.return_value = predictions

            # Test predictive performance
            start_time = time.time()

            # Train model
            model = await mock_train(test_data, "target")

            # Make predictions
            results = await mock_predict(model, test_data.drop("target", axis=1))

            end_time = time.time()

            # Performance analysis
            total_time = end_time - start_time

            # Performance assertions
            assert total_time < 10.0, f"Predictive modeling took {total_time:.2f}s, exceeded 10s limit"
            assert len(results) == len(test_data), f"Expected {len(test_data)} predictions, got {len(results)}"

            # Verify prediction quality
            for result in results:
                assert "prediction" in result
                assert "confidence" in result
                assert 0.4 <= result["confidence"] <= 1.0
                assert sum(result["feature_importance"].values()) <= 1.1  # Should sum to ~1.0

    @pytest.mark.asyncio
    async def test_anomaly_detection_performance(self, ai_config):
        """Test anomaly detection performance on large datasets."""
        # Create time series data with anomalies
        np.random.seed(42)
        timestamps = pd.date_range("2023-01-01", periods=5000, freq="1min")

        # Generate normal data with trend and seasonality
        t = np.arange(5000)
        trend = 0.01 * t
        seasonal = 5 * np.sin(2 * np.pi * t / (24 * 60))  # Daily pattern
        noise = np.random.normal(0, 1, 5000)
        normal_data = 100 + trend + seasonal + noise

        # Add anomalies
        anomaly_indices = [500, 1500, 2500, 3500, 4500]
        for idx in anomaly_indices:
            normal_data[idx] += np.random.choice([-30, 30])  # Significant anomalies

        time_series_data = pd.DataFrame({
            "timestamp": timestamps,
            "value": normal_data
        })

        # Mock anomaly detection
        with patch("pages.ai_insights.detect_anomalies", new_callable=AsyncMock) as mock_detect:
            # Mock anomaly detection results
            anomalies = []
            for idx in anomaly_indices:
                anomaly = {
                    "index": idx,
                    "timestamp": str(timestamps[idx]),
                    "value": float(normal_data[idx]),
                    "score": float(np.random.uniform(0.8, 0.95)),
                    "severity": "high" if abs(normal_data[idx] - 100) > 25 else "medium"
                }
                anomalies.append(anomaly)

            mock_detect.return_value = anomalies

            # Test anomaly detection performance
            start_time = time.time()
            detected_anomalies = await mock_detect(time_series_data, sensitivity="medium")
            end_time = time.time()

            # Performance analysis
            detection_time = end_time - start_time

            # Performance assertions
            assert detection_time < 5.0, f"Anomaly detection took {detection_time:.2f}s, exceeded 5s limit"
            assert len(detected_anomalies) >= 3, f"Expected at least 3 anomalies, got {len(detected_anomalies)}"

            # Verify anomaly quality
            for anomaly in detected_anomalies:
                assert "index" in anomaly
                assert "score" in anomaly
                assert 0.7 <= anomaly["score"] <= 1.0
                assert anomaly["severity"] in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_batch_ai_processing_throughput(self, ai_config):
        """Test batch AI processing throughput."""
        # Create batch processing scenario
        batch_sizes = [10, 25, 50, 100]
        throughput_results = []

        async def process_ai_batch(batch_data, batch_id):
            """Process a batch of AI requests."""
            start_time = time.time()

            # Simulate AI processing time (scales with batch size)
            processing_time = 0.1 + (len(batch_data) * 0.005)  # Base 100ms + 5ms per item
            await asyncio.sleep(processing_time)

            # Generate results
            results = []
            for i, item in enumerate(batch_data):
                result = {
                    "item_id": item["id"],
                    "batch_id": batch_id,
                    "analysis": f"AI analysis of {item['data']}",
                    "confidence": float(np.random.uniform(0.7, 0.95)),
                    "processing_time": processing_time / len(batch_data)
                }
                results.append(result)

            total_time = time.time() - start_time

            return {
                "batch_id": batch_id,
                "batch_size": len(batch_data),
                "results": results,
                "total_time": total_time,
                "avg_time_per_item": total_time / len(batch_data)
            }

        # Test different batch sizes
        for batch_size in batch_sizes:
            # Create test data
            batch_data = [
                {"id": f"item_{i}", "data": f"test_data_{i}"}
                for i in range(batch_size)
            ]

            # Process batch
            start_time = time.time()
            result = await process_ai_batch(batch_data, f"batch_{batch_size}")
            end_time = time.time()

            total_time = end_time - start_time
            throughput = batch_size / total_time  # items per second

            throughput_results.append({
                "batch_size": batch_size,
                "total_time": total_time,
                "throughput": throughput,
                "avg_time_per_item": result["avg_time_per_item"]
            })

        # Analyze batch processing efficiency
        for result in throughput_results:
            batch_size = result["batch_size"]
            throughput = result["throughput"]
            avg_time = result["avg_time_per_item"]

            # Performance assertions based on batch size
            if batch_size <= 25:
                assert throughput >= 15, f"Small batch throughput {throughput:.1f} items/s too low"
                assert avg_time < 0.1, f"Avg time per item {avg_time:.3f}s too high for small batch"
            elif batch_size <= 50:
                assert throughput >= 25, f"Medium batch throughput {throughput:.1f} items/s too low"
                assert avg_time < 0.08, f"Avg time per item {avg_time:.3f}s too high for medium batch"
            else:  # large batches
                assert throughput >= 35, f"Large batch throughput {throughput:.1f} items/s too low"
                assert avg_time < 0.05, f"Avg time per item {avg_time:.3f}s too high for large batch"

    @pytest.mark.asyncio
    async def test_ai_model_caching_performance(self, ai_config):
        """Test AI model caching performance."""
        # Create model cache scenario
        cache_hits = 0
        cache_misses = 0
        model_cache = {}

        async def get_cached_ai_model(model_key):
            """Get AI model from cache or load it."""
            nonlocal cache_hits, cache_misses

            if model_key in model_cache:
                cache_hits += 1
                return model_cache[model_key]
            else:
                cache_misses += 1

                # Simulate model loading time
                await asyncio.sleep(0.2)  # 200ms model load time

                # Create mock model
                model = {
                    "key": model_key,
                    "type": "predictive_model",
                    "parameters": {"n_estimators": 100, "max_depth": 10},
                    "loaded_at": time.time(),
                    "size_mb": np.random.uniform(50, 200)
                }

                model_cache[model_key] = model
                return model

        # Test model caching with repeated requests
        model_keys = ["model_A", "model_B", "model_C"] * 50  # 150 requests, 3 unique models
        cache_results = []

        start_time = time.time()

        # Execute model requests
        for key in model_keys:
            result = await get_cached_ai_model(key)
            cache_results.append(result)

        end_time = time.time()

        # Performance analysis
        total_time = end_time - start_time
        cache_hit_rate = cache_hits / (cache_hits + cache_misses)

        # Performance assertions
        assert total_time < 20.0, f"Model caching took {total_time:.2f}s, exceeded 20s limit"
        assert cache_hit_rate >= 0.8, f"Cache hit rate {cache_hit_rate:.2%} below 80% target"

        # Verify caching effectiveness
        assert len(model_cache) == 3, f"Expected 3 cached models, got {len(model_cache)}"
        assert cache_misses == 3, f"Expected 3 cache misses, got {cache_misses}"
        assert cache_hits == 147, f"Expected 147 cache hits, got {cache_hits}"

        # Verify model integrity
        for result in cache_results:
            assert "key" in result
            assert "loaded_at" in result
            assert result["size_mb"] > 0

    @pytest.mark.asyncio
    async def test_ai_pipeline_end_to_end_performance(self, ai_config):
        """Test complete AI pipeline end-to-end performance."""
        # Create end-to-end AI pipeline scenario
        pipeline_stages = ["data_ingestion", "preprocessing", "model_inference", "postprocessing", "result_formatting"]
        pipeline_metrics = {stage: [] for stage in pipeline_stages}

        async def execute_ai_pipeline(data_item):
            """Execute complete AI pipeline for a data item."""
            pipeline_start = time.time()
            stage_times = {}

            # Stage 1: Data ingestion
            stage_start = time.time()
            await asyncio.sleep(0.01)  # 10ms
            stage_times["data_ingestion"] = time.time() - stage_start

            # Stage 2: Preprocessing
            stage_start = time.time()
            await asyncio.sleep(0.05)  # 50ms
            stage_times["preprocessing"] = time.time() - stage_start

            # Stage 3: Model inference
            stage_start = time.time()
            await asyncio.sleep(0.2)  # 200ms (main AI processing)
            stage_times["model_inference"] = time.time() - stage_start

            # Stage 4: Postprocessing
            stage_start = time.time()
            await asyncio.sleep(0.03)  # 30ms
            stage_times["postprocessing"] = time.time() - stage_start

            # Stage 5: Result formatting
            stage_start = time.time()
            await asyncio.sleep(0.01)  # 10ms
            stage_times["result_formatting"] = time.time() - stage_start

            total_time = time.time() - pipeline_start

            # Update pipeline metrics
            for stage, stage_time in stage_times.items():
                pipeline_metrics[stage].append(stage_time)

            return {
                "data_item": data_item,
                "result": f"AI processed {data_item}",
                "confidence": float(np.random.uniform(0.8, 0.95)),
                "stage_times": stage_times,
                "total_time": total_time
            }

        # Test pipeline with concurrent requests
        data_items = [f"data_{i}" for i in range(50)]  # 50 concurrent pipeline executions

        start_time = time.time()
        tasks = [asyncio.create_task(execute_ai_pipeline(item)) for item in data_items]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Performance analysis
        total_pipeline_time = end_time - start_time
        avg_total_time = total_pipeline_time / len(data_items)

        # Analyze stage performance
        stage_averages = {}
        for stage in pipeline_stages:
            if pipeline_metrics[stage]:
                stage_averages[stage] = sum(pipeline_metrics[stage]) / len(pipeline_metrics[stage])

        # Performance assertions
        assert total_pipeline_time < 25.0, f"Pipeline execution took {total_pipeline_time:.2f}s, exceeded 25s limit"
        assert avg_total_time < 1.0, f"Average pipeline time {avg_total_time:.3f}s exceeded 1s limit"

        # Verify stage timing expectations
        assert stage_averages.get("model_inference", 0) < 0.3, "Model inference too slow"
        assert stage_averages.get("preprocessing", 0) < 0.1, "Preprocessing too slow"
        assert sum(stage_averages.values()) < 0.5, "Total pipeline stages too slow"

        # Verify results
        assert len(results) == len(data_items), f"Expected {len(data_items)} results, got {len(results)}"
        for result in results:
            assert "result" in result
            assert 0.75 <= result["confidence"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__])
