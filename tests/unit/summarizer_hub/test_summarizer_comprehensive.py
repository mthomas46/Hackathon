"""Comprehensive Summarizer Hub Tests.

Tests for multi-model LLM summarization, provider management, quality comparison,
and performance optimization in the LLM Documentation Ecosystem.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json

# Adjust path for local imports
import sys
from pathlib import Path

# Add the Summarizer Hub service directory to Python path
summarizer_path = Path(__file__).parent.parent.parent.parent / "services" / "summarizer-hub"
sys.path.insert(0, str(summarizer_path))

from modules.core.summarization_engine import SummarizationEngine
from modules.core.provider_manager import ProviderManager
from modules.core.quality_evaluator import QualityEvaluator
from modules.core.performance_optimizer import PerformanceOptimizer
from modules.models import SummarizationRequest, ProviderConfig, QualityMetrics

# Test markers for parallel execution and categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.summarizer_hub
]


@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway for testing."""
    with patch('modules.core.summarization_engine.LLMGateway') as mock_gateway_class:
        mock_gateway = MagicMock()
        mock_gateway_class.return_value = mock_gateway

        # Mock summarization responses
        mock_gateway.generate_summary = AsyncMock(return_value={
            "success": True,
            "summary": "This is a comprehensive summary of the document content.",
            "provider": "ollama",
            "tokens_used": 150,
            "processing_time": 2.3
        })

        mock_gateway.get_provider_status = AsyncMock(return_value={
            "status": "healthy",
            "response_time": 1.2,
            "model": "llama3"
        })

        yield mock_gateway


@pytest.fixture
def mock_provider_manager():
    """Mock Provider Manager for testing."""
    with patch('modules.core.summarization_engine.ProviderManager') as mock_manager_class:
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        mock_manager.get_available_providers = AsyncMock(return_value=[
            {"name": "ollama", "model": "llama3", "status": "healthy"},
            {"name": "openai", "model": "gpt-4", "status": "healthy"},
            {"name": "anthropic", "model": "claude-3", "status": "healthy"}
        ])

        yield mock_manager


@pytest.fixture
def summarization_engine(mock_llm_gateway, mock_provider_manager):
    """Create SummarizationEngine instance for testing."""
    return SummarizationEngine()


@pytest.fixture
def provider_manager(mock_llm_gateway):
    """Create ProviderManager instance for testing."""
    return ProviderManager()


@pytest.fixture
def quality_evaluator():
    """Create QualityEvaluator instance for testing."""
    return QualityEvaluator()


@pytest.fixture
def performance_optimizer():
    """Create PerformanceOptimizer instance for testing."""
    return PerformanceOptimizer()


