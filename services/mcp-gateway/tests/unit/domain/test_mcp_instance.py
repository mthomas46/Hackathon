"""Unit tests for MCPInstance entity."""

import pytest
from datetime import datetime, timedelta, timezone

from services.mcp_gateway.domain.entities.mcp_instance import MCPInstance
from services.mcp_gateway.domain.value_objects.mcp_instance_status import MCPInstanceStatus


def test_mcp_instance_creation():
    """Test creating a valid MCPInstance."""
    instance = MCPInstance(
        mcp_id="client-test",
        host="localhost",
        port=3000,
        name="Test MCP"
    )
    
    assert instance.mcp_id == "client-test"
    assert instance.host == "localhost"
    assert instance.port == 3000
    assert instance.name == "Test MCP"
    assert instance.status == MCPInstanceStatus.UNKNOWN
    assert instance.base_url == "http://localhost:3000"
    assert instance.health_check_url == "http://localhost:3000/health"
    assert instance.active_requests == 0
    assert instance.consecutive_failures == 0


def test_mcp_instance_missing_mcp_id():
    """Test that MCPInstance requires mcp_id."""
    with pytest.raises(ValueError, match="must have an mcp_id"):
        MCPInstance(
            mcp_id="",
            host="localhost",
            port=3000
        )


def test_mcp_instance_missing_host():
    """Test that MCPInstance requires host."""
    with pytest.raises(ValueError, match="must have a host"):
        MCPInstance(
            mcp_id="test",
            host="",
            port=3000
        )


def test_mcp_instance_invalid_port():
    """Test that MCPInstance requires valid port."""
    with pytest.raises(ValueError, match="must have a valid port"):
        MCPInstance(
            mcp_id="test",
            host="localhost",
            port=0
        )


def test_update_health_success():
    """Test updating health status when healthy."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000,
        status=MCPInstanceStatus.UNHEALTHY,
        consecutive_failures=3
    )
    
    instance.update_health(is_healthy=True)
    
    assert instance.consecutive_failures == 0
    assert instance.status == MCPInstanceStatus.AVAILABLE
    assert instance.last_health_check is not None


def test_update_health_failure():
    """Test updating health status when unhealthy."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000
    )
    
    # First failure
    instance.update_health(is_healthy=False)
    assert instance.consecutive_failures == 1
    assert instance.status != MCPInstanceStatus.UNHEALTHY
    
    # Second failure
    instance.update_health(is_healthy=False)
    assert instance.consecutive_failures == 2
    
    # Third failure - should mark as unhealthy
    instance.update_health(is_healthy=False)
    assert instance.consecutive_failures == 3
    assert instance.status == MCPInstanceStatus.UNHEALTHY


def test_mark_request_start():
    """Test marking request start."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000,
        max_concurrent_requests=10
    )
    
    assert instance.active_requests == 0
    assert instance.total_requests == 0
    
    instance.mark_request_start()
    
    assert instance.active_requests == 1
    assert instance.total_requests == 1


def test_mark_request_start_reaches_capacity():
    """Test that marking requests updates status when at capacity."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000,
        max_concurrent_requests=2,
        status=MCPInstanceStatus.AVAILABLE
    )
    
    instance.mark_request_start()
    assert instance.status == MCPInstanceStatus.AVAILABLE
    
    instance.mark_request_start()
    assert instance.status == MCPInstanceStatus.BUSY


def test_mark_request_end():
    """Test marking request end."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000
    )
    
    instance.mark_request_start()
    instance.mark_request_end(response_time_ms=150.0)
    
    assert instance.active_requests == 0
    assert instance.total_requests == 1
    assert instance.average_response_time_ms > 0


def test_mark_request_end_updates_status():
    """Test that marking request end updates status from busy to available."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000,
        max_concurrent_requests=10,
        status=MCPInstanceStatus.BUSY
    )
    
    # Add some requests
    for _ in range(10):
        instance.mark_request_start()
    
    # Complete enough to be below 80%
    for _ in range(3):
        instance.mark_request_end(response_time_ms=100.0)
    
    assert instance.status == MCPInstanceStatus.AVAILABLE


def test_set_draining():
    """Test setting instance to draining mode."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000,
        status=MCPInstanceStatus.AVAILABLE
    )
    
    instance.set_draining()
    
    assert instance.status == MCPInstanceStatus.DRAINING


def test_is_available_for_routing():
    """Test checking if instance is available for routing."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000,
        max_concurrent_requests=10,
        status=MCPInstanceStatus.AVAILABLE
    )
    
    assert instance.is_available_for_routing() is True
    
    # Fill to capacity
    for _ in range(10):
        instance.mark_request_start()
    
    assert instance.is_available_for_routing() is False
    
    # Set to unhealthy
    instance.active_requests = 0
    instance.status = MCPInstanceStatus.UNHEALTHY
    
    assert instance.is_available_for_routing() is False


def test_get_load_factor():
    """Test calculating load factor."""
    instance = MCPInstance(
        mcp_id="test",
        host="localhost",
        port=3000,
        max_concurrent_requests=10
    )
    
    assert instance.get_load_factor() == 0.0
    
    for i in range(5):
        instance.mark_request_start()
    
    assert instance.get_load_factor() == 0.5
    
    for i in range(5):
        instance.mark_request_start()
    
    assert instance.get_load_factor() == 1.0


def test_to_dict_from_dict():
    """Test serialization and deserialization."""
    original = MCPInstance(
        id="test-123",
        mcp_id="client-acme",
        name="ACME MCP",
        host="localhost",
        port=3000,
        tier=0,
        priority=100,
        weight=100,
        max_concurrent_requests=50,
        status=MCPInstanceStatus.AVAILABLE,
        tags=["production", "client"],
        metadata={"version": "1.0.0"}
    )
    
    # Mark some activity
    original.mark_request_start()
    original.mark_request_end(response_time_ms=125.5)
    
    # Serialize
    data = original.to_dict()
    
    # Deserialize
    restored = MCPInstance.from_dict(data)
    
    assert restored.id == original.id
    assert restored.mcp_id == original.mcp_id
    assert restored.name == original.name
    assert restored.host == original.host
    assert restored.port == original.port
    assert restored.status == original.status
    assert restored.total_requests == original.total_requests
    assert restored.tags == original.tags
    assert restored.metadata == original.metadata


def test_equality_and_hashing():
    """Test instance equality and hashing."""
    instance1 = MCPInstance(
        id="same-id",
        mcp_id="test",
        host="localhost",
        port=3000
    )
    
    instance2 = MCPInstance(
        id="same-id",
        mcp_id="different",
        host="different",
        port=4000
    )
    
    instance3 = MCPInstance(
        id="different-id",
        mcp_id="test",
        host="localhost",
        port=3000
    )
    
    # Same ID = equal
    assert instance1 == instance2
    assert hash(instance1) == hash(instance2)
    
    # Different ID = not equal
    assert instance1 != instance3
    assert hash(instance1) != hash(instance3)

