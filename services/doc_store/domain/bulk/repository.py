"""Bulk operations repository for data access operations.

Handles bulk operation data and batch processing.
"""
import asyncio
import json
import uuid
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from ...core.repository import BaseRepository
from ...db.queries import execute_query
from ...core.entities import BulkOperation, BulkDocumentItem


class BulkOperationsRepository(BaseRepository[BulkOperation]):
    """Repository for bulk operation data access."""

    def __init__(self):
        super().__init__("bulk_operations")

    def _row_to_entity(self, row: Dict[str, Any]) -> BulkOperation:
        """Convert database row to BulkOperation entity."""
        return BulkOperation(
            operation_id=row['operation_id'],
            operation_type=row['operation_type'],
            status=row['status'],
            total_items=row['total_items'],
            processed_items=row['processed_items'],
            successful_items=row['successful_items'],
            failed_items=row['failed_items'],
            errors=json.loads(row['errors'] or '[]'),
            metadata=json.loads(row['metadata'] or '{}'),
            created_at=row['created_at'],
            completed_at=row.get('completed_at'),
            results=json.loads(row['results'] or '[]')
        )

    def _entity_to_row(self, entity: BulkOperation) -> Dict[str, Any]:
        """Convert BulkOperation entity to database row."""
        return {
            'operation_id': entity.operation_id,
            'operation_type': entity.operation_type,
            'status': entity.status,
            'total_items': entity.total_items,
            'processed_items': entity.processed_items,
            'successful_items': entity.successful_items,
            'failed_items': entity.failed_items,
            'errors': json.dumps(entity.errors),
            'metadata': json.dumps(entity.metadata),
            'results': json.dumps(entity.results),
            'created_at': entity.created_at.isoformat(),
            'completed_at': entity.completed_at.isoformat() if entity.completed_at else None
        }

    def update_operation_progress(self, operation_id: str, processed: int, successful: int,
                                failed: int, errors: List[Dict[str, Any]] = None) -> None:
        """Update operation progress."""
        update_data = {
            'processed_items': processed,
            'successful_items': successful,
            'failed_items': failed
        }

        if errors:
            # Get current errors and append new ones
            current_op = self.get_by_id(operation_id)
            if current_op:
                all_errors = current_op.errors + errors
                update_data['errors'] = json.dumps(all_errors)

        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [operation_id]

        execute_query(
            f"UPDATE {self.table_name} SET {set_clause} WHERE operation_id = ?",
            values
        )

    def complete_operation(self, operation_id: str, results: List[Dict[str, Any]] = None) -> None:
        """Mark operation as completed."""
        update_data = {'status': 'completed'}
        if results:
            update_data['results'] = json.dumps(results)

        # This would need to be implemented with proper timestamp handling
        # For now, we'll use a simple approach
        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [operation_id]

        execute_query(
            f"UPDATE {self.table_name} SET {set_clause} WHERE operation_id = ?",
            values
        )

    def fail_operation(self, operation_id: str, errors: List[Dict[str, Any]]) -> None:
        """Mark operation as failed."""
        execute_query(
            f"UPDATE {self.table_name} SET status = ?, errors = ? WHERE operation_id = ?",
            ('failed', json.dumps(errors), operation_id)
        )

    def get_active_operations(self) -> List[BulkOperation]:
        """Get operations that are currently active (pending or processing)."""
        rows = execute_query(
            f"SELECT * FROM {self.table_name} WHERE status IN ('pending', 'processing') ORDER BY created_at ASC",
            fetch_all=True
        )
        return [self._row_to_entity(row) for row in rows]

    def cancel_operation(self, operation_id: str) -> None:
        """Cancel a pending or processing operation."""
        execute_query(
            f"UPDATE {self.table_name} SET status = 'cancelled' WHERE operation_id = ? AND status IN ('pending', 'processing')",
            (operation_id,)
        )

    def get_operations_by_status(self, status: str, limit: int = 50) -> List[BulkOperation]:
        """Get operations by status."""
        rows = execute_query(
            f"SELECT * FROM {self.table_name} WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
            fetch_all=True
        )
        return [self._row_to_entity(row) for row in rows]

    def cleanup_old_operations(self, days_to_keep: int = 30) -> int:
        """Clean up old completed operations."""
        # This would need proper date handling - simplified for now
        result = execute_query(
            f"DELETE FROM {self.table_name} WHERE status IN ('completed', 'failed', 'cancelled') AND created_at < date('now', '-{days_to_keep} days')",
            fetch_one=True
        )
        return result['changes'] if result else 0
