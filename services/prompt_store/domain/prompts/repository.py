"""Prompt repository implementation.

Handles database operations for prompts following domain-driven design.
"""

from typing import Any, Dict, Optional

from services.prompt_store.core.entities import Prompt
from services.shared.domain.repositories.base_repository import SqlRepository
from services.shared.infrastructure.utilities.utilities import validate_sql_identifier


class PromptRepository(SqlRepository[Prompt]):
    """Repository for prompt entities."""

    def __init__(self, connection_string: str):
        from ...db.connection import get_prompt_store_connection_string

        super().__init__(
            Prompt, connection_string or get_prompt_store_connection_string()
        )

        # Validate table name to prevent SQL injection
        if not validate_sql_identifier(self.table_name):
            raise ValueError(f"Invalid table name: {self.table_name}")

    def _dict_to_entity(self, data: Dict[str, Any]) -> Prompt:
        """Convert database row to Prompt entity."""
        # Handle JSON deserialization for variables and tags
        if "variables" in data and isinstance(data["variables"], str):
            import json

            data["variables"] = json.loads(data["variables"])
        if "tags" in data and isinstance(data["tags"], str):
            import json

            data["tags"] = json.loads(data["tags"])

        return Prompt.from_dict(data)
