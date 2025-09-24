"""A/B testing repository implementation.

Handles database operations for A/B testing entities.
"""

from typing import Any, Dict, Optional

from services.prompt_store.core.entities import ABTest, ABTestResult
from services.shared.utilities import SqlRepository, validate_sql_identifier


class ABTestRepository(SqlRepository[ABTest]):
    """Repository for A/B test entities."""

    def __init__(self, connection_string: str):
        from ...db.connection import get_prompt_store_connection_string

        super().__init__(
            ABTest, connection_string or get_prompt_store_connection_string()
        )

        # Validate table name to prevent SQL injection
        if not validate_sql_identifier(self.table_name):
            raise ValueError(f"Invalid table name: {self.table_name}")

    def _dict_to_entity(self, data: Dict[str, Any]) -> ABTest:
        """Convert database row to ABTest entity."""
        # Handle JSON deserialization for target_audience
        if "target_audience" in data and isinstance(data["target_audience"], str):
            import json

            data["target_audience"] = json.loads(data["target_audience"])

        return ABTest.from_dict(data)


class ABTestResultRepository(SqlRepository[ABTestResult]):
    """Repository for A/B test result entities."""

    def __init__(self, connection_string: str):
        from ...db.connection import get_prompt_store_connection_string

        super().__init__(
            ABTestResult, connection_string or get_prompt_store_connection_string()
        )

        # Validate table name to prevent SQL injection
        if not validate_sql_identifier(self.table_name):
            raise ValueError(f"Invalid table name: {self.table_name}")

    def _dict_to_entity(self, data: Dict[str, Any]) -> ABTestResult:
        """Convert database row to ABTestResult entity."""
        # Handle JSON deserialization for result_data
        if "result_data" in data and isinstance(data["result_data"], str):
            import json

            data["result_data"] = json.loads(data["result_data"])

        return ABTestResult.from_dict(data)
