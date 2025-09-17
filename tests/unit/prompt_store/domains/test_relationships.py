"""Tests for relationships domain.

Tests covering repository, service, and handler layers for prompt relationships.
"""

import pytest
from unittest.mock import Mock, patch

from services.prompt_store.domain.relationships.repository import RelationshipsRepository
from services.prompt_store.domain.relationships.service import RelationshipsService
from services.prompt_store.domain.relationships.handlers import RelationshipsHandlers
from services.prompt_store.core.models import PromptRelationshipCreate


@pytest.mark.unit
class TestRelationshipsRepository:
    """Test RelationshipsRepository operations."""

    def test_validate_relationship_type_valid(self, prompt_store_db):
        """Test validating valid relationship types."""
        repo = RelationshipsRepository()
        assert repo.validate_relationship_type("extends") is True
        assert repo.validate_relationship_type("references") is True
        assert repo.validate_relationship_type("alternative") is True

    def test_validate_relationship_type_invalid(self, prompt_store_db):
        """Test validating invalid relationship types."""
        repo = RelationshipsRepository()
        assert repo.validate_relationship_type("invalid_type") is False
        assert repo.validate_relationship_type("") is False

    def test_create_relationship_success(self, prompt_store_db):
        """Test successful relationship creation."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        # Create two prompts
        prompt1 = prompt_service.create_entity({
            "name": "source_prompt",
            "category": "test",
            "content": "Source content",
            "created_by": "test_user"
        })
        prompt2 = prompt_service.create_entity({
            "name": "target_prompt",
            "category": "test",
            "content": "Target content",
            "created_by": "test_user"
        })

        repo = RelationshipsRepository()
        relationship = repo.create_relationship(
            prompt1.id, prompt2.id, "extends", 0.8, {"test": "data"}
        )

        assert relationship.source_prompt_id == prompt1.id
        assert relationship.target_prompt_id == prompt2.id
        assert relationship.relationship_type == "extends"
        assert relationship.strength == 0.8

    def test_create_relationship_duplicate(self, prompt_store_db):
        """Test creating duplicate relationship."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt1 = prompt_service.create_entity({
            "name": "dup_source",
            "category": "test",
            "content": "Source content",
            "created_by": "test_user"
        })
        prompt2 = prompt_service.create_entity({
            "name": "dup_target",
            "category": "test",
            "content": "Target content",
            "created_by": "test_user"
        })

        repo = RelationshipsRepository()

        # Create first relationship
        repo.create_relationship(prompt1.id, prompt2.id, "extends")

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            repo.create_relationship(prompt1.id, prompt2.id, "extends")

    def test_get_relationships_for_prompt(self, prompt_store_db):
        """Test getting relationships for a prompt."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt1 = prompt_service.create_entity({
            "name": "rel_source",
            "category": "test",
            "content": "Source content",
            "created_by": "test_user"
        })
        prompt2 = prompt_service.create_entity({
            "name": "rel_target1",
            "category": "test",
            "content": "Target content 1",
            "created_by": "test_user"
        })
        prompt3 = prompt_service.create_entity({
            "name": "rel_target2",
            "category": "test",
            "content": "Target content 2",
            "created_by": "test_user"
        })

        repo = RelationshipsRepository()

        # Create relationships
        repo.create_relationship(prompt1.id, prompt2.id, "extends")
        repo.create_relationship(prompt1.id, prompt3.id, "references")

        # Get relationships
        relationships = repo.get_relationships_for_prompt(prompt1.id, "outgoing")
        assert len(relationships) == 2

        types = [r.relationship_type for r in relationships]
        assert "extends" in types
        assert "references" in types


@pytest.mark.unit
class TestRelationshipsService:
    """Test RelationshipsService business logic."""

    @pytest.mark.asyncio
    async def test_create_relationship_success(self, prompt_store_db):
        """Test successful relationship creation through service."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]

        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt1 = prompt_service.create_entity({
            "name": f"service_source_{unique_id}",
            "category": "test",
            "content": "Source content",
            "created_by": "test_user"
        })
        prompt2 = prompt_service.create_entity({
            "name": f"service_target_{unique_id}",
            "category": "test",
            "content": "Target content",
            "created_by": "test_user"
        })

        service = RelationshipsService()
        result = await service.create_relationship(
            prompt1.id,
            {
                "target_prompt_id": prompt2.id,
                "relationship_type": "extends",
                "strength": 0.9,
                "metadata": {"service_test": True}
            },
            "test_user"
        )

        assert result["source_prompt_id"] == prompt1.id
        assert result["target_prompt_id"] == prompt2.id
        assert result["relationship_type"] == "extends"
        assert result["strength"] == 0.9

    def test_get_relationships_for_prompt(self, prompt_store_db):
        """Test getting relationships for a prompt through service."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt1 = prompt_service.create_entity({
            "name": "service_rel_source",
            "category": "test",
            "content": "Source content",
            "created_by": "test_user"
        })

        service = RelationshipsService()
        result = service.get_relationships_for_prompt(prompt1.id)

        assert result["prompt_id"] == prompt1.id
        assert "outgoing_relationships" in result
        assert "incoming_relationships" in result
        assert result["total_relationships"] == 0  # No relationships yet

    def test_find_related_prompts(self, prompt_store_db):
        """Test finding related prompts."""
        from services.prompt_store.domain.prompts.service import PromptService
        prompt_service = PromptService()

        prompt1 = prompt_service.create_entity({
            "name": "find_source",
            "category": "test",
            "content": "Source content",
            "created_by": "test_user"
        })

        service = RelationshipsService()
        result = service.find_related_prompts(prompt1.id)

        assert result["source_prompt_id"] == prompt1.id
        assert result["related_prompts"] == []
        assert result["total_related"] == 0


@pytest.mark.unit
class TestRelationshipsHandlers:
    """Test RelationshipsHandlers HTTP operations."""

    @pytest.mark.asyncio
    async def test_handle_create_relationship_success(self):
        """Test successful relationship creation handler."""
        handlers = RelationshipsHandlers()

        with patch.object(handlers.relationships_service, 'create_relationship') as mock_create:
            mock_create.return_value = {
                "relationship_id": "test_rel_id",
                "source_prompt_id": "source_id",
                "target_prompt_id": "target_id",
                "relationship_type": "extends",
                "strength": 0.8
            }

            relationship_data = PromptRelationshipCreate(
                target_prompt_id="target_id",
                relationship_type="extends",
                strength=0.8
            )

            result = await handlers.handle_create_relationship("source_id", relationship_data)

            assert result["success"] is True
            assert result["data"]["relationship_type"] == "extends"
            mock_create.assert_called_once()

    def test_handle_get_relationships_success(self):
        """Test successful relationships retrieval handler."""
        handlers = RelationshipsHandlers()

        with patch.object(handlers.relationships_service, 'get_relationships_for_prompt') as mock_get:
            mock_get.return_value = {
                "prompt_id": "test_id",
                "outgoing_relationships": [],
                "incoming_relationships": [],
                "total_relationships": 0
            }

            result = handlers.handle_get_relationships("test_id")

            assert result["success"] is True
            assert result["data"]["total_relationships"] == 0
            mock_get.assert_called_once_with("test_id", "both")

    def test_handle_get_relationship_graph_success(self):
        """Test successful relationship graph retrieval."""
        handlers = RelationshipsHandlers()

        with patch.object(handlers.relationships_service, 'get_relationship_graph') as mock_graph:
            mock_graph.return_value = {
                "root_prompt_id": "test_id",
                "nodes": [{"id": "test_id", "name": "Test"}],
                "edges": [],
                "depth": 2,
                "total_nodes": 1,
                "total_edges": 0
            }

            result = handlers.handle_get_relationship_graph("test_id", 2)

            assert result["success"] is True
            assert result["data"]["total_nodes"] == 1
            mock_graph.assert_called_once_with("test_id", 2)
