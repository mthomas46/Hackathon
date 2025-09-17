"""Validation handlers for prompt testing and bias detection."""

from typing import Dict, Any, List
from ...core.handler import BaseHandler
from .service import ValidationService
from services.shared.core.responses.responses import create_success_response, create_error_response


class ValidationHandlers(BaseHandler):
    """Handlers for validation operations."""

    def __init__(self):
        super().__init__(ValidationService())

    async def handle_run_test_suite(self, prompt_id: str, version: int, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """Run a test suite against a prompt."""
        try:
            results = await self.service.run_test_suite(prompt_id, version, test_suite)
            return create_success_response(
                message="Test suite completed successfully",
                data=results
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to run test suite: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_lint_prompt(self, prompt_content: str) -> Dict[str, Any]:
        """Lint a prompt for issues."""
        try:
            linting_results = self.service.lint_prompt(prompt_content)
            return create_success_response(
                message="Prompt linting completed successfully",
                data=linting_results
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to lint prompt: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_detect_bias(self, prompt_content: str, prompt_id: str = None, version: int = None) -> Dict[str, Any]:
        """Detect bias in prompt content."""
        try:
            bias_results = await self.service.detect_bias(prompt_content, prompt_id, version)
            return create_success_response(
                message="Bias detection completed successfully",
                data={
                    "bias_issues_found": len(bias_results),
                    "bias_results": [result.to_dict() for result in bias_results]
                }
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to detect bias: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_validate_output(self, prompt_output: str, expected_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate prompt output against criteria."""
        try:
            validation_results = await self.service.validate_output(prompt_output, expected_criteria)
            return create_success_response(
                message="Output validation completed successfully",
                data=validation_results
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to validate output: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_create_test_suite(self, name: str, description: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new test suite."""
        try:
            test_suite = self.service.create_test_suite(name, description, test_cases)
            return create_success_response(
                message="Test suite created successfully",
                data=test_suite
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to create test suite: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_standard_test_suites(self) -> Dict[str, Any]:
        """Get standard test suites."""
        try:
            test_suites = self.service.get_standard_test_suites()
            return create_success_response(
                message="Standard test suites retrieved successfully",
                data={"test_suites": test_suites, "count": len(test_suites)}
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get test suites: {str(e)}", "INTERNAL_ERROR").model_dump()
