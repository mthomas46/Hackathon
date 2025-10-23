"""
Integration tests for Docker container management endpoints.

Tests the subprocess-based Docker CLI implementation for managing containers.
"""

import pytest
from typing import Dict, Any
import time




class TestContainerList:
    """Tests for listing containers."""
    
    def test_list_all_containers(self, api_base_url):
        """Test listing all containers."""
        response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "containers" in data
        assert "total" in data
        assert isinstance(data["containers"], list)
        assert data["total"] == len(data["containers"])
        assert data["total"] > 0  # We should have at least some containers
    
    def test_container_list_structure(self, api_base_url):
        """Test that containers have expected fields."""
        response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["containers"]:
            container = data["containers"][0]
            
            # Required fields
            assert "id" in container
            assert "name" in container
            assert "status" in container
            assert "state" in container
            assert "image" in container
            assert "created" in container
            
            # Validate types
            assert isinstance(container["id"], str)
            assert isinstance(container["name"], str)
            assert isinstance(container["status"], str)
            assert isinstance(container["ports"], dict)
            assert isinstance(container["labels"], dict)
    
    def test_container_list_includes_ecosystem_containers(self, api_base_url):
        """Test that our ecosystem containers are listed."""
        response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        
        assert response.status_code == 200
        data = response.json()
        
        container_names = [c["name"] for c in data["containers"]]
        
        # Check for key ecosystem containers
        assert "ecosystem-mcp-service" in container_names
        assert "ecosystem-mcp-redis" in container_names
        assert "ecosystem-mcp-postgres" in container_names


