"""Bulk operations handlers for API endpoints.

Handles bulk operation-related HTTP requests and responses.
"""

import time
from typing import Any, Dict, List

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities.logging_client import get_log_collector_client

from ...core.entities import BulkDocumentItem
from ...core.handler import BaseHandler
from .service import BulkOperationsService

# Global logger client instance
logger_client = None


async def get_logger_client():
    """Get or initialize the logger client."""
    global logger_client
    if logger_client is None:
        try:
            logger_client = await get_log_collector_client(ServiceNames.DOC_STORE)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


class BulkOperationsHandlers(BaseHandler):
    """Handlers for bulk operations API endpoints."""

    def __init__(self):
        super().__init__(BulkOperationsService())

    async def handle_bulk_create_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle bulk document creation."""
        start_time = time.time()
        request_id = f"bulk_doc_create_{int(time.time() * 1000)}"
        logger = await get_logger_client()

        try:
            # Validate request data
            if not documents:
                response_time = time.time() - start_time

                # Log empty bulk operation
                if logger:
                    await logger.log_business_event(
                        "bulk_documents_creation_rejected",
                        {
                            "request_id": request_id,
                            "operation": "bulk_document_operations",
                            "operation_type": "bulk_create_documents",
                            "response_time_seconds": response_time,
                            "error_type": "empty_request",
                            "documents_count": 0,
                            "validation_failed": True,
                        },
                    )

                return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("No documents provided")))

            documents_count = len(documents)

            # Log bulk creation start
            if logger:
                await logger.log_business_event(
                    "bulk_documents_creation_started",
                    {
                        "request_id": request_id,
                        "operation": "bulk_document_operations",
                        "operation_type": "bulk_create_documents",
                        "documents_count": documents_count,
                        "batch_processing_required": True,
                        "transaction_scope": "bulk_operation",
                        "data_ingestion_initiated": True,
                    },
                )

                await logger.log_info(
                    "Initiating bulk document creation",
                    {
                        "request_id": request_id,
                        "documents_count": documents_count,
                        "batch_size": documents_count,
                        "operation_scope": "bulk_document_ingestion",
                        "parallel_processing_enabled": True,
                        "transaction_management_activated": True,
                    },
                )

            # Convert to BulkDocumentItem objects
            bulk_items = []
            for doc_data in documents:
                # Handle both dict and Pydantic model inputs
                if hasattr(doc_data, "model_dump"):
                    # Pydantic model
                    doc_dict = doc_data.model_dump()
                else:
                    # Dict
                    doc_dict = doc_data

                item = BulkDocumentItem(
                    id=doc_dict.get("id"),
                    content=doc_dict.get("content", ""),
                    metadata=doc_dict.get("metadata"),
                    correlation_id=doc_dict.get("correlation_id"),
                )
                bulk_items.append(item)

            # Create bulk operation
            operation = self.service.create_bulk_operation("create_documents", bulk_items)

            response_time = time.time() - start_time
            operation_id = operation.id if hasattr(operation, "id") else str(operation)

            # Log successful bulk creation
            if logger:
                await logger.log_business_event(
                    "bulk_documents_created",
                    {
                        "request_id": request_id,
                        "operation_id": operation_id,
                        "operation": "bulk_document_operations",
                        "response_time_seconds": response_time,
                        "success": True,
                        "documents_count": documents_count,
                        "bulk_operation_type": "create_documents",
                        "batch_processing_completed": True,
                        "documents_ingested": documents_count,
                    },
                )

                await logger.log_performance_metric(
                    "bulk_document_creation",
                    response_time,
                    {
                        "request_id": request_id,
                        "operation_id": operation_id,
                        "documents_processed": documents_count,
                        "batch_success": True,
                        "bulk_operation_time": response_time,
                    },
                )

            return await self._handle_request(lambda: operation.to_dict())

        except Exception as e:
            error_time = time.time() - start_time

            # Log bulk creation failure
            if logger:
                await logger.log_error(
                    f"Bulk document creation failed: {str(e)}",
                    {
                        "request_id": request_id,
                        "operation": "bulk_document_operations",
                        "operation_type": "bulk_create_documents",
                        "documents_count": len(documents) if "documents" in locals() else 0,
                        "error_type": type(e).__name__,
                        "response_time_seconds": error_time,
                        "bulk_creation_failed": True,
                    },
                    error=e,
                )

                await logger.log_business_event(
                    "bulk_documents_creation_failed",
                    {
                        "request_id": request_id,
                        "operation": "bulk_document_operations",
                        "operation_type": "bulk_create_documents",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "response_time_seconds": error_time,
                    },
                )

            return await self._handle_request(lambda: operation.to_dict())

    async def handle_bulk_search(self, queries: List[str]) -> Dict[str, Any]:
        """Handle bulk search operation."""
        if not queries:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("No queries provided")))

        operation = self.service.create_bulk_operation("search_documents", queries)

        return await self._handle_request(lambda: operation.to_dict())

    async def handle_bulk_tag_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """Handle bulk tagging operation."""
        if not document_ids:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("No document IDs provided")))

        operation = self.service.create_bulk_operation("tag_documents", document_ids)

        return await self._handle_request(lambda: operation.to_dict())

    async def handle_get_bulk_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Handle operation status request."""
        operation = self.service.get_operation_status(operation_id)
        if not operation:
            return await self._handle_request(lambda: (_ for _ in ()).throw(ValueError("Operation not found")))

        return await self._handle_request(lambda: operation.to_dict())

    async def handle_list_bulk_operations(self, status: str = None, limit: int = 50) -> Dict[str, Any]:
        """Handle list operations request."""
        result = self.service.list_operations(status, limit)

        return await self._handle_request(lambda: result)

    async def handle_cancel_bulk_operation(self, operation_id: str) -> Dict[str, Any]:
        """Handle operation cancellation."""
        cancelled = self.service.cancel_operation(operation_id)

        if not cancelled:
            return await self._handle_request(
                lambda: (_ for _ in ()).throw(ValueError("Operation could not be cancelled"))
            )

        return await self._handle_request(lambda: {"operation_id": operation_id, "cancelled": True})

    async def handle_cleanup_bulk_operations(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Handle cleanup of old operations."""
        result = self.service.cleanup_old_operations(days_to_keep)

        return await self._handle_request(lambda: result)
