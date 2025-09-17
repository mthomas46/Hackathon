"""Unit tests for validation domain functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from services.prompt_store.domain.validation.service import ValidationService
from services.prompt_store.domain.validation.entities import (
    PromptTestingResult,
    BiasDetectionResult,
    ValidationReport
)


@pytest.fixture
def validation_service():
    """Create validation service for testing."""
    return ValidationService()


@pytest.mark.asyncio
class TestValidationService:
    """Test cases for validation service functionality."""

    async def test_run_prompt_test_success(self, validation_service):
        """Test running a prompt test successfully."""
        prompt_id = "test_prompt_123"
        version = 1
        test_suite_id = "suite_456"
        test_case = {
            "id": "test_001",
            "name": "Basic Functionality Test",
            "input": "Test input",
            "expected_output": "Expected result"
        }

        # Mock the LLM call for testing
        with patch.object(validation_service.clients, 'interpret_query', new_callable=AsyncMock) as mock_interpret:
            mock_interpret.return_value = {
                "success": True,
                "data": {
                    "response_text": "Test response",
                    "execution_time": 1.5
                }
            }

            result = await validation_service.run_prompt_test(
                prompt_id, version, test_suite_id, test_case
            )

            # Verify result structure
            assert isinstance(result, PromptTestingResult)
            assert result.prompt_id == prompt_id
            assert result.version == version
            assert result.test_suite_id == test_suite_id
            assert result.test_case_id == "test_001"
            assert result.test_name == "Basic Functionality Test"
            assert result.passed is True  # Mock passes
            assert result.execution_time_ms == 1500  # 1.5 * 1000

    async def test_run_test_suite(self, validation_service):
        """Test running a complete test suite."""
        prompt_id = "test_prompt_123"
        version = 1
        test_suite = {
            "id": "suite_456",
            "name": "Comprehensive Test Suite",
            "test_cases": [
                {
                    "id": "test_001",
                    "name": "Test 1",
                    "input": "Input 1"
                },
                {
                    "id": "test_002",
                    "name": "Test 2",
                    "input": "Input 2"
                }
            ]
        }

        with patch.object(validation_service, 'run_prompt_test', new_callable=AsyncMock) as mock_run_test:
            # Mock test results
            mock_run_test.side_effect = [
                PromptTestingResult(
                    id="result_1", prompt_id=prompt_id, version=version,
                    test_suite_id="suite_456", test_case_id="test_001",
                    test_name="Test 1", passed=True, execution_time_ms=1000,
                    output_quality_score=0.9, expected_output_similarity=0.95
                ),
                PromptTestingResult(
                    id="result_2", prompt_id=prompt_id, version=version,
                    test_suite_id="suite_456", test_case_id="test_002",
                    test_name="Test 2", passed=False, execution_time_ms=1200,
                    output_quality_score=0.7, expected_output_similarity=0.8
                )
            ]

            result = await validation_service.run_test_suite(prompt_id, version, test_suite)

            # Verify suite results
            assert result["test_suite_id"] == "suite_456"
            assert result["total_tests"] == 2
            assert result["passed_tests"] == 1
            assert result["failed_tests"] == 1
            assert result["success_rate"] == 0.5
            assert result["total_execution_time_ms"] == 2200
            assert result["average_execution_time_ms"] == 1100
            assert len(result["test_results"]) == 2

    async def test_lint_prompt_clean_prompt(self, validation_service):
        """Test linting a well-formed prompt."""
        clean_prompt = """Please analyze the following code and provide a detailed explanation of its functionality, including:

1. What the code does
2. Key algorithms or patterns used
3. Potential improvements or optimizations
4. Any security considerations

