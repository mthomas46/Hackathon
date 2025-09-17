"""Relationships repository.

Handles data access operations for prompt relationships and semantic connections.
"""

from typing import List, Optional, Dict, Any
from services.prompt_store.db.queries import execute_query
from services.prompt_store.core.entities import PromptRelationship


class RelationshipsRepository:
    """Repository for prompt relationship operations."""

    VALID_RELATIONSHIP_TYPES = {
        "extends",      # Target extends source (inheritance)
        "references",   # Source references target
        "alternative",  # Alternative to source
        "similar",      # Similar to source
        "depends_on",   # Source depends on target
        "replaces",     # Source replaces target
        "complements",  # Source complements target
        "conflicts"     # Source conflicts with target
    }

    def __init__(self):
        self.table_name = "prompt_relationships"

    def create_relationship(self, source_id: str, target_id: str,
                           relationship_type: str, strength: float = 1.0,
                           metadata: Optional[Dict[str, Any]] = None,
                           created_by: str = "system") -> PromptRelationship:
        """Create a new relationship between prompts."""

        if relationship_type not in self.VALID_RELATIONSHIP_TYPES:
            raise ValueError(f"Invalid relationship type: {relationship_type}")

        if source_id == target_id:
            raise ValueError("Cannot create relationship to self")

        # Check if relationship already exists
        existing = self.get_relationship(source_id, target_id, relationship_type)
        if existing:
            raise ValueError(f"Relationship {relationship_type} already exists between {source_id} and {target_id}")

        relationship = PromptRelationship(
            source_prompt_id=source_id,
            target_prompt_id=target_id,
            relationship_type=relationship_type,
            strength=strength,
            metadata=metadata or {},
            created_by=created_by
        )

        # Save to database
        query = f"""
            INSERT INTO {self.table_name}
            (id, source_prompt_id, target_prompt_id, relationship_type, strength, metadata, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        execute_query(query, (
            relationship.id,
            relationship.source_prompt_id,
            relationship.target_prompt_id,
            relationship.relationship_type,
            relationship.strength,
            str(relationship.metadata),
            relationship.created_by,
            relationship.created_at.isoformat(),
            relationship.updated_at.isoformat()
        ), fetch_all=False)

        return relationship

    def get_relationship(self, source_id: str, target_id: str,
                        relationship_type: str) -> Optional[PromptRelationship]:
        """Get a specific relationship."""
        query = f"""
            SELECT id, source_prompt_id, target_prompt_id, relationship_type,
                   strength, metadata, created_by, created_at, updated_at
            FROM {self.table_name}
            WHERE source_prompt_id = ? AND target_prompt_id = ? AND relationship_type = ?
        """

        row = execute_query(query, (source_id, target_id, relationship_type), fetch_one=True)
        if not row:
            return None

        return PromptRelationship.from_dict(row)

    def get_relationships_for_prompt(self, prompt_id: str,
                                   direction: str = "both") -> List[PromptRelationship]:
        """Get all relationships for a prompt."""

        if direction == "outgoing":
            # Relationships where this prompt is the source
            query = f"""
                SELECT id, source_prompt_id, target_prompt_id, relationship_type,
                       strength, metadata, created_by, created_at, updated_at
                FROM {self.table_name}
                WHERE source_prompt_id = ?
                ORDER BY created_at DESC
            """
            params = (prompt_id,)

        elif direction == "incoming":
            # Relationships where this prompt is the target
            query = f"""
                SELECT id, source_prompt_id, target_prompt_id, relationship_type,
                       strength, metadata, created_by, created_at, updated_at
                FROM {self.table_name}
                WHERE target_prompt_id = ?
                ORDER BY created_at DESC
            """
            params = (prompt_id,)

        else:  # both
            query = f"""
                SELECT id, source_prompt_id, target_prompt_id, relationship_type,
                       strength, metadata, created_by, created_at, updated_at
                FROM {self.table_name}
                WHERE source_prompt_id = ? OR target_prompt_id = ?
                ORDER BY created_at DESC
            """
            params = (prompt_id, prompt_id)

        rows = execute_query(query, params, fetch_all=True)
        return [PromptRelationship.from_dict(row) for row in rows]

    def update_relationship_strength(self, relationship_id: str,
                                   new_strength: float) -> bool:
        """Update the strength of a relationship."""
        if not (0.0 <= new_strength <= 1.0):
            raise ValueError("Relationship strength must be between 0.0 and 1.0")

        query = f"""
            UPDATE {self.table_name}
            SET strength = ?, updated_at = datetime('now')
            WHERE id = ?
        """

        execute_query(query, (new_strength, relationship_id), fetch_all=False)
        return True

    def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        execute_query(query, (relationship_id,), fetch_all=False)
        return True

    def delete_relationships_for_prompt(self, prompt_id: str) -> int:
        """Delete all relationships involving a prompt."""
        query = f"""
            DELETE FROM {self.table_name}
            WHERE source_prompt_id = ? OR target_prompt_id = ?
        """
        execute_query(query, (prompt_id, prompt_id), fetch_all=False)
        # Note: execute_query doesn't return affected rows, so we return 0
        # In a real implementation, you'd want to track this
        return 0

    def get_relationship_graph(self, prompt_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get a relationship graph starting from a prompt."""
        # This is a simplified implementation
        # In a real system, you'd want to build a proper graph structure

        visited = set()
        graph = {"nodes": [], "edges": []}

        def add_to_graph(current_id: str, current_depth: int):
            if current_id in visited or current_depth > depth:
                return

            visited.add(current_id)

            # Add node
            graph["nodes"].append({"id": current_id, "type": "prompt"})

            # Get relationships
            relationships = self.get_relationships_for_prompt(current_id)

            for rel in relationships:
                # Add edge
                graph["edges"].append({
                    "source": rel.source_prompt_id,
                    "target": rel.target_prompt_id,
                    "type": rel.relationship_type,
                    "strength": rel.strength
                })

                # Recursively add related prompts
                if rel.source_prompt_id == current_id:
                    add_to_graph(rel.target_prompt_id, current_depth + 1)
                else:
                    add_to_graph(rel.source_prompt_id, current_depth + 1)

        add_to_graph(prompt_id, 0)
        return graph

    def get_relationship_types_count(self) -> Dict[str, int]:
        """Get count of relationships by type."""
        query = f"""
            SELECT relationship_type, COUNT(*) as count
            FROM {self.table_name}
            GROUP BY relationship_type
        """

        rows = execute_query(query, fetch_all=True)
        counts = {rel_type: 0 for rel_type in self.VALID_RELATIONSHIP_TYPES}
        counts.update({row["relationship_type"]: row["count"] for row in rows})
        return counts

    def validate_relationship_type(self, relationship_type: str) -> bool:
        """Validate if a relationship type is valid."""
        return relationship_type in self.VALID_RELATIONSHIP_TYPES
