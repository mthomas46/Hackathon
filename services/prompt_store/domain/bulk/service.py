"""Bulk operations service implementation.

Handles business logic for bulk operations on prompts.
"""

import asyncio
from typing import List, Optional, Dict, Any, Callable
from services.prompt_store.core.service import BaseService
from services.prompt_store.core.entities import BulkOperation
from services.prompt_store.domain.bulk.repository import BulkOperationRepository
from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.shared.utilities import generate_id, utc_now


class BulkOperationService(BaseService[BulkOperation]):
    """Service for bulk operations business logic."""

    def __init__(self):
        super().__init__(BulkOperationRepository())
        self.prompt_service = PromptService()

    def create_entity(self, data: Dict[str, Any], entity_id: Optional[str] = None) -> BulkOperation:
        """Create a new bulk operation with validation."""
        # Validate required fields
        required_fields = ["operation_type", "created_by"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Validate operation type
        valid_operations = ["create_prompts", "update_prompts", "delete_prompts", "tag_prompts"]
        if data["operation_type"] not in valid_operations:
            raise ValueError(f"Invalid operation type. Must be one of: {', '.join(valid_operations)}")

        # Create bulk operation entity
        operation = BulkOperation(
            id=entity_id or generate_id(),
            operation_type=data["operation_type"],
            status="pending",
            total_items=data.get("total_items", 0),
            metadata=data.get("metadata", {}),
            created_by=data["created_by"]
        )

        # Save to database
        saved_operation = self.repository.save(operation)

        # Start processing asynchronously
        if data.get("auto_start", True):
            # Only create task if event loop is running (for tests and async contexts)
            try:
                asyncio.create_task(self._process_operation_async(saved_operation.id))
            except RuntimeError:
                # No event loop running, skip async processing
                pass

        return saved_operation

    def create_bulk_create_operation(self, prompts_data: List[Dict[str, Any]],
                                   created_by: str) -> BulkOperation:
        """Create a bulk create prompts operation."""
        return self.create_entity({
            "operation_type": "create_prompts",
            "total_items": len(prompts_data),
            "metadata": {"prompts_data": prompts_data},
            "created_by": created_by
        })

    def create_bulk_update_operation(self, updates: List[Dict[str, Any]],
                                   created_by: str) -> BulkOperation:
        """Create a bulk update prompts operation."""
        return self.create_entity({
            "operation_type": "update_prompts",
            "total_items": len(updates),
            "metadata": {"updates": updates},
            "created_by": created_by
        })

    def create_bulk_delete_operation(self, prompt_ids: List[str],
                                   created_by: str) -> BulkOperation:
        """Create a bulk delete prompts operation."""
        return self.create_entity({
            "operation_type": "delete_prompts",
            "total_items": len(prompt_ids),
            "metadata": {"prompt_ids": prompt_ids},
            "created_by": created_by
        })

    def create_bulk_tag_operation(self, prompt_ids: List[str],
                                tags_to_add: Optional[List[str]] = None,
                                tags_to_remove: Optional[List[str]] = None,
                                created_by: str = "system") -> BulkOperation:
        """Create a bulk tag operation."""
        return self.create_entity({
            "operation_type": "tag_prompts",
            "total_items": len(prompt_ids),
            "metadata": {
                "prompt_ids": prompt_ids,
                "tags_to_add": tags_to_add or [],
                "tags_to_remove": tags_to_remove or []
            },
            "created_by": created_by
        })

    def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get detailed status of a bulk operation."""
        operation = self.get_entity(operation_id)
        if not operation:
            raise ValueError(f"Bulk operation {operation_id} not found")

        # Calculate progress percentage
        progress_percentage = 0.0
        if operation.total_items > 0:
            progress_percentage = (operation.processed_items / operation.total_items) * 100

        # Estimate time remaining (simple implementation)
        time_estimate = self._estimate_time_remaining(operation)

        return {
            "operation": operation.to_dict(),
            "progress_percentage": progress_percentage,
            "time_estimate_seconds": time_estimate,
            "is_complete": operation.status in ["completed", "failed"],
            "has_errors": len(operation.errors or []) > 0
        }

    def cancel_operation(self, operation_id: str) -> BulkOperation:
        """Cancel a pending or processing bulk operation."""
        operation = self.get_entity(operation_id)
        if not operation:
            raise ValueError(f"Bulk operation {operation_id} not found")

        if operation.status not in ["pending", "processing"]:
            raise ValueError(f"Cannot cancel operation with status: {operation.status}")

        return self.update_entity(operation_id, {"status": "cancelled"})

    def retry_operation(self, operation_id: str) -> BulkOperation:
        """Retry a failed bulk operation."""
        operation = self.get_entity(operation_id)
        if not operation:
            raise ValueError(f"Bulk operation {operation_id} not found")

        if operation.status != "failed":
            raise ValueError(f"Can only retry failed operations. Current status: {operation.status}")

        # Reset progress counters
        updates = {
            "status": "pending",
            "processed_items": 0,
            "successful_items": 0,
            "failed_items": 0,
            "errors": [],
            "completed_at": None
        }

        updated_operation = self.update_entity(operation_id, updates)

        # Restart processing
        try:
            asyncio.create_task(self._process_operation_async(operation_id))
        except RuntimeError:
            # No event loop running, skip async processing
            pass

        return updated_operation

    async def _process_operation_async(self, operation_id: str) -> None:
        """Process a bulk operation asynchronously."""
        try:
            operation = self.get_entity(operation_id)
            if not operation or operation.status != "pending":
                return

            # Update status to processing
            self.update_entity(operation_id, {"status": "processing"})

            # Process based on operation type
            if operation.operation_type == "create_prompts":
                await self._process_bulk_create(operation)
            elif operation.operation_type == "update_prompts":
                await self._process_bulk_update(operation)
            elif operation.operation_type == "delete_prompts":
                await self._process_bulk_delete(operation)
            elif operation.operation_type == "tag_prompts":
                await self._process_bulk_tag(operation)

        except Exception as e:
            # Mark operation as failed
            self.repository.mark_failed(operation_id, [str(e)])
            print(f"Bulk operation {operation_id} failed: {e}")

    async def _process_bulk_create(self, operation: BulkOperation) -> None:
        """Process bulk create operation."""
        prompts_data = operation.metadata.get("prompts_data", [])
        results = []
        errors = []

        for i, prompt_data in enumerate(prompts_data):
            try:
                # Create prompt
                created_prompt = self.prompt_service.create_entity(prompt_data)
                results.append({
                    "index": i,
                    "prompt_id": created_prompt.id,
                    "status": "success"
                })

                # Update progress
                await self._update_progress_async(operation.id, i + 1, len(results), len(errors), errors)

            except Exception as e:
                error_msg = f"Failed to create prompt at index {i}: {str(e)}"
                errors.append(error_msg)
                results.append({
                    "index": i,
                    "status": "failed",
                    "error": str(e)
                })

                await self._update_progress_async(operation.id, i + 1, len(results) - len(errors), len(errors), errors)

        # Mark as completed
        if errors:
            self.repository.mark_failed(operation.id, errors)
        else:
            self.repository.mark_completed(operation.id, results)

    async def _process_bulk_update(self, operation: BulkOperation) -> None:
        """Process bulk update operation."""
        updates = operation.metadata.get("updates", [])
        results = []
        errors = []

        for i, update_data in enumerate(updates):
            try:
                prompt_id = update_data.pop("prompt_id")
                updated_prompt = self.prompt_service.update_entity(prompt_id, update_data)
                results.append({
                    "prompt_id": prompt_id,
                    "status": "success"
                })

                await self._update_progress_async(operation.id, i + 1, len(results), len(errors), errors)

            except Exception as e:
                error_msg = f"Failed to update prompt: {str(e)}"
                errors.append(error_msg)
                results.append({
                    "status": "failed",
                    "error": str(e)
                })

                await self._update_progress_async(operation.id, i + 1, len(results) - len(errors), len(errors), errors)

        # Mark as completed
        if errors:
            self.repository.mark_failed(operation.id, errors)
        else:
            self.repository.mark_completed(operation.id, results)

    async def _process_bulk_delete(self, operation: BulkOperation) -> None:
        """Process bulk delete operation."""
        prompt_ids = operation.metadata.get("prompt_ids", [])
        results = []
        errors = []

        for i, prompt_id in enumerate(prompt_ids):
            try:
                deleted = self.prompt_service.delete_entity(prompt_id)
                results.append({
                    "prompt_id": prompt_id,
                    "status": "success" if deleted else "not_found"
                })

                await self._update_progress_async(operation.id, i + 1, len(results), len(errors), errors)

            except Exception as e:
                error_msg = f"Failed to delete prompt {prompt_id}: {str(e)}"
                errors.append(error_msg)
                results.append({
                    "prompt_id": prompt_id,
                    "status": "failed",
                    "error": str(e)
                })

                await self._update_progress_async(operation.id, i + 1, len(results) - len(errors), len(errors), errors)

        # Mark as completed
        if errors:
            self.repository.mark_failed(operation.id, errors)
        else:
            self.repository.mark_completed(operation.id, results)

    async def _process_bulk_tag(self, operation: BulkOperation) -> None:
        """Process bulk tag operation."""
        prompt_ids = operation.metadata.get("prompt_ids", [])
        tags_to_add = operation.metadata.get("tags_to_add", [])
        tags_to_remove = operation.metadata.get("tags_to_remove", [])

        updated_count = self.prompt_service.bulk_update_tags(
            prompt_ids, tags_to_add, tags_to_remove
        )

        results = [{
            "operation": "bulk_tag_update",
            "updated_count": updated_count,
            "total_requested": len(prompt_ids),
            "tags_added": tags_to_add,
            "tags_removed": tags_to_remove
        }]

        self.repository.mark_completed(operation.id, results)

    async def _update_progress_async(self, operation_id: str, processed: int,
                                   successful: int, failed: int, errors: List[str]) -> None:
        """Update operation progress asynchronously."""
        try:
            self.repository.update_progress(operation_id, processed, successful, failed, errors)
        except Exception as e:
            print(f"Failed to update progress for operation {operation_id}: {e}")

    def _estimate_time_remaining(self, operation: BulkOperation) -> Optional[float]:
        """Estimate time remaining for operation completion (simple implementation)."""
        if operation.status not in ["processing"] or operation.processed_items == 0:
            return None

        # Simple linear extrapolation
        elapsed_time = (utc_now() - operation.created_at).total_seconds()
        avg_time_per_item = elapsed_time / operation.processed_items
        remaining_items = operation.total_items - operation.processed_items

        return avg_time_per_item * remaining_items

    def get_pending_operations(self) -> List[BulkOperation]:
        """Get all pending bulk operations."""
        return self.repository.get_pending_operations()

    def cleanup_old_operations(self, days_old: int = 30) -> int:
        """Clean up old completed/failed operations."""
        # This would delete operations older than specified days
        # Implementation depends on specific requirements
        return 0
