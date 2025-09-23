"""
A/B testing handlers for API endpoints.

Handles HTTP requests and responses for A/B testing operations.
"""

import time
from typing import Any, Dict, Optional

from services.prompt_store.core.handler import BaseHandler
from services.prompt_store.core.models import ABTestCreate
from services.prompt_store.domain.ab_testing.service import ABTestService
from services.shared.core.constants_new import ServiceNames
from services.shared.core.responses.responses import create_error_response, create_success_response
from services.shared.utilities.logging_client import get_log_collector_client

# Global logger client instance
logger_client = None


async def get_logger_client():
    """Get or initialize the logger client."""
    global logger_client
    if logger_client is None:
        try:
            logger_client = await get_log_collector_client(ServiceNames.PROMPT_STORE)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


class ABTestHandlers(BaseHandler):
    """Handlers for A/B testing operations."""

    def __init__(self):
        super().__init__(ABTestService())

    async def handle_create_ab_test(self, test_data: ABTestCreate) -> Dict[str, Any]:
        """Create a new A/B test."""
        start_time = time.time()
        request_id = f"ab_test_create_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Log A/B test creation start
            if logger:
                await logger.log_business_event(
                    "ab_test_creation_started",
                    {
                        "request_id": request_id,
                        "operation": "ab_testing_workflow",
                        "test_name": test_data.name,
                        "prompt_variants_count": len(test_data.prompt_variants) if test_data.prompt_variants else 0,
                        "target_metric": test_data.target_metric,
                        "traffic_distribution": test_data.traffic_distribution,
                        "duration_days": test_data.duration_days,
                        "test_configuration": True,
                    },
                )

                await logger.log_info(
                    "Initiating A/B test creation",
                    {
                        "request_id": request_id,
                        "test_name": test_data.name,
                        "variant_count": len(test_data.prompt_variants) if test_data.prompt_variants else 0,
                        "target_metric": test_data.target_metric,
                        "traffic_allocation": test_data.traffic_distribution,
                        "experiment_duration": test_data.duration_days,
                    },
                )

            ab_test_dict = self.service.create_ab_test(test_data.model_dump())

            response_time = time.time() - start_time
            test_id = ab_test_dict.get("test_id")

            # Log successful A/B test creation
            if logger:
                await logger.log_business_event(
                    "ab_test_created",
                    {
                        "request_id": request_id,
                        "test_id": test_id,
                        "operation": "ab_testing_workflow",
                        "response_time_seconds": response_time,
                        "success": True,
                        "test_name": test_data.name,
                        "variants_configured": len(test_data.prompt_variants) if test_data.prompt_variants else 0,
                        "experiment_ready": True,
                        "traffic_distribution_active": True,
                    },
                )

                await logger.log_performance_metric(
                    "ab_test_creation",
                    response_time,
                    {
                        "request_id": request_id,
                        "test_id": test_id,
                        "test_name": test_data.name,
                        "creation_success": True,
                        "configuration_processing_time": response_time,
                    },
                )

            return create_success_response(message="A/B test created successfully", data=ab_test_dict)

        except ValueError as e:
            error_time = time.time() - start_time

            # Log A/B test creation validation failure
            if logger:
                await logger.log_business_event(
                    "ab_test_creation_validation_failed",
                    {
                        "request_id": request_id,
                        "operation": "ab_testing_workflow",
                        "test_name": test_data.name,
                        "response_time_seconds": error_time,
                        "error_type": "validation_error",
                        "error_message": str(e),
                        "configuration_validation_failed": True,
                    },
                )

            return create_error_response(str(e), "VALIDATION_ERROR")

        except Exception as e:
            error_time = time.time() - start_time

            # Log A/B test creation failure
            if logger:
                await logger.log_error(
                    f"A/B test creation failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "operation": "ab_testing_workflow",
                        "test_name": test_data.name,
                        "variant_count": len(test_data.prompt_variants) if test_data.prompt_variants else 0,
                        "error_type": type(e).__name__,
                        "response_time_seconds": error_time,
                        "ab_test_creation_failed": True,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "ab_test_creation_failed",
                    {
                        "request_id": request_id,
                        "operation": "ab_testing_workflow",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "test_name": test_data.name,
                        "response_time_seconds": error_time,
                    },
                )

            return create_error_response(f"Failed to create A/B test: {str(e)}", "INTERNAL_ERROR")

    async def handle_select_prompt_for_test(
        self, test_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Select a prompt variant for A/B testing."""
        start_time = time.time()
        request_id = f"ab_test_select_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Log prompt selection start
            if logger:
                await logger.log_business_event(
                    "ab_test_prompt_selection_started",
                    {
                        "request_id": request_id,
                        "test_id": test_id,
                        "operation": "ab_testing_experimentation",
                        "user_id": user_id,
                        "session_id": session_id,
                        "user_targeted": bool(user_id),
                        "session_tracked": bool(session_id),
                        "variant_selection": True,
                    },
                )

                await logger.log_info(
                    "Selecting prompt variant for A/B testing",
                    {
                        "request_id": request_id,
                        "test_id": test_id,
                        "user_context": bool(user_id),
                        "session_context": bool(session_id),
                        "randomization_engine": True,
                        "traffic_distribution": True,
                    },
                )

            result = self.service.select_prompt_for_test(test_id, user_id, session_id)

            if not result:
                response_time = time.time() - start_time

                # Log A/B test not found
                if logger:
                    await logger.log_business_event(
                        "ab_test_not_found",
                        {
                            "request_id": request_id,
                            "test_id": test_id,
                            "operation": "ab_testing_experimentation",
                            "response_time_seconds": response_time,
                            "result_status": "test_inactive_or_missing",
                            "variant_selection_failed": True,
                        },
                    )

                return create_error_response("A/B test not found or inactive", "NOT_FOUND")

            response_time = time.time() - start_time
            selected_variant = result.get("variant_id") or result.get("selected_variant")

            # Log successful prompt selection
            if logger:
                await logger.log_business_event(
                    "ab_test_prompt_selected",
                    {
                        "request_id": request_id,
                        "test_id": test_id,
                        "variant_id": selected_variant,
                        "operation": "ab_testing_experimentation",
                        "response_time_seconds": response_time,
                        "success": True,
                        "user_id": user_id,
                        "session_id": session_id,
                        "experiment_participation": True,
                        "variant_assignment": True,
                    },
                )

                await logger.log_performance_metric(
                    "ab_test_prompt_selection",
                    response_time,
                    {
                        "request_id": request_id,
                        "test_id": test_id,
                        "variant_selected": selected_variant,
                        "selection_success": True,
                        "randomization_time": response_time,
                    },
                )

            return create_success_response(message="Prompt selected for A/B testing", data=result)

        except Exception as e:
            error_time = time.time() - start_time

            # Log prompt selection failure
            if logger:
                await logger.log_error(
                    f"A/B test prompt selection failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "operation": "ab_testing_experimentation",
                        "test_id": test_id,
                        "user_id": user_id,
                        "session_id": session_id,
                        "error_type": type(e).__name__,
                        "response_time_seconds": error_time,
                        "ab_test_selection_failed": True,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "ab_test_prompt_selection_failed",
                    {
                        "request_id": request_id,
                        "operation": "ab_testing_experimentation",
                        "test_id": test_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "user_id": user_id,
                        "session_id": session_id,
                        "response_time_seconds": error_time,
                    },
                )

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

            return create_success_response(message="A/B test retrieved successfully", data=data)
        except Exception as e:
            return create_error_response(f"Failed to get A/B test: {str(e)}", "INTERNAL_ERROR")

    async def handle_list_ab_tests(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """List A/B tests."""
        try:
            result = self.service.list_entities(limit=limit, offset=offset, **filters)
            return create_success_response(message="A/B tests retrieved successfully", data=result)
        except Exception as e:
            return create_error_response(f"Failed to list A/B tests: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results."""
        try:
            results = self.service.get_ab_test_results(test_id)
            return create_success_response(message="A/B test results retrieved successfully", data={"results": results})
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get test results: {str(e)}", "INTERNAL_ERROR")

    async def handle_record_test_result(
        self, test_id: str, prompt_id: str, metric_value: float, sample_size: int = 1
    ) -> Dict[str, Any]:
        """Record a result for an A/B test."""
        try:
            result = self.service.record_test_result(test_id, prompt_id, metric_value, sample_size)
            return create_success_response(message="Test result recorded successfully", data=result.to_dict())
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to record test result: {str(e)}", "INTERNAL_ERROR")

    async def handle_select_variant(self, test_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle variant selection for A/B testing."""
        try:
            result = self.service.select_prompt_variant(test_id, user_id)
            return create_success_response(message="Variant selected successfully", data={"selected_prompt_id": result})
        except Exception as e:
            return create_error_response(f"Failed to select variant: {str(e)}", "INTERNAL_ERROR")

    async def handle_end_test(self, test_id: str, winner: Optional[str] = None) -> Dict[str, Any]:
        """End an A/B test."""
        try:
            updated_test = self.service.end_test(test_id, winner)
            return create_success_response(message="A/B test ended successfully", data=updated_test.to_dict())
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
                "offset": 0,
            }
            return create_success_response(message="Active A/B tests retrieved successfully", data=result)
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
                "offset": 0,
            }
            return create_success_response(
                message=f"A/B tests for prompt {prompt_id} retrieved successfully", data=result
            )
        except Exception as e:
            return create_error_response(f"Failed to get tests for prompt: {str(e)}", "INTERNAL_ERROR")
