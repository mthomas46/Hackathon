"""Prompt handlers for API endpoints.

Handles HTTP requests and responses for prompt operations.
"""

from typing import Dict, Any, Optional, List
from services.prompt_store.core.handler import BaseHandler
from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.core.models import PromptCreate, PromptUpdate
from services.shared.responses import create_success_response, create_error_response


class PromptHandlers(BaseHandler):
    """Handlers for prompt CRUD operations."""

    def __init__(self):
        super().__init__(PromptService())

    async def handle_create_prompt(self, prompt_data: PromptCreate) -> Dict[str, Any]:
        """Create a new prompt."""
        try:
            prompt = self.service.create_entity(prompt_data.dict())
            return create_success_response(
                message="Prompt created successfully",
                data=prompt.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to create prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_prompt_by_name(self, category: str, name: str, **variables) -> Dict[str, Any]:
        """Get prompt by category/name and fill variables."""
        try:
            prompt = self.service.get_prompt_by_name(category, name)
            if not prompt:
                return create_error_response(f"Prompt '{name}' not found in category '{category}'", "NOT_FOUND")

            # Fill template if variables provided
            if variables:
                filled_content = self.service.fill_template(prompt, variables)
                response_data = prompt.to_dict()
                response_data["filled_content"] = filled_content
                return create_success_response(
                    message="Prompt retrieved and filled successfully",
                    data=response_data
                )
            else:
                return create_success_response(
                    message="Prompt retrieved successfully",
                    data=prompt.to_dict()
                )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_update_prompt(self, prompt_id: str, updates: PromptUpdate) -> Dict[str, Any]:
        """Update a prompt."""
        try:
            updated_prompt = self.service.update_entity(prompt_id, updates.dict(exclude_unset=True))
            if not updated_prompt:
                return create_error_response(f"Prompt {prompt_id} not found", "NOT_FOUND")

            return create_success_response(
                message="Prompt updated successfully",
                data=updated_prompt.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to update prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_delete_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Soft delete a prompt."""
        try:
            deleted = self.service.delete_entity(prompt_id)
            if not deleted:
                return create_error_response(f"Prompt {prompt_id} not found", "NOT_FOUND")

            return create_success_response(
                message="Prompt deleted successfully"
            )
        except Exception as e:
            return create_error_response(f"Failed to delete prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_list_prompts(self, category: Optional[str] = None, limit: int = 50,
                                 offset: int = 0, **filters) -> Dict[str, Any]:
        """List prompts with filtering and pagination."""
        try:
            # Build filters
            search_filters = {}
            if category:
                search_filters["category"] = category
            search_filters.update(filters)

            result = self.service.list_entities(limit=limit, offset=offset, **search_filters)

            return create_success_response(
                message="Prompts retrieved successfully",
                data=result
            )
        except Exception as e:
            return create_error_response(f"Failed to list prompts: {str(e)}", "INTERNAL_ERROR")

    async def handle_search_prompts(self, query: str, category: Optional[str] = None,
                                   tags: Optional[List[str]] = None, limit: int = 50) -> Dict[str, Any]:
        """Search prompts."""
        try:
            prompts = self.service.search_prompts(query, category, tags, limit)
            result = {
                "items": [p.to_dict() for p in prompts],
                "total": len(prompts),
                "has_more": False,
                "limit": limit,
                "offset": 0
            }

            return create_success_response(
                message="Prompts searched successfully",
                data=result
            )
        except Exception as e:
            return create_error_response(f"Failed to search prompts: {str(e)}", "INTERNAL_ERROR")

    async def handle_fork_prompt(self, prompt_id: str, new_name: str, created_by: str = "api_user",
                                **changes) -> Dict[str, Any]:
        """Fork a prompt."""
        try:
            forked_prompt = self.service.fork_prompt(prompt_id, new_name, created_by, changes)
            return create_success_response(
                message="Prompt forked successfully",
                data=forked_prompt.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to fork prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_update_prompt_content(self, prompt_id: str, content: str,
                                          variables: Optional[List[str]] = None,
                                          change_summary: str = "",
                                          updated_by: str = "api_user") -> Dict[str, Any]:
        """Update prompt content with versioning."""
        try:
            updated_prompt = self.service.update_prompt_content(
                prompt_id, content, variables, change_summary, updated_by
            )
            return create_success_response(
                message="Prompt content updated successfully",
                data=updated_prompt.to_dict()
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to update prompt content: {str(e)}", "INTERNAL_ERROR")

    async def handle_detect_drift(self, prompt_id: str) -> Dict[str, Any]:
        """Detect prompt drift."""
        try:
            drift_info = self.service.detect_drift(prompt_id)
            return create_success_response(
                message="Prompt drift analysis completed",
                data=drift_info
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to detect drift: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_suggestions(self, prompt_id: str) -> Dict[str, Any]:
        """Get prompt improvement suggestions."""
        try:
            suggestions = self.service.get_suggestions(prompt_id)
            return create_success_response(
                message="Suggestions generated successfully",
                data={"suggestions": suggestions}
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get suggestions: {str(e)}", "INTERNAL_ERROR")

    async def handle_bulk_update_tags(self, prompt_ids: List[str],
                                     tags_to_add: Optional[List[str]] = None,
                                     tags_to_remove: Optional[List[str]] = None) -> Dict[str, Any]:
        """Bulk update tags on prompts."""
        try:
            updated_count = self.service.bulk_update_tags(prompt_ids, tags_to_add, tags_to_remove)
            return create_success_response(
                message=f"Tags updated on {updated_count} prompts",
                data={"updated_count": updated_count}
            )
        except Exception as e:
            return create_error_response(f"Failed to update tags: {str(e)}", "INTERNAL_ERROR")
