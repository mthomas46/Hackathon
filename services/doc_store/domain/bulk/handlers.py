"""Bulk operations handlers for API endpoints.

Handles bulk operation-related HTTP requests and responses.
"""
from typing import Dict, Any, List
from ...core.handler import BaseHandler
from ...core.entities import BulkDocumentItem
from .service import BulkOperationsService


class BulkOperationsHandlers(BaseHandler):
    """Handlers for bulk operations API endpoints."""

    def __init__(self):
        super().__init__(BulkOperationsService())

    async def handle_bulk_create_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle bulk document creation."""
        # Validate request data
        if not documents:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("No documents provided")))

        # Convert to BulkDocumentItem objects
        bulk_items = []
        for doc_data in documents:
            item = BulkDocumentItem(
                id=doc_data.get('id'),
                content=doc_data.get('content', ''),
                metadata=doc_data.get('metadata'),
                correlation_id=doc_data.get('correlation_id')
            )
            bulk_items.append(item)

        # Create bulk operation
        operation = self.service.create_bulk_operation('create_documents', bulk_items)

        return await self._handle_request(lambda: operation.to_dict())

    async def handle_bulk_search(self, queries: List[str]) -> Dict[str, Any]:
        """Handle bulk search operation."""
        if not queries:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("No queries provided")))

        operation = self.service.create_bulk_operation('search_documents', queries)

        return await self._handle_request(
            lambda: operation.to_dict(),
            operation="bulk_search",
            query_count=len(queries)
        )

    async def handle_bulk_tag_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """Handle bulk tagging operation."""
        if not document_ids:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("No document IDs provided")))

        operation = self.service.create_bulk_operation('tag_documents', document_ids)

        return await self._handle_request(
            lambda: operation.to_dict(),
            operation="bulk_tag_documents",
            document_count=len(document_ids)
        )

    async def handle_get_bulk_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Handle operation status request."""
        operation = self.service.get_operation_status(operation_id)
        if not operation:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Operation not found")))

        return await self._handle_request(
            lambda: operation.to_dict(),
            operation="get_bulk_operation_status",
            operation_id=operation_id
        )

    async def handle_list_bulk_operations(self, status: str = None, limit: int = 50) -> Dict[str, Any]:
        """Handle list operations request."""
        result = self.service.list_operations(status, limit)

        return await self._handle_request(
            lambda: result,
            operation="list_bulk_operations",
            status_filter=status,
            limit=limit
        )

    async def handle_cancel_bulk_operation(self, operation_id: str) -> Dict[str, Any]:
        """Handle operation cancellation."""
        cancelled = self.service.cancel_operation(operation_id)

        if not cancelled:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Operation could not be cancelled")))

        return await self._handle_request(
            lambda: {"operation_id": operation_id, "cancelled": True},
            operation="cancel_bulk_operation",
            operation_id=operation_id
        )

    async def handle_cleanup_bulk_operations(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Handle cleanup of old operations."""
        result = self.service.cleanup_old_operations(days_to_keep)

        return await self._handle_request(
            lambda: result,
            operation="cleanup_bulk_operations",
            days_to_keep=days_to_keep
        )
