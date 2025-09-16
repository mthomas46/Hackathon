"""Unit tests for intelligence domain functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from services.prompt_store.domain.intelligence.service import IntelligenceService


@pytest.fixture
def intelligence_service():
    """Create intelligence service for testing."""
    return IntelligenceService()


class TestIntelligenceService:
    """Test cases for intelligence service functionality."""

    @pytest.mark.asyncio
    async def test_generate_prompts_from_code_success(self, intelligence_service):
        """Test generating prompts from code analysis successfully."""
        code_content = """
def calculate_fibonacci(n):
    '''Calculate the nth Fibonacci number.'''
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathUtils:
    '''Utility class for mathematical operations.'''

    def is_prime(self, num):
        '''Check if a number is prime.'''
        if num < 2:
            return False
        for i in range(2, int(num**0.5) + 1):
            if num % i == 0:
                return False
        return True
"""

        # Mock the code analyzer response
        mock_analysis = {
            "success": True,
            "data": {
                "language": "python",
                "functions": [
                    {
                        "name": "calculate_fibonacci",
                        "purpose": "Calculate the nth Fibonacci number",
                        "parameters": ["n"]
                    },
                    {
                        "name": "is_prime",
                        "purpose": "Check if a number is prime",
                        "parameters": ["num"]
                    }
                ],
                "classes": [
                    {
                        "name": "MathUtils",
                        "purpose": "Utility class for mathematical operations",
                        "methods": ["is_prime"]
                    }
                ],
                "complexity": {"overall": 3}
            }
        }

        with patch.object(intelligence_service.clients, 'analyze_code', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis

            result = await intelligence_service.generate_prompts_from_code(code_content, "python")

            # Verify the result structure
            assert "source_type" in result
            assert result["source_type"] == "code"
            assert result["language"] == "python"
            assert "analysis_summary" in result
            assert "generated_prompts" in result
            assert isinstance(result["generated_prompts"], list)
            assert len(result["generated_prompts"]) > 0

            # Check that prompts have required fields
            for prompt in result["generated_prompts"]:
                assert "id" in prompt
                assert "name" in prompt
                assert "content" in prompt
                assert "category" in prompt

    @pytest.mark.asyncio
    async def test_generate_prompts_from_code_analysis_failure(self, intelligence_service):
        """Test handling code analysis failure."""
        code_content = "print('hello')"

        with patch.object(intelligence_service.clients, 'analyze_code', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"success": False, "error": "Analysis failed"}

            result = await intelligence_service.generate_prompts_from_code(code_content, "python")

            # Should return error
            assert "error" in result
            assert "Analysis failed" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_prompts_from_document_success(self, intelligence_service):
        """Test generating prompts from document analysis successfully."""
        document_content = """
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables systems to learn from data.

## Key Concepts

1. **Supervised Learning**: Learning from labeled data
2. **Unsupervised Learning**: Finding patterns in unlabeled data
3. **Reinforcement Learning**: Learning through interaction

## Applications

