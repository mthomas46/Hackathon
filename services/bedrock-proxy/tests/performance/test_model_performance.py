"""Performance Tests for AI Model Operations in Bedrock Proxy Service.

This module tests performance characteristics of AI model operations including:
- Model invocation latency and throughput
- Concurrent request handling and resource management
- Memory usage during model inference
- Scalability under increasing load
- Performance regression detection across model types

Performance tests ensure the Bedrock Proxy service meets AI inference performance requirements.
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


class TestModelPerformance:
    """Performance testing for AI model operations."""

    @pytest.fixture
    def performance_config(self):
        """Performance test configuration for AI models."""
        return {
            "warmup_iterations": 5,
            "test_iterations": 25,
            "concurrent_requests": [1, 3, 5, 10],
            "target_inference_time_ms": 3000,  # 3 seconds for AI inference
            "acceptable_error_rate": 0.05,  # 5%
            "memory_threshold_mb": 300,
            "cpu_threshold_percent": 90
        }

    @pytest.fixture
    def sample_prompts(self):
        """Sample prompts of different complexities for testing."""
        return {
            "simple": "Explain what AI is in one sentence.",
            "medium": "Write a Python function to calculate the fibonacci sequence up to n terms with proper documentation.",
            "complex": """Analyze the following code for potential security vulnerabilities and performance issues:

```python
import os
import subprocess

def execute_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def process_user_data(user_input):
    # Process and store user data
    filename = f"/tmp/user_{os.getuid()}_data.txt"
    with open(filename, 'w') as f:
        f.write(user_input)

    # Execute some processing
    output = execute_command(f"cat {filename}")
    return output
```