Code to analyze:
{code}"""

        issues = validation_service.lint_prompt(clean_prompt)

        # Clean prompt should have few or no issues
        assert issues["issues_found"] <= 2  # Allow minor issues
        assert issues["overall_score"] >= 0.7

    async def test_lint_prompt_problematic_prompt(self, validation_service):
        """Test linting a problematic prompt."""
        bad_prompt = "do it"  # Too short and vague

        issues = validation_service.lint_prompt(bad_prompt)

        # Should identify multiple issues
        assert issues["issues_found"] >= 2
        assert issues["overall_score"] <= 0.7  # Allow for reasonable scores on problematic prompts

        # Should include specific issues
        issue_types = [issue["type"] for issue in issues["issues"]]
        assert "too_vague" in issue_types

    async def test_detect_bias_gender_bias(self, validation_service):
        """Test detecting gender bias in prompts."""
        biased_prompt = "The salesman should ensure the customer is satisfied with his purchase."

        results = await validation_service.detect_bias(biased_prompt)

        # Should detect gender bias
        assert len(results) > 0

        gender_bias = next((r for r in results if r.bias_type == "gender"), None)
        assert gender_bias is not None
        assert gender_bias.severity_score > 0
        assert "his" in gender_bias.detected_phrases

    async def test_detect_bias_racial_bias(self, validation_service):
        """Test detecting racial bias in prompts."""
        biased_prompt = "The immigrant worker completed the task efficiently despite the language barrier."

        results = await validation_service.detect_bias(biased_prompt)

        # May or may not detect depending on patterns, but should not crash
        assert isinstance(results, list)

    async def test_detect_bias_no_bias(self, validation_service):
        """Test detecting bias in neutral prompts."""
        neutral_prompt = "The team member completed the task efficiently and effectively."

        results = await validation_service.detect_bias(neutral_prompt)

        # Should detect little to no bias
        total_severity = sum(r.severity_score for r in results)
        assert total_severity < 0.5  # Low bias score

    async def test_validate_output_meets_criteria(self, validation_service):
        """Test validating output that meets all criteria."""
        prompt_output = """# Analysis of the Code

## Overview
This function implements a binary search algorithm to find an element in a sorted array.

## Key Features
- Time complexity: O(log n)
- Space complexity: O(1)
- Returns the index of the target element

