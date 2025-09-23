"""Unit Tests for Prompt Tuning in Data Services Dashboard.

This module tests prompt tuning capabilities including:
- Prompt editing and version management
- Performance testing and A/B testing
- AI-powered prompt enhancement
- Template library and customization

Tests cover the complete prompt tuning infrastructure within the Data Services Dashboard.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from pages.prompt_browser import PromptBrowser


class TestPromptEditingAndManagement:
    """Test Prompt Editing and Management functionality."""

    @pytest.fixture
    def prompt_browser(self, mock_prompt_client):
        """Create prompt browser instance."""
        return PromptBrowser(prompt_client=mock_prompt_client)

    def test_prompt_content_editing(self, prompt_browser):
        """Test prompt content editing capabilities."""
        original_prompt = {
            "id": "prompt_001",
            "name": "API Documentation Generator",
            "content": """You are an expert API documentation writer. Given the following API endpoint information:

{{api_endpoint}}
{{http_method}}
{{parameters}}
{{response_schema}}

Please generate comprehensive API documentation that includes:
1. Overview
2. Parameters description
3. Response format
4. Example usage
5. Error handling""",
            "category": "documentation",
            "tags": ["api", "documentation", "technical"],
            "version": "1.0",
            "variables": ["api_endpoint", "http_method", "parameters", "response_schema"]
        }

        edit_operations = [
            {
                "operation": "replace_text",
                "old_text": "API documentation writer",
                "new_text": "senior API documentation specialist"
            },
            {
                "operation": "add_section",
                "position": "end",
                "content": "\n\n6. Authentication requirements\n7. Rate limiting considerations"
            },
            {
                "operation": "update_variable",
                "variable_name": "parameters",
                "new_description": "List of API parameters with types and descriptions"
            }
        ]

        edit_result = prompt_browser.edit_prompt_content(original_prompt, edit_operations)

        assert edit_result["success"] is True
        assert "edited_prompt" in edit_result
        assert "edit_summary" in edit_result

        edited = edit_result["edited_prompt"]

        # Should apply text replacements
        assert "senior API documentation specialist" in edited["content"]
        assert "API documentation writer" not in edited["content"]

        # Should add new sections
        assert "Authentication requirements" in edited["content"]
        assert "Rate limiting considerations" in edited["content"]

        # Should track edit summary
        summary = edit_result["edit_summary"]
        assert summary["total_operations"] == len(edit_operations)
        assert summary["successful_operations"] == len(edit_operations)

    def test_prompt_version_management(self, prompt_browser):
        """Test prompt version management."""
        prompt_versions = [
            {
                "id": "prompt_001",
                "version": "1.0",
                "content": "Basic API documentation prompt",
                "created_at": datetime.now() - timedelta(days=10),
                "author": "john.doe",
                "performance_score": 0.75
            },
            {
                "id": "prompt_001",
                "version": "1.1",
                "content": "Enhanced API documentation prompt with examples",
                "created_at": datetime.now() - timedelta(days=5),
                "author": "jane.smith",
                "performance_score": 0.82
            },
            {
                "id": "prompt_001",
                "version": "2.0",
                "content": "Major rewrite with structured format",
                "created_at": datetime.now() - timedelta(days=1),
                "author": "john.doe",
                "performance_score": 0.89
            }
        ]

        version_result = prompt_browser.manage_prompt_versions(prompt_versions)

        assert version_result["success"] is True
        assert "version_history" in version_result
        assert "version_analysis" in version_result

        history = version_result["version_history"]

        # Should organize by version number
        assert len(history["versions"]) == len(prompt_versions)
        assert history["latest_version"] == "2.0"
        assert history["total_versions"] == 3

        # Should track version changes
        assert "version_changes" in history
        changes = history["version_changes"]
        assert len(changes) == 2  # Changes between versions

        analysis = version_result["version_analysis"]
        assert "performance_trend" in analysis
        assert "author_contributions" in analysis

        # Should show performance improvement
        assert analysis["performance_trend"] == "improving"


class TestPromptPerformanceTesting:
    """Test Prompt Performance Testing functionality."""

    @pytest.fixture
    def prompt_browser(self, mock_prompt_client):
        """Create prompt browser instance."""
        return PromptBrowser(prompt_client=mock_prompt_client)

    def test_prompt_performance_metrics(self, prompt_browser):
        """Test prompt performance metrics calculation."""
        performance_data = {
            "prompt_id": "prompt_001",
            "test_results": [
                {
                    "test_case": "api_doc_generation",
                    "execution_time_ms": 1250,
                    "output_quality_score": 0.85,
                    "token_usage": 450,
                    "success": True,
                    "metadata": {"complexity": "medium", "domain": "api_design"}
                },
                {
                    "test_case": "error_handling_doc",
                    "execution_time_ms": 980,
                    "output_quality_score": 0.92,
                    "token_usage": 380,
                    "success": True,
                    "metadata": {"complexity": "low", "domain": "error_handling"}
                },
                {
                    "test_case": "complex_microservice_doc",
                    "execution_time_ms": 2100,
                    "output_quality_score": 0.78,
                    "token_usage": 720,
                    "success": False,
                    "metadata": {"complexity": "high", "domain": "microservices"}
                }
            ],
            "baseline_comparison": {
                "previous_version_score": 0.82,
                "industry_average_score": 0.75
            }
        }

        metrics_result = prompt_browser.calculate_performance_metrics(performance_data)

        assert metrics_result["success"] is True
        assert "metrics" in metrics_result
        assert "analysis" in metrics_result

        metrics = metrics_result["metrics"]

        # Should calculate core metrics
        assert "average_execution_time_ms" in metrics
        assert "average_quality_score" in metrics
        assert "average_token_usage" in metrics
        assert "success_rate" in metrics

        # Should calculate derived metrics
        assert "efficiency_score" in metrics  # quality per token
        assert "reliability_score" in metrics  # success rate weighted
        assert "performance_consistency" in metrics  # standard deviation

        analysis = metrics_result["analysis"]
        assert "performance_trends" in analysis
        assert "strengths_weaknesses" in analysis
        assert "benchmarking_results" in analysis

        # Should compare to baseline
        benchmarking = analysis["benchmarking_results"]
        assert "vs_previous_version" in benchmarking
        assert "vs_industry_average" in benchmarking

    def test_ab_testing_framework(self, prompt_browser):
        """Test A/B testing framework for prompts."""
        ab_test_config = {
            "test_id": "prompt_ab_test_001",
            "name": "API Documentation Prompt Optimization",
            "description": "Testing two prompt variations for API documentation generation",
            "variants": [
                {
                    "variant_id": "variant_a",
                    "prompt_id": "prompt_001",
                    "name": "Structured Format",
                    "weight": 50  # 50% traffic
                },
                {
                    "variant_id": "variant_b",
                    "prompt_id": "prompt_002",
                    "name": "Conversational Format",
                    "weight": 50  # 50% traffic
                }
            ],
            "test_duration_days": 14,
            "sample_size": 1000,
            "success_metrics": [
                "output_quality_score",
                "user_satisfaction_rating",
                "generation_time_ms",
                "token_efficiency"
            ],
            "statistical_significance_threshold": 0.95,
            "early_stopping_rules": {
                "max_consecutive_wins": 5,
                "min_sample_size_per_variant": 100
            }
        }

        test_result = prompt_browser.setup_ab_test(ab_test_config)

        assert test_result["success"] is True
        assert "test_configuration" in test_result
        assert "traffic_distribution" in test_result

        config = test_result["test_configuration"]
        assert config["status"] == "initialized"
        assert "start_date" in config
        assert "end_date" in config

        distribution = test_result["traffic_distribution"]
        assert len(distribution) == len(ab_test_config["variants"])
        assert all(d["percentage"] == 50 for d in distribution)
