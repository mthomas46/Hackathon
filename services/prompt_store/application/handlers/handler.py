"""Base handler pattern for Prompt Store service.

Following domain-driven design principles with generic handler implementation.
"""

from abc import ABC
from typing import Any, Callable, Dict

from services.shared.presentation.responses import (
    create_error_response,
    create_success_response,
)
from services.shared.infrastructure.utilities.validation_utils import validate_required_fields
from services.shared.infrastructure.utilities.logging_utils import (
    log_operation_start,
    log_operation_success,
    log_operation_error,
)
from services.shared.utilities.error_handling import ServiceException


class BaseHandler(ABC):
    """Base handler with common HTTP response patterns."""

    def __init__(self, service):
        self.service = service

    async def _handle_request(
        self, operation: Callable, *args, **kwargs
    ) -> Dict[str, Any]:
        """Handle request with standardized error handling and logging.

        Error handling standardization: Uses consistent exception handling patterns
        and standardized logging across all services.
        """
        operation_name = f"{operation.__name__}"
        log_operation_start(operation_name, {"args_count": len(args), "kwargs_keys": list(kwargs.keys())})

        try:
            result = operation(*args, **kwargs)

            # Handle async operations
            if hasattr(result, "__await__"):
                result = await result

            log_operation_success(operation_name, {"result_type": type(result).__name__})
            return create_success_response(
                message="Operation completed successfully", data=result
            )

        except ServiceException as e:
            log_operation_error(operation_name, e, {"error_code": e.error_code})
            return create_error_response(str(e), e.error_code)
        except ValueError as e:
            log_operation_error(operation_name, e, {"error_type": "validation"})
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            log_operation_error(operation_name, e, {"error_type": "internal"})
            return create_error_response(f"Internal error: {str(e)}", "INTERNAL_ERROR")

    async def handle_create(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle entity creation."""
        return await self._handle_request(self.service.create_entity, request_data)

    async def handle_get(self, entity_id: str) -> Dict[str, Any]:
        """Handle entity retrieval."""
        entity = await self._handle_request(self.service.get_entity, entity_id)
        if isinstance(entity, dict) and entity.get("success"):
            return entity
        return create_error_response("Entity not found", "NOT_FOUND")

    async def handle_update(
        self, entity_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle entity update."""
        return await self._handle_request(
            self.service.update_entity, entity_id, updates
        )

    async def handle_delete(self, entity_id: str) -> Dict[str, Any]:
        """Handle entity deletion."""
        return await self._handle_request(self.service.delete_entity, entity_id)

    async def handle_list(
        self, limit: int = 50, offset: int = 0, **filters
    ) -> Dict[str, Any]:
        """Handle entity listing."""
        return await self._handle_request(
            self.service.list_entities, limit, offset, **filters
        )

    def _validate_request_data(
        self, data: Dict[str, Any], required_fields: list
    ) -> None:
        """Validate request data has required fields.

        DRY refactoring: Uses shared validation utility instead of duplicating
        validation logic. Reduces code duplication across services.
        """
        validate_required_fields(data, required_fields)

    def _sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data."""
        # Remove any None values and empty strings
        return {k: v for k, v in data.items() if v is not None and v != ""}
