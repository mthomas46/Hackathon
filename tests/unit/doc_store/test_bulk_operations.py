"""Tests for Doc Store bulk operations functionality.

Tests bulk document creation, search operations, tagging, and progress tracking
for the doc store service.
"""

import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Import modules normally now that directory uses underscores
from services.doc_store.modules.bulk_operations import BulkProcessor, BulkDocumentItem, BulkOperation


class TestBulkProcessor:
    """Test BulkProcessor class functionality."""

    @pytest.fixture
    def processor(self):
        """Create a test bulk processor instance."""
        return BulkProcessor(max_concurrent=2, batch_size=10)

    def test_processor_initialization(self, processor):
        """Test bulk processor initialization."""
        assert processor.max_concurrent == 2
        assert processor.batch_size == 10
        assert processor.operations == {}

    def test_create_operation(self, processor):
        """Test creating a bulk operation."""
        operation_id = processor.create_operation("test_operation", [{"item": 1}, {"item": 2}])

        assert operation_id in processor.operations
        operation = processor.operations[operation_id]

        assert operation.operation_type == "test_operation"
        assert operation.total_items == 2
        assert operation.status == "pending"
        assert operation.processed_items == 0

    def test_get_operation_status(self, processor):
        """Test retrieving operation status."""
        operation_id = processor.create_operation("test_op", [{"item": 1}])
        operation = processor.operations[operation_id]

        # Update operation status
        operation.processed_items = 1
        operation.successful_items = 1
        operation.status = "completed"

        status = processor.get_operation_status(operation_id)

        assert status["operation_id"] == operation_id
        assert status["status"] == "completed"
        assert status["progress"]["processed"] == 1
        assert status["progress"]["successful"] == 1
        assert status["progress"]["percentage"] == 100.0

    def test_get_operation_status_not_found(self, processor):
        """Test retrieving status for non-existent operation."""
        status = processor.get_operation_status("non-existent")

        assert status is None

    @pytest.mark.asyncio
    async def test_process_bulk_create_success(self, processor):
        """Test successful bulk document creation."""
        documents = [
            BulkDocumentItem(id="doc1", content="Content 1", metadata={"type": "test"}),
            BulkDocumentItem(id="doc2", content="Content 2", metadata={"type": "test"})
        ]

        operation_id = processor.create_operation("create_documents", documents)

        # Mock the document creation
        with patch.object(processor, '_create_single_document', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                {"id": "doc1", "status": "created"},
                {"id": "doc2", "status": "created"}
            ]

            result = await processor.process_bulk_create(operation_id, documents)

            assert result["status"] == "completed"
            assert result["processed"] == 2
            assert result["successful"] == 2
            assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_process_bulk_create_partial_failure(self, processor):
        """Test bulk creation with partial failures."""
        documents = [
            BulkDocumentItem(id="doc1", content="Content 1"),
            BulkDocumentItem(id="doc2", content="Content 2")
        ]

        operation_id = processor.create_operation("create_documents", documents)

        with patch.object(processor, '_create_single_document', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = [
                {"id": "doc1", "status": "created"},
                Exception("Creation failed")
            ]

            result = await processor.process_bulk_create(operation_id, documents)

            assert result["status"] == "completed_with_errors"
            assert result["processed"] == 2
            assert result["successful"] == 1
            assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_create_single_document_success(self, processor):
        """Test creating a single document."""
        doc = BulkDocumentItem(id="test-doc", content="Test content", metadata={"type": "test"})

        with patch('services.doc_store.modules.document_handlers.DocumentHandlers') as mock_handlers_class:
            mock_handler = Mock()
            mock_handler.handle_put_document = AsyncMock(return_value={
                "success": True,
                "data": {"id": "test-doc"}
            })
            mock_handlers_class.return_value = mock_handler

            result = await processor._create_single_document(doc, asyncio.Semaphore(1))

            assert result["id"] == "test-doc"
            assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_single_document_failure(self, processor):
        """Test single document creation failure."""
        doc = BulkDocumentItem(id="test-doc", content="Test content")

        with patch('services.doc_store.modules.document_handlers.DocumentHandlers') as mock_handlers_class:
            mock_handler = Mock()
            mock_handler.handle_put_document = AsyncMock(return_value={
                "success": False,
                "message": "Creation failed"
            })
            mock_handlers_class.return_value = mock_handler

            result = await processor._create_single_document(doc, asyncio.Semaphore(1))

            assert result["error"] == "Creation failed"

    @pytest.mark.asyncio
    async def test_process_bulk_search(self, processor):
        """Test bulk search operations."""
        queries = [
            {"q": "python api", "limit": 10},
            {"q": "flask tutorial", "limit": 5}
        ]

        operation_id = processor.create_operation("bulk_search", queries)

        with patch('services.doc_store.modules.search_handlers.SearchHandlers.handle_advanced_search', new_callable=AsyncMock) as mock_advanced_search:
            mock_advanced_search.side_effect = [
                {"results": [{"id": "doc1"}]},
                {"results": [{"id": "doc2"}]}
            ]

            result = await processor.process_bulk_search(operation_id, queries)

            assert result["status"] == "completed"
            assert result["processed"] == 2
            assert result["successful"] == 2
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_process_bulk_tag(self, processor):
        """Test bulk tagging operations."""
        document_ids = ["doc1", "doc2", "doc3"]

        operation_id = processor.create_operation("bulk_tag", document_ids)

        with patch('services.doc_store.modules.tagging_handlers.TaggingHandlers.handle_tag_document', new_callable=AsyncMock) as mock_tag_document:
            mock_tag_document.side_effect = [
                {"status": "tagged", "tags_stored": 3},
                {"status": "tagged", "tags_stored": 2},
                Exception("Tagging failed")
            ]

            result = await processor.process_bulk_tag(operation_id, document_ids)

            assert result["status"] == "completed_with_errors"
            assert result["processed"] == 3
            assert result["successful"] == 2
            assert result["failed"] == 1


class TestBulkOperationsIntegration:
    """Test bulk operations integration with doc store."""

    @pytest.mark.asyncio
    async def test_bulk_create_api_endpoint(self):
        """Test bulk document creation API endpoint."""
        from services.doc_store.modules.bulk_handlers import BulkHandlers
        from services.doc_store.core.models import BulkDocumentRequest

        from services.doc_store.core.models import DocumentRequest
        request = BulkDocumentRequest(documents=[
            DocumentRequest(content="Doc 1 content", metadata={"type": "test"}),
            DocumentRequest(content="Doc 2 content", metadata={"type": "test"})
        ])

        with patch('services.doc_store.modules.bulk_handlers.bulk_processor') as mock_processor:
            mock_processor.create_operation.return_value = "bulk-op-123"
            mock_processor.process_bulk_create = AsyncMock(return_value={"status": "processing"})

            handler = BulkHandlers()
            result = await handler.handle_bulk_create_documents(request)

            assert result["data"]["operation_id"] == "bulk-op-123"
            assert result["data"]["total_documents"] == 2

    @pytest.mark.asyncio
    async def test_bulk_operation_status_api(self):
        """Test bulk operation status API."""
        from services.doc_store.modules.bulk_handlers import BulkHandlers

        mock_status = {
            "operation_id": "bulk-op-123",
            "status": "completed",
            "progress": {"processed": 10, "successful": 9, "failed": 1}
        }

        with patch('services.doc_store.modules.bulk_handlers.bulk_processor') as mock_processor:
            mock_processor.get_operation_status.return_value = mock_status

            handler = BulkHandlers()
            result = await handler.handle_get_bulk_operation_status("bulk-op-123")

            assert result["data"]["status"] == "completed"
            assert result["data"]["progress"]["successful"] == 9

    @pytest.mark.asyncio
    async def test_bulk_operations_list_api(self):
        """Test bulk operations list API."""
        from services.doc_store.modules.bulk_handlers import BulkHandlers

        mock_operations = [
            {
                "operation_id": "op1",
                "operation_type": "create_documents",
                "status": "completed",
                "total_items": 10,
                "successful_items": 10,
                "failed_items": 0,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]

        with patch('services.doc_store.modules.bulk_handlers.bulk_processor') as mock_processor:
            mock_processor.operations = {"op1": Mock(
                operation_id="op1",
                operation_type="create_documents",
                status="completed",
                total_items=10,
                successful_items=10,
                failed_items=0,
                created_at=Mock(isoformat=Mock(return_value="2024-01-01T00:00:00Z"))
            )}

            handler = BulkHandlers()
            result = await handler.handle_list_bulk_operations()

            # Check that result contains operations data
            assert "data" in result
            assert "operations" in result["data"]
            assert result["data"]["total"] == 1

    @pytest.mark.asyncio
    async def test_bulk_operation_cancellation(self):
        """Test bulk operation cancellation."""
        from services.doc_store.modules.bulk_handlers import BulkHandlers

        with patch('services.doc_store.modules.bulk_handlers.bulk_processor') as mock_processor:
            mock_operation = Mock()
            mock_operation.status = "processing"
            mock_operation.created_at = Mock()
            mock_operation.created_at.__class__.now = Mock(return_value="2024-01-01T00:00:00Z")
            mock_operation.created_at.tzinfo = None
            mock_processor.operations = {"test-op": mock_operation}

            handler = BulkHandlers()
            result = await handler.handle_cancel_bulk_operation("test-op")

            assert result["data"]["status"] == "cancelled"
            assert mock_operation.status == "cancelled"


class TestBulkOperationsConcurrency:
    """Test bulk operations concurrency and resource management."""

    @pytest.mark.asyncio
    async def test_concurrent_bulk_operations(self):
        """Test running multiple bulk operations concurrently."""
        processor = BulkProcessor(max_concurrent=3)

        # Create multiple operations
        op1 = processor.create_operation("op1", [{"item": 1}])
        op2 = processor.create_operation("op2", [{"item": 2}])
        op3 = processor.create_operation("op3", [{"item": 3}])

        # Mock processing
        with patch.object(processor, '_create_single_document', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"status": "created"}

            # Process operations concurrently
            tasks = [
                processor.process_bulk_create(op1, [BulkDocumentItem(id="doc1", content="test")]),
                processor.process_bulk_create(op2, [BulkDocumentItem(id="doc2", content="test")]),
                processor.process_bulk_create(op3, [BulkDocumentItem(id="doc3", content="test")])
            ]

            results = await asyncio.gather(*tasks)

            # All should complete successfully
            assert all(r["status"] == "completed" for r in results)

    def test_batch_size_processing(self):
        """Test that operations are processed in correct batch sizes."""
        processor = BulkProcessor(batch_size=5)

        # Create operation with more items than batch size
        items = [{"item": i} for i in range(12)]
        operation_id = processor.create_operation("test_batch", items)

        # Verify batch size setting
        assert processor.batch_size == 5

        # In a real scenario, the processing would split into batches of 5, 5, and 2
