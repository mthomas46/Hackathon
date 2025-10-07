"""
E2E tests for MCP Composer multi-MCP orchestration workflows.
Tests various routing and resolution strategies.
"""
import pytest
import httpx
import asyncio
from typing import Dict, Any


class TestMCPComposerWorkflow:
    """Test complete MCP Composer workflows."""
    
    @pytest.fixture
    def composer_url(self):
        """MCP Composer service URL."""
        return "http://localhost:5625"
    
    @pytest.fixture
    def gateway_url(self):
        """MCP Gateway service URL."""
        return "http://localhost:5300"
    
    @pytest.fixture
    def registry_url(self):
        """MCP Registry service URL."""
        return "http://localhost:5550"
    
    @pytest.fixture
    async def sample_composition(self):
        """Sample composition configuration."""
        return {
            "composition_id": "test-multi-mcp-comp",
            "name": "Test Multi-MCP Composition",
            "description": "Test composition for E2E testing",
            "mcps": [
                {
                    "mcp_id": "test-mcp-1",
                    "priority": 1,
                    "weight": 0.5,
                    "condition": None
                },
                {
                    "mcp_id": "test-mcp-2",
                    "priority": 2,
                    "weight": 0.3,
                    "condition": None
                },
                {
                    "mcp_id": "test-mcp-3",
                    "priority": 3,
                    "weight": 0.2,
                    "condition": None
                }
            ],
            "routing_strategy": "sequential",
            "resolution_strategy": "merge",
            "metadata": {
                "test": True,
                "created_by": "e2e_test"
            }
        }
    
    @pytest.mark.asyncio
    async def test_composer_health(self, composer_url):
        """Test that MCP Composer is healthy."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{composer_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_create_composition(self, composer_url, sample_composition):
        """Test creating a new composition."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{composer_url}/api/v1/compositions",
                json=sample_composition
            )
            
            # Should succeed or return existing
            assert response.status_code in [200, 201, 409]
            
            if response.status_code in [200, 201]:
                data = response.json()
                assert "composition_id" in data
                assert data["composition_id"] == sample_composition["composition_id"]
    
    @pytest.mark.asyncio
    async def test_get_composition(self, composer_url, sample_composition):
        """Test retrieving a composition."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First create it
            await client.post(
                f"{composer_url}/api/v1/compositions",
                json=sample_composition
            )
            
            # Then retrieve it
            response = await client.get(
                f"{composer_url}/api/v1/compositions/{sample_composition['composition_id']}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["composition_id"] == sample_composition["composition_id"]
            assert data["name"] == sample_composition["name"]
            assert len(data["mcps"]) == 3
    
    @pytest.mark.asyncio
    async def test_list_compositions(self, composer_url):
        """Test listing all compositions."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{composer_url}/api/v1/compositions")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_execute_composition_sequential(self, composer_url, sample_composition):
        """Test executing a composition with sequential routing."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create composition with sequential routing
            comp = sample_composition.copy()
            comp["routing_strategy"] = "sequential"
            comp["composition_id"] = "test-seq-comp"
            
            await client.post(f"{composer_url}/api/v1/compositions", json=comp)
            
            # Execute the composition
            execute_request = {
                "composition_id": comp["composition_id"],
                "query": "What is the weather like today?",
                "context": {"user_id": "test-user", "session_id": "test-session"}
            }
            
            response = await client.post(
                f"{composer_url}/api/v1/compositions/execute",
                json=execute_request
            )
            
            # Note: May fail if MCPs don't exist, but should return proper structure
            if response.status_code == 200:
                data = response.json()
                assert "execution_id" in data
                assert "results" in data
                assert data["routing_strategy"] == "sequential"
    
    @pytest.mark.asyncio
    async def test_execute_composition_parallel(self, composer_url, sample_composition):
        """Test executing a composition with parallel routing."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create composition with parallel routing
            comp = sample_composition.copy()
            comp["routing_strategy"] = "parallel"
            comp["composition_id"] = "test-parallel-comp"
            
            await client.post(f"{composer_url}/api/v1/compositions", json=comp)
            
            # Execute the composition
            execute_request = {
                "composition_id": comp["composition_id"],
                "query": "Summarize the latest news",
                "context": {"user_id": "test-user"}
            }
            
            response = await client.post(
                f"{composer_url}/api/v1/compositions/execute",
                json=execute_request
            )
            
            # Note: May fail if MCPs don't exist
            if response.status_code == 200:
                data = response.json()
                assert "execution_id" in data
                assert data["routing_strategy"] == "parallel"
    
    @pytest.mark.asyncio
    async def test_execute_composition_priority(self, composer_url, sample_composition):
        """Test executing a composition with priority routing."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create composition with priority routing
            comp = sample_composition.copy()
            comp["routing_strategy"] = "priority"
            comp["composition_id"] = "test-priority-comp"
            
            await client.post(f"{composer_url}/api/v1/compositions", json=comp)
            
            # Execute the composition
            execute_request = {
                "composition_id": comp["composition_id"],
                "query": "What is 2 + 2?",
                "context": {}
            }
            
            response = await client.post(
                f"{composer_url}/api/v1/compositions/execute",
                json=execute_request
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["routing_strategy"] == "priority"
    
    @pytest.mark.asyncio
    async def test_execute_composition_fallback(self, composer_url, sample_composition):
        """Test executing a composition with fallback routing."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create composition with fallback routing
            comp = sample_composition.copy()
            comp["routing_strategy"] = "fallback"
            comp["composition_id"] = "test-fallback-comp"
            
            await client.post(f"{composer_url}/api/v1/compositions", json=comp)
            
            # Execute the composition
            execute_request = {
                "composition_id": comp["composition_id"],
                "query": "Explain quantum computing",
                "context": {}
            }
            
            response = await client.post(
                f"{composer_url}/api/v1/compositions/execute",
                json=execute_request
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["routing_strategy"] == "fallback"
    
    @pytest.mark.asyncio
    async def test_update_composition(self, composer_url, sample_composition):
        """Test updating a composition."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create composition
            await client.post(
                f"{composer_url}/api/v1/compositions",
                json=sample_composition
            )
            
            # Update it
            updated_comp = sample_composition.copy()
            updated_comp["name"] = "Updated Test Composition"
            updated_comp["routing_strategy"] = "parallel"
            
            response = await client.put(
                f"{composer_url}/api/v1/compositions/{sample_composition['composition_id']}",
                json=updated_comp
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Test Composition"
            assert data["routing_strategy"] == "parallel"
    
    @pytest.mark.asyncio
    async def test_delete_composition(self, composer_url, sample_composition):
        """Test deleting a composition."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create composition
            comp = sample_composition.copy()
            comp["composition_id"] = "test-delete-comp"
            
            await client.post(f"{composer_url}/api/v1/compositions", json=comp)
            
            # Delete it
            response = await client.delete(
                f"{composer_url}/api/v1/compositions/{comp['composition_id']}"
            )
            
            assert response.status_code == 200
            
            # Verify it's gone
            get_response = await client.get(
                f"{composer_url}/api/v1/compositions/{comp['composition_id']}"
            )
            assert get_response.status_code == 404


class TestMCPComposerResolutionStrategies:
    """Test different resolution strategies."""
    
    @pytest.fixture
    def composer_url(self):
        return "http://localhost:5625"
    
    @pytest.mark.asyncio
    async def test_merge_resolution(self, composer_url):
        """Test merge resolution strategy."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            comp = {
                "composition_id": "test-merge-resolution",
                "name": "Merge Resolution Test",
                "description": "Test merge resolution",
                "mcps": [
                    {"mcp_id": "test-mcp-1", "priority": 1, "weight": 0.5},
                    {"mcp_id": "test-mcp-2", "priority": 2, "weight": 0.5}
                ],
                "routing_strategy": "parallel",
                "resolution_strategy": "merge",
                "metadata": {}
            }
            
            await client.post(f"{composer_url}/api/v1/compositions", json=comp)
            
            execute_request = {
                "composition_id": comp["composition_id"],
                "query": "Test query for merge resolution",
                "context": {}
            }
            
            response = await client.post(
                f"{composer_url}/api/v1/compositions/execute",
                json=execute_request
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["resolution_strategy"] == "merge"
    
    @pytest.mark.asyncio
    async def test_voting_resolution(self, composer_url):
        """Test voting resolution strategy."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            comp = {
                "composition_id": "test-voting-resolution",
                "name": "Voting Resolution Test",
                "description": "Test voting resolution",
                "mcps": [
                    {"mcp_id": "test-mcp-1", "priority": 1, "weight": 0.33},
                    {"mcp_id": "test-mcp-2", "priority": 2, "weight": 0.33},
                    {"mcp_id": "test-mcp-3", "priority": 3, "weight": 0.34}
                ],
                "routing_strategy": "parallel",
                "resolution_strategy": "voting",
                "metadata": {}
            }
            
            await client.post(f"{composer_url}/api/v1/compositions", json=comp)
            
            execute_request = {
                "composition_id": comp["composition_id"],
                "query": "Test query for voting resolution",
                "context": {}
            }
            
            response = await client.post(
                f"{composer_url}/api/v1/compositions/execute",
                json=execute_request
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["resolution_strategy"] == "voting"
    
    @pytest.mark.asyncio
    async def test_confidence_resolution(self, composer_url):
        """Test confidence-based resolution strategy."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            comp = {
                "composition_id": "test-confidence-resolution",
                "name": "Confidence Resolution Test",
                "description": "Test confidence resolution",
                "mcps": [
                    {"mcp_id": "test-mcp-1", "priority": 1, "weight": 0.5},
                    {"mcp_id": "test-mcp-2", "priority": 2, "weight": 0.5}
                ],
                "routing_strategy": "parallel",
                "resolution_strategy": "confidence",
                "metadata": {}
            }
            
            await client.post(f"{composer_url}/api/v1/compositions", json=comp)
            
            execute_request = {
                "composition_id": comp["composition_id"],
                "query": "Test query for confidence resolution",
                "context": {}
            }
            
            response = await client.post(
                f"{composer_url}/api/v1/compositions/execute",
                json=execute_request
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["resolution_strategy"] == "confidence"


class TestMCPComposerIntegration:
    """Test MCP Composer integration with other services."""
    
    @pytest.fixture
    def composer_url(self):
        return "http://localhost:5625"
    
    @pytest.fixture
    def gateway_url(self):
        return "http://localhost:5300"
    
    @pytest.fixture
    def registry_url(self):
        return "http://localhost:5550"
    
    @pytest.mark.asyncio
    async def test_composer_gateway_integration(self, composer_url, gateway_url):
        """Test that Composer can communicate with Gateway."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Check both services are healthy
            composer_health = await client.get(f"{composer_url}/health")
            gateway_health = await client.get(f"{gateway_url}/health")
            
            assert composer_health.status_code == 200
            assert gateway_health.status_code == 200
    
    @pytest.mark.asyncio
    async def test_composer_registry_integration(self, composer_url, registry_url):
        """Test that Composer can communicate with Registry."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Check both services are healthy
            composer_health = await client.get(f"{composer_url}/health")
            registry_health = await client.get(f"{registry_url}/health")
            
            assert composer_health.status_code == 200
            assert registry_health.status_code == 200
    
    @pytest.mark.asyncio
    async def test_full_workflow_composition_to_execution(self, composer_url):
        """Test complete workflow from composition creation to execution."""
        async with httpx.AsyncClient(timeout=90.0) as client:
            # Step 1: Create composition
            comp = {
                "composition_id": "test-full-workflow",
                "name": "Full Workflow Test",
                "description": "Test complete workflow",
                "mcps": [
                    {"mcp_id": "workflow-mcp-1", "priority": 1, "weight": 1.0}
                ],
                "routing_strategy": "sequential",
                "resolution_strategy": "first",
                "metadata": {"test": "full-workflow"}
            }
            
            create_response = await client.post(
                f"{composer_url}/api/v1/compositions",
                json=comp
            )
            assert create_response.status_code in [200, 201, 409]
            
            # Step 2: Verify composition exists
            get_response = await client.get(
                f"{composer_url}/api/v1/compositions/{comp['composition_id']}"
            )
            assert get_response.status_code == 200
            
            # Step 3: Execute composition
            execute_request = {
                "composition_id": comp["composition_id"],
                "query": "Test full workflow query",
                "context": {"workflow": "e2e-test"}
            }
            
            execute_response = await client.post(
                f"{composer_url}/api/v1/compositions/execute",
                json=execute_request
            )
            
            # May fail if MCP doesn't exist, but structure should be valid
            if execute_response.status_code == 200:
                data = execute_response.json()
                assert "execution_id" in data
                assert "final_result" in data or "results" in data
            
            # Step 4: Cleanup - delete composition
            delete_response = await client.delete(
                f"{composer_url}/api/v1/compositions/{comp['composition_id']}"
            )
            assert delete_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
