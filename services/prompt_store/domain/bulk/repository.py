"""Bulk operations repository implementation.

Handles database operations for bulk operations and their results.
"""

from typing import List, Optional, Dict, Any
from services.prompt_store.core.repository import BaseRepository
from services.prompt_store.core.entities import BulkOperation
from services.prompt_store.db.queries import execute_query, serialize_json, deserialize_json


class BulkOperationRepository(BaseRepository[BulkOperation]):
    """Repository for bulk operation entities."""

    def __init__(self):
        super().__init__("bulk_operations")

    def _row_to_entity(self, row: Dict[str, Any]) -> BulkOperation:
        """Convert database row to BulkOperation entity."""
        return BulkOperation.from_dict({
            "id": row["id"],
            "operation_type": row["operation_type"],
            "status": row["status"],
            "total_items": row["total_items"],
            "processed_items": row["processed_items"],
            "successful_items": row["successful_items"],
            "failed_items": row["failed_items"],
            "errors": deserialize_json(row["errors"]),
            "metadata": deserialize_json(row["metadata"]),
            "results": deserialize_json(row["results"]),
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"]
        })

    def _entity_to_row(self, entity: BulkOperation) -> Dict[str, Any]:
        """Convert BulkOperation entity to database row."""
        return {
            "id": entity.id,
            "operation_type": entity.operation_type,
            "status": entity.status,
            "total_items": entity.total_items,
            "processed_items": entity.processed_items,
            "successful_items": entity.successful_items,
            "failed_items": entity.failed_items,
            "errors": serialize_json(entity.errors),
            "metadata": serialize_json(entity.metadata),
            "results": serialize_json(entity.results),
            "created_by": entity.created_by,
            "created_at": entity.created_at.isoformat(),
            "completed_at": entity.completed_at.isoformat() if entity.completed_at else None
        }

    def save(self, entity: BulkOperation) -> BulkOperation:
        """Save bulk operation to database."""
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

    def get_by_id(self, entity_id: str) -> Optional[BulkOperation]:
        """Get bulk operation by ID."""
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        row = execute_query(query, (entity_id,), fetch_one=True)
        return self._row_to_entity(row) if row else None

    def get_all(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """Get all bulk operations with pagination and filtering."""
        from services.prompt_store.db.queries import execute_paged_query
        return execute_paged_query(self.table_name, filters, limit=limit, offset=offset)

    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[BulkOperation]:
        """Update bulk operation."""
        if not updates:
            return self.get_by_id(entity_id)

        # Build update query
        set_parts = []
        values = []
        for key, value in updates.items():
            if key in ["errors", "metadata", "results"]:  # JSON fields
                set_parts.append(f"{key} = ?")
                values.append(serialize_json(value))
            else:
                set_parts.append(f"{key} = ?")
                values.append(value)

        values.append(entity_id)  # For WHERE clause

        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_parts)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        execute_query(query, values)
        return self.get_by_id(entity_id)

    def delete(self, entity_id: str) -> bool:
        """Delete bulk operation."""
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        execute_query(query, (entity_id,))
        return True

    def exists(self, entity_id: str) -> bool:
        """Check if bulk operation exists."""
        query = f"SELECT 1 FROM {self.table_name} WHERE id = ?"
        row = execute_query(query, (entity_id,), fetch_one=True)
        return row is not None

    def count(self, **filters) -> int:
        """Count bulk operations matching filters."""
        where_clause = ""
        params = []

        if filters:
            conditions = []
            for key, value in filters.items():
                if key == "status":
                    conditions.append("status = ?")
                    params.append(value)
                elif key == "operation_type":
                    conditions.append("operation_type = ?")
                    params.append(value)
                elif key == "created_by":
                    conditions.append("created_by = ?")
                    params.append(value)

            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"

        query = f"SELECT COUNT(*) as count FROM {self.table_name} {where_clause}"
        result = execute_query(query, tuple(params), fetch_one=True)
        return result["count"] if result else 0

    def get_pending_operations(self) -> List[BulkOperation]:
        """Get all pending bulk operations."""
        query = f"SELECT * FROM {self.table_name} WHERE status = 'pending' ORDER BY created_at ASC"
        rows = execute_query(query, fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def get_operations_by_status(self, status: str, limit: int = 50) -> List[BulkOperation]:
        """Get bulk operations by status."""
        query = f"SELECT * FROM {self.table_name} WHERE status = ? ORDER BY created_at DESC LIMIT ?"
        rows = execute_query(query, (status, limit), fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def update_progress(self, operation_id: str, processed: int, successful: int,
                       failed: int, errors: Optional[List[str]] = None) -> bool:
        """Update operation progress."""
        updates = {
            "processed_items": processed,
            "successful_items": successful,
            "failed_items": failed
        }

        if errors:
            # Get current operation to append errors
            operation = self.get_by_id(operation_id)
            if operation:
                current_errors = operation.errors or []
                current_errors.extend(errors)
                updates["errors"] = current_errors

        self.update(operation_id, updates)
        return True

    def mark_completed(self, operation_id: str, results: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Mark operation as completed."""
        from datetime import datetime, timezone

        updates = {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc)
        }

        if results:
            updates["results"] = results

        self.update(operation_id, updates)
        return True

    def mark_failed(self, operation_id: str, errors: List[str]) -> bool:
        """Mark operation as failed."""
        from datetime import datetime, timezone

        updates = {
            "status": "failed",
            "completed_at": datetime.now(timezone.utc),
            "errors": errors
        }

        self.update(operation_id, updates)
        return True
