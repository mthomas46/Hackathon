"""Bulk operations handlers for API endpoints.

Handles HTTP requests and responses for bulk operations.
"""

from typing import Dict, Any, Optional, List
from services.prompt_store.domain.bulk.service import BulkOperationService
from services.prompt_store.core.models import BulkOperationCreate
from services.shared.responses import create_success_response, create_error_response


class BulkOperationHandlers:
    """Handlers for bulk operations."""

    def __init__(self):
        self.service = BulkOperationService()

    async def handle_create_bulk_operation(self, operation_data: BulkOperationCreate) -> Dict[str, Any]:
        """Create a new bulk operation."""
        try:
            operation = self.service.create_entity(operation_data.dict())
            return create_success_response(
                message="Bulk operation created successfully",
                data=operation.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to create bulk operation: {str(e)}", "INTERNAL_ERROR")

    async def handle_bulk_create_prompts(self, prompts: List[Dict[str, Any]],
                                        created_by: str = "api_user") -> Dict[str, Any]:
        """Create bulk create prompts operation."""
        try:
            operation = self.service.create_bulk_create_operation(prompts, created_by)
            return create_success_response(
                message="Bulk create operation initiated",
                data=operation.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to create bulk operation: {str(e)}", "INTERNAL_ERROR")

    async def handle_bulk_update_prompts(self, updates: List[Dict[str, Any]],
                                        created_by: str = "api_user") -> Dict[str, Any]:
        """Create bulk update prompts operation."""
        try:
            operation = self.service.create_bulk_update_operation(updates, created_by)
            return create_success_response(
                message="Bulk update operation initiated",
                data=operation.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to create bulk operation: {str(e)}", "INTERNAL_ERROR")

    async def handle_bulk_delete_prompts(self, prompt_ids: List[str],
                                        created_by: str = "api_user") -> Dict[str, Any]:
        """Create bulk delete prompts operation."""
        try:
            operation = self.service.create_bulk_delete_operation(prompt_ids, created_by)
            return create_success_response(
                message="Bulk delete operation initiated",
                data=operation.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to create bulk operation: {str(e)}", "INTERNAL_ERROR")

    async def handle_bulk_update_tags(self, prompt_ids: List[str],
                                     tags_to_add: Optional[List[str]] = None,
                                     tags_to_remove: Optional[List[str]] = None,
                                     created_by: str = "api_user") -> Dict[str, Any]:
        """Create bulk tag update operation."""
        try:
            operation = self.service.create_bulk_tag_operation(
                prompt_ids, tags_to_add, tags_to_remove, created_by
            )
            return create_success_response(
                message="Bulk tag update operation initiated",
                data=operation.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to create bulk operation: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_bulk_operation(self, operation_id: str) -> Dict[str, Any]:
        """Get bulk operation details."""
        try:
            operation = self.service.get_entity(operation_id)
            if not operation:
                return create_error_response("Bulk operation not found", "NOT_FOUND")

            return create_success_response(
                message="Bulk operation retrieved successfully",
                data=operation.to_dict()
            )
        except Exception as e:
            return create_error_response(f"Failed to get bulk operation: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get detailed status of a bulk operation."""
        try:
            status = self.service.get_operation_status(operation_id)
            return create_success_response(
                message="Operation status retrieved successfully",
                data=status
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get operation status: {str(e)}", "INTERNAL_ERROR")

    async def handle_list_bulk_operations(self, status: Optional[str] = None,
                                         operation_type: Optional[str] = None,
                                         limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List bulk operations with filtering."""
        try:
            filters = {}
            if status:
                filters["status"] = status
            if operation_type:
                filters["operation_type"] = operation_type

            result = self.service.list_entities(limit=limit, offset=offset, **filters)
            return create_success_response(
                message="Bulk operations retrieved successfully",
                data=result
            )
        except Exception as e:
            return create_error_response(f"Failed to list bulk operations: {str(e)}", "INTERNAL_ERROR")

    async def handle_cancel_operation(self, operation_id: str) -> Dict[str, Any]:
        """Cancel a bulk operation."""
        try:
            operation = self.service.cancel_operation(operation_id)
            return create_success_response(
                message="Bulk operation cancelled successfully",
                data=operation.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to cancel operation: {str(e)}", "INTERNAL_ERROR")

    async def handle_retry_operation(self, operation_id: str) -> Dict[str, Any]:
        """Retry a failed bulk operation."""
        try:
            operation = self.service.retry_operation(operation_id)
            return create_success_response(
                message="Bulk operation retry initiated",
                data=operation.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to retry operation: {str(e)}", "INTERNAL_ERROR")

    async def handle_cleanup_operations(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old bulk operations."""
        try:
            cleaned_count = self.service.cleanup_old_operations(days_old)
            return create_success_response(
                message=f"Cleaned up {cleaned_count} old bulk operations",
                data={"cleaned_count": cleaned_count}
            )
        except Exception as e:
            return create_error_response(f"Failed to cleanup operations: {str(e)}", "INTERNAL_ERROR")
