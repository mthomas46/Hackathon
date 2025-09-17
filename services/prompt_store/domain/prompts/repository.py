"""Prompt repository implementation.

Handles database operations for prompts following domain-driven design.
"""

from typing import List, Optional, Dict, Any, Tuple
from services.prompt_store.core.repository import BaseRepository
from services.prompt_store.core.entities import Prompt
from services.prompt_store.db.queries import execute_paged_query, execute_query, serialize_json, deserialize_json


class PromptRepository(BaseRepository[Prompt]):
    """Repository for prompt entities."""

    def __init__(self):
        super().__init__("prompts")

    def _row_to_entity(self, row: Dict[str, Any]) -> Prompt:
        """Convert database row to Prompt entity."""
        return Prompt.from_dict({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "description": row["description"],
            "content": row["content"],
            "variables": deserialize_json(row["variables"]),
            "tags": deserialize_json(row["tags"]),
            "is_active": row["is_active"],
            "is_template": row["is_template"],
            "lifecycle_status": row["lifecycle_status"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "version": row["version"],
            "parent_id": row["parent_id"],
            "performance_score": row["performance_score"],
            "usage_count": row["usage_count"]
        })

    def _entity_to_row(self, entity: Prompt) -> Dict[str, Any]:
        """Convert Prompt entity to database row."""
        return {
            "id": entity.id,
            "name": entity.name,
            "category": entity.category,
            "description": entity.description,
            "content": entity.content,
            "variables": serialize_json(entity.variables),
            "tags": serialize_json(entity.tags),
            "is_active": entity.is_active,
            "is_template": entity.is_template,
            "lifecycle_status": entity.lifecycle_status,
            "created_by": entity.created_by,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat(),
            "version": entity.version,
            "parent_id": entity.parent_id,
            "performance_score": entity.performance_score,
            "usage_count": entity.usage_count
        }

    def save(self, entity: Prompt) -> Prompt:
        """Save prompt to database."""
        row = self._entity_to_row(entity)
        columns = list(row.keys())
        placeholders = ",".join("?" * len(columns))
        values = [row[col] for col in columns]

        query = f"""
            INSERT OR REPLACE INTO {self.table_name}
            ({','.join(columns)})
            VALUES ({placeholders})
        """

        execute_query(query, values)
        return entity

    def get_by_id(self, entity_id: str) -> Optional[Prompt]:
        """Get prompt by ID."""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        row = execute_query(query, (entity_id,), fetch_one=True)
        return self._row_to_entity(row) if row else None

    def get_all(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """Get all prompts with pagination and filtering."""
        return execute_paged_query(self.table_name, filters, limit=limit, offset=offset)

    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[Prompt]:
        """Update prompt."""
        if not updates:
            return self.get_by_id(entity_id)

        # Build update query
        set_parts = []
        values = []
        for key, value in updates.items():
            if key in ["variables", "tags"]:  # JSON fields
                set_parts.append(f"{key} = ?")
                values.append(serialize_json(value))
            else:
                set_parts.append(f"{key} = ?")
                values.append(value)

        values.append(entity_id)  # For WHERE clause

        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_parts)}, updated_at = ?
            WHERE id = ?
        """
        values.insert(-1, "CURRENT_TIMESTAMP")  # Insert updated_at before id

        execute_query(query, values)
        return self.get_by_id(entity_id)

    def delete(self, entity_id: str) -> bool:
        """Soft delete prompt."""
        query = f"UPDATE {self.table_name} SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        execute_query(query, (entity_id,))
        return True

    def exists(self, entity_id: str) -> bool:
        """Check if prompt exists."""
        query = f"SELECT 1 FROM {self.table_name} WHERE id = ? AND is_active = 1"
        row = execute_query(query, (entity_id,), fetch_one=True)
        return row is not None

    def count(self, **filters) -> int:
        """Count prompts matching filters."""
        where_clause = ""
        params = []

        if filters:
            conditions = []
            for key, value in filters.items():
                if key == "category":
                    conditions.append("category = ?")
                    params.append(value)
                elif key == "is_active":
                    conditions.append("is_active = ?")
                    params.append(value)
                elif key == "lifecycle_status":
                    conditions.append("lifecycle_status = ?")
                    params.append(value)
                elif key == "created_by":
                    conditions.append("created_by = ?")
                    params.append(value)
                elif key == "is_template":
                    conditions.append("is_template = ?")
                    params.append(value)

            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"

        query = f"SELECT COUNT(*) as count FROM {self.table_name} {where_clause}"
        result = execute_query(query, tuple(params), fetch_one=True)
        return result["count"] if result else 0

    def get_by_name(self, category: str, name: str) -> Optional[Prompt]:
        """Get prompt by category and name."""
        query = f"SELECT * FROM {self.table_name} WHERE category = ? AND name = ? AND is_active = 1"
        row = execute_query(query, (category, name), fetch_one=True)
        return self._row_to_entity(row) if row else None

    def search_prompts(self, query: str, category: Optional[str] = None,
                      tags: Optional[List[str]] = None, limit: int = 50) -> List[Prompt]:
        """Search prompts using FTS and filters."""
        from services.prompt_store.db.queries import execute_search_query

        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if tags:
            # For tags, we need to check if any of the search tags are in the prompt's tags
            # This is a simplified implementation - could be enhanced
            pass

        # Use FTS search
        results = execute_search_query(query, "prompts", limit=limit)
        prompts = [self._row_to_entity(row) for row in results]

        # Apply additional filters
        if tags:
            prompts = [p for p in prompts if any(tag in p.tags for tag in tags)]

        return prompts

    def get_by_category(self, category: str, limit: int = 50, offset: int = 0) -> List[Prompt]:
        """Get prompts by category."""
        query = f"SELECT * FROM {self.table_name} WHERE category = ? AND is_active = 1 ORDER BY created_at DESC LIMIT ? OFFSET ?"
        rows = execute_query(query, (category, limit, offset), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def get_by_tags(self, tags: List[str], limit: int = 50) -> List[Prompt]:
        """Get prompts containing any of the specified tags."""
        # This is a simplified implementation - in practice, you'd use JSON functions
        all_prompts = []
        for tag in tags:
            query = f"SELECT * FROM {self.table_name} WHERE tags LIKE ? AND is_active = 1 ORDER BY created_at DESC LIMIT ?"
            rows = execute_query(query, (f"%{tag}%", limit), fetch_all=True)
            all_prompts.extend([self._row_to_entity(row) for row in rows])

        # Remove duplicates and limit
        seen_ids = set()
        unique_prompts = []
        for prompt in all_prompts:
            if prompt.id not in seen_ids:
                seen_ids.add(prompt.id)
                unique_prompts.append(prompt)
                if len(unique_prompts) >= limit:
                    break

        return unique_prompts

    def increment_usage_count(self, prompt_id: str) -> bool:
        """Increment usage count for a prompt."""
        query = f"UPDATE {self.table_name} SET usage_count = usage_count + 1 WHERE id = ?"
        execute_query(query, (prompt_id,))
        return True

    def update_performance_score(self, prompt_id: str, score: float) -> bool:
        """Update performance score for a prompt."""
        query = f"UPDATE {self.table_name} SET performance_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        execute_query(query, (score, prompt_id))
        return True