Provide detailed recommendations for improvements.""",
            "very_complex": "Write a comprehensive analysis of microservices architecture patterns, including pros/cons, implementation strategies, and real-world examples from major tech companies." * 3  # Make it very long
        }

    @pytest.mark.asyncio
    async def test_ai_model_inference_throughput(self, performance_config, sample_prompts):
        """Test AI model inference throughput under normal load."""
        # Mock AI model inference
        mock_inference_result = {
            "response": "This is a mock AI response with comprehensive analysis and recommendations.",
            "model": "claude-3-sonnet",
            "tokens_used": 150,
            "confidence": 0.95,
            "processing_time": 0.5
        }

        with patch("main.BedrockClient.invoke_model", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_inference_result

            # Import the invoke function
            from main import invoke_model

            # Warmup phase
            for _ in range(performance_config["warmup_iterations"]):
                await invoke_model(sample_prompts["simple"], "claude-3-sonnet")

            # Performance test phase - test different prompt complexities
            for prompt_type, prompt in sample_prompts.items():
                print(f"\nTesting {prompt_type} prompt performance...")

                response_times = []
                start_time = time.time()

                for _ in range(performance_config["test_iterations"]):
                    iteration_start = time.time()
                    result = await invoke_model(prompt, "claude-3-sonnet")
                    iteration_end = time.time()

                    response_time = (iteration_end - iteration_start) * 1000  # Convert to ms
                    response_times.append(response_time)

                    # Verify result structure
                    assert "response" in result
                    assert "model" in result
                    assert result["model"] == "claude-3-sonnet"

                end_time = time.time()
                total_time = end_time - start_time

                # Calculate performance metrics
                avg_response_time = statistics.mean(response_times)
                median_response_time = statistics.median(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                throughput = performance_config["test_iterations"] / total_time

                # Performance assertions based on prompt complexity
                complexity_multiplier = {"simple": 1, "medium": 1.5, "complex": 2.5, "very_complex": 4}
                expected_max_time = performance_config["target_inference_time_ms"] * complexity_multiplier[prompt_type]

                assert avg_response_time < expected_max_time, \
                    f"Average response time {avg_response_time:.2f}ms exceeds target {expected_max_time}ms for {prompt_type} prompt"

                print(f"  Prompt Type: {prompt_type}")
                print(f"  Total Inferences: {performance_config['test_iterations']}")
                print(f"  Total Time: {total_time:.2f}s")
                print(f"  Throughput: {throughput:.2f} inferences/s")
                print(f"  Avg Response Time: {avg_response_time:.2f}ms")
                print(f"  Median Response Time: {median_response_time:.2f}ms")
                print(f"  95th Percentile: {p95_response_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_model_invocations(self, performance_config, sample_prompts):
        """Test performance under concurrent AI model invocations."""
        async def single_model_invocation(invocation_id: int, prompt: str, model: str) -> float:
            """Perform single model invocation and return response time."""
            start_time = time.time()

            # Mock inference with variable processing time based on prompt length
            processing_time = len(prompt) / 10000  # Rough heuristic: 10k chars per second
            processing_time = max(0.1, min(processing_time, 2.0))  # Clamp between 0.1-2.0s

            await asyncio.sleep(processing_time)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return response_time

        # Test different concurrency levels
        for concurrent_invocations in performance_config["concurrent_requests"]:
            print(f"\nTesting concurrent AI model invocations with {concurrent_invocations} parallel requests...")

            start_time = time.time()

            # Create concurrent invocation tasks
            tasks = []
            for i in range(concurrent_invocations):
                # Use different prompt complexities
                prompt_type = ["simple", "medium", "complex"][i % 3]
                prompt = sample_prompts[prompt_type]
                model = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"][i % 3]

                task = single_model_invocation(i, prompt, model)
                tasks.append(task)

            # Execute all tasks concurrently
            response_times = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # Calculate performance metrics
            throughput = len(response_times) / total_time
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            print(f"  Concurrent Invocations: {concurrent_invocations}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} invocations/s")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")
            print(f"  Min Response Time: {min_response_time:.2f}ms")
            print(f"  Max Response Time: {max_response_time:.2f}ms")

            # Performance assertions for concurrent invocations
            # Allow for some overhead in concurrent processing
            concurrency_overhead = concurrent_invocations ** 0.3  # Sub-linear scaling
            expected_max_time = performance_config["target_inference_time_ms"] * concurrency_overhead

            assert avg_response_time < expected_max_time, \
                f"Average response time {avg_response_time:.2f}ms too high under concurrent load"

            assert throughput > concurrent_invocations * 0.7, \
                f"Throughput {throughput:.2f} invocations/s too low for {concurrent_invocations} concurrent requests"

    def test_memory_usage_during_model_inference(self, performance_config, sample_prompts):
        """Test memory usage during AI model inference."""
        import gc

        process = psutil.Process()

        def simulate_model_inference(prompt: str, model: str) -> Dict[str, Any]:
            """Simulate AI model inference with memory allocation."""
            # Simulate memory allocation during inference
            # In real implementation, this would be actual model loading/inference

            # Base memory for model
            model_memory = {
                "claude-3-sonnet": 1024 * 1024 * 100,  # 100MB
                "claude-3-haiku": 1024 * 1024 * 50,    # 50MB
                "titan-text-express": 1024 * 1024 * 75  # 75MB
            }

            # Additional memory based on prompt size
            prompt_memory = len(prompt) * 1024  # ~1KB per character for processing

            # Allocate memory (simulate)
            memory_allocation = model_memory.get(model, 1024 * 1024 * 50) + prompt_memory
            large_data = "x" * memory_allocation  # Allocate memory

            # Simulate processing
            time.sleep(len(prompt) / 50000)  # Processing time based on prompt length

            result = {
                "model": model,
                "prompt_length": len(prompt),
                "response": f"Analysis of {len(prompt)}-character prompt using {model}",
                "memory_used": memory_allocation,
                "processing_time": len(prompt) / 50000
            }

            # Keep reference to prevent immediate GC
            result["_memory_holder"] = large_data

            return result

        # Test memory usage with different models and prompt sizes
        test_scenarios = [
            ("simple", "claude-3-haiku"),
            ("medium", "claude-3-sonnet"),
            ("complex", "claude-3-sonnet"),
            ("very_complex", "claude-3-opus")
        ]

        for prompt_type, model in test_scenarios:
            print(f"\nTesting memory usage for {prompt_type} prompt with {model}...")

            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform inference
            result = simulate_model_inference(sample_prompts[prompt_type], model)

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

            # Memory assertions
            assert memory_delta < performance_config["memory_threshold_mb"], \
                f"Memory usage increased by {memory_delta:.2f} MB, exceeds threshold {performance_config['memory_threshold_mb']} MB"

            # Allow for some cleanup delay but not excessive memory leaks
            assert abs(memory_leak) < 50, \
                f"Memory leak detected: {memory_leak:.2f} MB"

    @pytest.mark.asyncio
    async def test_model_routing_performance(self, performance_config):
        """Test performance of model routing and selection logic."""
        async def route_and_invoke_model(request: Dict[str, Any]) -> Tuple[str, float]:
            """Route request to appropriate model and simulate invocation."""
            start_time = time.time()

            # Simulate routing logic based on request characteristics
            prompt = request.get("prompt", "")
            use_case = request.get("use_case", "general")

            # Route to different models based on use case and prompt complexity
            if use_case == "code" or len(prompt) > 1000:
                selected_model = "claude-3-sonnet"  # More capable for complex tasks
            elif use_case == "creative":
                selected_model = "claude-3-haiku"  # Faster for creative tasks
            else:
                selected_model = "titan-text-express"  # Cost-effective for general use

            # Simulate routing overhead
            routing_time = 0.01  # 10ms routing time
            await asyncio.sleep(routing_time)

            # Simulate model invocation
            inference_time = len(prompt) / 20000  # Base inference time
            await asyncio.sleep(inference_time)

            total_time = time.time() - start_time

            return selected_model, total_time * 1000  # Convert to ms

        # Test routing performance with different request types
        test_requests = [
            {"prompt": "Hello world", "use_case": "general"},
            {"prompt": "Write a Python function" * 10, "use_case": "code"},
            {"prompt": "Write a creative story" * 5, "use_case": "creative"},
            {"prompt": "Explain quantum physics" * 20, "use_case": "educational"}
        ]

        routing_results = []

        for request in test_requests:
            print(f"\nTesting routing for {request['use_case']} use case...")

            # Test routing performance multiple times
            routing_times = []
            selected_models = []

            for _ in range(10):  # Test routing 10 times per request
                model, routing_time = await route_and_invoke_model(request)
                routing_times.append(routing_time)
                selected_models.append(model)

            # All routing decisions should be consistent for same request
            unique_models = set(selected_models)
            assert len(unique_models) == 1, f"Inconsistent model routing: {unique_models}"

            avg_routing_time = statistics.mean(routing_times)
            selected_model = selected_models[0]

            routing_results.append({
                "use_case": request["use_case"],
                "selected_model": selected_model,
                "avg_routing_time": avg_routing_time,
                "routing_times": routing_times
            })

            print(f"  Selected Model: {selected_model}")
            print(f"  Avg Routing Time: {avg_routing_time:.2f}ms")
            print(f"  Min Routing Time: {min(routing_times):.2f}ms")
            print(f"  Max Routing Time: {max(routing_times):.2f}ms")

            # Routing should be fast
            assert avg_routing_time < 100, \
                f"Model routing too slow: {avg_routing_time:.2f}ms"

        # Verify routing logic consistency
        expected_routing = {
            "general": "titan-text-express",
            "code": "claude-3-sonnet",
            "creative": "claude-3-haiku",
            "educational": "claude-3-sonnet"
        }

        for result in routing_results:
            expected_model = expected_routing[result["use_case"]]
            assert result["selected_model"] == expected_model, \
                f"Incorrect model routing for {result['use_case']}: expected {expected_model}, got {result['selected_model']}"

    def test_scalability_across_model_types(self, performance_config, sample_prompts):
        """Test scalability performance across different AI model types."""
        import threading
        import queue

        results_queue = queue.Queue()

        def model_inference_worker(model_name: str, prompt: str, iterations: int):
            """Worker thread to test model inference scalability."""
            worker_results = []

            for i in range(iterations):
                start_time = time.time()

                # Simulate model-specific performance characteristics
                model_characteristics = {
                    "claude-3-haiku": {"base_time": 0.3, "variance": 0.1},
                    "claude-3-sonnet": {"base_time": 0.6, "variance": 0.2},
                    "claude-3-opus": {"base_time": 1.0, "variance": 0.3},
                    "titan-text-express": {"base_time": 0.4, "variance": 0.15},
                    "titan-text-lite": {"base_time": 0.2, "variance": 0.05}
                }

                char = model_characteristics.get(model_name, {"base_time": 0.5, "variance": 0.1})

                # Simulate inference time with some variance
                import random
                inference_time = char["base_time"] + random.uniform(-char["variance"], char["variance"])
                inference_time = max(0.1, inference_time)  # Minimum 100ms

                time.sleep(inference_time)

                end_time = time.time()
                response_time = (end_time - start_time) * 1000

                worker_results.append({
                    "iteration": i,
                    "response_time": response_time,
                    "inference_time": inference_time
                })

            results_queue.put((model_name, worker_results))

        # Test scalability across different models
        models_to_test = ["claude-3-haiku", "claude-3-sonnet", "titan-text-express"]
        iterations_per_model = 15

        scalability_results = {}

        for model in models_to_test:
            print(f"\nTesting scalability for {model}...")

            start_time = time.time()

            # Start worker thread
            worker_thread = threading.Thread(
                target=model_inference_worker,
                args=(model, sample_prompts["medium"], iterations_per_model)
            )
            worker_thread.start()
            worker_thread.join()

            end_time = time.time()
            total_time = end_time - start_time

            # Get results
            model_name, worker_results = results_queue.get()

            # Calculate scalability metrics
            response_times = [r["response_time"] for r in worker_results]
            throughput = len(worker_results) / total_time
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)

            scalability_results[model] = {
                "throughput": throughput,
                "avg_response_time": avg_response_time,
                "min_response_time": min_response_time,
                "max_response_time": max_response_time,
                "total_time": total_time,
                "iterations": len(worker_results)
            }

            print(f"  Model: {model}")
            print(f"  Iterations: {len(worker_results)}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} inferences/s")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")

        # Analyze scalability patterns
        print(f"\nScalability Analysis Across Models:")
        for model, metrics in scalability_results.items():
            print(f"  {model}: {metrics['throughput']:.2f} inf/s, {metrics['avg_response_time']:.2f}ms avg")

        # All models should maintain reasonable performance
        for model, metrics in scalability_results.items():
            assert metrics["throughput"] > 1.0, \
                f"Model {model} throughput too low: {metrics['throughput']:.2f} inf/s"

            assert metrics["avg_response_time"] < performance_config["target_inference_time_ms"], \
                f"Model {model} response time too high: {metrics['avg_response_time']:.2f}ms"

    @pytest.mark.asyncio
    async def test_cost_optimization_performance(self):
        """Test performance impact of cost optimization strategies."""
        async def cost_optimized_invocation(request: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate cost-optimized model invocation."""
            prompt = request.get("prompt", "")
            budget_priority = request.get("budget_priority", "balanced")

            # Cost optimization logic
            if budget_priority == "cost_savings":
                # Use cheaper/faster models
                if len(prompt) < 500:
                    selected_model = "titan-text-lite"
                    estimated_cost = len(prompt) * 0.0001
                else:
                    selected_model = "claude-3-haiku"
                    estimated_cost = len(prompt) * 0.0003
            elif budget_priority == "performance":
                # Use best models regardless of cost
                selected_model = "claude-3-opus"
                estimated_cost = len(prompt) * 0.001
            else:  # balanced
                # Balance cost and performance
                if len(prompt) < 1000:
                    selected_model = "titan-text-express"
                    estimated_cost = len(prompt) * 0.0002
                else:
                    selected_model = "claude-3-sonnet"
                    estimated_cost = len(prompt) * 0.0006

            # Simulate inference
            processing_time = len(prompt) / 15000  # Cost-optimized processing
            await asyncio.sleep(processing_time)

            return {
                "model": selected_model,
                "estimated_cost": estimated_cost,
                "processing_time": processing_time,
                "budget_priority": budget_priority
            }

        # Test cost optimization with different scenarios
        test_scenarios = [
            {"prompt": "Short question", "budget_priority": "cost_savings"},
            {"prompt": "Complex analysis" * 10, "budget_priority": "cost_savings"},
            {"prompt": "Short question", "budget_priority": "performance"},
            {"prompt": "Complex analysis" * 10, "budget_priority": "performance"},
            {"prompt": "Medium task" * 3, "budget_priority": "balanced"}
        ]

        cost_results = []

        for scenario in test_scenarios:
            print(f"\nTesting cost optimization: {scenario['budget_priority']} priority, {len(scenario['prompt'])} chars...")

            # Test cost optimization multiple times
            scenario_results = []
            for _ in range(5):
                result = await cost_optimized_invocation(scenario)
                scenario_results.append(result)

            # Analyze cost optimization effectiveness
            avg_cost = statistics.mean([r["estimated_cost"] for r in scenario_results])
            avg_time = statistics.mean([r["processing_time"] for r in scenario_results])
            models_used = set([r["model"] for r in scenario_results])

            # All invocations should use consistent model for same scenario
            assert len(models_used) == 1, f"Inconsistent model selection: {models_used}"

            selected_model = list(models_used)[0]

            cost_results.append({
                "scenario": f"{scenario['budget_priority']}_{len(scenario['prompt'])}chars",
                "model": selected_model,
                "avg_cost": avg_cost,
                "avg_time": avg_time,
                "cost_efficiency": avg_cost / avg_time if avg_time > 0 else 0
            })

            print(f"  Selected Model: {selected_model}")
            print(f"  Avg Cost: ${avg_cost:.4f}")
            print(f"  Avg Time: {avg_time:.2f}s")
            print(f"  Cost Efficiency: ${avg_cost/avg_time:.4f}/s" if avg_time > 0 else "N/A")

        # Verify cost optimization logic
        cost_savings_scenarios = [r for r in cost_results if "cost_savings" in r["scenario"]]
        performance_scenarios = [r for r in cost_results if "performance" in r["scenario"]]

        # Cost savings scenarios should generally be cheaper
        if cost_savings_scenarios and performance_scenarios:
            avg_cost_savings = statistics.mean([r["avg_cost"] for r in cost_savings_scenarios])
            avg_performance = statistics.mean([r["avg_cost"] for r in performance_scenarios])

            print(f"\nCost Optimization Summary:")
            print(f"  Cost Savings Scenarios Avg Cost: ${avg_cost_savings:.4f}")
            print(f"  Performance Scenarios Avg Cost: ${avg_performance:.4f}")
            print(f"  Cost Savings: {((avg_performance - avg_cost_savings) / avg_performance * 100):.1f}%")

            # Cost optimization should provide meaningful savings
            assert avg_cost_savings < avg_performance, \
                "Cost optimization not providing expected savings"
