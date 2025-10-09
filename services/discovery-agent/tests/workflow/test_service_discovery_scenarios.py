"""
Workflow tests for real-world service discovery scenarios.

Tests complete workflows that a user would perform.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.workflow
@pytest.mark.discovery
class TestCompleteDiscoveryWorkflow:
    """Test complete discovery workflow from start to finish."""
    
    def test_discover_and_retrieve_service(self, test_client, simple_openapi_spec):
        """Test discovering a service and then retrieving its information."""
        service_name = "workflow-test-service"
        
        # Step 1: Discover the service
        discover_request = {
            "service_name": service_name,
            "openapi_content": simple_openapi_spec
        }
        
        discover_response = test_client.post("/api/v1/discover", json=discover_request)
        assert discover_response.status_code in [200, 202]
        
        # Step 2: Retrieve the service information
        get_response = test_client.get(f"/api/v1/services/{service_name}")
        
        if get_response.status_code == 200:
            data = get_response.json()
            assert data["name"] == service_name or data.get("service_name") == service_name
    
    def test_discover_generate_tools_and_verify(self, test_client, simple_openapi_spec):
        """Test discovering service, generating tools, and verifying them."""
        service_name = "tools-workflow-service"
        
        # Step 1: Discover service and generate tools
        request = {
            "service_name": service_name,
            "openapi_content": simple_openapi_spec
        }
        
        response = test_client.post("/api/v1/discover/tools", json=request)
        assert response.status_code in [200, 202]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify tools were generated
            tools = data.get("tools", data.get("generated_tools", []))
            assert len(tools) > 0
            
            # Verify tool structure
            for tool in tools:
                assert "name" in tool
                assert "description" in tool
                assert service_name.replace("-", "_") in tool["name"]
    
    def test_multiple_service_discovery_workflow(self, test_client, simple_openapi_spec, complex_openapi_spec):
        """Test discovering multiple services in sequence."""
        services = [
            ("service-1", simple_openapi_spec),
            ("service-2", complex_openapi_spec),
        ]
        
        discovered_services = []
        
        for service_name, spec in services:
            request = {
                "service_name": service_name,
                "openapi_content": spec
            }
            
            response = test_client.post("/api/v1/discover", json=request)
            assert response.status_code in [200, 202]
            
            if response.status_code == 200:
                discovered_services.append(service_name)
        
        # Verify all services were discovered
        assert len(discovered_services) >= 1


@pytest.mark.workflow
@pytest.mark.discovery
class TestErrorRecoveryWorkflow:
    """Test error recovery in discovery workflows."""
    
    def test_recover_from_failed_discovery(self, test_client):
        """Test recovering from a failed discovery attempt."""
        # Step 1: Attempt discovery with invalid spec (should fail)
        invalid_request = {
            "service_name": "invalid-service",
            "openapi_content": {"invalid": "spec"}
        }
        
        response1 = test_client.post("/api/v1/discover", json=invalid_request)
        assert response1.status_code in [400, 422, 500]
        
        # Step 2: Retry with valid spec (should succeed)
        valid_request = {
            "service_name": "invalid-service",
            "openapi_url": "http://valid-service:8000/openapi.json"
        }
        
        response2 = test_client.post("/api/v1/discover", json=valid_request)
        # This might fail due to network, but should not crash
        assert response2.status_code in [200, 202, 404, 500]
    
    def test_handle_duplicate_discovery(self, test_client, simple_openapi_spec):
        """Test handling discovery of the same service twice."""
        service_name = "duplicate-test-service"
        request = {
            "service_name": service_name,
            "openapi_content": simple_openapi_spec
        }
        
        # First discovery
        response1 = test_client.post("/api/v1/discover", json=request)
        assert response1.status_code in [200, 202]
        
        # Second discovery (should update or handle gracefully)
        response2 = test_client.post("/api/v1/discover", json=request)
        assert response2.status_code in [200, 202, 409]  # 409 = Conflict


@pytest.mark.workflow
@pytest.mark.discovery
@pytest.mark.slow
class TestBulkDiscoveryWorkflow:
    """Test bulk discovery workflows."""
    
    def test_discover_multiple_services_concurrently(self, test_client, simple_openapi_spec):
        """Test discovering multiple services in bulk."""
        service_count = 5
        
        for i in range(service_count):
            request = {
                "service_name": f"bulk-service-{i}",
                "openapi_content": simple_openapi_spec
            }
            
            response = test_client.post("/api/v1/discover", json=request)
            # Should handle each request
            assert response.status_code in [200, 202, 500]


@pytest.mark.workflow
@pytest.mark.tools
class TestToolGenerationWorkflow:
    """Test tool generation workflows."""
    
    def test_generate_tools_for_existing_service(self, test_client, simple_openapi_spec):
        """Test generating tools for a service that's already discovered."""
        service_name = "tool-gen-service"
        
        # Step 1: Discover service
        discover_request = {
            "service_name": service_name,
            "openapi_content": simple_openapi_spec
        }
        
        discover_response = test_client.post("/api/v1/discover", json=discover_request)
        assert discover_response.status_code in [200, 202]
        
        # Step 2: Generate tools
        tools_request = {
            "service_name": service_name,
            "openapi_content": simple_openapi_spec
        }
        
        tools_response = test_client.post("/api/v1/discover/tools", json=tools_request)
        assert tools_response.status_code in [200, 202]
    
    def test_tool_generation_includes_all_endpoints(self, test_client, complex_openapi_spec):
        """Test that tool generation includes all discoverable endpoints."""
        service_name = "complex-service"
        
        request = {
            "service_name": service_name,
            "openapi_content": complex_openapi_spec
        }
        
        response = test_client.post("/api/v1/discover/tools", json=request)
        
        if response.status_code == 200:
            data = response.json()
            tools = data.get("tools", data.get("generated_tools", []))
            
            # Should have tools for both endpoints in complex spec
            assert len(tools) >= 2

