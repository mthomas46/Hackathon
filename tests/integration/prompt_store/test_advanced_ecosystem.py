"""Integration tests for the advanced prompt ecosystem."""

import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from services.prompt_store.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create test client for the prompt store API."""
    return TestClient(app)


@pytest.mark.integration
class TestAdvancedEcosystemIntegration:
    """Integration tests for the complete advanced prompt ecosystem."""

    async def test_complete_analytics_workflow(self, test_client):
        """Test complete analytics workflow from prompt creation to metrics collection."""
        # Step 1: Create a prompt
        prompt_data = {
            "name": f"analytics_test_{uuid.uuid4().hex[:8]}",
            "category": "testing",
            "content": "Analyze this code: {code}",
            "description": "Test prompt for analytics",
            "variables": ["code"],
            "tags": ["analytics", "test"],
            "created_by": "test_user"
        }

        create_response = test_client.post("/api/v1/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["data"]["id"]

        # Step 2: Record usage metrics
        usage_data = {
            "success": True,
            "response_time_ms": 1200,
            "input_tokens": 50,
            "output_tokens": 100,
            "llm_service": "gpt-4"
        }

        metrics_response = test_client.post(
            f"/api/v1/analytics/usage?prompt_id={prompt_id}&version=1",
            json=usage_data
        )
        assert metrics_response.status_code == 200

        # Step 3: Record user satisfaction
        satisfaction_data = {
            "prompt_id": prompt_id,
            "user_id": "test_user_123",
            "session_id": f"session_{uuid.uuid4().hex[:8]}",
            "rating": 4.5,
            "feedback_text": "Great analysis!",
            "context_tags": ["code_review", "python"],
            "use_case_category": "development"
        }

        satisfaction_response = test_client.post(
            "/api/v1/analytics/satisfaction",
            json=satisfaction_data
        )
        assert satisfaction_response.status_code == 200

        # Step 4: Get analytics dashboard
        dashboard_response = test_client.get("/api/v1/analytics/dashboard?time_range_days=30")
        assert dashboard_response.status_code == 200

        dashboard_data = dashboard_response.json()["data"]
        assert "summary" in dashboard_data
        assert "performance_metrics" in dashboard_data
        assert "usage_trends" in dashboard_data

    async def test_ab_testing_complete_workflow(self, test_client):
        """Test complete A/B testing workflow."""
        # Step 1: Create two prompt variants
        prompt_a_data = {
            "name": f"ab_test_a_{uuid.uuid4().hex[:8]}",
            "category": "ab_testing",
            "content": "Version A: Analyze this code: {code}",
            "variables": ["code"],
            "created_by": "test_user"
        }

        prompt_b_data = {
            "name": f"ab_test_b_{uuid.uuid4().hex[:8]}",
            "category": "ab_testing",
            "content": "Version B: Review this code: {code}",
            "variables": ["code"],
            "created_by": "test_user"
        }

        # Create both prompts
        response_a = test_client.post("/api/v1/prompts", json=prompt_a_data)
        response_b = test_client.post("/api/v1/prompts", json=prompt_b_data)

        assert response_a.status_code == 201
        assert response_b.status_code == 201

        prompt_a_id = response_a.json()["data"]["id"]
        prompt_b_id = response_b.json()["data"]["id"]

        # Step 2: Create A/B test
        test_response = test_client.post(
            "/api/v1/optimization/ab-tests",
            params={
                "prompt_a_id": prompt_a_id,
                "prompt_b_id": prompt_b_id,
                "traffic_percentage": 50.0
            }
        )
        assert test_response.status_code == 200
        test_data = test_response.json()["data"]
        test_id = test_data["test_id"]

        # Step 3: Get prompt assignments for multiple users
        for i in range(10):
            user_id = f"user_{i}"
            assign_response = test_client.get(
                f"/api/v1/optimization/ab-tests/{test_id}/assign",
                params={"user_id": user_id}
            )
            assert assign_response.status_code == 200

            assignment = assign_response.json()["data"]
            assert assignment["assigned_prompt"] in [prompt_a_id, prompt_b_id]

        # Step 4: Record test results
        # Simulate some results favoring prompt_a
        for i in range(8):  # 8 results for prompt_a (good performance)
            result_response = test_client.post(
                f"/api/v1/optimization/ab-tests/{test_id}/results",
                params={
                    "prompt_id": prompt_a_id,
                    "success": True,
                    "score": 4.5
                }
            )
            assert result_response.status_code == 200

        for i in range(6):  # 6 results for prompt_b (mixed performance)
            success = i < 3  # First 3 succeed
            score = 4.0 if success else 2.0
            result_response = test_client.post(
                f"/api/v1/optimization/ab-tests/{test_id}/results",
                params={
                    "prompt_id": prompt_b_id,
                    "success": success,
                    "score": score
                }
            )
            assert result_response.status_code == 200

        # Step 5: Get test results
        results_response = test_client.get(f"/api/v1/optimization/ab-tests/{test_id}/results")
        assert results_response.status_code == 200

        results = results_response.json()["data"]
        assert results["status"] == "running"
        assert results["prompt_a"]["requests"] == 8
        assert results["prompt_b"]["requests"] == 6

        # Step 6: End test and declare winner
        end_response = test_client.post(f"/api/v1/optimization/ab-tests/{test_id}/end")
        assert end_response.status_code == 200

        end_data = end_response.json()["data"]
        assert "winner" in end_data
        # Should declare prompt_a as winner due to better performance

    async def test_orchestration_workflow_creation(self, test_client):
        """Test creating and executing orchestration workflows."""
        # Step 1: Create a conditional chain
        chain_definition = {
            "name": "Code Analysis Chain",
            "description": "Chain for comprehensive code analysis",
            "steps": [
                {
                    "type": "prompt",
                    "prompt_id": "analysis_prompt_123",
                    "conditions": []
                },
                {
                    "type": "llm_call",
                    "prompt_template": "Summarize the analysis: {result}",
                    "llm_service": "interpreter",
                    "conditions": [
                        {"field": "status", "operator": "equals", "value": "success"}
                    ]
                }
            ],
            "conditions": {}
        }

        chain_response = test_client.post("/api/v1/orchestration/chains", json=chain_definition)
        assert chain_response.status_code == 200
        chain_data = chain_response.json()["data"]
        chain_id = chain_data["id"]

        # Step 2: Execute the chain (would need proper prompt setup)
        # This is a basic structure test - full execution would require
        # actual prompts and LLM services to be available

        # Step 3: Create a pipeline
        pipeline_definition = {
            "name": "Document Processing Pipeline",
            "description": "Pipeline for processing documents",
            "stages": [
                {
                    "type": "parallel_prompts",
                    "prompts": [
                        {"name": "extractor_1", "id": "prompt_1"},
                        {"name": "extractor_2", "id": "prompt_2"}
                    ]
                },
                {
                    "type": "aggregation",
                    "aggregation_type": "concatenate",
                    "input_fields": ["result_1", "result_2"],
                    "output_field": "final_result"
                }
            ],
            "configuration": {"timeout": 30}
        }

        pipeline_response = test_client.post("/api/v1/orchestration/pipelines", json=pipeline_definition)
        assert pipeline_response.status_code == 200

    async def test_validation_workflow(self, test_client):
        """Test complete validation workflow."""
        # Step 1: Create a test suite
        test_suite = {
            "name": "Code Review Validation Suite",
            "description": "Comprehensive validation for code review prompts",
            "test_cases": [
                {
                    "id": "syntax_test",
                    "name": "Syntax Error Detection",
                    "input": "def broken_function(\n    print('hello'",
                    "expected_criteria": {
                        "min_length": 50,
                        "required_keywords": ["error", "syntax"],
                        "prohibited_words": ["correct", "valid"]
                    }
                },
                {
                    "id": "complexity_test",
                    "name": "Complexity Analysis",
                    "input": "def very_complex_function():\n    " + "x = 1\n    " * 20,
                    "expected_criteria": {
                        "min_length": 100,
                        "required_keywords": ["complexity", "maintainability"]
                    }
                }
            ]
        }

        suite_response = test_client.post("/api/v1/validation/test-suites", json=test_suite)
        assert suite_response.status_code == 200
        suite_data = suite_response.json()["data"]
        suite_id = suite_data["id"]

        # Step 2: Lint a prompt
        prompt_content = "Review this code and identify issues: {code}"
        lint_response = test_client.post(
            "/api/v1/validation/lint",
            json={"prompt_content": prompt_content}
        )
        assert lint_response.status_code == 200

        lint_data = lint_response.json()["data"]
        assert "issues_found" in lint_data
        assert "overall_score" in lint_data

        # Step 3: Detect bias
        biased_content = "The engineer should fix his code."
        bias_response = test_client.post(
            "/api/v1/validation/bias-detect",
            json={"prompt_content": biased_content}
        )
        assert bias_response.status_code == 200

        bias_data = bias_response.json()["data"]
        assert "bias_issues_found" in bias_data

        # Step 4: Validate output
        prompt_output = """# Code Review Results

