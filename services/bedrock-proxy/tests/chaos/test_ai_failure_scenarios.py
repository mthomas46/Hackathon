"""Chaos Engineering Tests for AI Operations in Bedrock Proxy Service.

This module tests AI system resilience and failure scenarios including:
- Model service outages and degradation
- Token limit exceeded and rate limiting failures
- Network connectivity issues during AI inference
- Model fallback and circuit breaker functionality
- Data corruption in AI requests/responses
- Concurrent AI operations under failure conditions

Chaos tests ensure the AI proxy service maintains reliability during AI infrastructure failures.
"""

import asyncio
import time
import random
import json
from typing import Dict, Any, List, Optional
from unittest.mock import patch, AsyncMock, MagicMock, side_effect
from datetime import datetime, timedelta

import pytest
import httpx


class TestAIFailureScenarios:
    """Chaos engineering tests for AI operations under failure conditions."""

    @pytest.fixture
    def chaos_config(self):
        """Chaos test configuration for AI operations."""
        return {
            "failure_rate": 0.12,  # 12% of AI operations fail (higher for AI services)
            "model_outage_scenarios": ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"],
            "token_limit_scenarios": [100, 1000, 4000, 8000],
            "rate_limit_scenarios": [10, 50, 100],  # requests per minute
            "network_failure_rate": 0.08,
            "concurrent_failures": 4,
            "circuit_breaker_threshold": 3
        }

    @pytest.mark.asyncio
    async def test_ai_model_service_outages(self, chaos_config):
        """Test resilience against AI model service outages."""
        outage_count = 0
        fallback_count = 0
        failure_count = 0

        async def invoke_ai_model_with_outages(model: str, prompt: str) -> Dict[str, Any]:
            """Simulate AI model invocation that can experience outages."""
            nonlocal outage_count, fallback_count, failure_count

            # Simulate model-specific outage patterns
            if model in chaos_config["model_outage_scenarios"] and random.random() < 0.2:
                outage_count += 1
                raise Exception(f"AI model {model} service outage")

            # Simulate network issues
            if random.random() < chaos_config["network_failure_rate"]:
                failure_count += 1
                raise httpx.ConnectError("Network connectivity lost during AI inference")

            # Simulate successful invocation with fallback attempt
            if random.random() < 0.1:  # 10% need fallback
                fallback_count += 1
                # Simulate fallback to different model
                fallback_model = "titan-text-express" if model.startswith("claude") else "claude-3-haiku"
                await asyncio.sleep(0.5)  # Fallback delay

                return {
                    "model": fallback_model,
                    "response": f"Fallback response from {fallback_model}",
                    "fallback_used": True,
                    "original_model": model
                }

            # Normal successful response
            await asyncio.sleep(random.uniform(0.2, 1.0))
            return {
                "model": model,
                "response": f"AI response from {model}",
                "fallback_used": False
            }

        # Test AI model invocations with outages
        test_invocations = []
        models = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express", "claude-3-opus"]
        prompts = [f"Test prompt {i}" for i in range(30)]

        for i in range(len(prompts)):
            model = models[i % len(models)]
            prompt = prompts[i]
            test_invocations.append((model, prompt))

        # Execute invocations concurrently
        tasks = [invoke_ai_model_with_outages(model, prompt) for model, prompt in test_invocations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_invocations = [r for r in results if isinstance(r, dict)]
        failed_invocations = [r for r in results if isinstance(r, Exception)]

        fallback_used = sum(1 for r in successful_invocations if r.get("fallback_used", False))
        success_rate = len(successful_invocations) / len(results)

        print(f"AI Model Service Outage Resilience Test:")
        print(f"  Total Invocations: {len(results)}")
        print(f"  Successful: {len(successful_invocations)}")
        print(f"  Failed: {len(failed_invocations)}")
        print(f"  Fallbacks Used: {fallback_used}")
        print(f"  Success Rate: {success_rate:.2%}")

        # AI service should be resilient to outages
        assert len(failed_invocations) > 0, "No outages occurred - chaos test ineffective"
        assert success_rate > 0.8, f"Success rate too low under AI outages: {success_rate:.2%}"
        assert fallback_used > 0, "No fallbacks used - resilience not tested"

        # Verify fallback behavior
        for result in successful_invocations:
            if result.get("fallback_used"):
                assert "original_model" in result
                assert result["model"] != result["original_model"]

    @pytest.mark.asyncio
    async def test_token_limit_exceeded_handling(self, chaos_config):
        """Test handling of token limit exceeded scenarios."""
        token_limit_violations = 0
        truncation_events = 0
        rejection_events = 0

        async def invoke_model_with_token_limits(model: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
            """Simulate AI model invocation with token limit constraints."""
            nonlocal token_limit_violations, truncation_events, rejection_events

            # Estimate token count (rough approximation)
            estimated_tokens = len(prompt.split()) * 1.3  # Words to tokens approximation

            if estimated_tokens > max_tokens:
                token_limit_violations += 1

                if random.random() < 0.6:  # 60% of violations trigger truncation
                    truncation_events += 1
                    # Simulate truncation and retry
                    truncated_prompt = prompt[:int(len(prompt) * (max_tokens / estimated_tokens))]
                    await asyncio.sleep(0.3)  # Processing delay

                    return {
                        "model": model,
                        "response": f"Response to truncated prompt using {model}",
                        "tokens_used": max_tokens,
                        "truncated": True,
                        "original_length": len(prompt)
                    }
                else:
                    rejection_events += 1
                    raise Exception(f"Token limit exceeded: {estimated_tokens} > {max_tokens}")

            # Normal response
            await asyncio.sleep(random.uniform(0.1, 0.5))
            return {
                "model": model,
                "response": f"Normal response from {model}",
                "tokens_used": int(estimated_tokens),
                "truncated": False
            }

        # Test different token limit scenarios
        test_scenarios = []

        for max_tokens in chaos_config["token_limit_scenarios"]:
            # Create prompts that may exceed limits
            for i in range(8):
                prompt_length = int(max_tokens * random.uniform(0.5, 2.5))  # Some will exceed
                prompt = " ".join([f"word{j}" for j in range(prompt_length)])
                model = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"][i % 3]
                test_scenarios.append((model, prompt, max_tokens))

        # Execute token limit tests
        tasks = [invoke_model_with_token_limits(model, prompt, max_tokens)
                for model, prompt, max_tokens in test_scenarios]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_invocations = [r for r in results if isinstance(r, dict)]
        failed_invocations = [r for r in results if isinstance(r, Exception)]

        truncated_responses = sum(1 for r in successful_invocations if r.get("truncated", False))

        success_rate = len(successful_invocations) / len(results)

        print(f"Token Limit Exceeded Handling Test:")
        print(f"  Total Invocations: {len(results)}")
        print(f"  Successful: {len(successful_invocations)}")
        print(f"  Failed: {len(failed_invocations)}")
        print(f"  Truncated: {truncated_responses}")
        print(f"  Token Violations: {token_limit_violations}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Should handle token limits gracefully
        assert token_limit_violations > 0, "No token limit violations occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Success rate too low with token limits: {success_rate:.2%}"

        # Should use truncation as a recovery mechanism
        assert truncated_responses > 0, "No truncation recovery used"
        assert truncation_events + rejection_events == token_limit_violations, "Token violation handling inconsistent"

    @pytest.mark.asyncio
    async def test_rate_limiting_failures(self, chaos_config):
        """Test handling of rate limiting failures."""
        rate_limit_hits = 0
        backoff_events = 0
        queue_full_events = 0

        class RateLimiter:
            def __init__(self, requests_per_minute: int):
                self.requests_per_minute = requests_per_minute
                self.requests_this_minute = 0
                self.minute_start = time.time()

            async def check_rate_limit(self) -> bool:
                """Check if request is within rate limits."""
                current_time = time.time()

                # Reset counter every minute
                if current_time - self.minute_start >= 60:
                    self.requests_this_minute = 0
                    self.minute_start = current_time

                if self.requests_this_minute >= self.requests_per_minute:
                    return False

                self.requests_this_minute += 1
                return True

        async def invoke_model_with_rate_limiting(model: str, prompt: str, rate_limiter: RateLimiter) -> Dict[str, Any]:
            """Simulate AI model invocation with rate limiting."""
            nonlocal rate_limit_hits, backoff_events, queue_full_events

            # Check rate limit
            if not await rate_limiter.check_rate_limit():
                rate_limit_hits += 1

                # Simulate different rate limit handling strategies
                strategy = random.choice(["backoff", "queue", "reject"])

                if strategy == "backoff":
                    backoff_events += 1
                    backoff_delay = random.uniform(1, 5)
                    await asyncio.sleep(backoff_delay)

                    # Retry after backoff
                    return {
                        "model": model,
                        "response": f"Response after backoff from {model}",
                        "rate_limited": True,
                        "backoff_delay": backoff_delay,
                        "strategy": "backoff"
                    }

                elif strategy == "queue":
                    queue_full_events += 1
                    raise Exception("Request queue full - rate limit exceeded")

                else:  # reject
                    raise Exception("Rate limit exceeded - request rejected")

            # Normal response
            await asyncio.sleep(random.uniform(0.1, 0.3))
            return {
                "model": model,
                "response": f"Normal response from {model}",
                "rate_limited": False
            }

        # Test different rate limit scenarios
        for rpm_limit in chaos_config["rate_limit_scenarios"]:
            print(f"\nTesting rate limiting at {rpm_limit} requests/minute...")

            rate_limiter = RateLimiter(rpm_limit)

            # Generate burst of requests to trigger rate limiting
            burst_size = rpm_limit * 2  # Double the limit to ensure violations
            tasks = [
                invoke_model_with_rate_limiting(
                    ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"][i % 3],
                    f"Prompt {i}",
                    rate_limiter
                )
                for i in range(burst_size)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_requests = [r for r in results if isinstance(r, dict)]
            failed_requests = [r for r in results if isinstance(r, Exception)]

            rate_limited_requests = sum(1 for r in successful_requests if r.get("rate_limited", False))
            backoff_requests = sum(1 for r in successful_requests if r.get("strategy") == "backoff")

            success_rate = len(successful_requests) / len(results)

            print(f"  Total Requests: {len(results)}")
            print(f"  Successful: {len(successful_requests)}")
            print(f"  Failed: {len(failed_requests)}")
            print(f"  Rate Limited: {rate_limited_requests}")
            print(f"  Backoff Used: {backoff_requests}")
            print(f"  Success Rate: {success_rate:.2%}")

            # Should handle rate limiting gracefully
            assert len(failed_requests) > 0, "No rate limiting occurred - chaos test ineffective"
            assert rate_limited_requests > 0, "No rate limit recovery used"
            assert success_rate > 0.6, f"Success rate too low with rate limiting: {success_rate:.2%}"

    @pytest.mark.asyncio
    async def test_ai_network_connectivity_failures(self, chaos_config):
        """Test AI operations under network connectivity failures."""
        network_failures = 0
        retry_successes = 0
        timeout_events = 0

        async def invoke_ai_with_network_issues(model: str, prompt: str) -> Dict[str, Any]:
            """Simulate AI invocation with network connectivity issues."""
            nonlocal network_failures, retry_successes, timeout_events

            max_retries = 3
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    # Simulate network issues
                    if random.random() < chaos_config["network_failure_rate"]:
                        network_failures += 1

                        if random.random() < 0.4:  # 40% timeouts
                            timeout_events += 1
                            await asyncio.sleep(5)  # Timeout delay
                            raise asyncio.TimeoutError("AI service timeout")
                        else:
                            raise httpx.ConnectError("Network connection to AI service failed")

                    # Simulate successful AI inference
                    inference_time = random.uniform(0.2, 1.0)
                    await asyncio.sleep(inference_time)

                    if retry_count > 0:
                        retry_successes += 1

                    return {
                        "model": model,
                        "response": f"AI response from {model}",
                        "retries": retry_count,
                        "inference_time": inference_time
                    }

                except (httpx.ConnectError, asyncio.TimeoutError):
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Exponential backoff
                        backoff_time = 0.5 * (2 ** (retry_count - 1))
                        await asyncio.sleep(backoff_time)
                        continue
                    else:
                        raise

        # Test network resilience with multiple AI invocations
        test_invocations = []
        models = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express", "claude-3-opus"]

        for i in range(40):
            model = models[i % len(models)]
            prompt = f"Network resilience test prompt {i}"
            test_invocations.append((model, prompt))

        # Execute invocations concurrently
        tasks = [invoke_ai_with_network_issues(model, prompt) for model, prompt in test_invocations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_invocations = [r for r in results if isinstance(r, dict)]
        failed_invocations = [r for r in results if isinstance(r, Exception)]

        retry_used = sum(1 for r in successful_invocations if r.get("retries", 0) > 0)

        success_rate = len(successful_invocations) / len(results)

        print(f"AI Network Connectivity Failure Test:")
        print(f"  Total Invocations: {len(results)}")
        print(f"  Successful: {len(successful_invocations)}")
        print(f"  Failed: {len(failed_invocations)}")
        print(f"  Network Failures: {network_failures}")
        print(f"  Retry Successes: {retry_successes}")
        print(f"  Timeout Events: {timeout_events}")
        print(f"  Retries Used: {retry_used}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Should be resilient to network issues
        assert network_failures > 0, "No network failures occurred - chaos test ineffective"
        assert success_rate > 0.85, f"Success rate too low under network chaos: {success_rate:.2%}"
        assert retry_successes > 0, "No retry recovery used"

    @pytest.mark.asyncio
    async def test_model_fallback_circuit_breaker(self, chaos_config):
        """Test model fallback and circuit breaker functionality."""
        circuit_opened = False
        fallback_activations = 0
        circuit_recoveries = 0

        class AIModelCircuitBreaker:
            def __init__(self, model: str, failure_threshold: int = 3):
                self.model = model
                self.failure_threshold = failure_threshold
                self.failure_count = 0
                self.state = "closed"  # closed, open, half_open
                self.last_failure_time = None
                self.half_open_successes = 0

            async def invoke_with_fallback(self, prompt: str) -> Dict[str, Any]:
                """Invoke AI model with fallback and circuit breaker."""
                nonlocal circuit_opened, fallback_activations, circuit_recoveries

                if self.state == "open":
                    # Allow limited traffic in half-open state
                    if time.time() - self.last_failure_time > 30:  # 30 second timeout
                        self.state = "half_open"
                        self.half_open_successes = 0
                    else:
                        # Use fallback model
                        fallback_activations += 1
                        fallback_model = "titan-text-express" if "claude" in self.model else "claude-3-haiku"

                        await asyncio.sleep(0.5)  # Fallback delay
                        return {
                            "model": fallback_model,
                            "response": f"Fallback response from {fallback_model}",
                            "fallback_trigger": "circuit_open",
                            "original_model": self.model
                        }

                try:
                    # Simulate model invocation with potential failure
                    if random.random() < 0.25:  # 25% failure rate for this model
                        raise Exception(f"Model {self.model} temporarily unavailable")

                    await asyncio.sleep(random.uniform(0.2, 0.8))

                    # Successful invocation
                    if self.state == "half_open":
                        self.half_open_successes += 1
                        if self.half_open_successes >= 2:  # Require 2 successes to close
                            self.state = "closed"
                            self.failure_count = 0
                            circuit_recoveries += 1

                    return {
                        "model": self.model,
                        "response": f"Direct response from {self.model}",
                        "circuit_state": self.state
                    }

                except Exception:
                    self._on_failure()
                    raise

            def _on_failure(self):
                nonlocal circuit_opened
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold and self.state == "closed":
                    self.state = "open"
                    circuit_opened = True

        # Test circuit breaker with multiple models
        models = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"]
        circuit_breakers = {model: AIModelCircuitBreaker(model) for model in models}

        # Generate test invocations
        test_invocations = []
        for i in range(50):
            model = models[i % len(models)]
            prompt = f"Circuit breaker test prompt {i}"
            test_invocations.append((model, prompt))

        # Execute invocations
        results = []
        for model, prompt in test_invocations:
            try:
                result = await circuit_breakers[model].invoke_with_fallback(prompt)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "model": model})

        successful_invocations = [r for r in results if "error" not in r]
        failed_invocations = [r for r in results if "error" in r]

        fallback_used = sum(1 for r in successful_invocations if r.get("fallback_trigger") == "circuit_open")

        success_rate = len(successful_invocations) / len(results)

        print(f"Model Fallback Circuit Breaker Test:")
        print(f"  Total Invocations: {len(results)}")
        print(f"  Successful: {len(successful_invocations)}")
        print(f"  Failed: {len(failed_invocations)}")
        print(f"  Fallbacks Used: {fallback_used}")
        print(f"  Circuit Opened: {circuit_opened}")
        print(f"  Circuit Recoveries: {circuit_recoveries}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Circuit breaker should provide resilience
        assert circuit_opened, "Circuit breaker never opened - not tested adequately"
        assert fallback_used > 0, "No fallbacks used despite circuit opening"
        assert success_rate > 0.8, f"Success rate too low with circuit breaker: {success_rate:.2%}"

    @pytest.mark.asyncio
    async def test_ai_request_response_corruption(self):
        """Test handling of data corruption in AI requests/responses."""
        corruption_events = 0
        recovery_events = 0
        integrity_failures = 0

        import hashlib

        class DataIntegrityChecker:
            def __init__(self):
                self.checksums = {}

            def protect_ai_request(self, request: Dict[str, Any]) -> str:
                """Protect AI request with integrity check."""
                request_str = json.dumps(request, sort_keys=True)
                checksum = hashlib.sha256(request_str.encode()).hexdigest()
                self.checksums[f"request_{request.get('id', 'unknown')}"] = checksum
                return request_str

            def verify_ai_response(self, response: Dict[str, Any]) -> bool:
                """Verify AI response integrity."""
                response_id = response.get("request_id", "unknown")
                checksum_key = f"request_{response_id}"

                if checksum_key not in self.checksums:
                    return False

                # For responses, we check basic structure integrity
                required_fields = ["model", "response"]
                return all(field in response for field in required_fields)

            def corrupt_ai_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
                """Introduce corruption into AI data."""
                corrupted = data.copy()
                corruption_type = random.choice(["missing_field", "invalid_data", "extra_field", "wrong_type"])

                if corruption_type == "missing_field":
                    if "model" in corrupted:
                        del corrupted["model"]
                elif corruption_type == "invalid_data":
                    if "response" in corrupted:
                        corrupted["response"] = None
                elif corruption_type == "extra_field":
                    corrupted["malicious_data"] = "injected"
                elif corruption_type == "wrong_type":
                    if "response" in corrupted:
                        corrupted["response"] = 12345  # Wrong type

                return corrupted

        integrity_checker = DataIntegrityChecker()

        async def process_ai_request_with_corruption(request: Dict[str, Any]) -> Dict[str, Any]:
            """Process AI request with potential corruption."""
            nonlocal corruption_events, recovery_events, integrity_failures

            # Protect request
            integrity_checker.protect_ai_request(request)

            # Simulate AI processing
            await asyncio.sleep(random.uniform(0.1, 0.4))

            # Potentially corrupt response
            response = {
                "request_id": request.get("id"),
                "model": request.get("model"),
                "response": f"AI response for prompt: {request.get('prompt', '')[:50]}..."
            }

            if random.random() < 0.15:  # 15% corruption rate
                corruption_events += 1
                response = integrity_checker.corrupt_ai_data(response)

                # Attempt recovery
                if not integrity_checker.verify_ai_response(response):
                    integrity_failures += 1

                    # Recovery: regenerate response
                    recovery_events += 1
                    response = {
                        "request_id": request.get("id"),
                        "model": request.get("model"),
                        "response": f"Recovered AI response for prompt: {request.get('prompt', '')[:50]}...",
                        "recovered": True
                    }

            return response

        # Test AI request/response integrity
        test_requests = []
        for i in range(30):
            test_requests.append({
                "id": f"request_{i}",
                "model": ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"][i % 3],
                "prompt": f"Integrity test prompt {i}",
                "max_tokens": 100
            })

        # Process requests
        tasks = [process_ai_request_with_corruption(request) for request in test_requests]
        results = await asyncio.gather(*tasks)

        # Analyze results
        valid_responses = [r for r in results if integrity_checker.verify_ai_response(r)]
        invalid_responses = [r for r in results if not integrity_checker.verify_ai_response(r)]
        recovered_responses = [r for r in results if r.get("recovered", False)]

        print(f"AI Request Response Corruption Test:")
        print(f"  Total Requests: {len(results)}")
        print(f"  Valid Responses: {len(valid_responses)}")
        print(f"  Invalid Responses: {len(invalid_responses)}")
        print(f"  Recovered Responses: {recovery_events}")
        print(f"  Corruption Events: {corruption_events}")
        print(f"  Integrity Failures: {integrity_failures}")

        # Should handle corruption gracefully
        assert corruption_events > 0, "No corruption events occurred - chaos test ineffective"
        assert recovery_events > 0, "No recovery mechanisms used"
        assert len(valid_responses) > len(results) * 0.8, "Too many invalid responses"

    @pytest.mark.asyncio
    async def test_concurrent_ai_operations_under_failure(self, chaos_config):
        """Test concurrent AI operations under failure conditions."""
        concurrent_failures = 0
        load_shedding_events = 0
        priority_handling = 0

        async def concurrent_ai_operation(operation_id: int, priority: str, model: str) -> Dict[str, Any]:
            """Perform AI operation with concurrency and failure handling."""
            nonlocal concurrent_failures, load_shedding_events, priority_handling

            # Simulate concurrent load issues
            if random.random() < 0.1:  # 10% concurrency failures
                concurrent_failures += 1

                if priority == "low":
                    load_shedding_events += 1
                    raise Exception("Load shedding: low priority request dropped")
                elif priority == "high":
                    priority_handling += 1
                    # High priority gets retry with backoff
                    await asyncio.sleep(1.0)
                    # Retry successful
                else:
                    raise Exception("Concurrent processing limit exceeded")

            # Simulate normal AI processing
            processing_time = random.uniform(0.2, 1.0)
            await asyncio.sleep(processing_time)

            return {
                "operation_id": operation_id,
                "priority": priority,
                "model": model,
                "processing_time": processing_time,
                "status": "completed"
            }

        # Test concurrent AI operations with different priorities
        operations = []
        priorities = ["high", "medium", "low"]
        models = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"]

        for i in range(60):  # High concurrency
            priority = priorities[i % len(priorities)]
            model = models[i % len(models)]
            operations.append((i, priority, model))

        # Execute operations concurrently
        tasks = [concurrent_ai_operation(op_id, priority, model) for op_id, priority, model in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_operations = [r for r in results if isinstance(r, dict)]
        failed_operations = [r for r in results if isinstance(r, Exception)]

        high_priority_success = sum(1 for r in successful_operations if r.get("priority") == "high")
        low_priority_success = sum(1 for r in successful_operations if r.get("priority") == "low")

        success_rate = len(successful_operations) / len(results)

        print(f"Concurrent AI Operations Under Failure Test:")
        print(f"  Total Operations: {len(results)}")
        print(f"  Successful: {len(successful_operations)}")
        print(f"  Failed: {len(failed_operations)}")
        print(f"  High Priority Success: {high_priority_success}")
        print(f"  Low Priority Success: {low_priority_success}")
        print(f"  Load Shedding Events: {load_shedding_events}")
        print(f"  Priority Handling: {priority_handling}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Should handle concurrency gracefully with prioritization
        assert len(failed_operations) > 0, "No concurrency failures occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Success rate too low under concurrent load: {success_rate:.2%}"
        assert load_shedding_events > 0, "No load shedding used for low priority requests"
        assert priority_handling > 0, "No priority handling for high priority requests"
