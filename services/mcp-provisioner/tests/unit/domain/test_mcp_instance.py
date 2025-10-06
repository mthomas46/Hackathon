"""Unit tests for MCPInstance entity."""

import pytest
from datetime import datetime, timedelta
from domain.entities.mcp_instance import MCPInstance
from domain.value_objects.mcp_state import MCPStateEnum, cold_state, hot_state
from domain.value_objects.mcp_config import default_config_for_tier
from domain.value_objects.resource_limits import small_resources, medium_resources


class TestMCPInstanceCreation:
    """Test MCPInstance creation and initialization."""
    
    def test_create_instance_with_defaults(self):
        """Can create instance with default values."""
        instance = MCPInstance()
        
        assert instance.mcp_id.startswith("mcp-")
        assert instance.state.state == MCPStateEnum.COLD
        assert instance.config is not None
        assert instance.resource_limits is not None
    
    def test_create_instance_with_custom_id(self):
        """Can create instance with custom ID."""
        instance = MCPInstance(mcp_id="mcp-test-123")
        
        assert instance.mcp_id == "mcp-test-123"
    
    def test_create_instance_with_custom_config(self):
        """Can create instance with custom config."""
        config = default_config_for_tier(tier=2, mcp_id="test")
        instance = MCPInstance(config=config)
        
        assert instance.config.tier == 2
    
    def test_instance_starts_in_cold_state(self):
        """New instance starts in COLD state."""
        instance = MCPInstance()
        
        assert instance.state.state == MCPStateEnum.COLD