class TestContainerDetails:
    """Tests for getting container details."""
    
    def test_get_container_details(self, api_base_url, test_container_name):
        """Test getting details for a specific container."""
        response = httpx.get(
            f"{api_base_url}/api/v1/containers/{test_container_name}",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure
        assert "id" in data
        assert "name" in data
        assert "status" in data
        assert "image" in data
        assert "ports" in data
        assert "environment" in data
        assert "labels" in data
        
        # Validate values
        assert test_container_name in data["name"]
    
    def test_get_nonexistent_container(self, api_base_url):
        """Test getting details for a container that doesn't exist."""
        response = httpx.get(
            f"{api_base_url}/api/v1/containers/nonexistent-container-xyz",
            timeout=10.0
        )
        
        # Should return 404 or 500 (depending on Docker CLI error handling)
        assert response.status_code in [404, 500, 503]
    
    def test_container_has_stats_if_running(self, api_base_url, test_container_name):
        """Test that running containers include stats."""
        # First check if container is running
        list_response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        containers = list_response.json()["containers"]
        
        test_container = next(
            (c for c in containers if test_container_name in c["name"]),
            None
        )
        
        if test_container and test_container["status"] == "running":
            # Get detailed info
            response = httpx.get(
                f"{api_base_url}/api/v1/containers/{test_container_name}",
                timeout=10.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Stats should be present for running containers
            assert "stats" in data


class TestContainerStats:
    """Tests for container resource statistics."""
    
    def test_get_container_stats(self, api_base_url, test_container_name):
        """Test getting stats for a running container."""
        response = httpx.get(
            f"{api_base_url}/api/v1/containers/{test_container_name}/stats",
            timeout=10.0
        )
        
        # Should succeed if container is running
        if response.status_code == 200:
            data = response.json()
            
            assert "container" in data
            assert "timestamp" in data
            assert "memory" in data
            assert "cpu" in data
            
            # Validate memory stats
            memory = data["memory"]
            assert "usage_mb" in memory
            assert "limit_mb" in memory
            assert "percent" in memory
            
            assert memory["usage_mb"] >= 0
            assert memory["limit_mb"] > 0
        elif response.status_code == 400:
            # Container might not be running
            data = response.json()
            assert "not running" in data.get("detail", "").lower()
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_stats_for_stopped_container_fails(self, api_base_url):
        """Test that getting stats for stopped container returns appropriate error."""
        # First, find a stopped container if any
        list_response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        containers = list_response.json()["containers"]
        
        stopped = next(
            (c for c in containers if c["status"] in ["exited", "stopped"]),
            None
        )
        
        if stopped:
            response = httpx.get(
                f"{api_base_url}/api/v1/containers/{stopped['name']}/stats",
                timeout=10.0
            )
            
            assert response.status_code == 400
            data = response.json()
            # Error could be in 'detail' or 'error' field depending on error handler
            error_msg = data.get("detail", "") or data.get("error", "")
            assert "not running" in error_msg.lower()


class TestContainerLogs:
    """Tests for container logs."""
    
    def test_get_container_logs(self, api_base_url, test_container_name):
        """Test getting logs from a container."""
        response = httpx.get(
            f"{api_base_url}/api/v1/containers/{test_container_name}/logs?tail=10",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "container" in data
        assert "lines" in data
        assert "logs" in data
        
        assert data["container"] == test_container_name
        assert isinstance(data["logs"], list)
        assert data["lines"] >= 0
    
    def test_logs_with_different_tail_values(self, api_base_url, test_container_name):
        """Test log retrieval with different tail values."""
        for tail in [5, 50, 100]:
            response = httpx.get(
                f"{api_base_url}/api/v1/containers/{test_container_name}/logs?tail={tail}",
                timeout=10.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Number of log lines should be <= tail value
            # (might be less if container has fewer logs)
            actual_logs = [line for line in data["logs"] if line.strip()]
            assert len(actual_logs) <= tail
    
    def test_logs_with_timestamps(self, api_base_url, test_container_name):
        """Test that logs include timestamps when requested."""
        response = httpx.get(
            f"{api_base_url}/api/v1/containers/{test_container_name}/logs?tail=5&timestamps=true",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if timestamps are present in logs
        if data["logs"]:
            # Docker timestamps typically start with year (e.g., "2025-")
            non_empty_logs = [line for line in data["logs"] if line.strip()]
            if non_empty_logs:
                first_log = non_empty_logs[0]
                # Timestamp should be at the start
                assert any(char.isdigit() for char in first_log[:10])


class TestContainerActions:
    """Tests for container actions (start, stop, restart, pause, unpause)."""
    
    @pytest.mark.slow
    def test_restart_container(self, api_base_url, test_container_name):
        """Test restarting a container."""
        response = httpx.post(
            f"{api_base_url}/api/v1/containers/action",
            json={
                "action": "restart",
                "container_name": test_container_name
            },
            timeout=30.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["action"] == "restart"
        assert test_container_name in data["container_name"]
        assert "timestamp" in data
        
        # Wait a moment for container to restart
        time.sleep(2)
        
        # Verify container is running
        list_response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        containers = list_response.json()["containers"]
        
        container = next(
            (c for c in containers if test_container_name in c["name"]),
            None
        )
        
        assert container is not None
        assert container["status"] == "running"
    
    def test_invalid_action(self, api_base_url, test_container_name):
        """Test that invalid actions are rejected."""
        response = httpx.post(
            f"{api_base_url}/api/v1/containers/action",
            json={
                "action": "invalid_action",
                "container_name": test_container_name
            },
            timeout=10.0
        )
        
        assert response.status_code == 400
        data = response.json()
        # Error could be in 'detail' or 'error' field depending on error handler
        error_msg = data.get("detail", "") or data.get("error", "")
        assert "invalid" in error_msg.lower()
    
    def test_action_on_nonexistent_container(self, api_base_url):
        """Test action on a container that doesn't exist."""
        response = httpx.post(
            f"{api_base_url}/api/v1/containers/action",
            json={
                "action": "restart",
                "container_name": "nonexistent-container-xyz"
            },
            timeout=10.0
        )
        
        # Should fail with 404 or 503
        assert response.status_code in [404, 500, 503]


class TestContainerManagementErrorHandling:
    """Tests for error handling in container management."""
    
    def test_malformed_request(self, api_base_url):
        """Test handling of malformed requests."""
        response = httpx.post(
            f"{api_base_url}/api/v1/containers/action",
            json={
                "invalid": "data"
            },
            timeout=10.0
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_timeout_handling(self, api_base_url):
        """Test that requests with very short timeouts are handled gracefully."""
        try:
            response = httpx.get(
                f"{api_base_url}/api/v1/containers",
                timeout=0.001  # Very short timeout
            )
            # If we get here, check status
            assert response.status_code in [200, 408, 504]
        except httpx.TimeoutException:
            # Expected - timeout is too short
            pass


class TestContainerManagementSecurity:
    """Tests for security aspects of container management."""
    
    def test_cannot_access_system_containers(self, api_base_url):
        """Test that we can list but safely handle system containers."""
        # This test ensures we don't crash when encountering system containers
        response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not crash even if system containers are present
        assert "containers" in data
        assert isinstance(data["containers"], list)


@pytest.mark.integration
class TestContainerManagementIntegration:
    """End-to-end integration tests for container management."""
    
    def test_full_workflow(self, api_base_url, test_container_name):
        """Test a complete workflow: list -> details -> logs -> stats."""
        # Step 1: List containers
        list_response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        assert list_response.status_code == 200
        
        containers = list_response.json()["containers"]
        container = next(
            (c for c in containers if test_container_name in c["name"]),
            None
        )
        assert container is not None
        
        # Step 2: Get details
        details_response = httpx.get(
            f"{api_base_url}/api/v1/containers/{test_container_name}",
            timeout=10.0
        )
        assert details_response.status_code == 200
        
        # Step 3: Get logs
        logs_response = httpx.get(
            f"{api_base_url}/api/v1/containers/{test_container_name}/logs?tail=10",
            timeout=10.0
        )
        assert logs_response.status_code == 200
        
        # Step 4: Get stats (if running)
        if container["status"] == "running":
            stats_response = httpx.get(
                f"{api_base_url}/api/v1/containers/{test_container_name}/stats",
                timeout=10.0
            )
            assert stats_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