class TestSummarizationEngine:
    """Comprehensive tests for the summarization engine."""

    def test_generate_single_provider_summary(self, summarization_engine, mock_llm_gateway):
        """Test summarization using a single provider."""
        content = """
        The API documentation describes a comprehensive authentication system
        that supports multiple authentication methods including OAuth2, JWT,
        and API keys. The system provides endpoints for user registration,
        login, token refresh, and logout functionality.
        """

        request = SummarizationRequest(
            content=content,
            provider="ollama",
            max_length=200,
            format="concise"
        )

        result = summarization_engine.generate_summary(request)

        assert isinstance(result, dict)
        assert "success" in result
        assert "summary" in result
        assert "provider" in result
        assert "tokens_used" in result

        # Verify LLM was called correctly
        mock_llm_gateway.generate_summary.assert_called_once()

    def test_multi_provider_summary_comparison(self, summarization_engine, mock_llm_gateway, mock_provider_manager):
        """Test summarization with multiple providers for comparison."""
        content = "This is test content for multi-provider summarization."

        result = summarization_engine.generate_multi_provider_summary(
            content=content,
            providers=["ollama", "openai"],
            max_length=150
        )

        assert isinstance(result, dict)
        assert "success" in result
        assert "summaries" in result

        summaries = result["summaries"]
        assert isinstance(summaries, list)
        assert len(summaries) >= 2  # At least 2 provider summaries

        # Each summary should have required fields
        for summary in summaries:
            assert "provider" in summary
            assert "summary" in summary
            assert "quality_score" in summary

    def test_adaptive_summarization(self, summarization_engine):
        """Test adaptive summarization based on content characteristics."""
        test_cases = [
            ("Short content under 100 words", "short"),
            ("A" * 1000, "long"),  # 1000 character content
            ("Technical content with code examples", "technical"),
            ("Simple user guide content", "simple")
        ]

        for content, expected_type in test_cases:
            result = summarization_engine.adaptive_summarize(content)

            assert isinstance(result, dict)
            assert "content_type" in result
            assert "adapted_strategy" in result
            assert "summary" in result

    def test_summary_quality_assessment(self, summarization_engine):
        """Test assessment of summary quality."""
        original_content = "The authentication API provides secure user login functionality."
        summary = "Auth API enables secure user login."

        quality = summarization_engine.assess_summary_quality(original_content, summary)

        assert isinstance(quality, dict)
        assert "completeness_score" in quality
        assert "conciseness_score" in quality
        assert "accuracy_score" in quality
        assert "overall_quality" in quality

        # All scores should be between 0 and 1
        for score_key in ["completeness_score", "conciseness_score", "accuracy_score", "overall_quality"]:
            assert 0.0 <= quality[score_key] <= 1.0

    def test_summary_format_handling(self, summarization_engine):
        """Test different summary output formats."""
        content = "Test content for format testing."
        formats = ["concise", "detailed", "bullet_points", "structured"]

        for fmt in formats:
            result = summarization_engine.generate_formatted_summary(content, format=fmt)

            assert isinstance(result, dict)
            assert "success" in result
            assert "format" in result
            assert result["format"] == fmt

    def test_content_chunking_and_summarization(self, summarization_engine):
        """Test summarization of large content through chunking."""
        # Create large content that would need chunking
        large_content = "This is a test paragraph. " * 100  # ~3000 characters

        result = summarization_engine.summarize_large_content(large_content)

        assert isinstance(result, dict)
        assert "success" in result
        assert "chunks_processed" in result
        assert "final_summary" in result

        # Should have processed multiple chunks
        assert result["chunks_processed"] > 1

    def test_incremental_summarization(self, summarization_engine):
        """Test incremental summarization of streaming content."""
        content_chunks = [
            "First part of the document.",
            "Second part with additional information.",
            "Third part concluding the content."
        ]

        incremental_summary = summarization_engine.incremental_summarize(content_chunks)

        assert isinstance(incremental_summary, dict)
        assert "current_summary" in incremental_summary
        assert "processed_chunks" in incremental_summary
        assert "can_continue" in incremental_summary

        assert incremental_summary["processed_chunks"] == len(content_chunks)

    def test_cross_provider_consensus_summarization(self, summarization_engine, mock_provider_manager):
        """Test consensus-based summarization across providers."""
        content = "Test content for consensus summarization."

        consensus = summarization_engine.generate_consensus_summary(
            content=content,
            providers=["ollama", "openai", "anthropic"],
            consensus_threshold=0.7
        )

        assert isinstance(consensus, dict)
        assert "consensus_summary" in consensus
        assert "agreement_score" in consensus
        assert "contributing_providers" in consensus
        assert "divergent_points" in consensus

    def test_summary_personalization(self, summarization_engine):
        """Test personalized summarization based on user preferences."""
        content = "Technical documentation content."
        user_preferences = {
            "style": "technical",
            "length": "detailed",
            "focus_areas": ["implementation", "examples"],
            "exclude_terms": ["basic"]
        }

        personalized = summarization_engine.generate_personalized_summary(
            content=content,
            preferences=user_preferences
        )

        assert isinstance(personalized, dict)
        assert "personalized_summary" in personalized
        assert "applied_preferences" in personalized
        assert "customization_score" in personalized

    def test_summary_versioning_and_comparison(self, summarization_engine):
        """Test versioning and comparison of summaries."""
        content = "Original content for versioning test."

        # Generate multiple versions
        versions = []
        for i in range(3):
            version = summarization_engine.generate_versioned_summary(
                content=content,
                version_id=f"v{i+1}"
            )
            versions.append(version)

        comparison = summarization_engine.compare_summary_versions(versions)

        assert isinstance(comparison, dict)
        assert "versions_compared" in comparison
        assert "similarity_matrix" in comparison
        assert "best_version" in comparison
        assert "improvement_trends" in comparison

    def test_error_handling_and_recovery(self, summarization_engine, mock_llm_gateway):
        """Test error handling and recovery mechanisms."""
        mock_llm_gateway.generate_summary.side_effect = Exception("Provider unavailable")

        content = "Test content for error handling."

        result = summarization_engine.generate_summary_with_recovery(
            content=content,
            fallback_providers=["openai", "anthropic"]
        )

        # Should handle error and attempt fallback
        assert isinstance(result, dict)
        assert "recovery_attempted" in result

    def test_summary_caching_and_retrieval(self, summarization_engine):
        """Test caching and retrieval of summaries."""
        content = "Content for caching test."
        cache_key = summarization_engine.generate_cache_key(content)

        # Generate and cache summary
        result1 = summarization_engine.generate_cached_summary(content)

        # Retrieve from cache
        result2 = summarization_engine.get_cached_summary(cache_key)

        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert result1["summary"] == result2["summary"]

    def test_batch_summarization_processing(self, summarization_engine):
        """Test batch processing of multiple documents."""
        documents = [
            {"id": "doc1", "content": "First document content"},
            {"id": "doc2", "content": "Second document content"},
            {"id": "doc3", "content": "Third document content"}
        ]

        batch_results = summarization_engine.batch_summarize_documents(documents)

        assert isinstance(batch_results, list)
        assert len(batch_results) == len(documents)

        for result in batch_results:
            assert isinstance(result, dict)
            assert "document_id" in result
            assert "summary" in result
            assert "success" in result

    def test_summary_length_optimization(self, summarization_engine):
        """Test optimization of summary lengths."""
        content = "Long content that needs summarization to different lengths."

        length_options = [50, 100, 200, 500]

        for target_length in length_options:
            optimized = summarization_engine.optimize_summary_length(
                content=content,
                target_length=target_length
            )

            assert isinstance(optimized, dict)
            assert "optimized_summary" in optimized
            assert "actual_length" in optimized
            assert "target_length" in optimized

            # Actual length should be close to target
            actual_length = optimized["actual_length"]
            assert abs(actual_length - target_length) / target_length < 0.3  # Within 30%

    def test_multilingual_summarization(self, summarization_engine):
        """Test summarization of multilingual content."""
        multilingual_content = {
            "en": "This is English content for summarization.",
            "es": "Este es contenido en español para resumir.",
            "fr": "Ceci est du contenu français à résumer.",
            "de": "Dies ist deutscher Inhalt zur Zusammenfassung."
        }

        for lang, content in multilingual_content.items():
            result = summarization_engine.summarize_multilingual_content(
                content=content,
                language=lang
            )

            assert isinstance(result, dict)
            assert "detected_language" in result
            assert "summary" in result
            assert result["detected_language"] == lang


