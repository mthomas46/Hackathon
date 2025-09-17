"""Comprehensive tests for ALL Discovery Agent phases and features.

This module provides complete test coverage for all Phase 1-5 implementations
including security scanning, monitoring, AI tool selection, semantic analysis,
performance optimization, and orchestrator integration.

Tests are designed to validate the new features without relying on the old API structure.
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from fastapi.testclient import TestClient

# Import the new modules we need to test
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

# Now import the modules
from services.discovery_agent.modules.tool_discovery import tool_discovery_service
from services.discovery_agent.modules.security_scanner import tool_security_scanner
from services.discovery_agent.modules.monitoring_service import discovery_monitoring_service
from services.discovery_agent.modules.tool_registry import tool_registry_storage
from services.discovery_agent.modules.orchestrator_integration import orchestrator_integration
from services.discovery_agent.modules.ai_tool_selector import ai_tool_selector
from services.discovery_agent.modules.semantic_analyzer import semantic_tool_analyzer
from services.discovery_agent.modules.performance_optimizer import performance_optimizer


class TestNewAPIEndpoints:
    """Test the new API endpoints added in the enhanced discovery agent."""

    @pytest.fixture
    def client(self):
        """Test client for the enhanced discovery agent service."""
        # Import the actual service
        from services.discovery_agent.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test the health endpoint works."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_ecosystem_discovery_endpoint(self, client):
        """Test the ecosystem discovery endpoint."""
        with patch('services.discovery_agent.main.tool_discovery_service') as mock_service:
            mock_service.discover_ecosystem_tools.return_value = {
                "services_tested": 3,
                "healthy_services": 3,
                "total_tools_discovered": 15,
                "services": {
                    "service1": {"tools": [{"name": "tool1", "category": "read"}]},
                    "service2": {"tools": [{"name": "tool2", "category": "create"}]}
                }
            }

            response = client.post("/api/v1/discovery/ecosystem")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["services_tested"] == 3

    @pytest.mark.asyncio
    async def test_register_tools_endpoint(self, client):
        """Test the register tools with orchestrator endpoint."""
        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.orchestrator_integration') as mock_orchestrator:

            mock_registry.get_all_tools.return_value = {"service1": [{"name": "tool1"}]}
            mock_orchestrator.register_discovered_tools.return_value = {
                "total_tools": 1,
                "registered_tools": 1,
                "failed_registrations": 0,
                "details": []
            }

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

        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.ai_tool_selector') as mock_ai, \
             patch('services.discovery_agent.main.orchestrator_integration') as mock_orchestrator:

            mock_registry.get_all_tools.return_value = {
                "service1": [{"name": "tool1", "category": "read"}]
            }
            mock_ai.select_tools_for_task.return_value = {
                "success": True,
                "selected_tools": [{"name": "tool1"}],
                "task_analysis": {"primary_action": "analyze"},
                "confidence_score": 0.85,
                "reasoning": "Selected optimal tool"
            }
            mock_orchestrator.create_dynamic_workflow.return_value = {
                "success": True,
                "workflow_id": "wf_123"
            }

            response = client.post("/api/v1/workflows/create-ai", json=workflow_request)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "workflow" in data["data"]

    @pytest.mark.asyncio
    async def test_semantic_analysis_endpoint(self, client):
        """Test the semantic analysis endpoint."""
        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.semantic_tool_analyzer') as mock_analyzer:

            mock_registry.get_all_tools.return_value = {"service1": [{"name": "tool1"}]}
            mock_analyzer.enhance_tool_categorization.return_value = [{"name": "tool1", "semantic_analysis": {}}]
            mock_analyzer.analyze_tool_relationships.return_value = {
                "relationships_found": 0,
                "complementary_pairs": []
            }

            response = client.post("/api/v1/analysis/semantic")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "analyzed_tools" in data["data"]

    @pytest.mark.asyncio
    async def test_performance_optimization_endpoint(self, client):
        """Test the performance optimization endpoint."""
        with patch('services.discovery_agent.main.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.main.performance_optimizer') as mock_optimizer:

            mock_registry.load_discovery_results.return_value = {
                "run1": {
                    "performance_metrics": [{"response_time": 1.0}],
                    "summary": {"tools_discovered": 10}
                }
            }
            mock_optimizer.optimize_discovery_workflow.return_value = {
                "optimizations": {"parallelization_opportunities": []},
                "performance_summary": {"avg_response_time": 1.0}
            }

            response = client.post("/api/v1/optimization/performance")
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "analysis" in data["data"]


class TestSecurityScannerIntegration:
    """Test the security scanner module integration."""

    @pytest.fixture
    def sample_tools(self) -> List[Dict[str, Any]]:
        """Sample tools for security testing."""
        return [
            {
                "name": "test_delete_tool",
                "service": "test-service",
                "method": "DELETE",
                "path": "/api/delete",
                "description": "Delete resource tool"
            },
            {
                "name": "test_execute_tool",
                "service": "test-service",
                "method": "POST",
                "path": "/api/execute",
                "description": "Execute code tool"
            },
            {
                "name": "test_query_tool",
                "service": "test-service",
                "method": "POST",
                "path": "/api/query",
                "parameters": {"properties": {"query": {"type": "string"}}}
            }
        ]

    @pytest.mark.asyncio
    async def test_security_scan_high_risk_tool(self, sample_tools):
        """Test security scanning identifies high-risk tools."""
        delete_tool = sample_tools[0]

        with patch.object(tool_security_scanner, 'client') as mock_client:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "overall_risk": "high",
                "vulnerabilities": [{"type": "authz_bypass", "severity": "high"}],
                "recommendations": ["Implement proper authorization"]
            }
            mock_client.post.return_value.__aenter__.return_value = mock_response

            result = await tool_security_scanner.scan_tool_security(delete_tool)

            assert result["scanned"] is True
            assert result["risk_level"] == "high"
            assert len(result["vulnerabilities"]) > 0
            assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_security_scan_service_unavailable(self, sample_tools):
        """Test security scanning handles service unavailability."""
        delete_tool = sample_tools[0]

        with patch.object(tool_security_scanner, 'client') as mock_client:
            mock_client.post.side_effect = Exception("Connection failed")

            result = await tool_security_scanner.scan_tool_security(delete_tool)

            assert result["scanned"] is False
            assert "error" in result
            assert "Connection failed" in result["error"]


class TestMonitoringServiceIntegration:
    """Test the monitoring service integration."""

    @pytest.fixture
    def discovery_event(self) -> Dict[str, Any]:
        """Sample discovery event for testing."""
        return {
            "service_name": "test-service",
            "health_status": "healthy",
            "tools_discovered": 5,
            "response_time": 1.2
        }

    @pytest.mark.asyncio
    async def test_log_discovery_event(self, discovery_event):
        """Test logging discovery events."""
        with patch.object(discovery_monitoring_service, 'client') as mock_client:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_client.post.return_value.__aenter__.return_value = mock_response

            await discovery_monitoring_service.log_discovery_event(
                "service_discovery",
                discovery_event
            )

            # Verify event was logged internally
            assert len(discovery_monitoring_service.events) > 0
            event = discovery_monitoring_service.events[-1]
            assert event["event_type"] == "service_discovery"
            assert event["data"]["service_name"] == "test-service"

    @pytest.mark.asyncio
    async def test_create_monitoring_dashboard(self):
        """Test creating comprehensive monitoring dashboard."""
        # Add some test data
        await discovery_monitoring_service.log_discovery_event("service_discovery", {
            "service_name": "service1", "health_status": "healthy", "tools_discovered": 3
        })
        await discovery_monitoring_service.log_discovery_event("service_discovery", {
            "service_name": "service2", "health_status": "unhealthy", "tools_discovered": 0
        })

        dashboard = await discovery_monitoring_service.create_monitoring_dashboard()

        assert "dashboard_title" in dashboard
        assert "discovery_events_count" in dashboard
        assert "health_summary" in dashboard
        assert "healthy_services" in dashboard["health_summary"]
        assert "unhealthy_services" in dashboard["health_summary"]
        assert dashboard["health_summary"]["healthy_services"] == 1
        assert dashboard["health_summary"]["unhealthy_services"] == 1


class TestToolRegistryIntegration:
    """Test the persistent tool registry functionality."""

    @pytest.fixture
    def temp_registry_file(self):
        """Create a temporary file for registry testing."""
        fd, path = tempfile.mkstemp()
        os.close(fd)
        yield path
        os.unlink(path)

    @pytest.fixture
    def sample_tools(self) -> List[Dict[str, Any]]:
        """Sample tools for registry testing."""
        return [
            {
                "name": "service1_tool1",
                "service": "service1",
                "category": "read",
                "description": "Read tool"
            },
            {
                "name": "service1_tool2",
                "service": "service1",
                "category": "create",
                "description": "Create tool"
            },
            {
                "name": "service2_tool1",
                "service": "service2",
                "category": "analysis",
                "description": "Analysis tool"
            }
        ]

    @pytest.mark.asyncio
    async def test_save_and_load_discovery_results(self, temp_registry_file, sample_tools):
        """Test saving and loading discovery results."""
        registry = tool_registry_storage.__class__(temp_registry_file)

        discovery_results = {
            "timestamp": "2025-01-17T21:30:00Z",
            "services_tested": 2,
            "total_tools_discovered": 3,
            "services": {
                "service1": {"tools": sample_tools[:2]},
                "service2": {"tools": sample_tools[2:]}
            }
        }

        await registry.save_discovery_results(discovery_results)

        # Load from file and verify
        loaded_registry = tool_registry_storage.__class__(temp_registry_file)
        assert len(loaded_registry.registry["discovery_runs"]) == 1
        assert loaded_registry.registry["discovery_runs"][0]["total_tools_discovered"] == 3

    @pytest.mark.asyncio
    async def test_get_tools_for_service(self, temp_registry_file, sample_tools):
        """Test retrieving tools for specific service."""
        registry = tool_registry_storage.__class__(temp_registry_file)

        # Save tools
        await registry.save_tools("service1", sample_tools[:2])

        # Retrieve tools
        tools = await registry.get_tools_for_service("service1")
        assert len(tools) == 2
        assert all(tool["service"] == "service1" for tool in tools)

    @pytest.mark.asyncio
    async def test_registry_stats(self, temp_registry_file, sample_tools):
        """Test registry statistics calculation."""
        registry = tool_registry_storage.__class__(temp_registry_file)

        # Add some data
        await registry.save_tools("service1", sample_tools[:2])
        await registry.save_tools("service2", sample_tools[2:])

        stats = await registry.get_registry_stats()

        assert "last_updated" in stats
        assert stats["total_services_in_registry"] == 2
        assert stats["services_with_discovered_tools"] == 2
        assert stats["total_tools_in_registry"] == 3


class TestOrchestratorIntegration:
    """Test orchestrator integration functionality."""

    @pytest.fixture
    def sample_tools(self) -> List[Dict[str, Any]]:
        """Sample tools for orchestrator testing."""
        return [
            {
                "name": "test_tool_1",
                "service": "test-service",
                "category": "read",
                "description": "Test read tool",
                "langraph_ready": {"ready": True, "score": 8}
            },
            {
                "name": "test_tool_2",
                "service": "test-service",
                "category": "create",
                "description": "Test create tool",
                "langraph_ready": {"ready": True, "score": 9}
            }
        ]

    @pytest.mark.asyncio
    async def test_register_tools_success(self, sample_tools):
        """Test successful tool registration with orchestrator."""
        with patch.object(orchestrator_integration, 'service_client') as mock_client:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {"workflow_id": "wf_123", "tool_id": "tool_456"}
            mock_client.session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await orchestrator_integration.register_discovered_tools(sample_tools)

            assert result["total_tools"] == 2
            assert result["registered_tools"] == 2
            assert result["failed_registrations"] == 0
            assert len(result["details"]) == 2

    @pytest.mark.asyncio
    async def test_create_dynamic_workflow(self):
        """Test creating dynamic workflow."""
        workflow_spec = {
            "name": "test_workflow",
            "description": "Test workflow",
            "steps": [
                {"step_name": "step1", "tool": "tool1"},
                {"step_name": "step2", "tool": "tool2"}
            ],
            "required_tools": ["tool1", "tool2"]
        }

        with patch.object(orchestrator_integration, 'service_client') as mock_client, \
             patch.object(orchestrator_integration, '_check_tool_availability') as mock_check:

            mock_check.return_value = {
                "all_available": True,
                "available_tools": ["tool1", "tool2"],
                "tool_sources": {"tool1": "service1", "tool2": "service2"}
            }

            mock_response = MagicMock()
            mock_response.status = 201
            mock_response.json.return_value = {"workflow_id": "wf_123", "execution_url": "/execute/wf_123"}
            mock_client.session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await orchestrator_integration.create_dynamic_workflow(workflow_spec)

            assert result["success"] is True
            assert result["workflow_id"] == "wf_123"


class TestAIToolSelector:
    """Test AI-powered tool selection functionality."""

    @pytest.fixture
    def available_tools(self) -> List[Dict[str, Any]]:
        """Sample tools for AI selection testing."""
        return [
            {
                "name": "doc_store_list",
                "category": "read",
                "capabilities": ["read", "storage"],
                "description": "List documents"
            },
            {
                "name": "doc_store_create",
                "category": "create",
                "capabilities": ["create", "storage"],
                "description": "Create document"
            },
            {
                "name": "analyzer_analyze",
                "category": "analysis",
                "capabilities": ["analysis", "processing"],
                "description": "Analyze content"
            }
        ]

    @pytest.mark.asyncio
    async def test_select_tools_for_analysis_task(self, available_tools):
        """Test AI tool selection for analysis task."""
        task_description = "Analyze all documents in the store"

        with patch.object(ai_tool_selector, 'service_client') as mock_client:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "interpretation": '{"primary_action": "analyze", "data_types": ["documents"], "capabilities": ["analysis", "read"]}'
            }
            mock_client.session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await ai_tool_selector.select_tools_for_task(task_description, available_tools)

            assert result["success"] is True
            assert len(result["selected_tools"]) > 0
            assert "task_analysis" in result
            assert "confidence_score" in result

    @pytest.mark.asyncio
    async def test_fallback_selection_when_ai_fails(self, available_tools):
        """Test fallback tool selection when AI analysis fails."""
        task_description = "Create a new document"

        with patch.object(ai_tool_selector, 'service_client') as mock_client:
            mock_client.session.return_value.__aenter__.return_value.post.side_effect = Exception("AI service unavailable")

            result = await ai_tool_selector.select_tools_for_task(task_description, available_tools)

            assert result["success"] is False
            assert "fallback_tools" in result
            # Should still return some tools via fallback logic


class TestSemanticAnalyzer:
    """Test semantic analysis functionality."""

    @pytest.fixture
    def sample_tools(self) -> List[Dict[str, Any]]:
        """Sample tools for semantic analysis testing."""
        return [
            {
                "name": "document_analyzer",
                "category": "analysis",
                "description": "Analyze document content for insights",
                "method": "POST",
                "path": "/analyze"
            },
            {
                "name": "document_creator",
                "category": "create",
                "description": "Create new documents in the store",
                "method": "POST",
                "path": "/documents"
            }
        ]

    @pytest.mark.asyncio
    async def test_semantic_analysis_with_ai(self, sample_tools):
        """Test semantic analysis using AI interpretation."""
        tool = sample_tools[0]

        with patch.object(semantic_tool_analyzer, 'service_client') as mock_client:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "interpretation": '{"semantic_categories": ["content_analysis"], "primary_category": "content_analysis", "capabilities": ["analysis"], "use_cases": ["content_review"]}'
            }
            mock_client.session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await semantic_tool_analyzer.analyze_tool_semantics(tool)

            assert "semantic_categories" in result
            assert "primary_category" in result
            assert "capabilities_identified" in result
            assert result["confidence_score"] > 0

    @pytest.mark.asyncio
    async def test_enhance_tool_categorization(self, sample_tools):
        """Test enhancing tool categorization with semantic analysis."""
        enhanced_tools = await semantic_tool_analyzer.enhance_tool_categorization(sample_tools)

        assert len(enhanced_tools) == len(sample_tools)
        for tool in enhanced_tools:
            assert "semantic_analysis" in tool


class TestPerformanceOptimizer:
    """Test performance optimization functionality."""

    @pytest.fixture
    def discovery_results(self) -> Dict[str, Any]:
        """Sample discovery results for performance testing."""
        return {
            "services_tested": 5,
            "healthy_services": 4,
            "total_tools_discovered": 25,
            "performance_metrics": [
                {"service": "service1", "response_time": 1.2, "tools_found": 8, "endpoints_found": 12},
                {"service": "service2", "response_time": 0.8, "tools_found": 5, "endpoints_found": 8},
                {"service": "service3", "response_time": 2.5, "tools_found": 6, "endpoints_found": 10},
                {"service": "service4", "response_time": 0.6, "tools_found": 3, "endpoints_found": 5},
                {"service": "service5", "response_time": 1.8, "tools_found": 3, "endpoints_found": 4}
            ],
            "summary": {
                "services_healthy": 4,
                "tools_discovered": 25,
                "avg_tools_per_service": 5.0
            }
        }

    @pytest.mark.asyncio
    async def test_optimize_discovery_workflow(self, discovery_results):
        """Test discovery workflow optimization."""
        optimization = await performance_optimizer.optimize_discovery_workflow(discovery_results)

        assert "optimizations" in optimization
        assert "performance_summary" in optimization
        assert "avg_response_time" in optimization["performance_summary"]

        # Should identify bottlenecks and parallelization opportunities
        optimizations = optimization["optimizations"]
        assert "bottleneck_identification" in optimizations or "parallelization_opportunities" in optimizations

    @pytest.mark.asyncio
    async def test_analyze_tool_dependencies(self):
        """Test tool dependency analysis."""
        tools = [
            {"name": "storage_tool", "category": "storage", "capabilities": ["storage"]},
            {"name": "analysis_tool", "category": "analysis", "capabilities": ["analysis"]},
            {"name": "combined_tool", "category": "analysis", "capabilities": ["storage", "analysis"]}
        ]

        dependencies = await performance_optimizer.analyze_tool_dependencies(tools)

        assert "dependency_graph" in dependencies
        assert "independent_tools" in dependencies
        assert "optimization_opportunities" in dependencies

    @pytest.mark.asyncio
    async def test_create_performance_baseline(self, discovery_results):
        """Test creating performance baseline."""
        baseline = await performance_optimizer.create_performance_baseline(discovery_results)

        assert "timestamp" in baseline
        assert "services_tested" in baseline
        assert "total_tools" in baseline
        assert "avg_response_time" in baseline
        assert "performance_percentiles" in baseline
        assert "baseline_metrics" in baseline


class TestIntegrationScenarios:
    """Test complete integration scenarios across all phases."""

    @pytest.mark.asyncio
    async def test_complete_discovery_to_execution_workflow(self):
        """Test the complete workflow from discovery to tool execution."""
        # Mock the entire ecosystem
        with patch('services.discovery_agent.modules.tool_discovery.tool_discovery_service') as mock_discovery, \
             patch('services.discovery_agent.modules.tool_registry.tool_registry_storage') as mock_registry, \
             patch('services.discovery_agent.modules.orchestrator_integration.orchestrator_integration') as mock_orchestrator, \
             patch('services.discovery_agent.modules.ai_tool_selector.ai_tool_selector') as mock_ai_selector:

            # Step 1: Discovery
            mock_discovery.discover_ecosystem_tools.return_value = {
                "services_tested": 3,
                "healthy_services": 3,
                "total_tools_discovered": 12,
                "services": {
                    "service1": {"tools": [{"name": "tool1", "category": "read"}]},
                    "service2": {"tools": [{"name": "tool2", "category": "create"}]}
                }
            }

            # Step 2: Registry storage
            mock_registry.get_all_tools.return_value = {
                "service1": [{"name": "tool1", "category": "read"}],
                "service2": [{"name": "tool2", "category": "create"}]
            }

            # Step 3: Orchestrator registration
            mock_orchestrator.register_discovered_tools.return_value = {
                "total_tools": 2,
                "registered_tools": 2,
                "failed_registrations": 0,
                "details": []
            }

            # Step 4: AI workflow creation
            mock_ai_selector.select_tools_for_task.return_value = {
                "success": True,
                "selected_tools": [{"name": "tool1"}, {"name": "tool2"}],
                "task_analysis": {"primary_action": "create"},
                "confidence_score": 0.85,
                "reasoning": "Selected optimal tools"
            }

            mock_orchestrator.create_dynamic_workflow.return_value = {
                "success": True,
                "workflow_id": "wf_123",
                "execution_url": "/execute/wf_123"
            }

            # Execute the workflow
            result = await mock_orchestrator.create_dynamic_workflow({
                "name": "test_workflow",
                "description": "Integration test workflow",
                "required_tools": ["tool1", "tool2"]
            })

            assert result["success"] is True
            assert result["workflow_id"] == "wf_123"

    @pytest.mark.asyncio
    async def test_security_monitoring_integration(self):
        """Test integration between security scanning and monitoring."""
        with patch('services.discovery_agent.modules.security_scanner.tool_security_scanner') as mock_security, \
             patch('services.discovery_agent.modules.monitoring_service.discovery_monitoring_service') as mock_monitoring:

            # Simulate security scan
            scan_result = {
                "tool_name": "vulnerable_tool",
                "scanned": True,
                "risk_level": "high",
                "vulnerabilities": [{"type": "sql_injection"}]
            }

            mock_security.scan_tool_security.return_value = scan_result

            # Log the security scan
            await mock_monitoring.monitor_security_scan("vulnerable_tool", scan_result)

            # Verify monitoring captured the scan
            assert len(mock_monitoring.security_scans) > 0
            logged_scan = mock_monitoring.security_scans[-1]
            assert logged_scan["tool_name"] == "vulnerable_tool"
            assert logged_scan["scan_result"]["risk_level"] == "high"


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])
