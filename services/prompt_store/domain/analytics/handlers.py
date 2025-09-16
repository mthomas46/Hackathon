"""Analytics handlers for API endpoints.

Handles HTTP requests and responses for analytics operations.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from services.prompt_store.domain.analytics.service import AnalyticsService
from services.shared.responses import create_success_response, create_error_response


class AnalyticsHandlers:
    """Handlers for analytics operations."""

    def __init__(self):
        self.service = AnalyticsService()

    async def handle_get_analytics_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics summary."""
        try:
            if days_back < 1 or days_back > 365:
                return create_error_response("days_back must be between 1 and 365", "VALIDATION_ERROR")

            analytics = self.service.get_system_analytics(days_back)
            return create_success_response(
                message="Analytics summary retrieved successfully",
                data=analytics
            )
        except Exception as e:
            return create_error_response(f"Failed to get analytics summary: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_prompt_analytics(self, prompt_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get analytics for a specific prompt."""
        try:
            if days_back < 1 or days_back > 365:
                return create_error_response("days_back must be between 1 and 365", "VALIDATION_ERROR")

            analytics = self.service.get_prompt_analytics(prompt_id, days_back)
            return create_success_response(
                message=f"Analytics for prompt {prompt_id} retrieved successfully",
                data=analytics
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get prompt analytics: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_usage_analytics(self, start_date: Optional[str] = None,
                                       end_date: Optional[str] = None,
                                       prompt_id: Optional[str] = None,
                                       user_id: Optional[str] = None,
                                       service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get filtered usage analytics."""
        try:
            # Parse dates if provided
            start_dt = None
            end_dt = None

            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except ValueError:
                    return create_error_response("Invalid start_date format", "VALIDATION_ERROR")

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except ValueError:
                    return create_error_response("Invalid end_date format", "VALIDATION_ERROR")

            analytics = self.service.get_usage_analytics(
                start_date=start_dt,
                end_date=end_dt,
                prompt_id=prompt_id,
                user_id=user_id,
                service_name=service_name
            )

            return create_success_response(
                message="Usage analytics retrieved successfully",
                data=analytics
            )
        except Exception as e:
            return create_error_response(f"Failed to get usage analytics: {str(e)}", "INTERNAL_ERROR")

    async def handle_record_usage(self, prompt_id: str, operation: str = "generate",
                                input_tokens: Optional[int] = None,
                                output_tokens: Optional[int] = None,
                                response_time_ms: Optional[float] = None,
                                success: bool = True,
                                error_message: Optional[str] = None,
                                service_name: str = "api",
                                user_id: Optional[str] = None,
                                session_id: Optional[str] = None) -> Dict[str, Any]:
        """Record prompt usage for analytics."""
        try:
            self.service.record_usage(
                prompt_id=prompt_id,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                service_name=service_name,
                user_id=user_id,
                session_id=session_id
            )

            return create_success_response(
                message="Usage recorded successfully"
            )
        except Exception as e:
            return create_error_response(f"Failed to record usage: {str(e)}", "INTERNAL_ERROR")