class TestProviderManager:
    """Comprehensive tests for provider management functionality."""

    def test_provider_registration_and_discovery(self, provider_manager):
        """Test provider registration and discovery."""
        provider_config = ProviderConfig(
            name="test_provider",
            model="test-model",
            endpoint="http://test-provider.com",
            api_key="test-key"
        )

        # Register provider
        registration_result = provider_manager.register_provider(provider_config)
        assert registration_result["success"] is True

        # Discover providers
        providers = provider_manager.discover_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0

        # Check if our provider is registered
        provider_names = [p["name"] for p in providers]
        assert "test_provider" in provider_names

    def test_provider_health_monitoring(self, provider_manager, mock_llm_gateway):
        """Test monitoring of provider health status."""
        health_status = provider_manager.monitor_provider_health("ollama")

        assert isinstance(health_status, dict)
        assert "status" in health_status
        assert "response_time" in health_status
        assert "last_checked" in health_status
        assert "error_rate" in health_status

    def test_provider_load_balancing(self, provider_manager):
        """Test load balancing across providers."""
        providers = ["ollama", "openai", "anthropic"]
        request_count = 100

        distribution = provider_manager.distribute_load(providers, request_count)

        assert isinstance(distribution, dict)
        assert "assignments" in distribution
        assert "balancing_strategy" in distribution

        # Total assignments should equal request count
        total_assigned = sum(distribution["assignments"].values())
        assert total_assigned == request_count

    def test_provider_failover_handling(self, provider_manager):
        """Test failover handling when providers fail."""
        primary_provider = "ollama"
        fallback_providers = ["openai", "anthropic"]

        failover_result = provider_manager.handle_provider_failover(
            primary_provider=primary_provider,
            fallback_providers=fallback_providers
        )

        assert isinstance(failover_result, dict)
        assert "failover_performed" in failover_result
        assert "new_primary" in failover_result
        assert "failover_reason" in failover_result

    def test_provider_performance_tracking(self, provider_manager):
        """Test tracking of provider performance metrics."""
        provider_name = "ollama"

        metrics = provider_manager.track_provider_performance(provider_name)

        assert isinstance(metrics, dict)
        assert "average_response_time" in metrics
        assert "success_rate" in metrics
        assert "throughput" in metrics
        assert "error_rate" in metrics
        assert "cost_efficiency" in metrics

    def test_dynamic_provider_scaling(self, provider_manager):
        """Test dynamic scaling of provider resources."""
        scaling_config = {
            "provider": "ollama",
            "current_load": 80,
            "target_load": 60,
            "scaling_strategy": "horizontal"
        }

        scaling_result = provider_manager.scale_provider_resources(scaling_config)

        assert isinstance(scaling_result, dict)
        assert "scaling_performed" in scaling_result
        assert "new_capacity" in scaling_result
        assert "scaling_cost" in scaling_result

    def test_provider_cost_optimization(self, provider_manager):
        """Test optimization of provider costs."""
        usage_patterns = {
            "ollama": {"requests": 1000, "cost": 5.0},
            "openai": {"requests": 500, "cost": 15.0},
            "anthropic": {"requests": 300, "cost": 12.0}
        }

        optimization = provider_manager.optimize_provider_costs(usage_patterns)

        assert isinstance(optimization, dict)
        assert "recommended_providers" in optimization
        assert "cost_savings" in optimization
        assert "optimization_strategy" in optimization

    def test_provider_compatibility_checking(self, provider_manager):
        """Test checking compatibility between providers."""
        provider1 = "ollama"
        provider2 = "openai"

        compatibility = provider_manager.check_provider_compatibility(provider1, provider2)

        assert isinstance(compatibility, dict)
        assert "compatible" in compatibility
        assert "compatibility_score" in compatibility
        assert "differences" in compatibility

    def test_provider_configuration_management(self, provider_manager):
        """Test management of provider configurations."""
        config_updates = {
            "ollama": {"model": "llama3", "timeout": 60},
            "openai": {"model": "gpt-4", "max_tokens": 4000}
        }

        config_result = provider_manager.update_provider_configurations(config_updates)

        assert isinstance(config_result, dict)
        assert "updates_applied" in config_result
        assert "validation_results" in config_result

    def test_provider_rate_limit_management(self, provider_manager):
        """Test management of provider rate limits."""
        rate_limits = {
            "ollama": {"requests_per_minute": 60, "tokens_per_minute": 10000},
            "openai": {"requests_per_minute": 20, "tokens_per_minute": 40000}
        }

        rate_management = provider_manager.manage_provider_rate_limits(rate_limits)

        assert isinstance(rate_management, dict)
        assert "rate_limits_set" in rate_management
        assert "throttling_applied" in rate_management
        assert "queue_management" in rate_management


