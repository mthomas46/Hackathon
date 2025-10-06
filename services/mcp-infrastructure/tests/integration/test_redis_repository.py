"""Integration tests for Redis repository.

These tests require a running Redis instance.
"""

import pytest

from services.mcp_infrastructure.domain.entities.mcp_context import MCPContext
from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType


@pytest.mark.asyncio
async def test_save_and_retrieve_context(redis_repository, sample_context):
    """Test saving and retrieving a context."""
    # Save
    await redis_repository.save(sample_context)
    
    # Retrieve
    retrieved = await redis_repository.find_by_id(sample_context.id)
    
    assert retrieved is not None
    assert retrieved.id == sample_context.id
    assert retrieved.mcp_id == sample_context.mcp_id
    assert retrieved.context_type == sample_context.context_type
    assert retrieved.data == sample_context.data


@pytest.mark.asyncio
async def test_find_by_id_not_found(redis_repository):
    """Test retrieving a non-existent context."""
    retrieved = await redis_repository.find_by_id("non-existent-id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_find_by_mcp_id(redis_repository, sample_mcp_id):
    """Test finding contexts by MCP ID."""
    # Create multiple contexts for same MCP
    context1 = MCPContext(
        mcp_id=sample_mcp_id,
        context_type=MCPContextType.INSTANCE,
        data={"status": "hot"},
    )
    context2 = MCPContext(
        mcp_id=sample_mcp_id,
        context_type=MCPContextType.TRAINING,
        data={"phase": "embedding"},
    )
    
    await redis_repository.save(context1)
    await redis_repository.save(context2)
    
    # Find all contexts for MCP
    contexts = await redis_repository.find_by_mcp_id(sample_mcp_id)
    
    assert len(contexts) == 2
    assert any(c.context_type == MCPContextType.INSTANCE for c in contexts)
    assert any(c.context_type == MCPContextType.TRAINING for c in contexts)


@pytest.mark.asyncio
async def test_find_by_mcp_id_with_type_filter(redis_repository, sample_mcp_id):
    """Test finding contexts by MCP ID with type filter."""
    # Create multiple contexts
    context1 = MCPContext(
        mcp_id=sample_mcp_id,
        context_type=MCPContextType.INSTANCE,
        data={"status": "hot"},
    )
    context2 = MCPContext(
        mcp_id=sample_mcp_id,
        context_type=MCPContextType.TRAINING,
        data={"phase": "embedding"},
    )
    
    await redis_repository.save(context1)
    await redis_repository.save(context2)
    
    # Find only training contexts
    contexts = await redis_repository.find_by_mcp_id(
        sample_mcp_id, MCPContextType.TRAINING
    )
    
    assert len(contexts) == 1
    assert contexts[0].context_type == MCPContextType.TRAINING


@pytest.mark.asyncio
async def test_find_by_type(redis_repository):
    """Test finding contexts by type."""
    # Create contexts of different types
    context1 = MCPContext(
        mcp_id="mcp-1",
        context_type=MCPContextType.TRAINING,
        data={"phase": "embedding"},
    )
    context2 = MCPContext(
        mcp_id="mcp-2",
        context_type=MCPContextType.TRAINING,
        data={"phase": "validation"},
    )
    context3 = MCPContext(
        mcp_id="mcp-3",
        context_type=MCPContextType.INSTANCE,
        data={"status": "hot"},
    )
    
    await redis_repository.save(context1)
    await redis_repository.save(context2)
    await redis_repository.save(context3)
    
    # Find training contexts
    training_contexts = await redis_repository.find_by_type(MCPContextType.TRAINING)
    
    assert len(training_contexts) == 2
    assert all(c.context_type == MCPContextType.TRAINING for c in training_contexts)


@pytest.mark.asyncio
async def test_find_by_tags(redis_repository):
    """Test finding contexts by tags."""
    # Create contexts with different tags
    context1 = MCPContext(
        mcp_id="mcp-1",
        context_type=MCPContextType.INSTANCE,
        data={},
        tags=["tier-0", "production"],
    )
    context2 = MCPContext(
        mcp_id="mcp-2",
        context_type=MCPContextType.INSTANCE,
        data={},
        tags=["tier-0", "staging"],
    )
    context3 = MCPContext(
        mcp_id="mcp-3",
        context_type=MCPContextType.INSTANCE,
        data={},
        tags=["tier-1"],
    )
    
    await redis_repository.save(context1)
    await redis_repository.save(context2)
    await redis_repository.save(context3)
    
    # Find by tag
    tier0_contexts = await redis_repository.find_by_tags(["tier-0"])
    
    assert len(tier0_contexts) == 2
    assert all("tier-0" in c.tags for c in tier0_contexts)


@pytest.mark.asyncio
async def test_delete_context(redis_repository, sample_context):
    """Test deleting a context."""
    # Save
    await redis_repository.save(sample_context)
    
    # Delete
    deleted = await redis_repository.delete(sample_context.id)
    assert deleted is True
    
    # Verify deleted
    retrieved = await redis_repository.find_by_id(sample_context.id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_context_not_found(redis_repository):
    """Test deleting a non-existent context."""
    deleted = await redis_repository.delete("non-existent-id")
    assert deleted is False


@pytest.mark.asyncio
async def test_delete_by_mcp_id(redis_repository, sample_mcp_id):
    """Test deleting all contexts for an MCP."""
    # Create multiple contexts
    context1 = MCPContext(mcp_id=sample_mcp_id, context_type=MCPContextType.INSTANCE, data={})
    context2 = MCPContext(mcp_id=sample_mcp_id, context_type=MCPContextType.TRAINING, data={})
    
    await redis_repository.save(context1)
    await redis_repository.save(context2)
    
    # Delete all
    count = await redis_repository.delete_by_mcp_id(sample_mcp_id)
    assert count == 2
    
    # Verify deleted
    contexts = await redis_repository.find_by_mcp_id(sample_mcp_id)
    assert len(contexts) == 0


@pytest.mark.asyncio
async def test_count_operations(redis_repository):
    """Test count operations."""
    # Create contexts
    context1 = MCPContext(mcp_id="mcp-1", context_type=MCPContextType.TRAINING, data={})
    context2 = MCPContext(mcp_id="mcp-2", context_type=MCPContextType.TRAINING, data={})
    context3 = MCPContext(mcp_id="mcp-3", context_type=MCPContextType.INSTANCE, data={})
    
    await redis_repository.save(context1)
    await redis_repository.save(context2)
    await redis_repository.save(context3)
    
    # Count all
    total_count = await redis_repository.count()
    assert total_count == 3
    
    # Count by type
    training_count = await redis_repository.count_by_type(MCPContextType.TRAINING)
    assert training_count == 2
    
    instance_count = await redis_repository.count_by_type(MCPContextType.INSTANCE)
    assert instance_count == 1


@pytest.mark.asyncio
async def test_update_context(redis_repository, sample_context):
    """Test updating an existing context."""
    # Save initial
    await redis_repository.save(sample_context)
    
    # Update
    sample_context.update_data({"queries_today": 200})
    await redis_repository.save(sample_context)
    
    # Retrieve and verify
    retrieved = await redis_repository.find_by_id(sample_context.id)
    assert retrieved.data["queries_today"] == 200
    assert retrieved.version == 2