Machine learning has many practical applications including:
- Image recognition
- Natural language processing
- Recommendation systems
"""

        # Mock the summarizer response
        mock_summary = {
            "success": True,
            "data": {
                "main_topics": ["Machine Learning", "Supervised Learning", "Applications"],
                "key_concepts": ["artificial intelligence", "supervised learning", "unsupervised learning"],
                "sentiment": "neutral",
                "word_count": 150
            }
        }

        with patch.object(intelligence_service.clients, 'summarize_document', new_callable=AsyncMock) as mock_summarize:
            mock_summarize.return_value = mock_summary

            result = await intelligence_service.generate_prompts_from_document(document_content, "markdown")

            # Verify the result structure
            assert result["source_type"] == "document"
            assert result["document_type"] == "markdown"
            assert "analysis_summary" in result
            assert "generated_prompts" in result
            assert isinstance(result["generated_prompts"], list)
            assert len(result["generated_prompts"]) > 0

    @pytest.mark.asyncio
    async def test_generate_prompts_from_document_analysis_failure(self, intelligence_service):
        """Test handling document analysis failure."""
        document_content = "Short document"

        with patch.object(intelligence_service.clients, 'summarize_document', new_callable=AsyncMock) as mock_summarize:
            mock_summarize.return_value = {"success": False, "error": "Summarization failed"}

            result = await intelligence_service.generate_prompts_from_document(document_content, "markdown")

            # Should return error
            assert "error" in result
            assert "Summarization failed" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_service_integration_prompts(self, intelligence_service):
        """Test generating service integration prompts."""
        service_name = "database"
        service_description = "PostgreSQL database service"

        prompts = await intelligence_service.generate_service_integration_prompts(service_name, service_description)

        # Should return a list of prompts
        assert isinstance(prompts, list)
        assert len(prompts) > 0

        # Check prompt structure
        for prompt in prompts:
            assert "id" in prompt
            assert "name" in prompt
            assert "content" in prompt
            assert "category" in prompt
            assert "tags" in prompt
            assert service_name.lower() in prompt["tags"]
            assert prompt["category"] == "service_integration"

    @pytest.mark.asyncio
    async def test_generate_service_integration_prompts_different_services(self, intelligence_service):
        """Test generating prompts for different service types."""
        services_to_test = ["api", "frontend", "testing"]

        for service_name in services_to_test:
            prompts = await intelligence_service.generate_service_integration_prompts(service_name)

            assert isinstance(prompts, list)
            assert len(prompts) > 0

            for prompt in prompts:
                assert service_name.lower() in prompt["tags"]

    @pytest.mark.asyncio
    async def test_analyze_prompt_effectiveness_success(self, intelligence_service):
        """Test analyzing prompt effectiveness successfully."""
        prompt_id = "test_prompt_123"
        usage_history = [
            {"success": True, "response_time_ms": 1200, "user_rating": 4.5},
            {"success": True, "response_time_ms": 1100, "user_rating": 5.0},
            {"success": False, "response_time_ms": 2000, "user_rating": 2.0},
            {"success": True, "response_time_ms": 1300, "user_rating": 4.0}
        ]

        result = await intelligence_service.analyze_prompt_effectiveness(prompt_id, usage_history)

        # Verify analysis structure
        assert result["prompt_id"] == prompt_id
        assert "metrics" in result
        assert "recommendations" in result
        assert "effectiveness_score" in result

        # Check metrics
        metrics = result["metrics"]
        assert metrics["total_uses"] == 4
        assert metrics["success_rate"] == 0.75  # 3 out of 4 successes
        assert metrics["avg_response_time_ms"] == 1400  # Average of all times
        assert abs(metrics["avg_user_satisfaction"] - 3.875) < 0.01  # Average rating

        # Should have recommendations for low satisfaction
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_prompt_effectiveness_no_history(self, intelligence_service):
        """Test analyzing prompt effectiveness with no usage history."""
        prompt_id = "test_prompt_123"
        usage_history = []

        result = await intelligence_service.analyze_prompt_effectiveness(prompt_id, usage_history)

        # Should return error for no history
        assert "error" in result
        assert "No usage history available" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_prompt_effectiveness_perfect_performance(self, intelligence_service):
        """Test analyzing prompt with perfect performance."""
        prompt_id = "perfect_prompt"
        usage_history = [
            {"success": True, "response_time_ms": 500, "user_rating": 5.0},
            {"success": True, "response_time_ms": 600, "user_rating": 5.0},
            {"success": True, "response_time_ms": 550, "user_rating": 5.0}
        ]

        result = await intelligence_service.analyze_prompt_effectiveness(prompt_id, usage_history)

        # Should have high effectiveness score
        assert result["effectiveness_score"] > 0.8

        # Should have few or no recommendations
        assert len(result["recommendations"]) == 0

    @pytest.mark.asyncio
    async def test_analyze_prompt_effectiveness_poor_performance(self, intelligence_service):
        """Test analyzing prompt with poor performance."""
        prompt_id = "poor_prompt"
        usage_history = [
            {"success": False, "response_time_ms": 5000, "user_rating": 1.0},
            {"success": False, "response_time_ms": 6000, "user_rating": 1.5},
            {"success": True, "response_time_ms": 4500, "user_rating": 2.0}
        ]

        result = await intelligence_service.analyze_prompt_effectiveness(prompt_id, usage_history)

        # Should have low effectiveness score
        assert result["effectiveness_score"] < 0.5

        # Should have multiple recommendations
        assert len(result["recommendations"]) >= 2

    def test_is_tutorial_document_positive(self, intelligence_service):
        """Test detecting tutorial documents."""
        tutorial_content = """
# How to Get Started with Python

This tutorial will teach you the basics of Python programming.

## Prerequisites

Before starting, you should know:
- Basic computer usage
- How to open a terminal

## Step 1: Installation

First, download Python from the official website...

## Step 2: Your First Program

Let's write our first "Hello, World!" program...

## Practice Exercises