## Issues Found:
1. Missing error handling
2. Inconsistent naming conventions
3. High cyclomatic complexity

## Recommendations:
- Add try-catch blocks
- Use consistent naming
- Refactor complex functions"""

        validation_criteria = {
            "min_length": 100,
            "required_keywords": ["issues", "recommendations"],
            "requires_structure": True
        }

        validate_response = test_client.post(
            "/api/v1/validation/output",
            json={
                "prompt_output": prompt_output,
                "expected_criteria": validation_criteria
            }
        )
        assert validate_response.status_code == 200

        validate_data = validate_response.json()["data"]
        assert "overall_score" in validate_data
        assert "criteria_results" in validate_data

    async def test_cross_service_intelligence(self, test_client):
        """Test cross-service intelligence features."""
        # Step 1: Generate prompts from code
        code_content = '''
def calculate_fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathOperations:
    """Mathematical operations utility."""

    def is_prime(self, num):
        """Check if number is prime."""
        if num < 2:
            return False
        for i in range(2, int(num**0.5) + 1):
            if num % i == 0:
                return False
        return True
'''

        code_response = test_client.post(
            "/api/v1/intelligence/code/generate",
            json={
                "code_content": code_content,
                "language": "python"
            }
        )
        assert code_response.status_code == 200

        code_data = code_response.json()["data"]
        assert "generated_prompts" in code_data
        assert len(code_data["generated_prompts"]) > 0

        # Step 2: Generate prompts from document
        document_content = """
