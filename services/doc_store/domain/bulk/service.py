"""Bulk operations service for business logic operations.

Handles bulk processing and batch operations business rules.
"""
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from ...core.service import BaseService
from ...core.entities import BulkOperation, BulkDocumentItem
from .repository import BulkOperationsRepository


class BulkOperationsService(BaseService[BulkOperation]):
    """Service for bulk operations business logic."""

    def __init__(self):
        super().__init__(BulkOperationsRepository())
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _validate_entity(self, entity: BulkOperation) -> None:
        """Validate bulk operation."""
        if not entity.operation_type:
            raise ValueError("Operation type is required")

        if entity.total_items <= 0:
            raise ValueError("Total items must be positive")

        valid_types = ['create_documents', 'search_documents', 'tag_documents', 'delete_documents']
        if entity.operation_type not in valid_types:
            raise ValueError(f"Invalid operation type: {entity.operation_type}")

    def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> BulkOperation:
        """Create bulk operation from data."""
        return BulkOperation(
            operation_id=entity_id,
            operation_type=data['operation_type'],
            total_items=data.get('total_items', 0),
            metadata=data.get('metadata', {})
        )

    def create_bulk_operation(self, operation_type: str, items: List[Any],
                            metadata: Optional[Dict[str, Any]] = None) -> BulkOperation:
        """Create a new bulk operation."""
        data = {
            'operation_type': operation_type,
            'total_items': len(items),
            'metadata': metadata or {}
        }

        operation = self.create_entity(data)

        # Start processing asynchronously
        asyncio.create_task(self._process_operation_async(operation.operation_id, items))

        return operation

    async def _process_operation_async(self, operation_id: str, items: List[Any]) -> None:
        """Process operation asynchronously."""
        try:
            # Update status to processing
            operation = self.repository.get_by_id(operation_id)
            if not operation:
                return

            operation.status = 'processing'
            self.repository.save(operation)

            # Process items based on operation type
            if operation.operation_type == 'create_documents':
                await self._process_document_creation(operation_id, items)
            elif operation.operation_type == 'search_documents':
                await self._process_document_search(operation_id, items)
            elif operation.operation_type == 'tag_documents':
                await self._process_document_tagging(operation_id, items)
            elif operation.operation_type == 'delete_documents':
                await self._process_document_deletion(operation_id, items)

        except Exception as e:
            # Mark operation as failed
            self.repository.fail_operation(operation_id, [{'error': str(e)}])

    async def _process_document_creation(self, operation_id: str, items: List[BulkDocumentItem]) -> None:
        """Process bulk document creation."""
        from ...domain.documents.service import DocumentService
        doc_service = DocumentService()

        successful = 0
        failed = 0
        errors = []

        for i, item in enumerate(items):
            try:
                # Create document
                document = doc_service.create_document(
                    content=item.content,
                    metadata=item.metadata,
                    document_id=item.id,
                    correlation_id=item.correlation_id
                )

                successful += 1

                # Update progress periodically
                if (i + 1) % 10 == 0:
                    self.repository.update_operation_progress(
                        operation_id, i + 1, successful, failed, errors
                    )

            except Exception as e:
                failed += 1
                errors.append({
                    'item_index': i,
                    'item_id': item.id,
                    'error': str(e)
                })

        # Complete operation
        results = {
            'successful': successful,
            'failed': failed,
            'total_processed': len(items)
        }
        self.repository.complete_operation(operation_id, [results])

    async def _process_document_search(self, operation_id: str, queries: List[str]) -> None:
        """Process bulk document search."""
        from ...domain.search.handlers import SearchHandlers
        search_handlers = SearchHandlers()

        successful = 0
        failed = 0
        errors = []
        results = []

        for i, query in enumerate(queries):
            try:
                # Perform search
                search_result = await search_handlers.handle_search_documents(query, limit=50)
                results.append({
                    'query': query,
                    'results': search_result.get('data', {}).get('items', [])
                })
                successful += 1

            except Exception as e:
                failed += 1
                errors.append({
                    'query_index': i,
                    'query': query,
                    'error': str(e)
                })

        # Complete operation
        summary = {
            'queries_processed': len(queries),
            'successful': successful,
            'failed': failed,
            'results': results
        }
        self.repository.complete_operation(operation_id, [summary])

    async def _process_document_tagging(self, operation_id: str, document_ids: List[str]) -> None:
        """Process bulk document tagging."""
        # This would integrate with the tagging domain when it's implemented
        # For now, just mark as completed
        self.repository.complete_operation(operation_id, [{
            'message': 'Bulk tagging not yet implemented',
            'document_ids': document_ids
        }])

    async def _process_document_deletion(self, operation_id: str, document_ids: List[str]) -> None:
        """Process bulk document deletion."""
        from ...domain.documents.service import DocumentService
        doc_service = DocumentService()

        successful = 0
        failed = 0
        errors = []

        for i, doc_id in enumerate(document_ids):
            try:
                doc_service.delete_entity(doc_id)
                successful += 1

            except Exception as e:
                failed += 1
                errors.append({
                    'document_id': doc_id,
                    'error': str(e)
                })

        # Complete operation
        results = {
            'successful': successful,
            'failed': failed,
            'total_processed': len(document_ids)
        }
        self.repository.complete_operation(operation_id, [results])

    def get_operation_status(self, operation_id: str) -> Optional[BulkOperation]:
        """Get operation status."""
        return self.repository.get_by_id(operation_id)

    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a pending or processing operation."""
        operation = self.repository.get_by_id(operation_id)
        if not operation or operation.status not in ['pending', 'processing']:
            return False

        self.repository.cancel_operation(operation_id)
        return True

    def list_operations(self, status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """List bulk operations."""
        if status:
            operations = self.repository.get_operations_by_status(status, limit)
        else:
            operations = self.repository.get_all(limit, 0)

        return {
            "operations": [op.to_dict() for op in operations],
            "total": len(operations),
            "status_filter": status,
            "limit": limit
        }

    def cleanup_old_operations(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old completed operations."""
        deleted_count = self.repository.cleanup_old_operations(days_to_keep)

        return {
            "deleted_operations": deleted_count,
            "days_kept": days_to_keep
        }