## Code Quality
The implementation is clean, efficient, and follows best practices."""

        expected_criteria = {
            "min_length": 100,
            "max_length": 2000,
            "required_keywords": ["algorithm", "complexity"],
            "prohibited_words": ["bad", "wrong"],
            "requires_structure": True
        }

        result = await validation_service.validate_output(prompt_output, expected_criteria)

        # Should pass most criteria
        assert result["overall_score"] > 0.8
        criteria_results = result["criteria_results"]
        assert criteria_results["length_check"] is True
        assert criteria_results["keyword_check"] is True
        assert criteria_results["prohibited_check"] is True
        assert criteria_results["structure_check"] is True

    async def test_validate_output_fails_criteria(self, validation_service):
        """Test validating output that fails criteria."""
        prompt_output = "This is a short response without proper structure."

        expected_criteria = {
            "min_length": 500,
            "required_keywords": ["algorithm", "analysis"],
            "prohibited_words": ["short"],
            "requires_structure": True
        }

        result = await validation_service.validate_output(prompt_output, expected_criteria)

        # Should fail multiple criteria
        assert result["overall_score"] < 0.5
        assert len(result["issues"]) >= 3

        criteria_results = result["criteria_results"]
        assert criteria_results["length_check"] is False
        assert criteria_results["keyword_check"] is False
        assert criteria_results["prohibited_check"] is False
        assert criteria_results["structure_check"] is False

    async def test_create_test_suite(self, validation_service):
        """Test creating a test suite."""
        name = "Code Review Test Suite"
        description = "Tests for code review prompt validation"
        test_cases = [
            {
                "id": "test_001",
                "name": "Basic Functionality",
                "input": "def hello(): pass",
                "expected_criteria": {"min_length": 50}
            },
            {
                "id": "test_002",
                "name": "Complex Code",
                "input": "class ComplexClass:\n    def method(self): return True",
                "expected_criteria": {"min_length": 100}
            }
        ]

        result = validation_service.create_test_suite(name, description, test_cases)

        # Verify test suite structure
        assert result["id"] is not None
        assert result["name"] == name
        assert result["description"] == description
        assert len(result["test_cases"]) == 2
        assert result["total_tests"] == 2
        assert "created_at" in result

    async def test_get_standard_test_suites(self, validation_service):
        """Test getting standard test suites."""
        suites = validation_service.get_standard_test_suites()

        # Should return predefined test suites
        assert isinstance(suites, list)
        assert len(suites) >= 2  # At least code generation and content writing

        # Check structure of first suite
        first_suite = suites[0]
        assert "id" in first_suite
        assert "name" in first_suite
        assert "description" in first_suite
        assert "test_cases" in first_suite
        assert isinstance(first_suite["test_cases"], list)


class TestBiasDetectionPatterns:
    """Test bias detection pattern matching."""

    def test_gender_bias_patterns(self, validation_service):
        """Test gender bias pattern detection."""
        patterns = validation_service._get_bias_patterns()["gender"]

        # Test male pronouns
        assert any("he" in p["pattern"] for p in patterns)
        assert any("him" in p["pattern"] for p in patterns)
        assert any("his" in p["pattern"] for p in patterns)

        # Test female pronouns
        assert any("she" in p["pattern"] for p in patterns)
        assert any("her" in p["pattern"] for p in patterns)

    def test_racial_bias_patterns(self, validation_service):
        """Test racial bias pattern detection."""
        patterns = validation_service._get_bias_patterns()["racial"]

        # Should include racial identifiers
        assert any("race" in p["pattern"] for p in patterns)
        assert any("ethnic" in p["pattern"] for p in patterns)

    def test_cultural_bias_patterns(self, validation_service):
        """Test cultural bias pattern detection."""
        patterns = validation_service._get_bias_patterns()["cultural"]

        # Should include cultural references
        assert any("western" in p["pattern"] for p in patterns)
        assert any("eastern" in p["pattern"] for p in patterns)

    def test_get_bias_alternatives(self, validation_service):
        """Test getting bias alternatives."""
        gender_alternatives = validation_service._get_bias_alternatives("gender")
        assert "they/them" in gender_alternatives
        assert "person" in gender_alternatives
        assert "individual" in gender_alternatives

        racial_alternatives = validation_service._get_bias_alternatives("racial")
        assert "person" in racial_alternatives
        assert "individual" in racial_alternatives

        unknown_alternatives = validation_service._get_bias_alternatives("unknown")
        assert isinstance(unknown_alternatives, list)
        assert len(unknown_alternatives) > 0


class TestPromptLintingRules:
    """Test prompt linting rules and scoring."""

    def test_lint_too_vague(self, validation_service):
        """Test detecting too vague prompts."""
        vague_prompt = "do it"

        issues = validation_service.lint_prompt(vague_prompt)

        too_vague_issue = next((i for i in issues["issues"] if i["type"] == "too_vague"), None)
        assert too_vague_issue is not None
        assert too_vague_issue["severity"] == "medium"

    def test_lint_unclear_references(self, validation_service):
        """Test detecting unclear pronoun references."""
        unclear_prompt = "Fix it so that it works properly."

        issues = validation_service.lint_prompt(unclear_prompt)

        unclear_ref_issue = next((i for i in issues["issues"] if i["type"] == "unclear_reference"), None)
        assert unclear_ref_issue is not None
        assert unclear_ref_issue["severity"] == "low"

    def test_lint_too_many_negatives(self, validation_service):
        """Test detecting excessive negative instructions."""
        negative_prompt = "Don't use this. Avoid that. Never do this. Don't forget to not include that."

        issues = validation_service.lint_prompt(negative_prompt)

        negative_issue = next((i for i in issues["issues"] if i["type"] == "too_many_negatives"), None)
        assert negative_issue is not None
        assert negative_issue["severity"] == "medium"

    def test_lint_overly_complex(self, validation_service):
        """Test detecting overly complex prompts."""
        complex_prompt = "\n\n" * 15  # Too many section breaks

        issues = validation_service.lint_prompt(complex_prompt)

        complex_issue = next((i for i in issues["issues"] if i["type"] == "overly_complex"), None)
        assert complex_issue is not None
        assert complex_issue["severity"] == "low"


class TestValidationReport:
    """Test validation report generation."""

    def test_validation_report_creation(self):
        """Test creating validation reports."""
        report = ValidationReport(
            id="report_123",
            prompt_id="prompt_456",
            version=1,
            linting_results={"issues_found": 2, "overall_score": 0.7},
            bias_detection_results=[
                {"bias_type": "gender", "severity_score": 0.3}
            ],
            testing_results=[
                {"test_name": "Test 1", "passed": True},
                {"test_name": "Test 2", "passed": False}
            ],
            overall_score=0.65,
            issues_count=3,
            recommendations=["Improve clarity", "Reduce bias"]
        )

        # Test serialization
        data = report.to_dict()

        assert data["id"] == "report_123"
        assert data["prompt_id"] == "prompt_456"
        assert data["version"] == 1
        assert data["overall_score"] == 0.65
        assert data["issues_count"] == 3
        assert len(data["recommendations"]) == 2