class TestMCPInstanceProvisioning:
    """Test provisioning state transitions."""
    
    def test_can_start_provisioning_from_cold(self):
        """Can start provisioning from COLD state."""
        instance = MCPInstance()
        
        instance.start_provisioning()
        
        assert instance.state.state == MCPStateEnum.WARMING
    
    def test_cannot_start_provisioning_from_hot(self):
        """Cannot provision when already HOT."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        with pytest.raises(ValueError, match="Cannot provision.*HOT"):
            instance.start_provisioning()
    
    def test_mark_as_hot_sets_runtime_info(self):
        """Marking as HOT sets container ID and endpoint."""
        instance = MCPInstance()
        instance.start_provisioning()
        
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        assert instance.state.state == MCPStateEnum.HOT
        assert instance.container_id == "container-123"
        assert instance.endpoint == "http://localhost:3000"
        assert instance.host_port == 8000
        assert instance.is_healthy
        assert instance.health_check_failures == 0
    
    def test_cannot_mark_as_hot_from_cold(self):
        """Cannot go directly from COLD to HOT."""
        instance = MCPInstance()
        
        with pytest.raises(ValueError, match="Cannot mark as HOT.*WARMING"):
            instance.mark_as_hot("container-123", "http://localhost:3000", 8000)


class TestMCPInstanceShutdown:
    """Test shutdown state transitions."""
    
    def test_can_start_cooling_from_hot(self):
        """Can start cooling down from HOT state."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        instance.start_cooling()
        
        assert instance.state.state == MCPStateEnum.COOLING
    
    def test_cannot_cool_from_cold(self):
        """Cannot cool down when not HOT."""
        instance = MCPInstance()
        
        with pytest.raises(ValueError, match="Cannot cool down.*HOT"):
            instance.start_cooling()
    
    def test_mark_as_cold_clears_runtime_info(self):
        """Marking as COLD clears runtime information."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        instance.start_cooling()
        
        instance.mark_as_cold()
        
        assert instance.state.state == MCPStateEnum.COLD
        assert instance.container_id is None
        assert instance.endpoint is None
        assert instance.host_port is None


class TestMCPInstanceFailure:
    """Test failure handling."""
    
    def test_can_mark_as_failed_from_any_state(self):
        """Can mark as FAILED from any state."""
        # From COLD
        instance = MCPInstance()
        instance.mark_as_failed()
        assert instance.state.state == MCPStateEnum.FAILED
        
        # From WARMING
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_failed()
        assert instance.state.state == MCPStateEnum.FAILED
        
        # From HOT
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        instance.mark_as_failed()
        assert instance.state.state == MCPStateEnum.FAILED
    
    def test_marking_as_failed_sets_unhealthy(self):
        """Marking as FAILED sets is_healthy to False."""
        instance = MCPInstance()
        instance.mark_as_failed()
        
        assert not instance.is_healthy
    
    def test_can_recover_from_failure(self):
        """Can manually recover from FAILED state."""
        instance = MCPInstance()
        instance.mark_as_failed()
        
        instance.recover_from_failure()
        
        assert instance.state.state == MCPStateEnum.COLD
        assert instance.is_healthy
        assert instance.health_check_failures == 0


class TestMCPInstanceQueryManagement:
    """Test query recording and idle detection."""
    
    def test_can_record_query_when_hot(self):
        """Can record query when HOT."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        instance.record_query()
        
        assert instance.query_count == 1
        assert instance.last_query_time is not None
    
    def test_cannot_record_query_when_cold(self):
        """Cannot record query when not HOT."""
        instance = MCPInstance()
        
        with pytest.raises(ValueError, match="Cannot query.*HOT"):
            instance.record_query()
    
    def test_instance_is_idle_when_never_queried(self):
        """Instance is idle if never queried."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        assert instance.is_idle(idle_threshold_minutes=15)
    
    def test_instance_is_idle_after_threshold(self):
        """Instance is idle after threshold time."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        instance.record_query()
        
        # Set last_query_time to 20 minutes ago
        instance.last_query_time = datetime.utcnow() - timedelta(minutes=20)
        
        assert instance.is_idle(idle_threshold_minutes=15)
    
    def test_instance_is_not_idle_within_threshold(self):
        """Instance is not idle within threshold time."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        instance.record_query()
        
        assert not instance.is_idle(idle_threshold_minutes=15)


class TestMCPInstanceHealthManagement:
    """Test health check management."""
    
    def test_update_health_status_success(self):
        """Updating health status to healthy."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        instance.update_health_status(is_healthy=True)
        
        assert instance.is_healthy
        assert instance.health_check_failures == 0
        assert instance.last_health_check is not None
    
    def test_update_health_status_failure_increments_count(self):
        """Health check failure increments failure count."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        instance.update_health_status(is_healthy=False)
        
        assert not instance.is_healthy
        assert instance.health_check_failures == 1
    
    def test_three_failures_marks_as_failed(self):
        """Three consecutive failures marks instance as FAILED."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        instance.update_health_status(is_healthy=False)
        instance.update_health_status(is_healthy=False)
        instance.update_health_status(is_healthy=False)
        
        assert instance.state.state == MCPStateEnum.FAILED
    
    def test_health_success_resets_failure_count(self):
        """Successful health check resets failure count."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        instance.update_health_status(is_healthy=False)
        instance.update_health_status(is_healthy=False)
        instance.update_health_status(is_healthy=True)
        
        assert instance.health_check_failures == 0
    
    def test_needs_health_check_when_never_checked(self):
        """Needs health check if never checked."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        instance.last_health_check = None
        
        assert instance.needs_health_check(interval_seconds=30)
    
    def test_needs_health_check_after_interval(self):
        """Needs health check after interval."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        instance.last_health_check = datetime.utcnow() - timedelta(seconds=60)
        
        assert instance.needs_health_check(interval_seconds=30)
    
    def test_does_not_need_health_check_within_interval(self):
        """Does not need health check within interval."""
        instance = MCPInstance()
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        instance.last_health_check = datetime.utcnow()
        
        assert not instance.needs_health_check(interval_seconds=30)


class TestMCPInstanceResourceManagement:
    """Test resource management."""
    
    def test_update_resource_usage(self):
        """Can update resource usage metrics."""
        instance = MCPInstance()
        
        instance.update_resource_usage(cpu_time=1.5, memory_mb=2048)
        
        assert instance.total_cpu_time == 1.5
        assert instance.total_memory_mb == 2048
    
    def test_is_overloaded_when_cpu_high(self):
        """Instance is overloaded when CPU usage exceeds threshold."""
        instance = MCPInstance(resource_limits=small_resources())
        
        # Set CPU time higher than limit * threshold
        instance.update_resource_usage(cpu_time=0.5 * 0.9, memory_mb=100)
        
        assert instance.is_overloaded(cpu_threshold=0.8)
    
    def test_is_overloaded_when_memory_high(self):
        """Instance is overloaded when memory usage exceeds threshold."""
        instance = MCPInstance(resource_limits=small_resources())
        
        # Set memory higher than limit * threshold
        instance.update_resource_usage(cpu_time=0.1, memory_mb=512 * 0.9)
        
        assert instance.is_overloaded(memory_threshold=0.8)


class TestMCPInstanceSerialization:
    """Test entity serialization."""
    
    def test_to_dict_includes_all_fields(self):
        """to_dict includes all important fields."""
        instance = MCPInstance(mcp_id="test-123")
        instance.start_provisioning()
        instance.mark_as_hot("container-123", "http://localhost:3000", 8000)
        
        data = instance.to_dict()
        
        assert data["mcp_id"] == "test-123"
        assert data["state"] == "hot"
        assert data["container_id"] == "container-123"
        assert data["endpoint"] == "http://localhost:3000"
        assert data["host_port"] == 8000
        assert "tier" in data
        assert "tier_name" in data
        assert "query_count" in data
        assert "is_healthy" in data

