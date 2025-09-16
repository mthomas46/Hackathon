"""Relationships service.

Contains business logic for prompt relationships and semantic connections.
"""

from typing import List, Dict, Any, Optional
from services.prompt_store.domain.relationships.repository import RelationshipsRepository
from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.shared.utilities import generate_id, utc_now


class RelationshipsService:
    """Service for managing prompt relationships."""

    def __init__(self):
        self.repo = RelationshipsRepository()
        self.prompt_service = PromptService()

    async def create_relationship(self, source_prompt_id: str, relationship_data: Dict[str, Any],
                                user_id: str = "api_user") -> Dict[str, Any]:
        """Create a new relationship between prompts."""

        # Validate that both prompts exist
        source_prompt = self.prompt_service.get_entity(source_prompt_id)
        if not source_prompt:
            raise ValueError(f"Source prompt {source_prompt_id} not found")

        target_prompt = self.prompt_service.get_entity(relationship_data["target_prompt_id"])
        if not target_prompt:
            raise ValueError(f"Target prompt {relationship_data['target_prompt_id']} not found")

        # Validate relationship type
        if not self.repo.validate_relationship_type(relationship_data["relationship_type"]):
            raise ValueError(f"Invalid relationship type: {relationship_data['relationship_type']}")

        # Create the relationship
        relationship = self.repo.create_relationship(
            source_id=source_prompt_id,
            target_id=relationship_data["target_prompt_id"],
            relationship_type=relationship_data["relationship_type"],
            strength=relationship_data.get("strength", 1.0),
            metadata=relationship_data.get("metadata", {}),
            created_by=user_id
        )

        # Invalidate caches
        await self._invalidate_relationship_caches(source_prompt_id, relationship_data["target_prompt_id"])

        return {
            "relationship_id": relationship.id,
            "source_prompt_id": relationship.source_prompt_id,
            "target_prompt_id": relationship.target_prompt_id,
            "relationship_type": relationship.relationship_type,
            "strength": relationship.strength,
            "created_at": relationship.created_at.isoformat(),
            "created_by": user_id
        }

    def get_relationships_for_prompt(self, prompt_id: str, direction: str = "both") -> Dict[str, Any]:
        """Get all relationships for a prompt."""

        # Validate prompt exists
        prompt = self.prompt_service.get_entity(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        relationships = self.repo.get_relationships_for_prompt(prompt_id, direction)

        # Group by direction for better API response
        outgoing = []
        incoming = []

        for rel in relationships:
            rel_dict = {
                "id": rel.id,
                "relationship_type": rel.relationship_type,
                "strength": rel.strength,
                "metadata": rel.metadata,
                "created_at": rel.created_at.isoformat(),
                "created_by": rel.created_by
            }

            if rel.source_prompt_id == prompt_id:
                rel_dict["target_prompt_id"] = rel.target_prompt_id
                outgoing.append(rel_dict)
            else:
                rel_dict["source_prompt_id"] = rel.source_prompt_id
                incoming.append(rel_dict)

        return {
            "prompt_id": prompt_id,
            "outgoing_relationships": outgoing,
            "incoming_relationships": incoming,
            "total_relationships": len(relationships)
        }

    def update_relationship_strength(self, relationship_id: str, new_strength: float,
                                   user_id: str = "api_user") -> Dict[str, Any]:
        """Update the strength of a relationship."""

        success = self.repo.update_relationship_strength(relationship_id, new_strength)
        if not success:
            raise ValueError(f"Relationship {relationship_id} not found")

        return {
            "relationship_id": relationship_id,
            "new_strength": new_strength,
            "updated_by": user_id,
            "updated_at": utc_now().isoformat()
        }

    def delete_relationship(self, relationship_id: str, user_id: str = "api_user") -> Dict[str, Any]:
        """Delete a relationship."""

        # Get relationship details before deletion for cache invalidation
        # Note: This is a simplified implementation
        success = self.repo.delete_relationship(relationship_id)
        if not success:
            raise ValueError(f"Relationship {relationship_id} not found or already deleted")

        return {
            "relationship_id": relationship_id,
            "deleted": True,
            "deleted_by": user_id,
            "deleted_at": utc_now().isoformat()
        }

    def get_relationship_graph(self, prompt_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get a relationship graph starting from a prompt."""

        # Validate prompt exists
        prompt = self.prompt_service.get_entity(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        graph = self.repo.get_relationship_graph(prompt_id, depth)

        # Enhance graph with prompt details
        enhanced_nodes = []
        for node in graph["nodes"]:
            prompt_details = self.prompt_service.get_entity(node["id"])
            if prompt_details:
                enhanced_nodes.append({
                    "id": node["id"],
                    "name": prompt_details.name,
                    "category": prompt_details.category,
                    "lifecycle_status": prompt_details.lifecycle_status
                })

        return {
            "root_prompt_id": prompt_id,
            "nodes": enhanced_nodes,
            "edges": graph["edges"],
            "depth": depth,
            "total_nodes": len(enhanced_nodes),
            "total_edges": len(graph["edges"])
        }

    def get_relationship_types_count(self) -> Dict[str, Any]:
        """Get statistics about relationship types."""

        counts = self.repo.get_relationship_types_count()
        total_relationships = sum(counts.values())

        return {
            "relationship_counts": counts,
            "total_relationships": total_relationships,
            "valid_types": list(self.repo.VALID_RELATIONSHIP_TYPES),
            "last_updated": utc_now().isoformat()
        }

    def find_related_prompts(self, prompt_id: str, relationship_types: Optional[List[str]] = None,
                           min_strength: float = 0.0) -> Dict[str, Any]:
        """Find prompts related to the given prompt with optional filtering."""

        # Validate prompt exists
        prompt = self.prompt_service.get_entity(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        relationships = self.repo.get_relationships_for_prompt(prompt_id)

        # Filter relationships
        filtered_relationships = []
        for rel in relationships:
            if relationship_types and rel.relationship_type not in relationship_types:
                continue
            if rel.strength < min_strength:
                continue
            filtered_relationships.append(rel)

        # Get related prompt details
        related_prompts = []
        for rel in filtered_relationships:
            related_id = rel.target_prompt_id if rel.source_prompt_id == prompt_id else rel.source_prompt_id
            related_prompt = self.prompt_service.get_entity(related_id)
            if related_prompt:
                related_prompts.append({
                    "prompt_id": related_id,
                    "name": related_prompt.name,
                    "category": related_prompt.category,
                    "relationship_type": rel.relationship_type,
                    "strength": rel.strength,
                    "direction": "outgoing" if rel.source_prompt_id == prompt_id else "incoming"
                })

        return {
            "source_prompt_id": prompt_id,
            "related_prompts": related_prompts,
            "total_related": len(related_prompts),
            "filters": {
                "relationship_types": relationship_types,
                "min_strength": min_strength
            }
        }

    def validate_relationship_creation(self, source_id: str, target_id: str,
                                     relationship_type: str) -> Dict[str, Any]:
        """Validate if a relationship can be created."""

        issues = []

        # Check if prompts exist
        source_prompt = self.prompt_service.get_entity(source_id)
        if not source_prompt:
            issues.append(f"Source prompt {source_id} not found")

        target_prompt = self.prompt_service.get_entity(target_id)
        if not target_prompt:
            issues.append(f"Target prompt {target_id} not found")

        # Check relationship type
        if not self.repo.validate_relationship_type(relationship_type):
            issues.append(f"Invalid relationship type: {relationship_type}")

        # Check for self-reference
        if source_id == target_id:
            issues.append("Cannot create relationship to self")

        # Check for existing relationship
        if source_prompt and target_prompt:
            existing = self.repo.get_relationship(source_id, target_id, relationship_type)
            if existing:
                issues.append(f"Relationship {relationship_type} already exists between prompts")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "source_prompt_id": source_id,
            "target_prompt_id": target_id,
            "relationship_type": relationship_type
        }

    async def _invalidate_relationship_caches(self, prompt_id_1: str, prompt_id_2: str) -> None:
        """Invalidate relationship caches for affected prompts."""
        await prompt_store_cache.delete(f"relationships:{prompt_id_1}")
        await prompt_store_cache.delete(f"relationships:{prompt_id_2}")
        await prompt_store_cache.delete("relationship_counts")
        await prompt_store_cache.delete_pattern("relationship_graph:*")
