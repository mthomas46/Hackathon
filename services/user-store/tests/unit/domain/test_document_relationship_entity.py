"""Unit tests for DocumentRelationship domain entity."""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from domain.entities.document_relationship import DocumentRelationship, RelationshipType


class TestDocumentRelationship:
    """Test cases for DocumentRelationship entity."""

    def test_relationship_creation_valid(self):
        """Test creating a valid document relationship."""
        relationship = DocumentRelationship(
            id="rel_123",
            user_id="user_123",
            document_id="doc_456",
            relationship_type=RelationshipType.OWNER,
            tags=["documentation", "api"],
            services=["user-store"]
        )

        assert relationship.id == "rel_123"
        assert relationship.user_id == "user_123"
        assert relationship.document_id == "doc_456"
        assert relationship.relationship_type == RelationshipType.OWNER
        assert relationship.tags == ["documentation", "api"]
        assert relationship.services == ["user-store"]

    def test_relationship_creation_invalid_empty_ids(self):
        """Test creating relationship with empty IDs."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            DocumentRelationship(
                id="",
                user_id="",
                document_id="",
                relationship_type=RelationshipType.OWNER
            )

    def test_relationship_to_dict(self):
        """Test converting relationship to dictionary."""
        relationship = DocumentRelationship(
            id="rel_123",
            user_id="user_123",
            document_id="doc_456",
            relationship_type=RelationshipType.OWNER,
            tags=["documentation"],
            services=["user-store"]
        )

        rel_dict = relationship.to_dict()

        assert rel_dict["id"] == "rel_123"
        assert rel_dict["user_id"] == "user_123"
        assert rel_dict["document_id"] == "doc_456"
        assert rel_dict["relationship_type"] == "owner"
        assert rel_dict["tags"] == ["documentation"]
        assert rel_dict["services"] == ["user-store"]
