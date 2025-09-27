"""Test the new API endpoints for the enhanced Discovery Agent.

This module tests all the new endpoints added in Phases 1-5 without
requiring complex module imports.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Test client for the enhanced discovery agent service."""
    # Import the actual service app
    import sys
    import os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
    sys.path.insert(0, project_root)

    from services.discovery_agent.main import app
    return TestClient(app)


class TestBasicEndpoints:
    """Test basic service endpoints."""

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "discovery-agent"


class TestPhase2EcosystemDiscovery:
    """Test Phase 2 ecosystem discovery endpoints."""

    @pytest.mark.asyncio
    async def test_ecosystem_discovery_endpoint(self, client):
        """Test the ecosystem discovery endpoint."""
        mock_result = {
            "services_tested": 3,
            "healthy_services": 3,
            "total_tools_discovered": 15,
            "services": {
                "service1": {"tools": [{"name": "tool1", "category": "read"}]},
                "service2": {"tools": [{"name": "tool2", "category": "create"}]}
            }
        }

        with patch('services.discovery_agent.main.tool_discovery_service') as mock_service:
            mock_service.discover_ecosystem_tools.return_value = mock_result

            response = client.post("/api/v1/discovery/ecosystem")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["services_tested"] == 3
            assert data["data"]["total_tools_discovered"] == 15


class TestPhase3OrchestratorIntegration:
    """Test Phase 3 orchestrator integration endpoints."""

    @pytest.mark.asyncio
    async def test_register_tools_endpoint(self, client):
        """Test the register tools with orchestrator endpoint."""
        mock_tools = {"service1": [{"name": "tool1"}]}
        mock_registration = {
            "total_tools": 1,
            "registered_tools": 1,
            "failed_registrations": 0,
            "details": []
        }

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.orchestrator_integration') as mock_orchestrator:

            mock_registry.get_all_tools.return_value = mock_tools
            mock_orchestrator.register_discovered_tools.return_value = mock_registration

            response = client.post("/api/v1/orchestrator/register-tools")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["registered_tools"] == 1

    @pytest.mark.asyncio
    async def test_ai_workflow_creation_endpoint(self, client):
        """Test the AI-powered workflow creation endpoint."""
        workflow_request = {
            "task_description": "Analyze all documents in the store",
            "name": "test_workflow"
        }

        mock_tools = {"service1": [{"name": "tool1", "category": "read"}]}
        mock_selection = {
            "success": True,
            "selected_tools": [{"name": "tool1"}],
            "task_analysis": {"primary_action": "analyze"},
            "confidence_score": 0.85,
            "reasoning": "Selected optimal tool"
        }
        mock_workflow = {
            "success": True,
            "workflow_id": "wf_123"
        }

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.ai_tool_selector') as mock_ai, \
             patch('services.discovery_agent.main.orchestrator_integration') as mock_orchestrator:

            mock_registry.get_all_tools.return_value = mock_tools
            mock_ai.select_tools_for_task.return_value = mock_selection
            mock_orchestrator.create_dynamic_workflow.return_value = mock_workflow

            response = client.post("/api/v1/workflows/create-ai", json=workflow_request)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "workflow" in data["data"]

    @pytest.mark.asyncio
    async def test_ai_workflow_creation_missing_description(self, client):
        """Test AI workflow creation with missing task description."""
        workflow_request = {"name": "test_workflow"}  # Missing task_description

        response = client.post("/api/v1/workflows/create-ai", json=workflow_request)
        assert response.status_code == 200  # Should return error response

        data = response.json()
        assert data["success"] is False
        assert "task_description is required" in data["error"]


class TestPhase4SemanticAnalysis:
    """Test Phase 4 semantic analysis endpoints."""

    @pytest.mark.asyncio
    async def test_semantic_analysis_endpoint(self, client):
        """Test the semantic analysis endpoint."""
        mock_tools = {"service1": [{"name": "tool1"}]}
        mock_analysis = {
            "relationships_found": 0,
            "complementary_pairs": []
        }

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.semantic_tool_analyzer') as mock_analyzer:

            mock_registry.get_all_tools.return_value = mock_tools
            mock_analyzer.enhance_tool_categorization.return_value = [{"name": "tool1", "semantic_analysis": {}}]
            mock_analyzer.analyze_tool_relationships.return_value = mock_analysis

            response = client.post("/api/v1/analysis/semantic")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "analyzed_tools" in data["data"]
            assert data["data"]["relationships_found"] == 0


