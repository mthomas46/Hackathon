"""Base handler for API endpoint operations.

Provides common HTTP response patterns and error handling.
"""
import asyncio
from abc import ABC
from typing import Dict, Any, Optional
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ServiceException


class BaseHandler(ABC):
    """Base handler with common HTTP response patterns."""

    def __init__(self, service):
        self.service = service

    async def _handle_request(self, operation: callable, *args, **kwargs) -> Dict[str, Any]:
        """Handle request with common error handling."""
        try:
            result = operation(*args, **kwargs)

            # Handle async operations
            if asyncio.iscoroutine(result):
                result = await result

            return create_success_response(
                f"Operation completed successfully",
                result
            )

        except ServiceException as e:
            return create_error_response(str(e), e.error_code)
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
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

    async def handle_update(self, entity_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Handle entity update."""
        return await self._handle_request(self.service.update_entity, entity_id, updates)

    async def handle_delete(self, entity_id: str) -> Dict[str, Any]:
        """Handle entity deletion."""
        return await self._handle_request(self.service.delete_entity, entity_id)

    async def handle_list(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """Handle entity listing."""
        return await self._handle_request(self.service.list_entities, limit, offset)

    def _validate_request_data(self, data: Dict[str, Any], required_fields: list) -> None:
        """Validate request data has required fields."""
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    def _sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data."""
        # Remove any None values and empty strings
        return {k: v for k, v in data.items() if v is not None and v != ""}