class TestQualityEvaluator:
    """Comprehensive tests for quality evaluation functionality."""

    def test_summary_quality_scoring(self, quality_evaluator):
        """Test comprehensive quality scoring of summaries."""
        original_text = """
        The authentication service provides secure user login functionality
        with support for OAuth2, JWT tokens, and multi-factor authentication.
        The API includes endpoints for user registration, password reset,
        and session management.
        """

        summary = "Auth service supports OAuth2, JWT, MFA with user management endpoints."

        quality_scores = quality_evaluator.score_summary_quality(original_text, summary)

        assert isinstance(quality_scores, dict)
        assert "completeness" in quality_scores
        assert "conciseness" in quality_scores
        assert "accuracy" in quality_scores
        assert "coherence" in quality_scores
        assert "overall_score" in quality_scores

        # All scores should be between 0 and 1
        for score in quality_scores.values():
            assert isinstance(score, (int, float))
            assert 0.0 <= score <= 1.0

    def test_cross_provider_quality_comparison(self, quality_evaluator):
        """Test quality comparison across different providers."""
        summaries = [
            {"provider": "ollama", "content": "Auth service with OAuth2 and JWT support.", "quality_score": 0.85},
            {"provider": "openai", "content": "Authentication service provides OAuth2, JWT, and MFA.", "quality_score": 0.92},
            {"provider": "anthropic", "content": "The auth service supports OAuth2 and JWT tokens.", "quality_score": 0.78}
        ]

        comparison = quality_evaluator.compare_provider_qualities(summaries)

        assert isinstance(comparison, dict)
        assert "best_provider" in comparison
        assert "quality_distribution" in comparison
        assert "performance_analysis" in comparison
        assert "recommendations" in comparison

    def test_quality_benchmarking(self, quality_evaluator):
        """Test quality benchmarking against standards."""
        quality_metrics = {
            "completeness": 0.88,
            "accuracy": 0.95,
            "conciseness": 0.82,
            "coherence": 0.90
        }

        benchmark = quality_evaluator.benchmark_quality(quality_metrics)

        assert isinstance(benchmark, dict)
        assert "benchmark_score" in benchmark
        assert "grade" in benchmark
        assert "standards_met" in benchmark
        assert "improvement_areas" in benchmark

    def test_quality_trend_analysis(self, quality_evaluator):
        """Test analysis of quality trends over time."""
        historical_quality = [
            {"date": "2024-01-01", "score": 0.75},
            {"date": "2024-01-08", "score": 0.78},
            {"date": "2024-01-15", "score": 0.82},
            {"date": "2024-01-22", "score": 0.85}
        ]

        trends = quality_evaluator.analyze_quality_trends(historical_quality)

        assert isinstance(trends, dict)
        assert "trend_direction" in trends
        assert "improvement_rate" in trends
        assert "stability_score" in trends
        assert "forecasted_quality" in trends

    def test_content_type_specific_quality(self, quality_evaluator):
        """Test quality evaluation specific to content types."""
        content_types = [
            ("api_documentation", "API docs content for quality testing"),
            ("user_guide", "User guide content for quality assessment"),
            ("technical_spec", "Technical specification content"),
            ("code_commentary", "Code documentation and comments")
        ]

        for content_type, content in content_types:
            type_specific_quality = quality_evaluator.evaluate_content_type_quality(
                content=content,
                content_type=content_type
            )

            assert isinstance(type_specific_quality, dict)
            assert "content_type_score" in type_specific_quality
            assert "type_specific_criteria" in type_specific_quality

    def test_quality_feedback_loop(self, quality_evaluator):
        """Test quality improvement through feedback loops."""
        initial_quality = {"overall_score": 0.75}
        feedback_data = {
            "user_ratings": [4, 5, 3, 4],
            "improvement_suggestions": ["more concise", "better structure"],
            "usage_patterns": ["frequently_used", "high_engagement"]
        }

        improved_quality = quality_evaluator.apply_quality_feedback(
            initial_quality=initial_quality,
            feedback=feedback_data
        )

        assert isinstance(improved_quality, dict)
        assert "improved_score" in improved_quality
        assert "applied_improvements" in improved_quality
        assert "feedback_impact" in improved_quality

    def test_quality_validation_rules(self, quality_evaluator):
        """Test validation of quality assessment rules."""
        quality_rules = [
            {"name": "completeness", "min_score": 0.7, "max_score": 1.0},
            {"name": "accuracy", "min_score": 0.8, "max_score": 1.0},
            {"name": "conciseness", "min_score": 0.6, "max_score": 1.0}
        ]

        validation = quality_evaluator.validate_quality_rules(quality_rules)

        assert isinstance(validation, dict)
        assert "rules_valid" in validation
        assert "validation_results" in validation
        assert "conflicts_detected" in validation

    def test_adaptive_quality_thresholds(self, quality_evaluator):
        """Test adaptive quality thresholds based on context."""
        contexts = [
            {"difficulty": "simple", "expected_quality": 0.8},
            {"difficulty": "complex", "expected_quality": 0.9},
            {"importance": "critical", "expected_quality": 0.95},
            {"audience": "expert", "expected_quality": 0.85}
        ]

        for context in contexts:
            adaptive_thresholds = quality_evaluator.calculate_adaptive_thresholds(context)

            assert isinstance(adaptive_thresholds, dict)
            assert "adjusted_thresholds" in adaptive_thresholds
            assert "context_factors" in adaptive_thresholds
            assert "justification" in adaptive_thresholds

    def test_quality_cost_tradeoff_analysis(self, quality_evaluator):
        """Test analysis of quality vs cost tradeoffs."""
        quality_options = [
            {"quality_score": 0.9, "cost": 10, "time": 30},
            {"quality_score": 0.8, "cost": 5, "time": 15},
            {"quality_score": 0.95, "cost": 20, "time": 60}
        ]

        tradeoff_analysis = quality_evaluator.analyze_quality_cost_tradeoffs(quality_options)

        assert isinstance(tradeoff_analysis, dict)
        assert "optimal_choice" in tradeoff_analysis
        assert "tradeoff_analysis" in tradeoff_analysis
        assert "recommendations" in tradeoff_analysis

    def test_quality_assurance_automation(self, quality_evaluator):
        """Test automated quality assurance processes."""
        quality_checks = [
            {"name": "grammar_check", "automated": True},
            {"name": "factual_accuracy", "automated": False},
            {"name": "completeness", "automated": True},
            {"name": "consistency", "automated": False}
        ]

        automation_result = quality_evaluator.automate_quality_assurance(quality_checks)

        assert isinstance(automation_result, dict)
        assert "automated_checks" in automation_result
        assert "manual_checks_required" in automation_result
        assert "automation_coverage" in automation_result


