"""Tests for lifecycle domain.

Tests covering repository, service, and handler layers for prompt lifecycle management.
"""

import pytest
from unittest.mock import Mock, patch

from services.prompt_store.domain.lifecycle.repository import LifecycleRepository
from services.prompt_store.domain.lifecycle.service import LifecycleService
from services.prompt_store.domain.lifecycle.handlers import LifecycleHandlers
from services.prompt_store.core.models import PromptLifecycleUpdate


@pytest.mark.unit
class TestLifecycleRepository:
    """Test LifecycleRepository operations."""

    def test_validate_transition_valid(self, prompt_store_db):
        """Test validating valid lifecycle transitions."""
        repo = LifecycleRepository()

        # draft -> published should be valid
        assert repo.validate_transition("draft", "published") is True
        # published -> deprecated should be valid
        assert repo.validate_transition("published", "deprecated") is True

    def test_validate_transition_invalid(self, prompt_store_db):
        """Test validating invalid lifecycle transitions."""
        repo = LifecycleRepository()

        # draft -> archived should be valid
        assert repo.validate_transition("draft", "archived") is True
        # published -> draft should be invalid
        assert repo.validate_transition("published", "draft") is False

    def test_get_transition_rules(self, prompt_store_db):
        """Test getting all transition rules."""
        repo = LifecycleRepository()
        rules = repo.get_transition_rules()

        assert "draft" in rules
        assert "published" in rules["draft"]
        assert "archived" in rules["draft"]

    def test_update_lifecycle_status_success(self, prompt_store_db):
        """Test successful lifecycle status update."""
        # First create a prompt to update
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "lifecycle_test",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        repo = LifecycleRepository()
        success = repo.update_lifecycle_status(prompt.id, "published", "Testing")
        assert success is True

        # Verify the update
        updated_prompt = prompt_service.get_entity(prompt.id)
        assert updated_prompt.lifecycle_status == "published"

    def test_update_lifecycle_status_invalid_transition(self, prompt_store_db):
        """Test lifecycle status update with invalid transition."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "invalid_transition_test",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        repo = LifecycleRepository()
        with pytest.raises(ValueError, match="Invalid transition"):
            repo.update_lifecycle_status(prompt.id, "draft", "Invalid transition")

    def test_get_lifecycle_history(self, prompt_store_db):
        """Test getting lifecycle history."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "history_test",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        repo = LifecycleRepository()

        # Update status multiple times
        repo.update_lifecycle_status(prompt.id, "published", "First update")
        repo.update_lifecycle_status(prompt.id, "deprecated", "Second update")

        # Get history
        history = repo.get_lifecycle_history(prompt.id)
        assert len(history) >= 2  # Should have at least the two transitions

        # Check the structure of history entries
        for entry in history:
            assert "timestamp" in entry
            assert "from_status" in entry
            assert "to_status" in entry
            assert "reason" in entry
            assert "updated_by" in entry


@pytest.mark.unit
class TestLifecycleService:
    """Test LifecycleService business logic."""

    def test_update_lifecycle_status_success(self, prompt_store_db):
        """Test successful lifecycle status update through service."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "service_lifecycle_test",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        service = LifecycleService()
        result = service.update_lifecycle_status(
            prompt.id, "published", "Service test", "test_user"
        )

        assert result["prompt_id"] == prompt.id
        assert result["previous_status"] == "draft"
        assert result["new_status"] == "published"
        assert result["reason"] == "Service test"

    def test_get_lifecycle_history(self, prompt_store_db):
        """Test getting lifecycle history through service."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "service_history_test",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        service = LifecycleService()

        # Update status
        service.update_lifecycle_status(prompt.id, "published", "Test update")

        # Get history
        history = service.get_lifecycle_history(prompt.id)
        assert history["prompt_id"] == prompt.id
        assert history["current_status"] == "published"
        assert len(history["lifecycle_history"]) >= 1

    def test_validate_transition(self, prompt_store_db):
        """Test transition validation through service."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()
        prompt = prompt_service.create_entity({
            "name": "validation_test",
            "category": "test",
            "content": "Test content",
            "created_by": "test_user"
        })

        service = LifecycleService()

        # Valid transition
        result = service.validate_transition(prompt.id, "published")
        assert result["valid"] is True

        # Invalid transition
        result = service.validate_transition(prompt.id, "draft")  # already draft
        assert result["valid"] is False


@pytest.mark.unit
class TestLifecycleHandlers:
    """Test LifecycleHandlers HTTP operations."""

    def test_handle_update_lifecycle_status_success(self):
        """Test successful lifecycle update handler."""
        handlers = LifecycleHandlers()

        with patch.object(handlers.lifecycle_service, 'update_lifecycle_status') as mock_update:
            mock_update.return_value = {
                "prompt_id": "test_id",
                "previous_status": "draft",
                "new_status": "published",
                "reason": "Test",
                "timestamp": "2024-01-01T00:00:00"
            }

            update_data = PromptLifecycleUpdate(status="published", reason="Test")
            result = handlers.handle_update_lifecycle_status("test_id", update_data)

            assert result["success"] is True
            assert result["data"]["new_status"] == "published"
            mock_update.assert_called_once()

    def test_handle_get_lifecycle_history_success(self):
        """Test successful lifecycle history retrieval."""
        handlers = LifecycleHandlers()

        with patch.object(handlers.lifecycle_service, 'get_lifecycle_history') as mock_history:
            mock_history.return_value = {
                "prompt_id": "test_id",
                "current_status": "published",
                "lifecycle_history": [],
                "history_count": 0
            }

            result = handlers.handle_get_lifecycle_history("test_id")

            assert result["success"] is True
            assert result["data"]["current_status"] == "published"
            mock_history.assert_called_once_with("test_id")

    def test_handle_get_status_counts_success(self):
        """Test successful status counts retrieval."""
        handlers = LifecycleHandlers()

        with patch.object(handlers.lifecycle_service, 'get_status_counts') as mock_counts:
            mock_counts.return_value = {
                "status_counts": {"draft": 5, "published": 3},
                "total_prompts": 8,
                "last_updated": "2024-01-01T00:00:00"
            }

            result = handlers.handle_get_status_counts()

            assert result["success"] is True
            assert result["data"]["total_prompts"] == 8
            mock_counts.assert_called_once()

    def test_handle_validate_transition_success(self):
        """Test successful transition validation."""
        handlers = LifecycleHandlers()

        with patch.object(handlers.lifecycle_service, 'validate_transition') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "current_status": "draft",
                "requested_status": "published",
                "reason": None
            }

            result = handlers.handle_validate_transition("test_id", "published")

            assert result["success"] is True
            assert result["data"]["valid"] is True
            mock_validate.assert_called_once_with("test_id", "published")
