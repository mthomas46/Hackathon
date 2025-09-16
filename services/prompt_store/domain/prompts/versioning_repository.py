"""Prompt versioning repository implementation.

Handles database operations for prompt versions.
"""

from typing import List, Optional, Dict, Any
from services.prompt_store.core.entities import PromptVersion
from services.prompt_store.db.queries import execute_query, serialize_json, deserialize_json


class PromptVersioningRepository:
    """Repository for prompt version entities."""

    def __init__(self):
        self.table_name = "prompt_versions"

    def _row_to_entity(self, row: Dict[str, Any]) -> PromptVersion:
        """Convert database row to PromptVersion entity."""
        return PromptVersion.from_dict({
            "id": row["id"],
            "prompt_id": row["prompt_id"],
            "version": row["version"],
            "content": row["content"],
            "variables": deserialize_json(row["variables"]),
            "change_summary": row["change_summary"],
            "change_type": row["change_type"],
            "created_by": row["created_by"],
            "created_at": row["created_at"]
        })

    def save(self, entity: PromptVersion) -> PromptVersion:
        """Save prompt version to database."""
        row = {
            "id": entity.id,
            "prompt_id": entity.prompt_id,
            "version": entity.version,
            "content": entity.content,
            "variables": serialize_json(entity.variables),
            "change_summary": entity.change_summary,
            "change_type": entity.change_type,
            "created_by": entity.created_by,
            "created_at": entity.created_at.isoformat()
        }

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

    def get_versions_for_prompt(self, prompt_id: str, limit: int = 50) -> List[PromptVersion]:
        """Get version history for a prompt."""
        query = f"SELECT * FROM {self.table_name} WHERE prompt_id = ? ORDER BY version DESC LIMIT ?"
        rows = execute_query(query, (prompt_id, limit), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def get_version_by_number(self, prompt_id: str, version: int) -> Optional[PromptVersion]:
        """Get specific version of a prompt."""
        query = f"SELECT * FROM {self.table_name} WHERE prompt_id = ? AND version = ?"
        row = execute_query(query, (prompt_id, version), fetch_one=True)
        return self._row_to_entity(row) if row else None

    def get_latest_version(self, prompt_id: str) -> Optional[PromptVersion]:
        """Get latest version for a prompt."""
        query = f"SELECT * FROM {self.table_name} WHERE prompt_id = ? ORDER BY version DESC LIMIT 1"
        row = execute_query(query, (prompt_id,), fetch_one=True)
        return self._row_to_entity(row) if row else None
