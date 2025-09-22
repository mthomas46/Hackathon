"""Unit Tests for LLM Integration in Interpreter Service.

This module tests LLM gateway integration including:
- AI-powered text generation and analysis
- Model selection and routing
- Prompt engineering and optimization
- Response processing and validation
- Error handling and fallback mechanisms
- Performance optimization and caching

Tests cover the AI-powered capabilities of the interpreter service.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from modules.llm_gateway_integration import LLMGatewayIntegration
from modules.prompt_engineering import PromptEngineering
from modules.output_generator import OutputGenerator
from modules.models import QueryContext, DocumentAnalysis


class TestLLMGatewayIntegration:
    """Test LLM Gateway integration functionality."""

    @pytest.fixture
    def llm_gateway(self, mock_llm_gateway):
        """Create LLM gateway integration instance."""
        return LLMGatewayIntegration(llm_gateway=mock_llm_gateway)

    def test_basic_text_generation(self, llm_gateway):
        """Test basic text generation capabilities."""
        prompt = "Explain what machine learning is in simple terms."
        result = asyncio.run(llm_gateway.generate_text(prompt))

        assert "response" in result
        assert len(result["response"]) > 0
        assert "model" in result
        assert "tokens_used" in result

    def test_context_aware_generation(self, llm_gateway, sample_query_context):
        """Test context-aware text generation."""
        context = {
            "user_history": ["Previous questions about AI", "Interest in machine learning"],
            "domain": "technology",
            "complexity_preference": "intermediate"
        }

        prompt = "Explain neural networks"
        result = asyncio.run(llm_gateway.generate_text_with_context(prompt, context))

        assert "response" in result
        # Should adapt to user's context and preferences
        assert "neural" in result["response"].lower()
        assert result["adaptation_score"] > 0.5  # Should show context adaptation

    def test_model_selection_routing(self, llm_gateway):
        """Test intelligent model selection and routing."""
        test_cases = [
            ("Simple question about weather", "fast_model", "basic"),
            ("Complex analysis of financial data", "advanced_model", "comprehensive"),
            ("Creative writing task", "creative_model", "generative"),
            ("Code generation request", "code_model", "technical")
        ]

        for prompt, expected_model, expected_type in test_cases:
            result = asyncio.run(llm_gateway.select_and_route_model(prompt))

            assert result["selected_model"] == expected_model
            assert result["model_type"] == expected_type
            assert "routing_reason" in result

    def test_generation_parameter_optimization(self, llm_gateway):
        """Test dynamic parameter optimization for generation."""
        prompt_types = [
            ("Creative writing", {"temperature": 0.9, "max_tokens": 500}),
            ("Technical explanation", {"temperature": 0.3, "max_tokens": 300}),
            ("Code generation", {"temperature": 0.1, "max_tokens": 1000}),
            ("Summarization", {"temperature": 0.2, "max_tokens": 200})
        ]

        for prompt_type, expected_params in prompt_types:
            prompt = f"Generate a {prompt_type.lower()} example"
            result = asyncio.run(llm_gateway.optimize_generation_parameters(prompt))

            optimized_params = result["optimized_parameters"]

            # Temperature should be close to expected
            assert abs(optimized_params["temperature"] - expected_params["temperature"]) < 0.2
            # Max tokens should be reasonable
            assert abs(optimized_params["max_tokens"] - expected_params["max_tokens"]) < 100

    def test_response_quality_validation(self, llm_gateway):
        """Test response quality validation and scoring."""
        test_responses = [
            ("Clear, well-structured explanation with examples", "high_quality"),
            ("Confusing response with poor grammar", "low_quality"),
            ("Partially correct but incomplete", "medium_quality")
        ]

        for response_text, expected_quality in test_responses:
            quality_score = asyncio.run(llm_gateway.validate_response_quality(response_text))

            assert quality_score["overall_quality"] == expected_quality
            assert "criteria_scores" in quality_score
            assert "improvement_suggestions" in quality_score

            # Quality thresholds
            if expected_quality == "high_quality":
                assert quality_score["confidence"] > 0.8
            elif expected_quality == "low_quality":
                assert quality_score["confidence"] < 0.6

    def test_error_handling_and_fallback(self, llm_gateway):
        """Test error handling and fallback mechanisms."""
        # Simulate LLM service failure
        llm_gateway.llm_gateway.generate_response.side_effect = Exception("Service unavailable")

        prompt = "Explain basic programming concepts"
        result = asyncio.run(llm_gateway.generate_with_fallback(prompt))

        # Should provide fallback response
        assert "response" in result
        assert "fallback_used" in result
        assert result["fallback_used"] is True
        assert "fallback_reason" in result

        # Fallback response should still be useful
        assert len(result["response"]) > 50

    def test_response_caching_optimization(self, llm_gateway):
        """Test response caching for performance optimization."""
        prompt = "What is the capital of France?"

        # First call - should generate and cache
        result1 = asyncio.run(llm_gateway.generate_with_caching(prompt))
        assert "response" in result1
        assert result1.get("cached", False) is False

        # Second call - should use cache
        result2 = asyncio.run(llm_gateway.generate_with_caching(prompt))
        assert "response" in result2
        assert result2.get("cached", False) is True

        # Cached response should be identical
        assert result1["response"] == result2["response"]

        # Should be much faster (cache hit)
        assert result2["response_time_ms"] < result1["response_time_ms"]


class TestPromptEngineering:
    """Test Prompt Engineering functionality."""

    @pytest.fixture
    def prompt_engineer(self, mock_llm_gateway):
        """Create prompt engineering instance."""
        return PromptEngineering(llm_gateway=mock_llm_gateway)

    def test_dynamic_prompt_construction(self, prompt_engineer):
        """Test dynamic prompt construction based on context."""
        base_task = "analyze_sentiment"
        context = {
            "domain": "customer_reviews",
            "complexity": "detailed",
            "output_format": "structured",
            "language": "english"
        }

        constructed_prompt = prompt_engineer.construct_dynamic_prompt(base_task, context)

        # Should include context-specific elements
        assert "customer reviews" in constructed_prompt.lower()
        assert "detailed" in constructed_prompt.lower()
        assert "structured" in constructed_prompt.lower()

        # Should have proper prompt structure
        assert "Task:" in constructed_prompt or "Instructions:" in constructed_prompt
        assert "Output:" in constructed_prompt

    def test_prompt_optimization_scoring(self, prompt_engineer):
        """Test prompt optimization and scoring."""
        test_prompts = [
            "Analyze this text",  # Basic
            "Please analyze the following text and provide detailed insights about sentiment, tone, and key themes.",  # Good
            "Can you maybe, like, analyze this text if you have time? It would be great if you could provide some insights.",  # Poor
        ]

        scores = []
        for prompt in test_prompts:
            score = asyncio.run(prompt_engineer.score_prompt_quality(prompt))
            scores.append(score)

        # Scores should reflect prompt quality
        assert scores[0]["overall_score"] < scores[1]["overall_score"]  # Basic < Good
        assert scores[2]["overall_score"] < scores[1]["overall_score"]  # Poor < Good

        # Good prompt should have high scores
        assert scores[1]["overall_score"] > 0.7

    def test_context_aware_prompt_adaptation(self, prompt_engineer):
        """Test context-aware prompt adaptation."""
        base_prompt = "Summarize this document"
        contexts = [
            {"audience": "executive", "expected_length": "brief"},
            {"audience": "technical", "expected_length": "detailed"},
            {"audience": "general", "expected_length": "medium"}
        ]

        adapted_prompts = []
        for context in contexts:
            adapted = prompt_engineer.adapt_prompt_to_context(base_prompt, context)
            adapted_prompts.append(adapted)

        # Each adapted prompt should be different
        assert len(set(adapted_prompts)) == len(adapted_prompts)

        # Should reflect audience and length preferences
        assert "executive" in adapted_prompts[0].lower() or "brief" in adapted_prompts[0].lower()
        assert "technical" in adapted_prompts[1].lower() or "detailed" in adapted_prompts[1].lower()

    def test_prompt_template_library(self, prompt_engineer):
        """Test prompt template library and selection."""
        task_requirements = {
            "task_type": "content_analysis",
            "domain": "technical",
            "complexity": "advanced",
            "output_format": "structured"
        }

        selected_template = prompt_engineer.select_template_from_library(task_requirements)

        assert "template_id" in selected_template
        assert "template_content" in selected_template
        assert "matching_score" in selected_template

        # Should have high matching score for requirements
        assert selected_template["matching_score"] > 0.7

        # Template should be appropriate for the requirements
        template_content = selected_template["template_content"]
        assert "analysis" in template_content.lower()
        assert "technical" in template_content.lower()

    def test_prompt_iteration_and_refinement(self, prompt_engineer):
        """Test iterative prompt refinement."""
        initial_prompt = "Tell me about AI"
        target_performance = 0.85  # Target quality score

        refinement_result = asyncio.run(prompt_engineer.iterative_prompt_refinement(
            initial_prompt, target_performance
        ))

        assert "final_prompt" in refinement_result
        assert "iterations" in refinement_result
        assert "final_score" in refinement_result
        assert "improvement_history" in refinement_result

        # Should achieve target performance
        assert refinement_result["final_score"] >= target_performance

        # Should show improvement over iterations
        improvements = refinement_result["improvement_history"]
        assert len(improvements) > 1

        # Final score should be better than initial
        assert refinement_result["final_score"] > improvements[0]["score"]

    def test_prompt_ab_testing(self, prompt_engineer):
        """Test A/B testing for prompt optimization."""
        prompt_variants = [
            "Analyze this text for sentiment",
            "Please analyze the sentiment of the following text",
            "Perform a detailed sentiment analysis on this content"
        ]

        test_data = [
            {"text": "I love this product!", "expected_sentiment": "positive"},
            {"text": "This is terrible", "expected_sentiment": "negative"},
            {"text": "It's okay", "expected_sentiment": "neutral"}
        ]

        ab_test_result = asyncio.run(prompt_engineer.run_prompt_ab_test(
            prompt_variants, test_data
        ))

        assert "winner" in ab_test_result
        assert "variant_scores" in ab_test_result
        assert "statistical_significance" in ab_test_result
        assert "recommendations" in ab_test_result

        # Should identify a winning variant
        assert ab_test_result["winner"] in prompt_variants

        # Should have scores for all variants
        assert len(ab_test_result["variant_scores"]) == len(prompt_variants)

        # Winner should have highest score
        winner_score = ab_test_result["variant_scores"][ab_test_result["winner"]]
        other_scores = [score for prompt, score in ab_test_result["variant_scores"].items()
                       if prompt != ab_test_result["winner"]]
        assert all(winner_score >= score for score in other_scores)


class TestOutputGenerator:
    """Test Output Generator functionality."""

    @pytest.fixture
    def output_generator(self, mock_llm_gateway):
        """Create output generator instance."""
        return OutputGenerator(llm_gateway=mock_llm_gateway)

    def test_structured_output_generation(self, output_generator):
        """Test structured output generation."""
        analysis_result = {
            "document_id": "doc_123",
            "sentiment": "positive",
            "key_topics": ["technology", "innovation"],
            "confidence_scores": {"sentiment": 0.89, "topics": 0.76}
        }

        output_format = {
            "type": "json",
            "schema": {
                "summary": "string",
                "insights": ["string"],
                "recommendations": ["string"],
                "confidence": "number"
            }
        }

        structured_output = asyncio.run(output_generator.generate_structured_output(
            analysis_result, output_format
        ))

        assert "summary" in structured_output
        assert "insights" in structured_output
        assert "recommendations" in structured_output
        assert "confidence" in structured_output

        # Should validate against schema
        assert isinstance(structured_output["insights"], list)
        assert isinstance(structured_output["recommendations"], list)
        assert isinstance(structured_output["confidence"], (int, float))

    def test_adaptive_output_formatting(self, output_generator):
        """Test adaptive output formatting based on context."""
        content = {
            "analysis_type": "document_summary",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "sentiment_score": 0.75
        }

        contexts = [
            {"audience": "executive", "format": "brief"},
            {"audience": "analyst", "format": "detailed"},
            {"audience": "developer", "format": "technical"}
        ]

        for context in contexts:
            formatted_output = asyncio.run(output_generator.adapt_output_format(
                content, context
            ))

            assert "formatted_content" in formatted_output
            assert "format_type" in formatted_output
            assert formatted_output["format_type"] == context["format"]

            # Content should be adapted to audience
            if context["audience"] == "executive":
                assert len(formatted_output["formatted_content"]) < 500  # Brief
            elif context["audience"] == "analyst":
                assert "sentiment_score" in formatted_output["formatted_content"]  # Detailed

    def test_multimodal_output_generation(self, output_generator):
        """Test multimodal output generation (text, charts, etc.)."""
        data = {
            "time_series": {
                "dates": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "values": [10, 15, 12]
            },
            "categories": {
                "labels": ["A", "B", "C"],
                "values": [30, 45, 25]
            },
            "insights": [
                "Trend shows increasing values",
                "Category B has highest value",
                "Overall positive trajectory"
            ]
        }

        multimodal_output = asyncio.run(output_generator.generate_multimodal_output(data))

        assert "text_summary" in multimodal_output
        assert "visualizations" in multimodal_output
        assert "structured_data" in multimodal_output

        # Should include multiple visualization types
        visualizations = multimodal_output["visualizations"]
        assert len(visualizations) >= 2  # At least line chart and bar chart

        # Should have text insights
        assert len(multimodal_output["text_summary"]) > 0

    def test_output_quality_enhancement(self, output_generator):
        """Test output quality enhancement and polishing."""
        raw_output = "The analysis shows that the document is mostly positive. There are some good points and some areas for improvement. Overall it's decent work."

        enhanced_output = asyncio.run(output_generator.enhance_output_quality(raw_output))

        assert "enhanced_text" in enhanced_output
        assert "quality_improvements" in enhanced_output
        assert "readability_score" in enhanced_output

        # Enhanced output should be more polished
        assert len(enhanced_output["enhanced_text"]) >= len(raw_output)

        # Should show quality improvements
        improvements = enhanced_output["quality_improvements"]
        assert len(improvements) > 0

        # Readability should be improved
        assert enhanced_output["readability_score"] > 50  # Decent readability

    def test_output_validation_and_correction(self, output_generator):
        """Test output validation and error correction."""
        potentially_invalid_outputs = [
            {"sentiment": "invalid_sentiment_value", "confidence": 1.5},  # Invalid values
            {"missing_required_field": "incomplete"},  # Missing fields
            {"inconsistent_data": {"score": 0.8, "category": "inconsistent"}}  # Inconsistent data
        ]

        for invalid_output in potentially_invalid_outputs:
            validated_output = asyncio.run(output_generator.validate_and_correct_output(
                invalid_output
            ))

            assert "corrected_output" in validated_output
            assert "validation_errors" in validated_output
            assert "corrections_applied" in validated_output

            # Should have identified errors
            assert len(validated_output["validation_errors"]) > 0

            # Should have applied corrections
            assert len(validated_output["corrections_applied"]) > 0

    def test_real_time_output_streaming(self, output_generator):
        """Test real-time output streaming capabilities."""
        content_stream = [
            {"chunk": "The analysis", "timestamp": datetime.now()},
            {"chunk": " shows positive", "timestamp": datetime.now()},
            {"chunk": " sentiment with", "timestamp": datetime.now()},
            {"chunk": " high confidence", "timestamp": datetime.now()}
        ]

        streaming_result = asyncio.run(output_generator.stream_output_realtime(content_stream))

        assert "streamed_content" in streaming_result
        assert "streaming_metrics" in streaming_result
        assert "quality_checks" in streaming_result

        # Should maintain streaming order
        streamed = streaming_result["streamed_content"]
        assert streamed == "The analysis shows positive sentiment with high confidence"

        # Should have timing metrics
        metrics = streaming_result["streaming_metrics"]
        assert "total_streaming_time" in metrics
        assert "chunks_processed" in metrics
        assert metrics["chunks_processed"] == len(content_stream)


class TestLLMPerformanceOptimization:
    """Test LLM performance optimization features."""

    @pytest.fixture
    def performance_optimizer(self, mock_llm_gateway):
        """Create performance optimizer instance."""
        return LLMGatewayIntegration(llm_gateway=mock_llm_gateway)

    def test_request_batching_optimization(self, performance_optimizer):
        """Test request batching for performance optimization."""
        requests = [
            {"prompt": "Summarize text 1", "priority": "normal"},
            {"prompt": "Summarize text 2", "priority": "high"},
            {"prompt": "Summarize text 3", "priority": "normal"},
            {"prompt": "Summarize text 4", "priority": "low"}
        ]

        batching_result = asyncio.run(performance_optimizer.optimize_request_batching(requests))

        assert "batches" in batching_result
        assert "optimization_metrics" in batching_result

        # Should create multiple batches
        assert len(batching_result["batches"]) > 1

        # High priority should be in first batch
        first_batch = batching_result["batches"][0]
        high_priority_in_first = any(req["priority"] == "high" for req in first_batch["requests"])
        assert high_priority_in_first

        # Should show performance improvements
        metrics = batching_result["optimization_metrics"]
        assert "estimated_time_savings" in metrics
        assert metrics["estimated_time_savings"] > 0

    def test_model_caching_strategy(self, performance_optimizer):
        """Test intelligent model caching strategy."""
        usage_patterns = {
            "frequent_requests": [
                {"model": "gpt-3.5-turbo", "frequency": 100, "avg_response_time": 2000},
                {"model": "gpt-4", "frequency": 50, "avg_response_time": 5000},
                {"model": "claude-2", "frequency": 25, "avg_response_time": 3000}
            ],
            "cache_size_mb": 1024,
            "cache_ttl_hours": 24
        }

        caching_strategy = asyncio.run(performance_optimizer.optimize_model_caching(usage_patterns))

        assert "cache_recommendations" in caching_strategy
        assert "performance_impact" in caching_strategy
        assert "cache_efficiency" in caching_strategy

        # Should recommend caching frequently used models
        recommendations = caching_strategy["cache_recommendations"]
        assert len(recommendations) > 0

        # Should prioritize by frequency and response time
        top_recommendation = recommendations[0]
        assert top_recommendation["model"] == "gpt-3.5-turbo"  # Most frequent

    def test_load_balancing_across_models(self, performance_optimizer):
        """Test load balancing across multiple LLM models."""
        models = [
            {"name": "gpt-3.5-turbo", "capacity": 100, "current_load": 80, "response_time": 2000},
            {"name": "gpt-4", "capacity": 50, "current_load": 45, "response_time": 5000},
            {"name": "claude-2", "capacity": 75, "current_load": 30, "response_time": 3000}
        ]

        requests = [
            {"type": "fast_response", "complexity": "low"},
            {"type": "high_quality", "complexity": "high"},
            {"type": "balanced", "complexity": "medium"}
        ]

        load_balancing = asyncio.run(performance_optimizer.balance_load_across_models(
            models, requests
        ))

        assert "routing_decisions" in load_balancing
        assert "load_distribution" in load_balancing
        assert "performance_predictions" in load_balancing

        # Should route fast requests to fastest available model
        routing = load_balancing["routing_decisions"]
        fast_request_routing = next(r for r in routing if r["request_type"] == "fast_response")
        assert fast_request_routing["assigned_model"] == "gpt-3.5-turbo"

        # Should route complex requests to high-capacity models
        complex_request_routing = next(r for r in routing if r["request_type"] == "high_quality")
        assert complex_request_routing["assigned_model"] in ["gpt-4", "claude-2"]

    def test_adaptive_rate_limiting(self, performance_optimizer):
        """Test adaptive rate limiting based on system load."""
        system_metrics = {
            "current_load": 75,
            "response_time_p95": 3000,
            "error_rate": 0.02,
            "available_models": ["gpt-3.5-turbo", "gpt-4", "claude-2"]
        }

        rate_limits = asyncio.run(performance_optimizer.calculate_adaptive_rate_limits(system_metrics))

        assert "rate_limits" in rate_limits
        assert "adjustment_reasons" in rate_limits
        assert "predicted_impact" in rate_limits

        # Should adjust limits based on load
        limits = rate_limits["rate_limits"]
        assert "requests_per_minute" in limits
        assert limits["requests_per_minute"] > 0

        # High load should result in lower limits
        if system_metrics["current_load"] > 70:
            assert any("load" in reason.lower() for reason in rate_limits["adjustment_reasons"])

    def test_cost_optimization_strategies(self, performance_optimizer):
        """Test cost optimization strategies for LLM usage."""
        usage_patterns = {
            "monthly_budget": 5000,
            "current_spending": 3200,
            "model_usage": {
                "gpt-4": {"requests": 1000, "cost_per_request": 0.03, "avg_tokens": 2000},
                "gpt-3.5-turbo": {"requests": 5000, "cost_per_request": 0.002, "avg_tokens": 500},
                "claude-2": {"requests": 500, "cost_per_request": 0.015, "avg_tokens": 1500}
            },
            "performance_requirements": {
                "min_quality_score": 0.8,
                "max_response_time": 5000
            }
        }

        cost_optimization = asyncio.run(performance_optimizer.optimize_cost_strategy(usage_patterns))

        assert "optimization_recommendations" in cost_optimization
        assert "estimated_savings" in cost_optimization
        assert "performance_impact" in cost_optimization
        assert "implementation_plan" in cost_optimization

        # Should recommend cost-effective alternatives
        recommendations = cost_optimization["optimization_recommendations"]
        assert len(recommendations) > 0

        # Should show significant savings potential
        assert cost_optimization["estimated_savings"]["monthly_dollars"] > 500

        # Should maintain performance requirements
        performance_impact = cost_optimization["performance_impact"]
        assert performance_impact["quality_degradation"] < 0.1  # Less than 10% degradation
