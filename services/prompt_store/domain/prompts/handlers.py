"""Prompt handlers for API endpoints.

Handles HTTP requests and responses for prompt operations.
"""

import time
from typing import Any, Dict, List, Optional

from services.prompt_store.core.handler import BaseHandler
from services.prompt_store.core.models import PromptCreate, PromptUpdate
from services.prompt_store.domain.prompts.service import PromptService
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


class PromptHandlers(BaseHandler):
    """Handlers for prompt CRUD operations."""

    def __init__(self):
        super().__init__(PromptService())

    async def handle_create_prompt(self, prompt_data: PromptCreate) -> Dict[str, Any]:
        """Create a new prompt."""
        start_time = time.time()
        request_id = f"prompt_create_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Log prompt creation start
            if logger:
                await logger.log_business_event(
                    "prompt_creation_started",
                    {
                        "request_id": request_id,
                        "prompt_name": prompt_data.name,
                        "category": prompt_data.category,
                        "content_length": len(prompt_data.content) if prompt_data.content else 0,
                        "has_variables": bool(prompt_data.variables),
                        "has_tags": bool(prompt_data.tags),
                        "has_metadata": bool(prompt_data.metadata),
                    },
                )

                await logger.log_info(
                    "Creating new prompt",
                    {
                        "request_id": request_id,
                        "prompt_name": prompt_data.name,
                        "category": prompt_data.category,
                        "content_preview": (
                            prompt_data.content[:100] + "..."
                            if prompt_data.content and len(prompt_data.content) > 100
                            else prompt_data.content
                        ),
                    },
                )

            # Create the prompt
            prompt = self.service.create_entity(prompt_data.model_dump())
            response_time = time.time() - start_time

            # Log successful creation
            if logger:
                await logger.log_business_event(
                    "prompt_created",
                    {
                        "request_id": request_id,
                        "prompt_id": prompt.id,
                        "prompt_name": prompt.name,
                        "category": prompt.category,
                        "version": prompt.version,
                        "response_time_seconds": response_time,
                        "success": True,
                    },
                )

                await logger.log_performance_metric(
                    "prompt_creation",
                    response_time,
                    {
                        "request_id": request_id,
                        "prompt_id": prompt.id,
                        "category": prompt.category,
                        "creation_success": True,
                    },
                )

            response = create_success_response(message="Prompt created successfully", data=prompt.to_dict())
            return response.model_dump()

        except ValueError as e:
            error_time = time.time() - start_time

            # Log validation error
            if logger:
                await logger.log_error(
                    f"Prompt creation validation failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "prompt_name": prompt_data.name if prompt_data else None,
                        "category": prompt_data.category if prompt_data else None,
                        "error_type": "validation_error",
                        "response_time_seconds": error_time,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "prompt_creation_validation_failed",
                    {
                        "request_id": request_id,
                        "prompt_name": prompt_data.name if prompt_data else None,
                        "category": prompt_data.category if prompt_data else None,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

            error_response = create_error_response(str(e), "VALIDATION_ERROR")
            return error_response.model_dump()

        except Exception as e:
            error_time = time.time() - start_time

            # Log internal error
            if logger:
                await logger.log_error(
                    f"Prompt creation failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "prompt_name": prompt_data.name if prompt_data else None,
                        "category": prompt_data.category if prompt_data else None,
                        "error_type": type(e).__name__,
                        "response_time_seconds": error_time,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "prompt_creation_failed",
                    {
                        "request_id": request_id,
                        "prompt_name": prompt_data.name if prompt_data else None,
                        "category": prompt_data.category if prompt_data else None,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

            error_response = create_error_response(f"Failed to create prompt: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    async def handle_get_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Get a single prompt by ID."""
        try:
            prompt = self.service.get_entity(prompt_id)
            if not prompt:
                error_response = create_error_response(f"Prompt '{prompt_id}' not found", "NOT_FOUND")
                return error_response.model_dump()

            response = create_success_response(message="Prompt retrieved successfully", data=prompt.to_dict())
            return response.model_dump()
        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
            return error_response.model_dump()
        except Exception as e:
            error_response = create_error_response(f"Failed to retrieve prompt: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    async def handle_get_prompt_by_name(self, category: str, name: str, **variables) -> Dict[str, Any]:
        """Get prompt by category/name and fill variables."""
        try:
            prompt = self.service.get_prompt_by_name(category, name)
            if not prompt:
                error_response = create_error_response(
                    f"Prompt '{name}' not found in category '{category}'", "NOT_FOUND"
                )

            # Fill template if variables provided
            if variables:
                filled_content = self.service.fill_template(prompt, variables)
                response_data = prompt.to_dict()
                response_data["filled_content"] = filled_content
                return create_success_response(message="Prompt retrieved and filled successfully", data=response_data)
            else:
                return create_success_response(message="Prompt retrieved successfully", data=prompt.to_dict())
        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            error_response = create_error_response(f"Failed to get prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_update_prompt(self, prompt_id: str, updates: PromptUpdate) -> Dict[str, Any]:
        """Update a prompt."""
        try:
            updated_prompt = self.service.update_entity(prompt_id, updates.model_dump(exclude_unset=True))
            if not updated_prompt:
                error_response = create_error_response(f"Prompt {prompt_id} not found", "NOT_FOUND")
                return error_response.model_dump()

            response = create_success_response(message="Prompt updated successfully", data=updated_prompt.to_dict())
            return response.model_dump()
        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
            return error_response.model_dump()
        except Exception as e:
            error_response = create_error_response(f"Failed to update prompt: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    async def handle_delete_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Soft delete a prompt."""
        try:
            deleted = self.service.delete_entity(prompt_id)
            if not deleted:
                error_response = create_error_response(f"Prompt {prompt_id} not found", "NOT_FOUND")

            return create_success_response(message="Prompt deleted successfully")
        except Exception as e:
            error_response = create_error_response(f"Failed to delete prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_list_prompts(
        self, category: Optional[str] = None, limit: int = 50, offset: int = 0, **filters
    ) -> Dict[str, Any]:
        """List prompts with filtering and pagination."""
        try:
            # Build filters
            search_filters = {}
            if category:
                search_filters["category"] = category
            search_filters.update(filters)

            result = self.service.list_entities(limit=limit, offset=offset, **search_filters)

            return create_success_response(message="Prompts retrieved successfully", data=result)
        except Exception as e:
            return create_error_response(f"Failed to list prompts: {str(e)}", "INTERNAL_ERROR")

    async def handle_search_prompts(
        self, query: str, category: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """Search prompts."""
        try:
            prompts = self.service.search_prompts(query, category, tags, limit)
            result = {
                "items": [p.to_dict() for p in prompts],
                "total": len(prompts),
                "has_more": False,
                "limit": limit,
                "offset": 0,
            }

            return create_success_response(message="Prompts searched successfully", data=result)
        except Exception as e:
            error_response = create_error_response(f"Failed to search prompts: {str(e)}", "INTERNAL_ERROR")

    async def handle_fork_prompt(
        self, prompt_id: str, new_name: str, created_by: str = "api_user", **changes
    ) -> Dict[str, Any]:
        """Fork a prompt."""
        try:
            forked_prompt = self.service.fork_prompt(prompt_id, new_name, created_by, changes)
            return create_success_response(message="Prompt forked successfully", data=forked_prompt.to_dict())
        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            error_response = create_error_response(f"Failed to fork prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_update_prompt_content(
        self,
        prompt_id: str,
        content: str,
        variables: Optional[List[str]] = None,
        change_summary: str = "",
        updated_by: str = "api_user",
    ) -> Dict[str, Any]:
        """Update prompt content with versioning."""
        try:
            updated_prompt = self.service.update_prompt_content(
                prompt_id, content, variables, change_summary, updated_by
            )
            return create_success_response(message="Prompt content updated successfully", data=updated_prompt.to_dict())
        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            error_response = create_error_response(f"Failed to update prompt content: {str(e)}", "INTERNAL_ERROR")

    async def handle_detect_drift(self, prompt_id: str) -> Dict[str, Any]:
        """Detect prompt drift."""
        try:
            drift_info = self.service.detect_drift(prompt_id)
            return create_success_response(message="Prompt drift analysis completed", data=drift_info)
        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            error_response = create_error_response(f"Failed to detect drift: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_suggestions(self, prompt_id: str) -> Dict[str, Any]:
        """Get prompt improvement suggestions."""
        try:
            suggestions = self.service.get_suggestions(prompt_id)
            return create_success_response(
                message="Suggestions generated successfully", data={"suggestions": suggestions}
            )
        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            error_response = create_error_response(f"Failed to get suggestions: {str(e)}", "INTERNAL_ERROR")

    async def handle_bulk_update_tags(
        self, prompt_ids: List[str], tags_to_add: Optional[List[str]] = None, tags_to_remove: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Bulk update tags on prompts."""
        try:
            updated_count = self.service.bulk_update_tags(prompt_ids, tags_to_add, tags_to_remove)
            return create_success_response(
                message=f"Tags updated on {updated_count} prompts", data={"updated_count": updated_count}
            )
        except Exception as e:
            error_response = create_error_response(f"Failed to update tags: {str(e)}", "INTERNAL_ERROR")
