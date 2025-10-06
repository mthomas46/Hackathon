"""Unit tests for MCPContext entity."""

import pytest
from datetime import datetime, timedelta, timezone

from services.mcp_infrastructure.domain.entities.mcp_context import MCPContext
from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType


def test_mcp_context_creation(sample_mcp_id, sample_context_data):
    """Test creating an MCPContext entity."""
    context = MCPContext(
        mcp_id=sample_mcp_id,
        context_type=MCPContextType.INSTANCE,
        data=sample_context_data,
        ttl=3600,
    )
    
    assert context.mcp_id == sample_mcp_id
    assert context.context_type == MCPContextType.INSTANCE
    assert context.data == sample_context_data
    assert context.ttl == 3600
    assert isinstance(context.id, str)
    assert len(context.id) > 0
    assert context.version == 1


def test_mcp_context_requires_mcp_id(sample_context_data):
    """Test that MCPContext requires an mcp_id."""
    with pytest.raises(ValueError, match="MCPContext must have an mcp_id"):
        MCPContext(
            mcp_id="",
            context_type=MCPContextType.INSTANCE,
            data=sample_context_data,
        )


def test_mcp_context_requires_valid_context_type(sample_mcp_id, sample_context_data):
    """Test that MCPContext requires a valid context type."""
    with pytest.raises(TypeError, match="context_type must be an instance of MCPContextType"):
        MCPContext(
            mcp_id=sample_mcp_id,
            context_type="invalid",
            data=sample_context_data,
        )


def test_mcp_context_update_data(sample_context):
    """Test updating context data."""
    original_version = sample_context.version
    original_updated_at = sample_context.updated_at
    
    new_data = {"queries_today": 200}
    sample_context.update_data(new_data)
    
    assert sample_context.data["queries_today"] == 200
    assert sample_context.version == original_version + 1
    assert sample_context.updated_at > original_updated_at


def test_mcp_context_add_tag(sample_context):
    """Test adding a tag to context."""
    original_tags = len(sample_context.tags)
    
    sample_context.add_tag("new-tag")
    
    assert "new-tag" in sample_context.tags
    assert len(sample_context.tags) == original_tags + 1


def test_mcp_context_add_duplicate_tag(sample_context):
    """Test that adding a duplicate tag doesn't create duplicates."""
    existing_tag = sample_context.tags[0]
    original_count = len(sample_context.tags)
    
    sample_context.add_tag(existing_tag)
    
    assert len(sample_context.tags) == original_count


def test_mcp_context_remove_tag(sample_context):
    """Test removing a tag from context."""
    tag_to_remove = sample_context.tags[0]
    original_count = len(sample_context.tags)
    
    sample_context.remove_tag(tag_to_remove)
    
    assert tag_to_remove not in sample_context.tags
    assert len(sample_context.tags) == original_count - 1


def test_mcp_context_refresh_ttl(sample_context):
    """Test refreshing the TTL."""
    original_expires_at = sample_context.expires_at
    
    # Refresh with new TTL
    sample_context.refresh_ttl(7200)
    
    assert sample_context.ttl == 7200
    assert sample_context.expires_at > original_expires_at


def test_mcp_context_is_expired():
    """Test checking if context is expired."""
    # Create context with very short TTL
    context = MCPContext(
        mcp_id="test-mcp",
        context_type=MCPContextType.INSTANCE,
        data={"test": "data"},
        ttl=1,
    )
    
    # Set expires_at to the past
    context.expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    
    assert context.is_expired() is True


def test_mcp_context_is_not_expired(sample_context):
    """Test that a fresh context is not expired."""
    assert sample_context.is_expired() is False


def test_mcp_context_to_dict(sample_context):
    """Test converting context to dictionary."""
    context_dict = sample_context.to_dict()
    
    assert context_dict["id"] == sample_context.id
    assert context_dict["mcp_id"] == sample_context.mcp_id
    assert context_dict["context_type"] == sample_context.context_type.value
    assert context_dict["data"] == sample_context.data
    assert context_dict["ttl"] == sample_context.ttl
    assert context_dict["tags"] == sample_context.tags
    assert context_dict["version"] == sample_context.version


def test_mcp_context_from_dict(sample_context):
    """Test creating context from dictionary."""
    context_dict = sample_context.to_dict()
    recreated = MCPContext.from_dict(context_dict)
    
    assert recreated.id == sample_context.id
    assert recreated.mcp_id == sample_context.mcp_id
    assert recreated.context_type == sample_context.context_type
    assert recreated.data == sample_context.data
    assert recreated.ttl == sample_context.ttl
    assert recreated.tags == sample_context.tags
    assert recreated.version == sample_context.version


def test_mcp_context_equality(sample_mcp_id, sample_context_data):
    """Test context equality based on ID."""
    context1 = MCPContext(
        id="same-id",
        mcp_id=sample_mcp_id,
        context_type=MCPContextType.INSTANCE,
        data=sample_context_data,
    )
    
    context2 = MCPContext(
        id="same-id",
        mcp_id="different-mcp",
        context_type=MCPContextType.TRAINING,
        data={"different": "data"},
    )
    
    assert context1 == context2  # Same ID


def test_mcp_context_hash(sample_context):
    """Test that contexts are hashable."""
    context_set = {sample_context}
    assert sample_context in context_set


def test_mcp_context_repr(sample_context):
    """Test string representation."""
    repr_str = repr(sample_context)
    
    assert "MCPContext" in repr_str
    assert sample_context.id in repr_str
    assert sample_context.mcp_id in repr_str