1. Write a program that prints your name
2. Create a simple calculator
"""

        result = intelligence_service._is_tutorial_document(tutorial_content)
        assert result is True

    def test_is_tutorial_document_negative(self, intelligence_service):
        """Test rejecting non-tutorial documents."""
        non_tutorial_content = """
# Company Financial Report Q3 2025

## Executive Summary

This quarter, the company achieved record revenues of $10M...

## Market Analysis

The competitive landscape shows increasing pressure from new entrants...

## Financial Metrics

Revenue: $10,000,000
Gross Margin: 65%
Net Profit: $2,500,000
"""

        result = intelligence_service._is_tutorial_document(non_tutorial_content)
        assert result is False

    def test_create_function_doc_prompt(self, intelligence_service):
        """Test creating function documentation prompts."""
        func = {
            "name": "validate_email",
            "purpose": "Validate email address format",
            "parameters": ["email", "strict"]
        }

        prompt = intelligence_service._create_function_doc_prompt(func, "python")

        assert "validate_email" in prompt["name"]
        assert "validate_email" in prompt["content"]
        assert prompt["category"] == "code_documentation"
        assert "python" in prompt["tags"]
        assert "function" in prompt["tags"]
        assert "auto_generated" in prompt["tags"]

    def test_create_class_doc_prompt(self, intelligence_service):
        """Test creating class documentation prompts."""
        cls = {
            "name": "UserManager",
            "purpose": "Manage user accounts and authentication",
            "methods": ["create_user", "authenticate", "update_profile"]
        }

        prompt = intelligence_service._create_class_doc_prompt(cls, "javascript")

        assert "UserManager" in prompt["name"]
        assert "UserManager" in prompt["content"]
        assert prompt["category"] == "code_documentation"
        assert "javascript" in prompt["tags"]
        assert "class" in prompt["tags"]

    def test_create_api_doc_prompt(self, intelligence_service):
        """Test creating API documentation prompts."""
        analysis_data = {
            "functions": [
                {"name": "get_users", "purpose": "Retrieve user list"},
                {"name": "create_user", "purpose": "Create new user"},
                {"name": "update_user", "purpose": "Update user data"}
            ]
        }

        prompt = intelligence_service._create_api_doc_prompt(analysis_data)

        assert prompt is not None
        assert "API Documentation Suite" in prompt["name"]
        assert prompt["category"] == "api_documentation"
        assert "api" in prompt["tags"]
        assert "rest" in prompt["tags"]

    def test_is_api_code_positive(self, intelligence_service):
        """Test detecting API code patterns."""
        api_code = '''
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    return jsonify(created_user), 201

@app.route('/api/users/<id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    return jsonify(updated_user)
'''

        result = intelligence_service._is_api_code(api_code)
        assert result is True

    def test_is_api_code_negative(self, intelligence_service):
        """Test rejecting non-API code."""
        regular_code = '''
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathUtils:
    def factorial(self, n):
        if n == 0:
            return 1
        return n * self.factorial(n-1)
'''

        result = intelligence_service._is_api_code(regular_code)
        assert result is False

    def test_create_topic_expansion_prompt(self, intelligence_service):
        """Test creating topic expansion prompts."""
        topic = "Neural Networks"

        prompt = intelligence_service._create_topic_expansion_prompt(topic, "markdown")

        assert "Neural Networks" in prompt["name"]
        assert "Neural Networks" in prompt["content"]
        assert prompt["category"] == "content_creation"
        assert "content" in prompt["tags"]
        assert "expansion" in prompt["tags"]

    def test_create_concept_explanation_prompt(self, intelligence_service):
        """Test creating concept explanation prompts."""
        concept = "Backpropagation"

        prompt = intelligence_service._create_concept_explanation_prompt(concept)

        assert "Backpropagation" in prompt["name"]
        assert "Backpropagation" in prompt["content"]
        assert prompt["category"] == "educational"
        assert "explanation" in prompt["tags"]
        assert "concept" in prompt["tags"]

    def test_create_tutorial_prompt(self, intelligence_service):
        """Test creating tutorial prompts."""
        summary_data = {
            "main_topics": ["Python Basics", "Data Types", "Control Flow"],
            "key_concepts": ["variables", "loops", "functions"]
        }

        prompt = intelligence_service._create_tutorial_prompt(summary_data)

        assert "Comprehensive Tutorial" in prompt["name"]
        assert prompt["category"] == "educational"
        assert "tutorial" in prompt["tags"]
        assert "step-by-step" in prompt["tags"]
        assert "Python Basics" in prompt["content"]
