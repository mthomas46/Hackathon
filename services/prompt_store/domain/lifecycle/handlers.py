"""Lifecycle management API handlers.

Handles HTTP requests and responses for prompt lifecycle operations.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException

from services.prompt_store.core.handler import BaseHandler
from services.prompt_store.domain.lifecycle.service import LifecycleService
from services.prompt_store.core.models import (
    PromptLifecycleUpdate, LifecycleStatusResponse, LifecycleHistoryResponse,
    LifecycleCountsResponse, LifecycleTransitionValidation, BulkLifecycleUpdate
)
from services.shared.responses import create_success_response, create_error_response


class LifecycleHandlers(BaseHandler):
    """Handlers for prompt lifecycle management endpoints."""

    def __init__(self):
        self.lifecycle_service = LifecycleService()
        super().__init__(self.lifecycle_service)

    async def handle_update_lifecycle_status(self, prompt_id: str, update_data: PromptLifecycleUpdate,
                                           user_id: str = "api_user") -> Dict[str, Any]:
        """Handle lifecycle status update request."""

        try:
            result = await self.lifecycle_service.update_lifecycle_status(
                prompt_id=prompt_id,
                new_status=update_data.status,
                reason=update_data.reason or "",
                user_id=user_id
            )

            response = create_success_response(
                data=result,
                message=f"Prompt lifecycle status updated to {update_data.status}"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update lifecycle status: {str(e)}")

    async def handle_get_prompts_by_status(self, status: str, limit: int = 50,
                                         offset: int = 0) -> Dict[str, Any]:
        """Handle request to get prompts by lifecycle status."""

        try:
            result = await self.lifecycle_service.get_prompts_by_status(
                status=status, limit=limit, offset=offset
            )

            response = create_success_response(
                data=result,
                message=f"Retrieved prompts with status '{status}'"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve prompts: {str(e)}")

    def handle_get_lifecycle_history(self, prompt_id: str) -> Dict[str, Any]:
        """Handle request to get lifecycle history for a prompt."""

        try:
            result = self.lifecycle_service.get_lifecycle_history(prompt_id)

            response = create_success_response(
                data=result,
                message=f"Retrieved lifecycle history for prompt {prompt_id}"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve lifecycle history: {str(e)}")

    def handle_get_status_counts(self) -> Dict[str, Any]:
        """Handle request to get lifecycle status counts."""

        try:
            result = self.lifecycle_service.get_status_counts()

            response = create_success_response(
                data=result,
                message="Retrieved lifecycle status counts"
            )
            return response.model_dump()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve status counts: {str(e)}")

    def handle_get_transition_rules(self) -> Dict[str, Any]:
        """Handle request to get lifecycle transition rules."""

        try:
            result = self.lifecycle_service.get_transition_rules()

            response = create_success_response(
                data=result,
                message="Retrieved lifecycle transition rules"
            )
            return response.model_dump()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve transition rules: {str(e)}")

    def handle_validate_transition(self, prompt_id: str, new_status: str) -> Dict[str, Any]:
        """Handle request to validate a lifecycle transition."""

        try:
            result = self.lifecycle_service.validate_transition(prompt_id, new_status)

            response = create_success_response(
                data=result,
                message=f"Validated transition for prompt {prompt_id}"
            )
            return response.model_dump()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to validate transition: {str(e)}")

    async def handle_bulk_lifecycle_update(self, update_data: BulkLifecycleUpdate,
                                         user_id: str = "api_user") -> Dict[str, Any]:
        """Handle bulk lifecycle status update request."""

        try:
            result = await self.lifecycle_service.bulk_lifecycle_update(
                prompt_ids=update_data.prompt_ids,
                new_status=update_data.status,
                reason=update_data.reason or "",
                user_id=user_id
            )

            response = create_success_response(
                data=result,
                message=f"Bulk lifecycle update completed: {result['successful']} successful, {result['failed']} failed"
            )
            return response.model_dump()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to perform bulk update: {str(e)}")