class TestPhase5PerformanceOptimization:
    """Test Phase 5 performance optimization endpoints."""

    @pytest.mark.asyncio
    async def test_performance_optimization_endpoint(self, client):
        """Test the performance optimization endpoint."""
        mock_results = {
            "run1": {
                "performance_metrics": [{"response_time": 1.0}],
                "summary": {"tools_discovered": 10}
            }
        }
        mock_optimization = {
            "optimizations": {"parallelization_opportunities": []},
            "performance_summary": {"avg_response_time": 1.0}
        }

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.performance_optimizer') as mock_optimizer:

            mock_registry.load_discovery_results.return_value = mock_results
            mock_optimizer.optimize_discovery_workflow.return_value = mock_optimization

            response = client.post("/api/v1/optimization/performance")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "analysis" in data["data"]

    @pytest.mark.asyncio
    async def test_dependency_analysis_endpoint(self, client):
        """Test the tool dependency analysis endpoint."""
        mock_tools = {"service1": [{"name": "tool1"}]}
        mock_dependencies = {
            "dependency_graph": {},
            "independent_tools": ["tool1"],
            "optimization_opportunities": []
        }

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.performance_optimizer') as mock_optimizer:

            mock_registry.get_all_tools.return_value = mock_tools
            mock_optimizer.analyze_tool_dependencies.return_value = mock_dependencies

            response = client.post("/api/v1/optimization/dependencies")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "independent_tools" in data["data"]["dependency_analysis"]

    @pytest.mark.asyncio
    async def test_performance_baseline_endpoint(self, client):
        """Test the performance baseline creation endpoint."""
        mock_results = {
            "services_tested": 3,
            "total_tools_discovered": 15,
            "performance_metrics": [{"response_time": 1.0}]
        }
        mock_baseline = {
            "timestamp": "2025-01-17T21:30:00Z",
            "services_tested": 3,
            "total_tools": 15
        }

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.performance_optimizer') as mock_optimizer:

            mock_registry.load_discovery_results.return_value = {"latest": mock_results}
            mock_optimizer.create_performance_baseline.return_value = mock_baseline

            response = client.post("/api/v1/optimization/baseline")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "baseline" in data["data"]

    @pytest.mark.asyncio
    async def test_optimization_status_endpoint(self, client):
        """Test the optimization status endpoint."""
        mock_stats = {
            "total_tools": 10,
            "services_with_discovered_tools": 3,
            "last_updated": "2025-01-17T21:30:00Z"
        }

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry:
            mock_registry.get_registry_stats.return_value = mock_stats

            response = client.get("/api/v1/optimization/status")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "registry_health" in data["data"]
            assert data["data"]["registry_health"]["total_tools"] == 10


class TestRegistryEndpoints:
    """Test the registry query endpoints."""

    @pytest.mark.asyncio
    async def test_registry_tools_endpoint(self, client):
        """Test querying tools from registry."""
        mock_tools = [
            {"name": "tool1", "service": "service1", "category": "read"},
            {"name": "tool2", "service": "service2", "category": "create"}
        ]
        mock_all_tools = {"service1": mock_tools[:1], "service2": mock_tools[1:]}

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry:
            mock_registry.get_all_tools.return_value = mock_all_tools

            response = client.get("/api/v1/registry/tools")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "tools" in data["data"]
            assert len(data["data"]["tools"]) == 2

    @pytest.mark.asyncio
    async def test_registry_stats_endpoint(self, client):
        """Test getting registry statistics."""
        mock_stats = {
            "total_tools_in_registry": 15,
            "services_with_discovered_tools": 5,
            "last_updated": "2025-01-17T21:30:00Z"
        }

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry:
            mock_registry.get_registry_stats.return_value = mock_stats

            response = client.get("/api/v1/registry/stats")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_tools_in_registry"] == 15


class TestMonitoringEndpoints:
    """Test the monitoring and dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_monitoring_dashboard_endpoint(self, client):
        """Test getting monitoring dashboard."""
        mock_dashboard = {
            "dashboard_title": "Discovery Agent Monitoring Dashboard",
            "discovery_events_count": 5,
            "health_summary": {"healthy_services": 4, "unhealthy_services": 1}
        }

        with patch('services.discovery_agent.main.discovery_monitoring_service') as mock_monitoring:
            mock_monitoring.create_monitoring_dashboard.return_value = mock_dashboard

            response = client.get("/api/v1/monitoring/dashboard")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "dashboard_title" in data["data"]
            assert data["data"]["discovery_events_count"] == 5


class TestErrorHandling:
    """Test error handling across endpoints."""

    @pytest.mark.asyncio
    async def test_ecosystem_discovery_no_tools(self, client):
        """Test ecosystem discovery when no tools are available."""
        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry:
            mock_registry.get_all_tools.return_value = {}

            response = client.post("/api/v1/orchestrator/register-tools")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["registered_tools"] == 0
            assert "Run ecosystem discovery first" in data["data"]["message"]

    @pytest.mark.asyncio
    async def test_semantic_analysis_no_tools(self, client):
        """Test semantic analysis when no tools are available."""
        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry:
            mock_registry.get_all_tools.return_value = {}

            response = client.post("/api/v1/analysis/semantic")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["analyzed_tools"] == 0
            assert "Run ecosystem discovery first" in data["data"]["message"]

    @pytest.mark.asyncio
    async def test_performance_optimization_no_data(self, client):
        """Test performance optimization when no discovery data exists."""
        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry:
            mock_registry.load_discovery_results.return_value = {}

            response = client.post("/api/v1/optimization/performance")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["optimizations"] == []
            assert "No discovery results found" in data["data"]["message"]


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])
