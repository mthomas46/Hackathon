"""A/B testing handlers for API endpoints.

Handles HTTP requests and responses for A/B testing operations.
"""

from typing import Dict, Any, Optional
from services.prompt_store.core.handler import BaseHandler
from services.prompt_store.domain.ab_testing.service import ABTestService
from services.prompt_store.core.models import ABTestCreate
from services.shared.responses import create_success_response, create_error_response


class ABTestHandlers(BaseHandler):
    """Handlers for A/B testing operations."""

    def __init__(self):
        super().__init__(ABTestService())

    async def handle_create_ab_test(self, test_data: ABTestCreate) -> Dict[str, Any]:
        """Create a new A/B test."""
        try:
            ab_test_dict = self.service.create_ab_test(test_data.model_dump())
            return create_success_response(
                message="A/B test created successfully",
                data=ab_test_dict
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to create A/B test: {str(e)}", "INTERNAL_ERROR")

    async def handle_select_prompt_for_test(self, test_id: str, user_id: Optional[str] = None,
                                          session_id: Optional[str] = None) -> Dict[str, Any]:
        """Select a prompt variant for A/B testing."""
        try:
            result = self.service.select_prompt_for_test(test_id, user_id, session_id)
            if not result:
                return create_error_response("A/B test not found or inactive", "NOT_FOUND")

            return create_success_response(
                message="Prompt selected for A/B testing",
                data=result
            )
        except Exception as e:
            return create_error_response(f"Failed to select prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_ab_test(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test details."""
        try:
            ab_test = self.service.get_ab_test(test_id)
            if not ab_test:
                return create_error_response("A/B test not found", "NOT_FOUND")

            # Handle both dict and ABTest object returns
            if isinstance(ab_test, dict):
                data = ab_test
            else:
                data = ab_test.to_dict()

            return create_success_response(
                message="A/B test retrieved successfully",
                data=data
            )
        except Exception as e:
            return create_error_response(f"Failed to get A/B test: {str(e)}", "INTERNAL_ERROR")

    async def handle_list_ab_tests(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """List A/B tests."""
        try:
            result = self.service.list_entities(limit=limit, offset=offset, **filters)
            return create_success_response(
                message="A/B tests retrieved successfully",
                data=result
            )
        except Exception as e:
            return create_error_response(f"Failed to list A/B tests: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results."""
        try:
            results = self.service.get_ab_test_results(test_id)
            return create_success_response(
                message="A/B test results retrieved successfully",
                data={"results": results}
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get test results: {str(e)}", "INTERNAL_ERROR")

    async def handle_record_test_result(self, test_id: str, prompt_id: str, metric_value: float,
                                      sample_size: int = 1) -> Dict[str, Any]:
        """Record a result for an A/B test."""
        try:
            result = self.service.record_test_result(test_id, prompt_id, metric_value, sample_size)
            return create_success_response(
                message="Test result recorded successfully",
                data=result.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to record test result: {str(e)}", "INTERNAL_ERROR")

    async def handle_select_variant(self, test_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle variant selection for A/B testing."""
        try:
            result = self.service.select_prompt_variant(test_id, user_id)
            return create_success_response(
                message="Variant selected successfully",
                data={"selected_prompt_id": result}
            )
        except Exception as e:
            return create_error_response(f"Failed to select variant: {str(e)}", "INTERNAL_ERROR")

    async def handle_end_test(self, test_id: str, winner: Optional[str] = None) -> Dict[str, Any]:
        """End an A/B test."""
        try:
            updated_test = self.service.end_test(test_id, winner)
            return create_success_response(
                message="A/B test ended successfully",
                data=updated_test.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to end test: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_active_tests(self) -> Dict[str, Any]:
        """Get all active A/B tests."""
        try:
            tests = self.service.get_active_tests()
            result = {
                "items": [test.to_dict() for test in tests],
                "total": len(tests),
                "has_more": False,
                "limit": len(tests),
                "offset": 0
            }
            return create_success_response(
                message="Active A/B tests retrieved successfully",
                data=result
            )
        except Exception as e:
            return create_error_response(f"Failed to get active tests: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_tests_for_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Get A/B tests for a specific prompt."""
        try:
            tests = self.service.get_tests_for_prompt(prompt_id)
            result = {
                "items": [test.to_dict() for test in tests],
                "total": len(tests),
                "has_more": False,
                "limit": len(tests),
                "offset": 0
            }
            return create_success_response(
                message=f"A/B tests for prompt {prompt_id} retrieved successfully",
                data=result
            )
        except Exception as e:
            return create_error_response(f"Failed to get tests for prompt: {str(e)}", "INTERNAL_ERROR")
