# ============================================================================
# BULK OPERATIONS MODULE
# ============================================================================
"""
Bulk operations and batch processing for Doc Store service.

Provides high-performance batch operations for document management including:
- Batch document creation, updates, and deletion
- Batch search and retrieval operations
- Batch tagging and relationship operations
- Progress tracking and error handling
- Queue-based asynchronous processing
"""

import json
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from services.shared.utilities import utc_now
from .shared_utils import execute_db_query, build_doc_store_context, create_doc_store_success_response, handle_doc_store_error
from .caching import docstore_cache


@dataclass
class BulkOperation:
    """Represents a bulk operation with progress tracking."""
    operation_id: str
    operation_type: str
    total_items: int
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BulkDocumentItem:
    """Represents a document in a bulk operation."""
    id: Optional[str]
    content: str
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class BulkProcessor:
    """Processes bulk operations with progress tracking and error handling."""

    def __init__(self, max_concurrent: int = 10, batch_size: int = 100):
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.operations: Dict[str, BulkOperation] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)

    def create_operation(self, operation_type: str, items: List[Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new bulk operation."""
        operation_id = f"bulk_{operation_type}_{int(time.time())}_{hash(str(items)) % 10000}"
        operation = BulkOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            total_items=len(items),
            metadata=metadata or {}
        )
        self.operations[operation_id] = operation
        return operation_id

    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a bulk operation."""
        operation = self.operations.get(operation_id)
        if not operation:
            return None

        return {
            "operation_id": operation.operation_id,
            "operation_type": operation.operation_type,
            "status": operation.status,
            "progress": {
                "total": operation.total_items,
                "processed": operation.processed_items,
                "successful": operation.successful_items,
                "failed": operation.failed_items,
                "percentage": (operation.processed_items / operation.total_items * 100) if operation.total_items > 0 else 0
            },
            "created_at": operation.created_at.isoformat(),
            "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
            "errors": operation.errors[:10],  # Limit error details
            "metadata": operation.metadata
        }

    async def process_bulk_create(self, operation_id: str, documents: List[BulkDocumentItem]) -> Dict[str, Any]:
        """Process bulk document creation."""
        operation = self.operations.get(operation_id)
        if not operation:
            return {"error": "Operation not found"}

        operation.status = "processing"

        try:
            # Process in batches
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def process_batch(batch: List[BulkDocumentItem]) -> List[Dict[str, Any]]:
                tasks = []
                for doc in batch:
                    task = asyncio.create_task(self._create_single_document(doc, semaphore))
                    tasks.append(task)
                return await asyncio.gather(*tasks, return_exceptions=True)

            results = []
            for i in range(0, len(documents), self.batch_size):
                batch = documents[i:i + self.batch_size]
                batch_results = await process_batch(batch)
                results.extend(batch_results)

            # Process results
            successful = 0
            failed = 0
            errors = []

            for result in results:
                operation.processed_items += 1

                if isinstance(result, Exception):
                    failed += 1
                    errors.append({"error": str(result)})
                elif isinstance(result, dict) and "error" in result:
                    failed += 1
                    errors.append(result)
                else:
                    successful += 1
                    operation.results.append(result)

            operation.successful_items = successful
            operation.failed_items = failed
            operation.errors = errors
            operation.status = "completed" if failed == 0 else "completed_with_errors"
            operation.completed_at = utc_now()

            # Invalidate relevant caches
            await docstore_cache.invalidate(tags=["documents", "analytics"])

            return {
                "operation_id": operation_id,
                "status": operation.status,
                "processed": operation.processed_items,
                "successful": successful,
                "failed": failed,
                "results": operation.results[:100],  # Limit results
                "errors": errors[:50]  # Limit errors
            }

        except Exception as e:
            operation.status = "failed"
            operation.completed_at = utc_now()
            operation.errors.append({"error": str(e)})
            return {"error": str(e)}

    async def _create_single_document(self, doc: BulkDocumentItem, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Create a single document within a bulk operation."""
        async with semaphore:
            try:
                # Import here to avoid circular imports
                from .document_handlers import DocumentHandlers
                from .models import PutDocumentRequest

                # Create request object
                request = PutDocumentRequest(
                    id=doc.id,
                    content=doc.content,
                    metadata=doc.metadata or {},
                    correlation_id=doc.correlation_id
                )

                # Create document using existing handler
                handler = DocumentHandlers()
                result = await handler.handle_put_document(request)

                if isinstance(result, dict) and "success" in result and result["success"]:
                    return {"id": result.get("data", {}).get("id"), "status": "created"}
                else:
                    return {"error": result.get("message", "Unknown error")}

            except Exception as e:
                return {"error": str(e)}

    async def process_bulk_search(self, operation_id: str, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process bulk search operations."""
        operation = self.operations.get(operation_id)
        if not operation:
            return {"error": "Operation not found"}

        operation.status = "processing"

        try:
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def process_search(query: Dict[str, Any]) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        from .search_handlers import SearchHandlers

                        # Use advanced search if filters are provided, otherwise basic search
                        if any(key in query for key in ['content_type', 'source_type', 'language', 'tags', 'date_from', 'date_to', 'has_analysis']):
                            result = await SearchHandlers.handle_advanced_search(
                                q=query.get('q'),
                                content_type=query.get('content_type'),
                                source_type=query.get('source_type'),
                                language=query.get('language'),
                                tags=query.get('tags'),
                                date_from=query.get('date_from'),
                                date_to=query.get('date_to'),
                                has_analysis=query.get('has_analysis'),
                                limit=query.get('limit', 20),
                                offset=query.get('offset', 0)
                            )
                        else:
                            result = await SearchHandlers.handle_search(query.get('q', ''), query.get('limit', 20))

                        return {"query": query, "results": result}
                    except Exception as e:
                        return {"query": query, "error": str(e)}

            # Process all queries concurrently
            tasks = [process_search(query) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful = 0
            failed = 0
            search_results = []

            for result in results:
                operation.processed_items += 1

                if isinstance(result, Exception):
                    failed += 1
                    operation.errors.append({"error": str(result)})
                elif isinstance(result, dict) and "error" in result:
                    failed += 1
                    operation.errors.append(result)
                else:
                    successful += 1
                    search_results.append(result)

            operation.successful_items = successful
            operation.failed_items = failed
            operation.status = "completed" if failed == 0 else "completed_with_errors"
            operation.completed_at = utc_now()
            operation.results = search_results

            return {
                "operation_id": operation_id,
                "status": operation.status,
                "processed": operation.processed_items,
                "successful": successful,
                "failed": failed,
                "results": search_results[:50]  # Limit results
            }

        except Exception as e:
            operation.status = "failed"
            operation.completed_at = utc_now()
            operation.errors.append({"error": str(e)})
            return {"error": str(e)}

    async def process_bulk_tag(self, operation_id: str, document_ids: List[str]) -> Dict[str, Any]:
        """Process bulk tagging operations."""
        operation = self.operations.get(operation_id)
        if not operation:
            return {"error": "Operation not found"}

        operation.status = "processing"

        try:
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def tag_document(doc_id: str) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        from .tagging_handlers import TaggingHandlers
                        result = await TaggingHandlers.handle_tag_document(doc_id)
                        return {"document_id": doc_id, "result": result}
                    except Exception as e:
                        return {"document_id": doc_id, "error": str(e)}

            # Process all documents concurrently
            tasks = [tag_document(doc_id) for doc_id in document_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful = 0
            failed = 0
            tagging_results = []

            for result in results:
                operation.processed_items += 1

                if isinstance(result, Exception):
                    failed += 1
                    operation.errors.append({"error": str(result)})
                elif isinstance(result, dict) and "error" in result:
                    failed += 1
                    operation.errors.append(result)
                else:
                    successful += 1
                    tagging_results.append(result)

            operation.successful_items = successful
            operation.failed_items = failed
            operation.status = "completed" if failed == 0 else "completed_with_errors"
            operation.completed_at = utc_now()
            operation.results = tagging_results

            # Invalidate tag caches
            await docstore_cache.invalidate(tags=["tags"])

            return {
                "operation_id": operation_id,
                "status": operation.status,
                "processed": operation.processed_items,
                "successful": successful,
                "failed": failed,
                "results": tagging_results[:50]  # Limit results
            }

        except Exception as e:
            operation.status = "failed"
            operation.completed_at = utc_now()
            operation.errors.append({"error": str(e)})
            return {"error": str(e)}


# Global bulk processor instance
bulk_processor = BulkProcessor()
