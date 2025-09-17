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
from services.doc_store.core.entities import BulkOperation, BulkDocumentItem
from services.doc_store.domain.bulk.service import BulkOperationsService


class TestBulkOperationsService:
    """Test BulkOperationsService class functionality."""

    @pytest.fixture
    def service(self):
        """Create a test bulk operations service instance."""
        return BulkOperationsService()

    def test_service_initialization(self, service):
        """Test bulk operations service initialization."""
        assert service.repository is not None
        assert hasattr(service, 'create_bulk_operation')

    def test_create_bulk_operation(self, service):
        """Test creating a bulk operation."""
        docs = [
            BulkDocumentItem(content="test content 1"),
            BulkDocumentItem(content="test content 2")
        ]

        operation = service.create_bulk_operation("create_documents", docs)

        assert operation.operation_type == "create_documents"
        assert operation.total_items == 2
        assert operation.status == "pending"
        assert operation.operation_id is not None

    def test_get_operation_status(self, service):
        """Test retrieving operation status."""
        docs = [BulkDocumentItem(content="test content")]
        operation = service.create_bulk_operation("create_documents", docs)

        retrieved = service.get_operation_status(operation.operation_id)
        assert retrieved is not None
        assert retrieved.operation_id == operation.operation_id

        # Update operation status via repository
        operation.processed_items = 1
        operation.successful_items = 1
        operation.status = "completed"
        service.repository.save(operation)

        retrieved = service.get_operation_status(operation.operation_id)

        assert retrieved.operation_id == operation.operation_id
        assert retrieved.status == "completed"
        assert retrieved.processed_items == 1
        assert retrieved.successful_items == 1

    def test_get_operation_status_not_found(self, service):
        """Test retrieving status for non-existent operation."""
        status = service.get_operation_status("non-existent")
        assert status is None

    @pytest.mark.asyncio
    async def test_process_bulk_create_success(self, service):
        """Test successful bulk document creation."""
        documents = [
            BulkDocumentItem(id="doc1", content="Content 1", metadata={"type": "test"}),
            BulkDocumentItem(id="doc2", content="Content 2", metadata={"type": "test"})
        ]

        operation = service.create_bulk_operation("create_documents", documents)

        # Verify operation was created
        assert operation.operation_type == "create_documents"
        assert operation.total_items == 2


class TestBulkOperationsIntegration:
    """Test bulk operations integration with handlers."""

    @pytest.fixture
    def service(self):
        """Create a test bulk operations service."""
        return BulkOperationsService()

    @pytest.mark.asyncio
    async def test_bulk_create_api_endpoint(self, service):
        """Test bulk document creation API endpoint."""
        from services.doc_store.domain.bulk.handlers import BulkOperationsHandlers

        handler = BulkOperationsHandlers()
        documents = [
            {"content": "Test document 1", "metadata": {"type": "test"}},
            {"content": "Test document 2", "metadata": {"type": "test"}}
        ]

        # Mock the service to avoid actual database operations
        with patch.object(service, 'create_bulk_operation') as mock_create:
            mock_operation = BulkOperation(
                operation_id="test-op-123",
                operation_type="create_documents",
                total_items=2
            )
            mock_create.return_value = mock_operation
            handler.service = service

            result = await handler.handle_bulk_create_documents(documents)

            result_dict = result.model_dump()
            assert result_dict["success"] is True
            assert "operation_id" in result_dict["data"]
