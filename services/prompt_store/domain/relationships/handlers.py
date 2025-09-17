"""Relationships API handlers.

Handles HTTP requests and responses for prompt relationship operations.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException

from services.prompt_store.domain.relationships.service import RelationshipsService
from services.prompt_store.core.models import PromptRelationshipCreate
from services.shared.core.responses.responses import create_success_response, create_error_response


class RelationshipsHandlers:
    """Handlers for prompt relationship management endpoints."""

    def __init__(self):
        self.relationships_service = RelationshipsService()

    async def handle_create_relationship(self, source_prompt_id: str,
                                       relationship_data: PromptRelationshipCreate,
                                       user_id: str = "api_user") -> Dict[str, Any]:
        """Handle relationship creation request."""

        try:
            # Convert to dict for service
            rel_dict = {
                "target_prompt_id": relationship_data.target_prompt_id,
                "relationship_type": relationship_data.relationship_type,
                "strength": relationship_data.strength,
                "metadata": relationship_data.metadata
            }

            result = await self.relationships_service.create_relationship(
                source_prompt_id, rel_dict, user_id
            )

            response = create_success_response(
                data=result,
                message=f"Relationship '{relationship_data.relationship_type}' created between prompts"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create relationship: {str(e)}")

    def handle_get_relationships(self, prompt_id: str, direction: str = "both") -> Dict[str, Any]:
        """Handle request to get relationships for a prompt."""

        try:
            result = self.relationships_service.get_relationships_for_prompt(prompt_id, direction)

            response = create_success_response(
                data=result,
                message=f"Retrieved relationships for prompt {prompt_id}"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve relationships: {str(e)}")

    def handle_update_relationship_strength(self, relationship_id: str, new_strength: float,
                                          user_id: str = "api_user") -> Dict[str, Any]:
        """Handle request to update relationship strength."""

        try:
            result = self.relationships_service.update_relationship_strength(
                relationship_id, new_strength, user_id
            )

            response = create_success_response(
                data=result,
                message=f"Relationship strength updated to {new_strength}"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update relationship: {str(e)}")

    def handle_delete_relationship(self, relationship_id: str, user_id: str = "api_user") -> Dict[str, Any]:
        """Handle request to delete a relationship."""

        try:
            result = self.relationships_service.delete_relationship(relationship_id, user_id)

            response = create_success_response(
                data=result,
                message="Relationship deleted successfully"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete relationship: {str(e)}")

    def handle_get_relationship_graph(self, prompt_id: str, depth: int = 2) -> Dict[str, Any]:
        """Handle request to get relationship graph."""

        try:
            result = self.relationships_service.get_relationship_graph(prompt_id, depth)

            response = create_success_response(
                data=result,
                message=f"Retrieved relationship graph for prompt {prompt_id}"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve relationship graph: {str(e)}")

    def handle_get_relationship_stats(self) -> Dict[str, Any]:
        """Handle request to get relationship statistics."""

        try:
            result = self.relationships_service.get_relationship_types_count()

            response = create_success_response(
                data=result,
                message="Retrieved relationship statistics"
            )
            return response.model_dump()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")

    def handle_find_related_prompts(self, prompt_id: str,
                                  relationship_types: Optional[List[str]] = None,
                                  min_strength: float = 0.0) -> Dict[str, Any]:
        """Handle request to find related prompts."""

        try:
            result = self.relationships_service.find_related_prompts(
                prompt_id, relationship_types, min_strength
            )

            response = create_success_response(
                data=result,
                message=f"Found {result['total_related']} related prompts"
            )
            return response.model_dump()

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to find related prompts: {str(e)}")

    def handle_validate_relationship(self, source_prompt_id: str, target_prompt_id: str,
                                   relationship_type: str) -> Dict[str, Any]:
        """Handle request to validate relationship creation."""

        try:
            result = self.relationships_service.validate_relationship_creation(
                source_prompt_id, target_prompt_id, relationship_type
            )

            response = create_success_response(
                data=result,
                message="Relationship validation completed"
            )
            return response.model_dump()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to validate relationship: {str(e)}")
