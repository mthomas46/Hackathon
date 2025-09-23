"""Tests for bulk operations domain.

Tests covering repository, service, and handler layers for bulk prompt operations.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from services.prompt_store.domain.bulk.repository import BulkOperationRepository
from services.prompt_store.domain.bulk.service import BulkOperationService
from services.prompt_store.domain.bulk.handlers import BulkOperationHandlers
from services.prompt_store.core.models import BulkOperationCreate


@pytest.mark.unit
class TestBulkOperationRepository:
    """Test BulkOperationRepository operations."""

    def test_create_bulk_operation_success(self, prompt_store_db):
        """Test successful bulk operation creation."""
        repo = BulkOperationRepository()
        operation_data = {
            "operation_type": "create_prompts",
            "total_items": 10,
            "created_by": "test_user",
            "metadata": {"source": "test_import"}
        }

        operation = repo.create_bulk_operation(operation_data)
        assert operation.operation_type == "create_prompts"
        assert operation.total_items == 10
        assert operation.status == "pending"
        assert operation.created_by == "test_user"

    def test_update_operation_status_success(self, prompt_store_db):
        """Test updating bulk operation status."""
        repo = BulkOperationRepository()
        operation_data = {
            "operation_type": "update_prompts",
            "total_items": 5,
            "created_by": "test_user"
        }

        operation = repo.create_bulk_operation(operation_data)

        # Update status
        updated = repo.update_operation_status(
            operation.id, "processing", processed_items=2, successful_items=2
        )

        assert updated is True

        # Verify update
        retrieved = repo.get_operation(operation.id)
        assert retrieved.status == "processing"
        assert retrieved.processed_items == 2
        assert retrieved.successful_items == 2

    def test_get_pending_operations_success(self, prompt_store_db):
        """Test getting pending bulk operations."""
        repo = BulkOperationRepository()

        # Create multiple operations
        for i in range(3):
            repo.create_bulk_operation({
                "operation_type": "create_prompts",
                "total_items": 10 + i,
                "created_by": "test_user"
            })

        pending = repo.get_pending_operations(limit=5)
        assert len(pending) >= 3

        for operation in pending:
            assert operation.status == "pending"


@pytest.mark.unit
class TestBulkOperationService:
    """Test BulkOperationService business logic."""

    @pytest.mark.asyncio
    async def test_create_bulk_operation_success(self, prompt_store_db):
        """Test successful bulk operation creation through service."""
        service = BulkOperationService()
        operation_data = {
            "operation_type": "create_prompts",
            "total_items": 20,
            "created_by": "test_user",
            "metadata": {"batch_id": "batch_123"}
        }

        result = await service.create_bulk_operation(operation_data)
        assert result["operation_type"] == "create_prompts"
        assert result["status"] == "pending"
        assert result["total_items"] == 20

    def test_get_operation_status_success(self, prompt_store_db):
        """Test getting bulk operation status."""
        service = BulkOperationService()

        # Create operation
        operation_data = {
            "operation_type": "update_prompts",
            "total_items": 15,
            "created_by": "test_user"
        }

        created = service.create_bulk_operation_sync(operation_data)
        status = service.get_operation_status(created.id)

        assert status["operation_id"] == created.id
        assert status["status"] == "pending"
        assert status["progress_percentage"] == 0.0

    def test_cancel_operation_success(self, prompt_store_db):
        """Test canceling bulk operation."""
        service = BulkOperationService()

        # Create operation
        operation_data = {
            "operation_type": "delete_prompts",
            "total_items": 8,
            "created_by": "test_user"
        }

        created = service.create_bulk_operation_sync(operation_data)
        result = service.cancel_operation(created.id)

        assert result is True

        # Verify cancellation
        status = service.get_operation_status(created.id)
        assert status["status"] == "cancelled"


@pytest.mark.unit
class TestBulkOperationHandlers:
    """Test BulkOperationHandlers HTTP operations."""

    @pytest.mark.asyncio
    async def test_handle_create_bulk_operation_success(self):
        """Test successful bulk operation creation handler."""
        handlers = BulkOperationHandlers()

        with patch.object(handlers.bulk_service, 'create_bulk_operation') as mock_create:
            mock_create.return_value = {
                "id": "test_operation_id",
                "operation_type": "create_prompts",
                "status": "pending",
                "total_items": 25
            }

            operation_data = BulkOperationCreate(
                operation_type="create_prompts",
                total_items=25
            )

            result = await handlers.handle_create_bulk_operation(operation_data)

            assert result["success"] is True
            assert result["data"]["total_items"] == 25
            mock_create.assert_called_once()

    def test_handle_get_operation_status_success(self):
        """Test successful operation status retrieval handler."""
        handlers = BulkOperationHandlers()

        with patch.object(handlers.bulk_service, 'get_operation_status') as mock_status:
            mock_status.return_value = {
                "operation_id": "test_id",
                "status": "processing",
                "progress_percentage": 60.0,
                "processed_items": 15,
                "successful_items": 12
            }

            result = handlers.handle_get_operation_status("test_id")

            assert result["success"] is True
            assert result["data"]["status"] == "processing"
            assert result["data"]["progress_percentage"] == 60.0
            mock_status.assert_called_once_with("test_id")

    def test_handle_list_operations_success(self):
        """Test successful operations listing handler."""
        handlers = BulkOperationHandlers()

        with patch.object(handlers.bulk_service, 'list_operations') as mock_list:
            mock_list.return_value = {
                "operations": [
                    {"id": "op_1", "status": "completed"},
                    {"id": "op_2", "status": "processing"}
                ],
                "total": 2,
                "limit": 50,
                "offset": 0
            }

            result = handlers.handle_list_operations()

            assert result["success"] is True
            assert len(result["data"]["operations"]) == 2
            mock_list.assert_called_once()

    def test_handle_cancel_operation_success(self):
        """Test successful operation cancellation handler."""
        handlers = BulkOperationHandlers()

        with patch.object(handlers.bulk_service, 'cancel_operation') as mock_cancel:
            mock_cancel.return_value = True

            result = handlers.handle_cancel_operation("test_id")

            assert result["success"] is True
            assert result["data"] is True
            mock_cancel.assert_called_once_with("test_id")
