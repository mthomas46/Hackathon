# ============================================================================
# BULK OPERATIONS HANDLERS MODULE
# ============================================================================
"""
Bulk operations handlers for Doc Store service.

Provides endpoints for batch processing operations including:
- Bulk document creation and management
- Batch search operations
- Bulk tagging operations
- Progress tracking and status monitoring
"""

from typing import Dict, Any, List, Optional
from .bulk_operations import bulk_processor, BulkDocumentItem
from .shared_utils import (
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .models import (
    BulkDocumentCreateRequest,
    BulkSearchRequest,
    BulkTagRequest,
    BulkOperationStatus
)


class BulkHandlers:
    """Handles bulk operations."""

    @staticmethod
    async def handle_bulk_create_documents(req: BulkDocumentCreateRequest) -> Dict[str, Any]:
        """Create multiple documents in a bulk operation."""
        try:
            # Convert request items to BulkDocumentItem objects
            documents = [
                BulkDocumentItem(
                    id=item.id,
                    content=item.content,
                    metadata=item.metadata,
                    correlation_id=item.correlation_id
                ) for item in req.documents
            ]

            # Create bulk operation
            operation_id = bulk_processor.create_operation(
                "create_documents",
                documents,
                {"total_size": len(documents)}
            )

            # Start processing (fire and forget for async processing)
            # In a real implementation, this would be handled by a background task queue
            import asyncio
            asyncio.create_task(bulk_processor.process_bulk_create(operation_id, documents))

            context = build_doc_store_context("bulk_create_started", operation_id=operation_id)
            return create_doc_store_success_response("bulk create operation started", {
                "operation_id": operation_id,
                "total_documents": len(documents),
                "status": "processing"
            }, **context)

        except Exception as e:
            context = build_doc_store_context("bulk_create_failed")
            return handle_doc_store_error("start bulk document creation", e, **context)

    @staticmethod
    async def handle_bulk_search(req: BulkSearchRequest) -> Dict[str, Any]:
        """Perform multiple search operations in bulk."""
        try:
            # Create bulk operation
            operation_id = bulk_processor.create_operation(
                "bulk_search",
                req.queries,
                {"total_queries": len(req.queries)}
            )

            # Start processing
            import asyncio
            asyncio.create_task(bulk_processor.process_bulk_search(operation_id, req.queries))

            context = build_doc_store_context("bulk_search_started", operation_id=operation_id)
            return create_doc_store_success_response("bulk search operation started", {
                "operation_id": operation_id,
                "total_queries": len(req.queries),
                "status": "processing"
            }, **context)

        except Exception as e:
            context = build_doc_store_context("bulk_search_failed")
            return handle_doc_store_error("start bulk search", e, **context)

    @staticmethod
    async def handle_bulk_tag_documents(req: BulkTagRequest) -> Dict[str, Any]:
        """Tag multiple documents in bulk."""
        try:
            # Create bulk operation
            operation_id = bulk_processor.create_operation(
                "bulk_tag",
                req.document_ids,
                {"total_documents": len(req.document_ids)}
            )

            # Start processing
            import asyncio
            asyncio.create_task(bulk_processor.process_bulk_tag(operation_id, req.document_ids))

            context = build_doc_store_context("bulk_tag_started", operation_id=operation_id)
            return create_doc_store_success_response("bulk tagging operation started", {
                "operation_id": operation_id,
                "total_documents": len(req.document_ids),
                "status": "processing"
            }, **context)

        except Exception as e:
            context = build_doc_store_context("bulk_tag_failed")
            return handle_doc_store_error("start bulk tagging", e, **context)

    @staticmethod
    async def handle_get_bulk_operation_status(operation_id: str) -> Dict[str, Any]:
        """Get the status of a bulk operation."""
        try:
            status = bulk_processor.get_operation_status(operation_id)

            if not status:
                return handle_doc_store_error("get bulk operation status", f"Operation {operation_id} not found")

            context = build_doc_store_context("bulk_status_retrieved", operation_id=operation_id)
            return create_doc_store_success_response("bulk operation status retrieved", status, **context)

        except Exception as e:
            context = build_doc_store_context("bulk_status_failed", operation_id=operation_id)
            return handle_doc_store_error("get bulk operation status", e, **context)

    @staticmethod
    async def handle_list_bulk_operations(status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """List bulk operations with optional status filtering."""
        try:
            # Get all operations and filter by status
            operations = []
            for op_id, operation in bulk_processor.operations.items():
                if not status or operation.status == status:
                    operations.append(bulk_processor.get_operation_status(op_id))

            # Sort by creation time (most recent first)
            operations.sort(key=lambda x: x["created_at"], reverse=True)
            operations = operations[:limit]

            context = build_doc_store_context("bulk_operations_listed", count=len(operations))
            return create_doc_store_success_response("bulk operations listed", {
                "operations": operations,
                "total": len(operations),
                "status_filter": status
            }, **context)

        except Exception as e:
            context = build_doc_store_context("bulk_operations_list_failed")
            return handle_doc_store_error("list bulk operations", e, **context)

    @staticmethod
    async def handle_cancel_bulk_operation(operation_id: str) -> Dict[str, Any]:
        """Cancel a running bulk operation."""
        try:
            # In a real implementation, this would signal the operation to stop
            # For now, just mark as cancelled if it's still pending/processing
            operation = bulk_processor.operations.get(operation_id)
            if not operation:
                return handle_doc_store_error("cancel bulk operation", f"Operation {operation_id} not found")

            if operation.status in ["pending", "processing"]:
                operation.status = "cancelled"
                operation.completed_at = bulk_processor.operations[operation_id].created_at.__class__.now(bulk_processor.operations[operation_id].created_at.tzinfo)  # Use utc_now equivalent

                context = build_doc_store_context("bulk_operation_cancelled", operation_id=operation_id)
                return create_doc_store_success_response("bulk operation cancelled", {
                    "operation_id": operation_id,
                    "status": "cancelled"
                }, **context)
            else:
                return handle_doc_store_error("cancel bulk operation", f"Operation {operation_id} cannot be cancelled (status: {operation.status})")

        except Exception as e:
            context = build_doc_store_context("bulk_operation_cancel_failed", operation_id=operation_id)
            return handle_doc_store_error("cancel bulk operation", e, **context)
