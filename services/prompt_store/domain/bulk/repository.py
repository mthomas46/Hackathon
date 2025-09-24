"""Bulk operations repository implementation.

Handles database operations for bulk operations and their results.
"""

from typing import Any, Dict

from services.prompt_store.core.entities import BulkOperation
from services.shared.utilities import SqlRepository, validate_sql_identifier


class BulkOperationRepository(SqlRepository[BulkOperation]):
    """Repository for bulk operation entities."""

    def __init__(self, connection_string: str):
        from ...db.connection import get_prompt_store_connection_string

        super().__init__(
            BulkOperation, connection_string or get_prompt_store_connection_string()
        )

        # Validate table name to prevent SQL injection
        if not validate_sql_identifier(self.table_name):
            raise ValueError(f"Invalid table name: {self.table_name}")

    def _dict_to_entity(self, data: Dict[str, Any]) -> BulkOperation:
        """Convert database row to BulkOperation entity."""
        # Handle JSON deserialization for errors, metadata, and results
        if "errors" in data and isinstance(data["errors"], str):
            import json

            data["errors"] = json.loads(data["errors"])
        if "metadata" in data and isinstance(data["metadata"], str):
            import json

            data["metadata"] = json.loads(data["metadata"])
        if "results" in data and isinstance(data["results"], str):
            import json

            data["results"] = json.loads(data["results"])

        return BulkOperation.from_dict(data)
