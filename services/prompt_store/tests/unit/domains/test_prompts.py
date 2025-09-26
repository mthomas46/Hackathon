"""Tests for prompts domain.

Comprehensive tests covering repository, service, and handler layers for prompt management.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from services.prompt_store.core.entities import Prompt
from services.prompt_store.domain.prompts.repository import PromptRepository
from services.prompt_store.domain.prompts.service import PromptService
from services.prompt_store.domain.prompts.handlers import PromptHandlers
from services.prompt_store.core.models import PromptCreate, PromptUpdate


@pytest.mark.unit
class TestPromptRepository:
    """Test PromptRepository data access operations."""

    def test_get_entity_found(self, prompt_store_db):
        """Test getting an existing prompt entity."""
        # Create a test prompt first
        repo = PromptRepository()
        prompt_data = {
            "id": "test_prompt_001",
            "name": "test_prompt",
            "category": "test",
            "content": "Test prompt content",
            "created_by": "test_user"
        }

        # Save the prompt
        prompt = Prompt(
            name=prompt_data["name"],
            category=prompt_data["category"],
            content=prompt_data["content"],
            created_by=prompt_data["created_by"]
        )
        prompt.id = prompt_data["id"]
        saved = repo.save(prompt)

        # Retrieve it
        retrieved = repo.get_by_id("test_prompt_001")
        assert retrieved is not None
        assert retrieved.id == "test_prompt_001"
        assert retrieved.name == "test_prompt"
        assert retrieved.category == "test"

    def test_get_entity_not_found(self, prompt_store_db):
        """Test getting a non-existent prompt entity."""
        repo = PromptRepository()
        result = repo.get_by_id("non_existent_id")
        assert result is None

    def test_save_new_entity(self, prompt_store_db):
        """Test saving a new prompt entity."""
        repo = PromptRepository()
        prompt = Prompt(
            name="new_test_prompt",
            category="test",
            content="New test content",
            created_by="test_user"
        )

        saved = repo.save(prompt)
        assert saved.id is not None
        assert saved.name == "new_test_prompt"
        assert saved.created_at is not None
        assert saved.updated_at is not None

    def test_update_entity(self, prompt_store_db):
        """Test updating an existing prompt entity."""
        repo = PromptRepository()

        # Create initial prompt
        prompt = Prompt(
            name="update_test",
            category="test",
            content="Initial content",
            created_by="test_user"
        )
        saved = repo.save(prompt)

        # Update it
        updated = repo.update(saved.id, {"content": "Updated content"})
        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.updated_at > updated.created_at

    def test_delete_entity(self, prompt_store_db):
        """Test deleting a prompt entity."""
        repo = PromptRepository()

        # Create and save prompt
        prompt = Prompt(
            name="delete_test",
            category="test",
            content="Content to delete",
            created_by="test_user"
        )
        saved = repo.save(prompt)

        # Delete it
        result = repo.delete(saved.id)
        assert result is True

        # Verify it's gone
        retrieved = repo.get_by_id(saved.id)
        assert retrieved is None

    def test_exists_entity(self, prompt_store_db):
        """Test checking if a prompt entity exists."""
        repo = PromptRepository()

        # Create and save prompt
        prompt = Prompt(
            name="exists_test",
            category="test",
            content="Content for exists test",
            created_by="test_user"
        )
        saved = repo.save(prompt)

        # Check existence
        assert repo.exists(saved.id) is True
        assert repo.exists("non_existent") is False

    def test_count_entities(self, prompt_store_db):
        """Test counting prompt entities."""
        repo = PromptRepository()

        # Create multiple prompts
        for i in range(3):
            prompt = Prompt(
                name=f"count_test_{i}",
                category="test",
                content=f"Content {i}",
                created_by="test_user"
            )
            repo.save(prompt)

        # Count all
        count = repo.count()
        assert count >= 3  # May have more from other tests

        # Count with filter
        filtered_count = repo.count(category="test")
        assert filtered_count >= 3


@pytest.mark.unit
class TestPromptService:
    """Test PromptService business logic operations."""

    def test_create_entity_success(self, prompt_store_db):
        """Test successful prompt creation."""
        service = PromptService()

        prompt_data = {
            "name": "service_test_prompt",
            "category": "test",
            "content": "Service test content with variables {{var1}} and {{var2}}",
            "variables": ["var1", "var2"],
            "is_template": True,
            "created_by": "test_user"
        }

        result = service.create_entity(prompt_data)
        assert result.name == "service_test_prompt"
        assert result.category == "test"
        assert result.is_template is True
        assert result.variables == ["var1", "var2"]
        assert result.created_by == "test_user"

    def test_create_entity_validation_error(self, prompt_store_db):
        """Test prompt creation with validation errors."""
        service = PromptService()

        # Missing required field
        invalid_data = {
            "name": "test_prompt",
            # Missing category
            "content": "Test content",
            "created_by": "test_user"
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            service.create_entity(invalid_data)

    def test_create_entity_duplicate_name(self, prompt_store_db):
        """Test creating prompt with duplicate name in same category."""
        service = PromptService()

        # Create first prompt
        data1 = {
            "name": "duplicate_test",
            "category": "test",
            "content": "First content",
            "created_by": "test_user"
        }
        service.create_entity(data1)

        # Try to create duplicate
        data2 = {
            "name": "duplicate_test",
            "category": "test",
            "content": "Second content",
            "created_by": "test_user"
        }

        with pytest.raises(ValueError, match="already exists"):
            service.create_entity(data2)

    def test_get_entity_by_id(self, prompt_store_db):
        """Test retrieving prompt by ID."""
        service = PromptService()

        # Create prompt
        created = service.create_entity({
            "name": "get_test",
            "category": "test",
            "content": "Get test content",
            "created_by": "test_user"
        })

        # Retrieve it
        retrieved = service.get_entity(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "get_test"

    def test_update_entity(self, prompt_store_db):
        """Test updating prompt entity."""
        service = PromptService()

        # Create prompt
        created = service.create_entity({
            "name": "update_test",
            "category": "test",
            "content": "Original content",
            "created_by": "test_user"
        })

        # Update it
        updated = service.update_entity(created.id, {"content": "Updated content"})
        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.updated_at > updated.created_at

    def test_delete_entity(self, prompt_store_db):
        """Test deleting prompt entity."""
        service = PromptService()

        # Create prompt
        created = service.create_entity({
            "name": "delete_test",
            "category": "test",
            "content": "Content to delete",
            "created_by": "test_user"
        })

        # Delete it
        result = service.delete_entity(created.id)
        assert result is True

        # Verify it's gone
        retrieved = service.get_entity(created.id)
        assert retrieved is None

    def test_list_entities_with_pagination(self, prompt_store_db):
        """Test listing prompts with pagination."""
        service = PromptService()

        # Create multiple prompts
        for i in range(5):
            service.create_entity({
                "name": f"list_test_{i}",
                "category": "test",
                "content": f"Content {i}",
                "created_by": "test_user"
            })

        # List with pagination
        result = service.list_entities(limit=3, offset=0)
        assert result["total"] >= 5
        assert len(result["items"]) == 3
        assert result["limit"] == 3
        assert result["offset"] == 0

    def test_get_prompt_by_name(self, prompt_store_db):
        """Test getting prompt by category and name."""
        service = PromptService()

        # Create prompt
        service.create_entity({
            "name": "named_prompt",
            "category": "test",
            "content": "Named prompt content",
            "created_by": "test_user"
        })

        # Retrieve by name
        retrieved = service.get_prompt_by_name("test", "named_prompt")
        assert retrieved is not None
        assert retrieved.name == "named_prompt"
        assert retrieved.category == "test"


@pytest.mark.unit
class TestPromptHandlers:
    """Test PromptHandlers HTTP request/response handling."""

    def test_handle_create_prompt_success(self):
        """Test successful prompt creation handler."""
        handlers = PromptHandlers()

        # Mock the service
        with patch.object(handlers.service, 'create_entity') as mock_create:
            mock_prompt = Mock()
            mock_prompt.to_dict.return_value = {"id": "test_id", "name": "test"}
            mock_create.return_value = mock_prompt

            request_data = PromptCreate(
                name="test_prompt",
                category="test",
                content="Test content"
            )

            result = handlers.handle_create_prompt(request_data)

            # Verify the response structure
            assert result["success"] is True
            assert result["data"]["id"] == "test_id"
            assert result["data"]["name"] == "test"
            mock_create.assert_called_once()

    def test_handle_create_prompt_validation_error(self):
        """Test prompt creation handler with validation error."""
        handlers = PromptHandlers()

        # Mock the service to raise ValueError
        with patch.object(handlers.service, 'create_entity') as mock_create:
            mock_create.side_effect = ValueError("Invalid prompt data")

            request_data = PromptCreate(
                name="",
                category="test",
                content="Test content"
            )

            result = handlers.handle_create_prompt(request_data)

            # Should return error response
            assert result["success"] is False
            assert "Invalid prompt data" in result["message"]

    def test_handle_get_prompt_success(self):
        """Test successful prompt retrieval handler."""
        handlers = PromptHandlers()

        with patch.object(handlers.service, 'get_entity') as mock_get:
            mock_prompt = Mock()
            mock_prompt.to_dict.return_value = {"id": "test_id", "name": "test"}
            mock_get.return_value = mock_prompt

            result = handlers.handle_get_prompt("test_id")

            assert result["success"] is True
            assert result["data"]["id"] == "test_id"
            mock_get.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_handle_get_prompt_not_found(self):
        """Test prompt retrieval handler when prompt not found."""
        handlers = PromptHandlers()

        with patch.object(handlers.service, 'get_entity') as mock_get:
            mock_get.return_value = None

            result = await handlers.handle_get_prompt("non_existent_id")

            # Handle both dict and SuccessResponse returns
            if hasattr(result, 'success'):
                assert result.success is False
                assert "not found" in result.message
            else:
                assert result["success"] is False
                assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_update_prompt_success(self):
        """Test successful prompt update handler."""
        handlers = PromptHandlers()

        with patch.object(handlers.service, 'update_entity') as mock_update:
            mock_updated_prompt = Mock()
            mock_updated_prompt.to_dict.return_value = {"id": "test_id", "name": "updated"}
            mock_update.return_value = mock_updated_prompt

            update_data = PromptUpdate(content="Updated content")
            result = await handlers.handle_update_prompt("test_id", update_data)

            # Handle both dict and SuccessResponse returns
            if hasattr(result, 'success'):
                assert result.success is True
                assert result.data["name"] == "updated"
            else:
                assert result["success"] is True
                assert result["data"]["name"] == "updated"
            mock_update.assert_called_once_with("test_id", {"content": "Updated content"})

    @pytest.mark.asyncio
    async def test_handle_delete_prompt_success(self):
        """Test successful prompt deletion handler."""
        handlers = PromptHandlers()

        with patch.object(handlers.service, 'delete_entity') as mock_delete:
            mock_delete.return_value = True

            result = await handlers.handle_delete_prompt("test_id")

            assert result.success is True
            # Delete operation returns None for data, which is fine
            assert result.data is None or result.data is True
            mock_delete.assert_called_once_with("test_id")