# Machine Learning Fundamentals

## Supervised Learning
Supervised learning uses labeled data to train models.

## Unsupervised Learning
Unsupervised learning finds patterns in unlabeled data.

## Key Applications
- Image classification
- Natural language processing
- Predictive analytics
"""

        doc_response = test_client.post(
            "/api/v1/intelligence/document/generate",
            json={
                "document_content": document_content,
                "doc_type": "markdown"
            }
        )
        assert doc_response.status_code == 200

        doc_data = doc_response.json()["data"]
        assert "generated_prompts" in doc_data

        # Step 3: Generate service integration prompts
        service_response = test_client.post(
            "/api/v1/intelligence/service/generate",
            params={"service_name": "database"}
        )
        assert service_response.status_code == 200

        service_data = service_response.json()["data"]
        assert "prompts" in service_data
        assert len(service_data["prompts"]) > 0

    async def test_end_to_end_prompt_lifecycle(self, test_client):
        """Test complete prompt lifecycle from creation to optimization."""
        # Step 1: Create initial prompt
        prompt_data = {
            "name": f"lifecycle_test_{uuid.uuid4().hex[:8]}",
            "category": "lifecycle_testing",
            "content": "Analyze this: {input}",
            "description": "Test prompt for lifecycle management",
            "variables": ["input"],
            "tags": ["lifecycle", "test"],
            "created_by": "test_user"
        }

        create_response = test_client.post("/api/v1/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["data"]["id"]

        # Step 2: Lint the prompt
        lint_response = test_client.post(
            "/api/v1/validation/lint",
            json={"prompt_content": prompt_data["content"]}
        )
        assert lint_response.status_code == 200

        # Step 3: Generate prompt variations
        variations_response = test_client.post(
            "/api/v1/optimization/variations",
            json={
                "prompt_content": prompt_data["content"],
                "count": 2
            }
        )
        assert variations_response.status_code == 200

        variations_data = variations_response.json()["data"]
        assert "variations" in variations_data
        assert len(variations_data["variations"]) <= 2

        # Step 4: Create A/B test with variations (would need to create actual prompts)
        # This demonstrates the integration capability

        # Step 5: Record some usage analytics
        usage_data = {
            "success": True,
            "response_time_ms": 800,
            "input_tokens": 25,
            "output_tokens": 75,
            "llm_service": "gpt-3.5-turbo"
        }

        analytics_response = test_client.post(
            f"/api/v1/analytics/usage?prompt_id={prompt_id}&version=1",
            json=usage_data
        )
        assert analytics_response.status_code == 200

        # Step 6: Get performance overview
        perf_response = test_client.get("/api/v1/analytics/performance?time_range_days=7")
        assert perf_response.status_code == 200

        # Step 7: Analyze prompt effectiveness
        effectiveness_response = test_client.post(
            f"/api/v1/intelligence/prompts/{prompt_id}/analyze"
        )
        assert effectiveness_response.status_code == 200

    async def test_get_standard_test_suites(self, test_client):
        """Test retrieving standard test suites."""
        response = test_client.get("/api/v1/validation/test-suites/standard")
        assert response.status_code == 200

        data = response.json()["data"]
        assert "test_suites" in data
        assert isinstance(data["test_suites"], list)
        assert len(data["test_suites"]) >= 2  # At least code generation and content writing

        # Verify suite structure
        suite = data["test_suites"][0]
        assert "id" in suite
        assert "name" in suite
        assert "description" in suite
        assert "test_cases" in suite

    async def test_select_optimal_prompt(self, test_client):
        """Test optimal prompt selection."""
        task_description = "Review Python code for bugs and improvements"

        response = test_client.post(
            "/api/v1/orchestration/prompts/select",
            json={
                "task_description": task_description,
                "context": {
                    "language": "python",
                    "complexity": "medium",
                    "domain": "software_development"
                }
            }
        )
        assert response.status_code == 200

        data = response.json()["data"]
        assert "prompt_id" in data
        assert data["task_description"] == task_description

    async def test_get_prompt_recommendations(self, test_client):
        """Test getting prompt recommendations."""
        task_description = "Generate comprehensive documentation"

        response = test_client.post(
            "/api/v1/orchestration/prompts/recommend",
            json={
                "task_description": task_description,
                "context": {"format": "markdown", "audience": "developers"}
            }
        )
        assert response.status_code == 200

        data = response.json()["data"]
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
