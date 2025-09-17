"""Prompt refinement handlers for API endpoints.

Handles HTTP requests and responses for prompt refinement operations.
"""

from typing import Dict, Any, Optional, List
from services.prompt_store.domain.refinement.service import PromptRefinementService
from services.shared.core.responses.responses import create_success_response, create_error_response


class PromptRefinementHandlers:
    """Handlers for prompt refinement operations."""

    def __init__(self):
        self.service = PromptRefinementService()

    async def handle_refine_prompt(self, prompt_id: str, refinement_instructions: str,
                                 llm_service: str = "interpreter",
                                 context_documents: Optional[List[str]] = None,
                                 user_id: str = "api_user") -> Dict[str, Any]:
        """Start prompt refinement workflow."""
        try:
            result = await self.service.refine_prompt(
                prompt_id=prompt_id,
                refinement_instructions=refinement_instructions,
                llm_service=llm_service,
                context_documents=context_documents,
                user_id=user_id
            )
            return create_success_response(
                message="Prompt refinement started successfully",
                data=result
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to start prompt refinement: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_refinement_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a refinement session."""
        try:
            status = await self.service.get_refinement_status(session_id)
            return create_success_response(
                message="Refinement status retrieved successfully",
                data=status
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get refinement status: {str(e)}", "INTERNAL_ERROR")

    async def handle_compare_prompt_versions(self, prompt_id: str,
                                           version_a: Optional[int] = None,
                                           version_b: Optional[int] = None) -> Dict[str, Any]:
        """Compare different versions of a prompt."""
        try:
            comparison = await self.service.compare_prompt_versions(
                prompt_id=prompt_id,
                version_a=version_a,
                version_b=version_b
            )
            return create_success_response(
                message="Prompt versions compared successfully",
                data=comparison
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to compare prompt versions: {str(e)}", "INTERNAL_ERROR")

    async def handle_compare_refinement_documents(self, session_a: str, session_b: str) -> Dict[str, Any]:
        """Compare documents from different refinement sessions."""
        try:
            comparison = await self.service.compare_refinement_documents(session_a, session_b)
            return create_success_response(
                message="Refinement documents compared successfully",
                data=comparison
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to compare refinement documents: {str(e)}", "INTERNAL_ERROR")

    async def handle_replace_prompt_with_refined(self, prompt_id: str, session_id: str,
                                               user_id: str = "api_user") -> Dict[str, Any]:
        """Replace original prompt with refined version."""
        try:
            result = await self.service.replace_prompt_with_refined(
                prompt_id=prompt_id,
                session_id=session_id,
                user_id=user_id
            )
            return create_success_response(
                message="Prompt replaced with refined version successfully",
                data=result
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to replace prompt: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_refinement_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get refinement history for a prompt."""
        try:
            history = await self.service.get_refinement_history(prompt_id)
            return create_success_response(
                message="Refinement history retrieved successfully",
                data=history
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get refinement history: {str(e)}", "INTERNAL_ERROR")

    async def handle_get_version_refinement_details(self, prompt_id: str, version: int) -> Dict[str, Any]:
        """Get detailed refinement information for a specific version."""
        try:
            details = await self.service.get_version_refinement_details(prompt_id, version)
            return create_success_response(
                message="Version refinement details retrieved successfully",
                data=details
            )
        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to get version refinement details: {str(e)}", "INTERNAL_ERROR")

    async def handle_list_active_refinements(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """List all active refinement sessions."""
        try:
            # This would query for active refinement sessions
            # For now, return a placeholder
            return create_success_response(
                message="Active refinements retrieved successfully",
                data={
                    "active_sessions": [],
                    "total_active": 0
                }
            )
        except Exception as e:
            return create_error_response(f"Failed to list active refinements: {str(e)}", "INTERNAL_ERROR")
