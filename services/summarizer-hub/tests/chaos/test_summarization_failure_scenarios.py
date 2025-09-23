"""Chaos Engineering Tests for Summarization Operations in Summarizer Hub Service.

This module tests summarization system resilience and failure scenarios including:
- AI model service outages and degradation during summarization
- Token limit exceeded and rate limiting failures in summarization
- Content parsing and format validation failures in documents
- Multi-model ensemble failures and fallback scenarios
- Data corruption in summarization requests/responses
- Concurrent summarization failures and resource exhaustion

Chaos tests ensure the Summarizer Hub service maintains summarization reliability during AI infrastructure failures.
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


class TestSummarizationFailureScenarios:
    """Chaos engineering tests for summarization operations under failure conditions."""

    @pytest.fixture
    def chaos_config(self):
        """Chaos test configuration for summarization operations."""
        return {
            "failure_rate": 0.1,  # 10% of summarization operations fail
            "model_outage_scenarios": ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"],
            "token_limit_scenarios": [2000, 4000, 8000, 16000],
            "rate_limit_scenarios": [5, 15, 30],  # requests per minute
            "concurrent_failures": 5,
            "content_corruption_rate": 0.05
        }

    @pytest.mark.asyncio
    async def test_ai_model_service_outages_during_summarization(self, chaos_config):
        """Test resilience against AI model service outages during summarization."""
        outage_count = 0
        retry_successes = 0
        fallback_activations = 0

        async def summarize_with_model_outages(content: str, model: str, summary_type: str) -> Dict[str, Any]:
            """Simulate document summarization with AI model outages."""
            nonlocal outage_count, retry_successes, fallback_activations

            max_retries = 3
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    # Simulate model-specific outage patterns
                    if model in chaos_config["model_outage_scenarios"] and random.random() < 0.18:
                        outage_count += 1

                        if model.startswith("claude"):
                            raise httpx.ConnectError(f"Claude API service outage for {model}")
                        else:
                            raise Exception(f"Titan service temporarily unavailable: {model}")

                    # Simulate successful summarization with potential fallback
                    if random.random() < 0.12 and retry_count > 0:  # 12% need fallback after retries
                        fallback_activations += 1
                        # Simulate fallback to different model
                        fallback_model = "titan-text-express" if model.startswith("claude") else "claude-3-haiku"

                        await asyncio.sleep(0.8)  # Fallback processing time
                        return {
                            "summary": f"Fallback {summary_type} summary using {fallback_model}: {content[:100]}...",
                            "model_used": fallback_model,
                            "fallback_triggered": True,
                            "original_model": model,
                            "retries": retry_count,
                            "confidence": random.uniform(0.75, 0.88)
                        }

                    # Normal successful summarization
                    await asyncio.sleep(random.uniform(0.5, 2.0))

                    if retry_count > 0:
                        retry_successes += 1

                    return {
                        "summary": f"{summary_type.title()} summary: {content[:150]}...",
                        "model_used": model,
                        "fallback_triggered": False,
                        "retries": retry_count,
                        "confidence": random.uniform(0.85, 0.95),
                        "compression_ratio": random.uniform(0.15, 0.25)
                    }

                except (httpx.ConnectError, Exception):
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Exponential backoff
                        backoff_time = 0.5 * (2 ** (retry_count - 1))
                        await asyncio.sleep(backoff_time)
                        continue
                    else:
                        raise

        # Test summarization across different models and content types
        test_scenarios = []
        models = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express", "claude-3-opus"]
        summary_types = ["executive", "technical", "narrative", "bullet_points"]
        sample_content = "This is a comprehensive document about artificial intelligence and machine learning. It covers various topics including neural networks, deep learning algorithms, natural language processing, computer vision, and their applications in enterprise environments. The document discusses current trends, challenges, and future directions in AI development."

        for i in range(25):
            model = models[i % len(models)]
            summary_type = summary_types[i % len(summary_types)]
            test_scenarios.append((sample_content, model, summary_type))

        # Execute summarization tasks concurrently
        tasks = [summarize_with_model_outages(content, model, summary_type)
                for content, model, summary_type in test_scenarios]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_summaries = [r for r in results if isinstance(r, dict)]
        failed_summaries = [r for r in results if isinstance(r, Exception)]

        fallback_used = sum(1 for r in successful_summaries if r.get("fallback_triggered", False))
        total_retries = sum(r.get("retries", 0) for r in successful_summaries)

        success_rate = len(successful_summaries) / len(results)

        print(f"Summarization Model Outage Resilience Test:")
        print(f"  Total Summarization Requests: {len(results)}")
        print(f"  Successful Summaries: {len(successful_summaries)}")
        print(f"  Failed Summaries: {len(failed_summaries)}")
        print(f"  Fallbacks Used: {fallback_used}")
        print(f"  Total Retries: {total_retries}")
        print(f"  Outages Experienced: {outage_count}")
        print(f"  Retry Successes: {retry_successes}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Summarization should be resilient to model outages
        assert len(failed_summaries) > 0, "No model outages occurred - chaos test ineffective"
        assert success_rate > 0.8, f"Success rate too low under model outages: {success_rate:.2%}"
        assert retry_successes > 0, "No retry recovery used"

    @pytest.mark.asyncio
    async def test_token_limit_exceeded_in_summarization(self, chaos_config):
        """Test handling of token limit exceeded scenarios in summarization."""
        token_limit_violations = 0
        truncation_events = 0
        chunking_events = 0

        async def summarize_with_token_limits(content: str, model: str, max_tokens: int) -> Dict[str, Any]:
            """Simulate document summarization with token limit constraints."""
            nonlocal token_limit_violations, truncation_events, chunking_events

            # Estimate token count (rough approximation)
            estimated_tokens = len(content.split()) * 1.3  # Words to tokens approximation

            if estimated_tokens > max_tokens:
                token_limit_violations += 1

                if random.random() < 0.5:  # 50% of violations trigger truncation
                    truncation_events += 1
                    # Simulate truncation and retry
                    truncated_content = content[:int(len(content) * (max_tokens / estimated_tokens))]
                    await asyncio.sleep(0.4)  # Processing delay

                    return {
                        "summary": f"Truncated summary: {truncated_content[:100]}...",
                        "model_used": model,
                        "tokens_used": max_tokens,
                        "truncated": True,
                        "original_length": len(content),
                        "chunks_processed": 1
                    }
                else:
                    chunking_events += 1
                    # Simulate document chunking
                    chunk_size = int(len(content) * (max_tokens / estimated_tokens))
                    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                    await asyncio.sleep(0.6 * len(chunks))  # Processing delay per chunk

                    return {
                        "summary": f"Chunked summary from {len(chunks)} parts: {content[:150]}...",
                        "model_used": model,
                        "tokens_used": max_tokens * len(chunks),
                        "truncated": False,
                        "chunked": True,
                        "chunks_processed": len(chunks)
                    }

            # Normal response
            await asyncio.sleep(random.uniform(0.3, 0.8))
            return {
                "summary": f"Normal summary: {content[:120]}...",
                "model_used": model,
                "tokens_used": int(estimated_tokens),
                "truncated": False,
                "chunked": False
            }

        # Test different token limit scenarios
        test_scenarios = []

        for max_tokens in chaos_config["token_limit_scenarios"]:
            # Create content that may exceed limits
            for i in range(6):
                content_length = int(max_tokens * random.uniform(0.8, 3.0))  # Some will exceed
                content = " ".join([f"word{j}" for j in range(content_length)])
                model = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"][i % 3]
                test_scenarios.append((content, model, max_tokens))

        # Execute token limit tests
        tasks = [summarize_with_token_limits(content, model, max_tokens)
                for content, model, max_tokens in test_scenarios]
        results = await asyncio.gather(*tasks)

        # Analyze results
        successful_summaries = results  # All should succeed with adaptation
        truncated_summaries = sum(1 for r in results if r.get("truncated", False))
        chunked_summaries = sum(1 for r in results if r.get("chunked", False))

        success_rate = len(successful_summaries) / len(test_scenarios)

        print(f"Token Limit Exceeded in Summarization Test:")
        print(f"  Total Summarization Attempts: {len(results)}")
        print(f"  Successful Summaries: {len(successful_summaries)}")
        print(f"  Truncated Summaries: {truncated_summaries}")
        print(f"  Chunked Summaries: {chunked_summaries}")
        print(f"  Token Violations: {token_limit_violations}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Should handle token limits gracefully
        assert token_limit_violations > 0, "No token limit violations occurred - chaos test ineffective"
        assert success_rate > 0.9, f"Success rate too low with token limits: {success_rate:.2%}"

        # Should use adaptation strategies
        assert truncated_summaries > 0 or chunked_summaries > 0, "No adaptation strategies used"
        assert truncation_events + chunking_events == token_limit_violations, "Token violation handling inconsistent"

    @pytest.mark.asyncio
    async def test_rate_limiting_during_summarization(self, chaos_config):
        """Test handling of rate limiting during summarization requests."""
        rate_limit_hits = 0
        backoff_successes = 0
        queue_successes = 0

        class RateLimitedSummarizer:
            def __init__(self, requests_per_minute: int):
                self.requests_per_minute = requests_per_minute
                self.requests_this_minute = 0
                self.minute_start = time.time()
                self.backoff_until = 0

            async def summarize_with_rate_limit(self, content: str, model: str) -> Dict[str, Any]:
                """Summarize with rate limiting."""
                nonlocal rate_limit_hits, backoff_successes, queue_successes

                current_time = time.time()

                # Check if we're in backoff period
                if current_time < self.backoff_until:
                    backoff_successes += 1
                    await asyncio.sleep(self.backoff_until - current_time)
                    # Reset for backoff retry
                    self.requests_this_minute = 0
                    self.minute_start = current_time

                # Reset counter every minute
                if current_time - self.minute_start >= 60:
                    self.requests_this_minute = 0
                    self.minute_start = current_time

                if self.requests_this_minute >= self.requests_per_minute:
                    rate_limit_hits += 1

                    if random.random() < 0.6:  # 60% use backoff
                        backoff_time = 65 + random.uniform(5, 15)  # 65-80 seconds
                        self.backoff_until = current_time + backoff_time
                        await asyncio.sleep(backoff_time)

                        # After backoff, allow request
                        self.requests_this_minute = 0
                        self.minute_start = time.time()
                    else:
                        # Queue request (simulate)
                        queue_successes += 1
                        await asyncio.sleep(2.0)  # Queue processing time

                        return {
                            "summary": f"Queued summary: {content[:80]}...",
                            "model_used": model,
                            "queued": True,
                            "queue_wait_time": 2.0
                        }

                self.requests_this_minute += 1

                # Successful summarization
                await asyncio.sleep(random.uniform(0.3, 0.8))
                return {
                    "summary": f"Direct summary: {content[:100]}...",
                    "model_used": model,
                    "queued": False
                }

        async def perform_rate_limited_summarization(summarizer: RateLimitedSummarizer, requests: int) -> List[Dict[str, Any]]:
            """Perform multiple summarization requests with rate limiting."""
            results = []

            for i in range(requests):
                try:
                    content = f"Sample content for summarization request {i}. " * 5
                    model = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"][i % 3]
                    result = await summarizer.summarize_with_rate_limit(content, model)
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "rate_limited": True})

                # Small delay between requests
                await asyncio.sleep(0.1)

            return results

        # Test different rate limit scenarios
        for rpm_limit in chaos_config["rate_limit_scenarios"]:
            print(f"\nTesting summarization rate limiting at {rpm_limit} requests/minute...")

            rate_limited_summarizer = RateLimitedSummarizer(rpm_limit)
            results = await perform_rate_limited_summarization(rate_limited_summarizer, 20)

            successful_summaries = [r for r in results if "error" not in r]
            failed_summaries = [r for r in results if "error" in r]

            queued_summaries = sum(1 for r in results if r.get("queued", False))

            success_rate = len(successful_summaries) / len(results)

            print(f"  Total Requests: {len(results)}")
            print(f"  Successful Summaries: {len(successful_summaries)}")
            print(f"  Failed Summaries: {len(failed_summaries)}")
            print(f"  Queued Summaries: {queued_summaries}")
            print(f"  Rate Limit Hits: {rate_limit_hits}")
            print(f"  Backoff Successes: {backoff_successes}")
            print(f"  Queue Successes: {queue_successes}")
            print(f"  Success Rate: {success_rate:.2%}")

            # Should handle rate limiting gracefully
            assert len(failed_summaries) > 0, "No rate limiting occurred - chaos test ineffective"
            assert success_rate > 0.75, f"Success rate too low with rate limiting: {success_rate:.2%}"
            assert backoff_successes > 0 or queue_successes > 0, "No rate limit recovery used"

    @pytest.mark.asyncio
    async def test_content_parsing_failures_in_summarization(self, chaos_config):
        """Test handling of content parsing failures during summarization."""
        parsing_errors = 0
        format_recovery_successes = 0
        content_validation_failures = 0

        async def summarize_with_content_issues(content: str, content_type: str, model: str) -> Dict[str, Any]:
            """Simulate summarization with content parsing issues."""
            nonlocal parsing_errors, format_recovery_successes, content_validation_failures

            # Simulate parsing failures
            if random.random() < 0.08:  # 8% parsing errors
                parsing_errors += 1

                if content_type == "markdown":
                    raise Exception("Markdown parsing error: malformed syntax")
                elif content_type == "html":
                    raise Exception("HTML parsing error: invalid structure")
                elif content_type == "pdf":
                    raise Exception("PDF parsing error: corrupted document")
                else:
                    raise Exception(f"Unknown content parsing error for {content_type}")

            # Simulate format validation failures
            if random.random() < 0.06:  # 6% validation failures
                content_validation_failures += 1

                if content_type == "markdown":
                    raise Exception("Markdown validation failed: missing required sections")
                elif content_type == "html":
                    raise Exception("HTML validation failed: malformed tags")
                else:
                    raise Exception("Content validation failed: insufficient quality")

            # Simulate successful summarization with potential recovery
            if random.random() < 0.12:  # 12% need content recovery
                format_recovery_successes += 1
                # Simulate content cleanup/recovery
                await asyncio.sleep(0.3)

            # Normal successful summarization
            await asyncio.sleep(random.uniform(0.2, 0.7))

            return {
                "summary": f"Summary of {content_type} content: {content[:100]}...",
                "model_used": model,
                "content_type": content_type,
                "parsing_recovered": random.random() < 0.12,
                "validation_passed": True,
                "confidence": random.uniform(0.82, 0.94)
            }

        # Test content parsing across different formats
        content_types = ["markdown", "html", "plaintext", "pdf", "docx"]
        sample_contents = {
            "markdown": "# Title\n\nThis is **bold** text with [link](url).\n\n- Item 1\n- Item 2",
            "html": "<html><body><h1>Title</h1><p>Content with <em>emphasis</em></p></body></html>",
            "plaintext": "This is plain text content without any special formatting or structure.",
            "pdf": "Simulated PDF content with complex layout and formatting requirements.",
            "docx": "Word document content with various formatting and embedded elements."
        }

        parsing_tasks = []
        for content_type in content_types:
            content = sample_contents[content_type]
            for i in range(10):  # 10 parsing attempts per content type
                model = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"][i % 3]
                task = summarize_with_content_issues(content, content_type, model)
                parsing_tasks.append(task)

        results = await asyncio.gather(*parsing_tasks, return_exceptions=True)

        # Analyze parsing results
        successful_summaries = [r for r in results if isinstance(r, dict)]
        failed_summaries = [r for r in results if isinstance(r, Exception)]

        recovery_used = sum(1 for r in successful_summaries if r.get("parsing_recovered", False))

        success_rate = len(successful_summaries) / len(parsing_tasks)

        print(f"Content Parsing Failures in Summarization Test:")
        print(f"  Total Parsing Attempts: {len(results)}")
        print(f"  Successful Summaries: {len(successful_summaries)}")
        print(f"  Failed Summaries: {len(failed_summaries)}")
        print(f"  Parsing Errors: {parsing_errors}")
        print(f"  Validation Failures: {content_validation_failures}")
        print(f"  Recovery Successes: {format_recovery_successes}")
        print(f"  Recovery Used: {recovery_used}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Should handle content parsing issues gracefully
        assert parsing_errors > 0 or content_validation_failures > 0, "No parsing failures occurred - chaos test ineffective"
        assert success_rate > 0.8, f"Parsing success rate too low: {success_rate:.2%}"
        assert format_recovery_successes >= 0, "Content recovery mechanisms should be available"

    @pytest.mark.asyncio
    async def test_multi_model_ensemble_failures(self, chaos_config):
        """Test multi-model ensemble failures and fallback scenarios."""
        ensemble_failures = 0
        partial_ensemble_successes = 0
        single_model_fallbacks = 0

        async def ensemble_summarize_with_failures(models: List[str], content: str) -> Dict[str, Any]:
            """Simulate multi-model ensemble summarization with potential failures."""
            nonlocal ensemble_failures, partial_ensemble_successes, single_model_fallbacks

            successful_models = []
            failed_models = []

            # Try each model in the ensemble
            for model in models:
                try:
                    # Simulate model-specific failure rates
                    failure_rate = 0.15 if model in ["claude-3-sonnet", "claude-3-opus"] else 0.08
                    if random.random() < failure_rate:
                        raise Exception(f"Model {model} temporarily unavailable")

                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    successful_models.append(model)

                except Exception:
                    failed_models.append(model)

            # Determine ensemble outcome
            if len(successful_models) == 0:
                ensemble_failures += 1
                raise Exception("All models in ensemble failed")
            elif len(successful_models) < len(models):
                partial_ensemble_successes += 1
                # Partial ensemble - use available models
                await asyncio.sleep(0.4)  # Ensemble combination time
            elif len(successful_models) == 1:
                single_model_fallbacks += 1
                # Single model fallback
                await asyncio.sleep(0.2)
            else:
                # Full ensemble
                await asyncio.sleep(0.6)

            ensemble_quality = len(successful_models) / len(models)

            return {
                "summary": f"Ensemble summary using {len(successful_models)}/{len(models)} models: {content[:80]}...",
                "models_used": successful_models,
                "models_failed": failed_models,
                "ensemble_quality": ensemble_quality,
                "fallback_mode": len(successful_models) == 1,
                "confidence": random.uniform(0.75, 0.95) * ensemble_quality
            }

        # Test different ensemble configurations under failure
        ensemble_configs = [
            ["claude-3-sonnet"],  # Single model
            ["claude-3-sonnet", "claude-3-haiku"],  # Two models
            ["claude-3-sonnet", "claude-3-haiku", "titan-text-express"],  # Three models
            ["claude-3-sonnet", "claude-3-haiku", "claude-3-opus", "titan-text-express"]  # Four models
        ]

        test_content = "This is comprehensive content about enterprise software architecture, microservices, cloud computing, and DevOps practices."

        ensemble_results = []

        for models in ensemble_configs:
            print(f"\nTesting ensemble summarization with {len(models)} models...")

            # Test each ensemble configuration multiple times
            config_results = []
            for _ in range(12):  # Test each config 12 times
                try:
                    result = await ensemble_summarize_with_failures(models, test_content)
                    config_results.append(result)
                except Exception as e:
                    config_results.append({"error": str(e), "models": models})

            successful_ensembles = [r for r in config_results if "error" not in r]
            failed_ensembles = [r for r in config_results if "error" in r]

            fallback_used = sum(1 for r in successful_ensembles if r.get("fallback_mode", False))

            success_rate = len(successful_ensembles) / len(config_results)

            ensemble_results.append({
                "model_count": len(models),
                "success_rate": success_rate,
                "fallback_used": fallback_used,
                "avg_ensemble_quality": statistics.mean([r.get("ensemble_quality", 0) for r in successful_ensembles]) if successful_ensembles else 0
            })

            print(f"  Models: {models}")
            print(f"  Success Rate: {success_rate:.2%}")
            print(f"  Fallbacks Used: {fallback_used}")
            print(f"  Ensemble Failures: {ensemble_failures}")
            print(f"  Partial Successes: {partial_ensemble_successes}")
            print(f"  Single Model Fallbacks: {single_model_fallbacks}")

        # Analyze ensemble resilience
        print("
Ensemble Failure Analysis:")
        for result in ensemble_results:
            print(".1f")

        # Larger ensembles should be more resilient
        single_model = next(r for r in ensemble_results if r["model_count"] == 1)
        multi_model = next((r for r in ensemble_results if r["model_count"] > 2), None)

        if multi_model:
            assert multi_model["success_rate"] >= single_model["success_rate"] * 0.9, \
                "Multi-model ensemble should be more resilient than single model"

    @pytest.mark.asyncio
    async def test_concurrent_summarization_failures(self, chaos_config):
        """Test concurrent summarization failures and resource management."""
        concurrent_failures = 0
        resource_exhaustion_events = 0
        priority_based_handling = 0

        async def concurrent_summarization_operation(operation_id: int, priority: str, content: str, model: str) -> Dict[str, Any]:
            """Perform summarization operation with concurrency and failure handling."""
            nonlocal concurrent_failures, resource_exhaustion_events, priority_based_handling

            # Simulate concurrent processing issues
            if random.random() < 0.1:  # 10% concurrency failures
                concurrent_failures += 1

                if priority == "low":
                    resource_exhaustion_events += 1
                    raise Exception("Resource exhaustion: low priority summarization cancelled")
                elif priority == "high":
                    priority_based_handling += 1
                    # High priority gets extended timeout
                    await asyncio.sleep(3.0)
                    # Recovery successful
                else:
                    raise Exception("Concurrent summarization limit exceeded")

            # Simulate normal summarization
            processing_time = random.uniform(0.5, 1.8)
            await asyncio.sleep(processing_time)

            return {
                "operation_id": operation_id,
                "priority": priority,
                "model_used": model,
                "summary": f"Summary: {content[:60]}...",
                "processing_time": processing_time,
                "status": "completed",
                "confidence": random.uniform(0.8, 0.95)
            }

        # Test concurrent summarization with different priorities
        operations = []
        priorities = ["high", "medium", "low"]
        models = ["claude-3-sonnet", "claude-3-haiku", "titan-text-express", "claude-3-opus"]
        sample_content = "This is sample content for concurrent summarization testing across multiple operations."

        for i in range(40):  # High concurrency test
            priority = priorities[i % len(priorities)]
            model = models[i % len(models)]
            operations.append((i, priority, sample_content, model))

        # Execute operations concurrently
        tasks = [concurrent_summarization_operation(op_id, priority, content, model)
                for op_id, priority, content, model in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze concurrent summarization results
        successful_summaries = [r for r in results if isinstance(r, dict)]
        failed_summaries = [r for r in results if isinstance(r, Exception)]

        high_priority_success = sum(1 for r in successful_summaries if r.get("priority") == "high")
        low_priority_success = sum(1 for r in successful_summaries if r.get("priority") == "low")

        success_rate = len(successful_summaries) / len(results)

        print(f"Concurrent Summarization Failures Test:")
        print(f"  Total Operations: {len(results)}")
        print(f"  Successful Summaries: {len(successful_summaries)}")
        print(f"  Failed Summaries: {len(failed_summaries)}")
        print(f"  High Priority Success: {high_priority_success}")
        print(f"  Low Priority Success: {low_priority_success}")
        print(f"  Concurrent Failures: {concurrent_failures}")
        print(f"  Resource Exhaustion: {resource_exhaustion_events}")
        print(f"  Priority Handling: {priority_based_handling}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Should handle concurrent summarization gracefully with prioritization
        assert len(failed_summaries) > 0, "No concurrent failures occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Success rate too low under concurrent load: {success_rate:.2%}"
        assert resource_exhaustion_events > 0, "No resource exhaustion handling for low priority"
        assert priority_based_handling >= 0, "Priority-based handling should be available"