class TestPerformanceOptimizer:
    """Comprehensive tests for performance optimization functionality."""

    def test_response_time_optimization(self, performance_optimizer):
        """Test optimization of response times across providers."""
        provider_times = {
            "ollama": {"avg_response_time": 2.1, "success_rate": 0.98},
            "openai": {"avg_response_time": 1.8, "success_rate": 0.95},
            "anthropic": {"avg_response_time": 3.2, "success_rate": 0.99}
        }

        optimization = performance_optimizer.optimize_response_times(provider_times)

        assert isinstance(optimization, dict)
        assert "optimal_provider" in optimization
        assert "performance_gains" in optimization
        assert "optimization_strategy" in optimization

    def test_throughput_optimization(self, performance_optimizer):
        """Test optimization of throughput for batch processing."""
        batch_config = {
            "documents": 100,
            "max_concurrent": 10,
            "target_time": 60  # seconds
        }

        throughput_opt = performance_optimizer.optimize_throughput(batch_config)

        assert isinstance(throughput_opt, dict)
        assert "optimal_batch_size" in throughput_opt
        assert "estimated_throughput" in throughput_opt
        assert "resource_utilization" in throughput_opt

    def test_cost_performance_optimization(self, performance_optimizer):
        """Test optimization balancing cost and performance."""
        cost_performance_data = {
            "ollama": {"cost_per_token": 0.001, "tokens_per_second": 50},
            "openai": {"cost_per_token": 0.01, "tokens_per_second": 100},
            "anthropic": {"cost_per_token": 0.008, "tokens_per_second": 80}
        }

        optimization = performance_optimizer.optimize_cost_performance(cost_performance_data)

        assert isinstance(optimization, dict)
        assert "cost_efficient_choice" in optimization
        assert "performance_efficient_choice" in optimization
        assert "balanced_recommendation" in optimization

    def test_caching_strategy_optimization(self, performance_optimizer):
        """Test optimization of caching strategies."""
        cache_config = {
            "cache_hit_rate": 0.75,
            "cache_size": 1000,
            "invalidation_strategy": "lru",
            "access_patterns": ["frequent", "bursty", "predictable"]
        }

        cache_opt = performance_optimizer.optimize_caching_strategy(cache_config)

        assert isinstance(cache_opt, dict)
        assert "recommended_strategy" in cache_opt
        assert "expected_improvement" in cache_opt
        assert "cache_efficiency" in cache_opt

    def test_load_balancing_optimization(self, performance_optimizer):
        """Test optimization of load balancing across providers."""
        load_data = {
            "providers": ["ollama", "openai", "anthropic"],
            "current_loads": [70, 50, 30],  # percentages
            "capacities": [100, 100, 100],
            "response_times": [2.1, 1.8, 3.2]
        }

        load_opt = performance_optimizer.optimize_load_balancing(load_data)

        assert isinstance(load_opt, dict)
        assert "balancing_recommendations" in load_opt
        assert "expected_improvement" in load_opt
        assert "failover_strategy" in load_opt

    def test_memory_usage_optimization(self, performance_optimizer):
        """Test optimization of memory usage in summarization."""
        memory_config = {
            "available_memory": 8,  # GB
            "document_sizes": [100, 500, 1000],  # KB
            "batch_size": 50,
            "caching_enabled": True
        }

        memory_opt = performance_optimizer.optimize_memory_usage(memory_config)

        assert isinstance(memory_opt, dict)
        assert "recommended_batch_size" in memory_opt
        assert "memory_efficiency" in memory_opt
        assert "optimization_suggestions" in memory_opt

    def test_concurrent_processing_optimization(self, performance_optimizer):
        """Test optimization of concurrent processing."""
        concurrent_config = {
            "max_workers": 10,
            "task_queue_size": 100,
            "task_complexity": "medium",
            "resource_constraints": {"cpu": 4, "memory": 8}
        }

        concurrent_opt = performance_optimizer.optimize_concurrent_processing(concurrent_config)

        assert isinstance(concurrent_opt, dict)
        assert "optimal_worker_count" in concurrent_opt
        assert "queue_optimization" in concurrent_opt
        assert "resource_efficiency" in concurrent_opt

    def test_provider_selection_optimization(self, performance_optimizer):
        """Test optimization of provider selection based on requirements."""
        requirements = {
            "quality_priority": 0.8,
            "cost_priority": 0.6,
            "speed_priority": 0.7,
            "reliability_priority": 0.9
        }

        provider_opt = performance_optimizer.optimize_provider_selection(requirements)

        assert isinstance(provider_opt, dict)
        assert "recommended_provider" in provider_opt
        assert "selection_criteria" in provider_opt
        assert "tradeoff_analysis" in provider_opt

    def test_performance_monitoring_setup(self, performance_optimizer):
        """Test setup of comprehensive performance monitoring."""
        monitoring_config = {
            "metrics": ["response_time", "throughput", "error_rate", "cost"],
            "alerts": ["high_latency", "high_error_rate", "cost_overrun"],
            "reporting": ["daily", "weekly", "monthly"]
        }

        monitoring_setup = performance_optimizer.setup_performance_monitoring(monitoring_config)

        assert isinstance(monitoring_setup, dict)
        assert "monitoring_configured" in monitoring_setup
        assert "alerts_configured" in monitoring_setup
        assert "reporting_setup" in monitoring_setup

    def test_performance_baseline_establishment(self, performance_optimizer):
        """Test establishment of performance baselines."""
        baseline_data = {
            "response_times": [1.8, 2.1, 1.9, 2.3, 1.7],
            "throughput_rates": [45, 48, 42, 50, 46],
            "error_rates": [0.02, 0.01, 0.03, 0.015, 0.025]
        }

        baseline = performance_optimizer.establish_performance_baseline(baseline_data)

        assert isinstance(baseline, dict)
        assert "baseline_metrics" in baseline
        assert "acceptable_ranges" in baseline
        assert "anomaly_thresholds" in baseline

    def test_performance_regression_detection(self, performance_optimizer):
        """Test detection of performance regressions."""
        current_metrics = {
            "response_time": 3.2,  # Increased from baseline
            "throughput": 35,      # Decreased from baseline
            "error_rate": 0.08     # Increased from baseline
        }

        baseline = {
            "response_time": 2.0,
            "throughput": 45,
            "error_rate": 0.02
        }

        regression = performance_optimizer.detect_performance_regression(
            current_metrics=current_metrics,
            baseline=baseline
        )

        assert isinstance(regression, dict)
        assert "regression_detected" in regression
        assert "affected_metrics" in regression
        assert "severity_level" in regression
        assert "recommended_actions" in regression

    def test_adaptive_performance_tuning(self, performance_optimizer):
        """Test adaptive performance tuning based on workload."""
        workload_patterns = {
            "peak_hours": {"load": "high", "response_time_target": 1.5},
            "off_hours": {"load": "low", "response_time_target": 3.0},
            "maintenance": {"load": "maintenance", "response_time_target": 10.0}
        }

        adaptive_tuning = performance_optimizer.adaptive_performance_tuning(workload_patterns)

        assert isinstance(adaptive_tuning, dict)
        assert "tuning_recommendations" in adaptive_tuning
        assert "workload_adaptation" in adaptive_tuning
        assert "resource_scaling" in adaptive_tuning
