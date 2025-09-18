"""Optimization handlers for A/B testing and automated prompt improvement."""

from typing import Dict, Any, Optional
from ...core.handler import BaseHandler
from .service import OptimizationService
from services.shared.core.responses.responses import create_success_response, create_error_response


class OptimizationHandlers(BaseHandler):
    """Handlers for optimization operations."""

    def __init__(self):
        super().__init__(OptimizationService())

    async def handle_create_ab_test(self, prompt_a_id: str, prompt_b_id: str,
                                  traffic_percentage: float = 50.0) -> Dict[str, Any]:
        """Create a new A/B test."""
        try:
            test = await self.service.create_ab_test(prompt_a_id, prompt_b_id, traffic_percentage)
            return create_success_response(
                message="A/B test created successfully",
                data=test.get_results()
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to create A/B test: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_prompt_assignment(self, test_id: str, user_id: str) -> Dict[str, Any]:
        """Get prompt assignment for a user in an A/B test."""
        try:
            prompt_id = await self.service.get_prompt_for_user(test_id, user_id)
            if prompt_id:
                return create_success_response(
                    message="Prompt assignment retrieved successfully",
                    data={"test_id": test_id, "user_id": user_id, "assigned_prompt": prompt_id}
                ).model_dump()
            else:
                return create_error_response("Test not found or not running", "NOT_FOUND").model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get prompt assignment: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_record_test_result(self, test_id: str, prompt_id: str,
                                      success: bool, score: float = 0.0) -> Dict[str, Any]:
        """Record the result of using a prompt in an A/B test."""
        try:
            await self.service.record_test_result(test_id, prompt_id, success, score)
            return create_success_response(
                message="Test result recorded successfully"
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to record test result: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get results for an A/B test."""
        try:
            results = await self.service.get_test_results(test_id)
            if results:
                return create_success_response(
                    message="Test results retrieved successfully",
                    data=results
                ).model_dump()
            else:
                return create_error_response("Test not found", "NOT_FOUND").model_dump()
        except Exception as e:
            return create_error_response(f"Failed to get test results: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_end_test(self, test_id: str) -> Dict[str, Any]:
        """End an A/B test."""
        try:
            winner = await self.service.end_test(test_id)
            return create_success_response(
                message="A/B test ended successfully",
                data={"test_id": test_id, "winner": winner}
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to end test: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_run_optimization(self, prompt_id: str, base_version: int) -> Dict[str, Any]:
        """Run automated optimization cycle."""
        try:
            cycle = await self.service.run_automated_optimization(prompt_id, base_version)
            return create_success_response(
                message="Optimization cycle started successfully",
                data=cycle
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to start optimization: {str(e)}", "INTERNAL_ERROR").model_dump()

    async def handle_generate_variations(self, prompt_content: str, count: int = 3) -> Dict[str, Any]:
        """Generate prompt variations."""
        try:
            variations = await self.service.generate_prompt_variations(prompt_content, count)
            return create_success_response(
                message="Prompt variations generated successfully",
                data={"original_prompt": prompt_content, "variations": variations}
            ).model_dump()
        except Exception as e:
            return create_error_response(f"Failed to generate variations: {str(e)}", "INTERNAL_ERROR").model_dump()
