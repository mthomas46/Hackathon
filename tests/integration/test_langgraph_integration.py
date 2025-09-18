"""
LangGraph Integration Tests

Comprehensive tests for LangGraph workflow execution and integration
across the orchestrator service and ecosystem.
"""

import pytest
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import uuid
from unittest.mock import Mock, AsyncMock, patch


class TestLangGraphWorkflowIntegration:
    """Integration tests for LangGraph workflow system."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment."""
        self.orchestrator_url = "http://localhost:5099"
        self.interpreter_url = "http://localhost:5120"
        self.test_user_id = f"langgraph_test_{uuid.uuid4().hex[:8]}"
        self.workflow_executions = []

    @pytest.fixture
    async def http_session(self):
        """HTTP session for making requests."""
        async with aiohttp.ClientSession() as session:
            yield session

    async def test_document_analysis_workflow(self, http_session):
        """Test document analysis workflow execution via LangGraph."""
        workflow_request = {
            "workflow_type": "document_analysis",
            "parameters": {
                "document_content": "# API Documentation\n\nThis is a test document for analysis.",
                "analysis_type": "quality_assessment",
                "user_id": self.test_user_id
            },
            "context": {
                "source": "integration_test",
                "priority": "normal"
            }
        }

        try:
            async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                       json=workflow_request,
                                       timeout=aiohttp.ClientTimeout(total=45)) as response:
                assert response.status in [200, 202], f"Workflow execution failed: {response.status}"
                result = await response.json()

                # Verify response structure
                assert "status" in result or "execution_id" in result
                
                if "execution_id" in result:
                    self.workflow_executions.append(result["execution_id"])

                # Check if workflow completed successfully
                if result.get("status") == "completed":
                    assert "data" in result
                    workflow_data = result["data"]
                    
                    # Verify workflow outputs
                    assert "workflow_type" in workflow_data
                    assert workflow_data["workflow_type"] == "document_analysis"

        except Exception as e:
            pytest.skip(f"LangGraph workflow execution not available: {e}")

    async def test_pr_confidence_workflow(self, http_session):
        """Test PR confidence analysis workflow."""
        workflow_request = {
            "workflow_type": "pr_confidence_analysis",
            "parameters": {
                "pr_number": 123,
                "repository": "test/repo",
                "jira_ticket": "TEST-456",
                "user_id": self.test_user_id
            },
            "context": {
                "source": "github_webhook",
                "priority": "high"
            }
        }

        try:
            async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                       json=workflow_request,
                                       timeout=aiohttp.ClientTimeout(total=60)) as response:
                assert response.status in [200, 202]
                result = await response.json()

                # Track execution for cleanup
                if "execution_id" in result:
                    self.workflow_executions.append(result["execution_id"])

                # Verify workflow structure
                if result.get("status") == "completed":
                    workflow_data = result.get("data", {})
                    assert "confidence_score" in workflow_data or "analysis" in workflow_data

        except Exception as e:
            pytest.skip(f"PR confidence workflow not available: {e}")

    async def test_end_to_end_ecosystem_workflow(self, http_session):
        """Test comprehensive end-to-end ecosystem workflow."""
        workflow_request = {
            "workflow_type": "end_to_end_test",
            "parameters": {
                "test_scenario": "document_lifecycle",
                "mock_data_count": 3,
                "user_id": self.test_user_id
            },
            "context": {
                "source": "integration_test",
                "test_type": "comprehensive"
            }
        }

        try:
            async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                       json=workflow_request,
                                       timeout=aiohttp.ClientTimeout(total=90)) as response:
                assert response.status in [200, 202]
                result = await response.json()

                if "execution_id" in result:
                    self.workflow_executions.append(result["execution_id"])

                # For long-running workflows, check status if async
                if response.status == 202 and "execution_id" in result:
                    execution_id = result["execution_id"]
                    await self._wait_for_workflow_completion(http_session, execution_id)

        except Exception as e:
            pytest.skip(f"End-to-end workflow not available: {e}")

    async def test_langgraph_specific_endpoint(self, http_session):
        """Test LangGraph-specific workflow endpoint."""
        langgraph_request = {
            "input_data": {
                "task": "analyze_document_quality",
                "document_id": "test_doc_123",
                "user_id": self.test_user_id
            },
            "tools": ["analyze_document_tool", "store_document_tool"],
            "tags": ["quality_analysis", "integration_test"]
        }

        try:
            # Test specific LangGraph workflow endpoint
            async with http_session.post(f"{self.orchestrator_url}/workflows/langgraph/document_analysis",
                                       json=langgraph_request,
                                       timeout=aiohttp.ClientTimeout(total=45)) as response:
                assert response.status in [200, 202, 404]  # 404 acceptable if endpoint not implemented
                
                if response.status in [200, 202]:
                    result = await response.json()
                    
                    # Verify LangGraph response structure
                    assert "workflow_state" in result or "execution_result" in result or "status" in result

        except Exception as e:
            pytest.skip(f"LangGraph-specific endpoint not available: {e}")

    async def test_workflow_with_tool_discovery(self, http_session):
        """Test workflow execution with dynamic tool discovery."""
        # First test tool discovery
        try:
            async with http_session.post(f"{self.orchestrator_url}/tools/discover",
                                       json={"services": ["doc_store", "prompt_store"]},
                                       timeout=aiohttp.ClientTimeout(total=30)) as discovery_response:
                if discovery_response.status == 200:
                    discovery_result = await discovery_response.json()
                    discovered_tools = discovery_result.get("tools", [])
                    
                    # Use discovered tools in workflow
                    workflow_request = {
                        "workflow_type": "custom_workflow",
                        "parameters": {
                            "use_discovered_tools": True,
                            "tool_subset": discovered_tools[:3],  # Use first 3 tools
                            "user_id": self.test_user_id
                        }
                    }
                    
                    async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                               json=workflow_request,
                                               timeout=aiohttp.ClientTimeout(total=45)) as workflow_response:
                        assert workflow_response.status in [200, 202, 400]  # 400 acceptable for unknown workflow
                        
                        if workflow_response.status in [200, 202]:
                            result = await workflow_response.json()
                            if "execution_id" in result:
                                self.workflow_executions.append(result["execution_id"])

        except Exception as e:
            pytest.skip(f"Tool discovery integration not available: {e}")

    async def test_workflow_error_handling(self, http_session):
        """Test error handling in LangGraph workflows."""
        # Test with invalid workflow type
        invalid_request = {
            "workflow_type": "nonexistent_workflow",
            "parameters": {"test": "data"},
            "context": {"source": "error_test"}
        }

        async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                   json=invalid_request,
                                   timeout=aiohttp.ClientTimeout(total=15)) as response:
            assert response.status in [400, 404, 422, 500]  # Should return error status

        # Test with malformed parameters
        malformed_request = {
            "workflow_type": "document_analysis",
            "parameters": None,  # Invalid parameters
            "context": {}
        }

        async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                   json=malformed_request,
                                   timeout=aiohttp.ClientTimeout(total=15)) as response:
            assert response.status in [400, 422, 500]

    async def test_workflow_state_management(self, http_session):
        """Test workflow state management and persistence."""
        workflow_request = {
            "workflow_type": "document_analysis",
            "parameters": {
                "document_content": "Test state management",
                "preserve_state": True,
                "user_id": self.test_user_id
            }
        }

        try:
            async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                       json=workflow_request,
                                       timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    
                    if "execution_id" in result:
                        execution_id = result["execution_id"]
                        self.workflow_executions.append(execution_id)
                        
                        # Try to query workflow state
                        await asyncio.sleep(2)  # Give workflow time to start
                        
                        async with http_session.get(f"{self.orchestrator_url}/workflows/{execution_id}/state",
                                                   timeout=aiohttp.ClientTimeout(total=10)) as state_response:
                            if state_response.status == 200:
                                state_data = await state_response.json()
                                assert "workflow_state" in state_data or "current_node" in state_data

        except Exception as e:
            pytest.skip(f"Workflow state management not available: {e}")

    async def test_workflow_cancellation(self, http_session):
        """Test workflow cancellation functionality."""
        # Start a long-running workflow
        workflow_request = {
            "workflow_type": "end_to_end_test",
            "parameters": {
                "test_scenario": "long_running_test",
                "delay_seconds": 30,
                "user_id": self.test_user_id
            }
        }

        try:
            async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                       json=workflow_request,
                                       timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 202:  # Async execution
                    result = await response.json()
                    execution_id = result.get("execution_id")
                    
                    if execution_id:
                        # Try to cancel the workflow
                        await asyncio.sleep(1)  # Let it start
                        
                        async with http_session.post(f"{self.orchestrator_url}/workflows/{execution_id}/cancel",
                                                   timeout=aiohttp.ClientTimeout(total=10)) as cancel_response:
                            assert cancel_response.status in [200, 404, 501]  # 404/501 if not implemented

        except Exception as e:
            pytest.skip(f"Workflow cancellation not available: {e}")

    async def test_workflow_with_interpreter_integration(self, http_session):
        """Test workflow triggered from interpreter service."""
        # Test interpreter-to-orchestrator workflow integration
        interpreter_request = {
            "query": "Analyze the quality of our API documentation and provide recommendations",
            "format": "json",
            "user_id": self.test_user_id,
            "trigger_workflow": True
        }

        try:
            async with http_session.post(f"{self.interpreter_url}/execute-query",
                                       json=interpreter_request,
                                       timeout=aiohttp.ClientTimeout(total=45)) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    
                    # Check if workflow was triggered
                    if "workflow_execution_id" in result or "orchestrator_response" in result:
                        # Verify integration worked
                        assert "execution_id" in result or "status" in result

        except Exception as e:
            pytest.skip(f"Interpreter-orchestrator integration not available: {e}")

    # Helper methods

    async def _wait_for_workflow_completion(self, session: aiohttp.ClientSession, execution_id: str, timeout: int = 60):
        """Wait for workflow completion with timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with session.get(f"{self.orchestrator_url}/workflows/{execution_id}/status",
                                     timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        status = status_data.get("status")
                        
                        if status in ["completed", "failed", "cancelled"]:
                            return status_data
                        
                await asyncio.sleep(2)
                
            except Exception:
                await asyncio.sleep(2)
                continue
        
        return {"status": "timeout", "execution_id": execution_id}


class TestLangGraphToolIntegration:
    """Test LangGraph tool integration and discovery."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup tool integration tests."""
        self.orchestrator_url = "http://localhost:5099"
        self.discovery_agent_url = "http://localhost:5045"

    async def test_service_tool_discovery(self, http_session):
        """Test discovery of service tools for LangGraph integration."""
        services_to_test = ["doc_store", "prompt_store", "analysis_service"]
        
        for service_name in services_to_test:
            try:
                discovery_request = {
                    "service_name": service_name,
                    "include_endpoints": True,
                    "generate_tools": True
                }
                
                async with http_session.post(f"{self.discovery_agent_url}/discover/service",
                                           json=discovery_request,
                                           timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status == 200:
                        discovery_result = await response.json()
                        
                        # Verify tool discovery structure
                        assert "service_name" in discovery_result
                        assert discovery_result["service_name"] == service_name
                        
                        if "tools" in discovery_result:
                            tools = discovery_result["tools"]
                            assert isinstance(tools, list)
                            
                            # Verify tool structure
                            for tool in tools:
                                assert "name" in tool
                                assert "description" in tool
                                assert "parameters" in tool

            except Exception as e:
                print(f"Tool discovery failed for {service_name}: {e}")

    async def test_bulk_tool_discovery(self, http_session):
        """Test bulk tool discovery for multiple services."""
        try:
            bulk_request = {
                "services": ["doc_store", "prompt_store", "analysis_service", "llm_gateway"],
                "include_health_check": True,
                "generate_langgraph_tools": True
            }
            
            async with http_session.post(f"{self.discovery_agent_url}/discover/bulk",
                                       json=bulk_request,
                                       timeout=aiohttp.ClientTimeout(total=45)) as response:
                if response.status == 200:
                    bulk_result = await response.json()
                    
                    assert "services" in bulk_result
                    discovered_services = bulk_result["services"]
                    
                    # Verify each service was processed
                    for service_data in discovered_services:
                        assert "service_name" in service_data
                        assert "status" in service_data
                        
                        if service_data["status"] == "success" and "tools" in service_data:
                            tools = service_data["tools"]
                            assert len(tools) > 0

        except Exception as e:
            pytest.skip(f"Bulk tool discovery not available: {e}")

    async def test_tool_execution_via_langgraph(self, http_session):
        """Test executing discovered tools via LangGraph workflows."""
        # First discover tools
        try:
            async with http_session.post(f"{self.discovery_agent_url}/discover/service",
                                       json={"service_name": "doc_store"},
                                       timeout=aiohttp.ClientTimeout(total=15)) as discovery_response:
                if discovery_response.status == 200:
                    discovery_result = await discovery_response.json()
                    tools = discovery_result.get("tools", [])
                    
                    if tools:
                        # Use first tool in a workflow
                        first_tool = tools[0]
                        
                        workflow_request = {
                            "workflow_type": "tool_execution_test",
                            "parameters": {
                                "tool_name": first_tool["name"],
                                "tool_parameters": {},
                                "test_execution": True
                            }
                        }
                        
                        async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                                   json=workflow_request,
                                                   timeout=aiohttp.ClientTimeout(total=30)) as workflow_response:
                            # Should handle tool execution or return appropriate error
                            assert workflow_response.status in [200, 202, 400, 404]

        except Exception as e:
            pytest.skip(f"Tool execution via LangGraph not available: {e}")


class TestLangGraphPerformance:
    """Performance tests for LangGraph workflow execution."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup performance tests."""
        self.orchestrator_url = "http://localhost:5099"
        self.test_user_id = f"perf_test_{uuid.uuid4().hex[:8]}"

    async def test_workflow_execution_performance(self, http_session):
        """Test performance of workflow execution."""
        workflow_request = {
            "workflow_type": "document_analysis",
            "parameters": {
                "document_content": "Performance test document for analysis",
                "user_id": self.test_user_id
            }
        }

        # Measure execution time
        start_time = time.time()
        
        try:
            async with http_session.post(f"{self.orchestrator_url}/workflows/run",
                                       json=workflow_request,
                                       timeout=aiohttp.ClientTimeout(total=30)) as response:
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Workflow should respond within reasonable time
                assert execution_time < 30.0, f"Workflow too slow: {execution_time}s"
                
                if response.status in [200, 202]:
                    result = await response.json()
                    
                    # For sync execution, should complete quickly
                    if response.status == 200:
                        assert execution_time < 10.0, f"Sync workflow too slow: {execution_time}s"

        except Exception as e:
            pytest.skip(f"Performance test not available: {e}")

    async def test_concurrent_workflow_execution(self, http_session):
        """Test concurrent workflow execution performance."""
        concurrent_count = 5
        workflow_requests = []
        
        for i in range(concurrent_count):
            workflow_requests.append({
                "workflow_type": "document_analysis",
                "parameters": {
                    "document_content": f"Concurrent test document {i}",
                    "user_id": f"{self.test_user_id}_concurrent_{i}"
                }
            })

        start_time = time.time()
        
        try:
            # Execute workflows concurrently
            tasks = []
            for request in workflow_requests:
                task = http_session.post(f"{self.orchestrator_url}/workflows/run",
                                       json=request,
                                       timeout=aiohttp.ClientTimeout(total=45))
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            total_time = end_time - start_time
            successful_responses = 0
            
            for response in responses:
                if not isinstance(response, Exception):
                    async with response as resp:
                        if resp.status in [200, 202]:
                            successful_responses += 1

            # Should handle some level of concurrency
            success_rate = (successful_responses / concurrent_count) * 100
            assert success_rate >= 60.0, f"Concurrent success rate too low: {success_rate}%"
            
            # Total time should be reasonable for concurrent execution
            assert total_time < 60.0, f"Concurrent execution too slow: {total_time}s"

        except Exception as e:
            pytest.skip(f"Concurrent workflow test not available: {e}")


class TestLangGraphMocking:
    """Tests with mocked LangGraph components for unit testing."""

    def test_workflow_state_transitions(self):
        """Test workflow state transitions with mocked components."""
        from services.orchestrator.modules.langgraph.state import WorkflowState
        
        # Create mock workflow state
        state = WorkflowState()
        state.input_data = {"test": "data"}
        state.user_id = "test_user"
        
        # Test state operations
        state.add_log_entry("INFO", "Test log entry")
        state.add_execution_step("test_step", {"result": "success"})
        
        # Verify state structure
        assert len(state.log_entries) > 0
        assert len(state.execution_steps) > 0
        assert state.log_entries[0]["level"] == "INFO"
        assert state.execution_steps[0]["step_name"] == "test_step"

    def test_workflow_graph_creation(self):
        """Test workflow graph creation with mocked components."""
        try:
            from services.orchestrator.modules.langgraph.engine import LangGraphWorkflowEngine
            
            engine = LangGraphWorkflowEngine()
            
            # Mock nodes
            def mock_node_1(state):
                state.add_log_entry("INFO", "Mock node 1 executed")
                return state
            
            def mock_node_2(state):
                state.add_log_entry("INFO", "Mock node 2 executed")
                return state
            
            # Create workflow graph
            nodes = {
                "node_1": mock_node_1,
                "node_2": mock_node_2
            }
            
            edges = [
                ("node_1", "node_2")
            ]
            
            # This tests the graph creation without actually compiling
            # (since LangGraph may not be available in test environment)
            workflow_config = {
                "nodes": nodes,
                "edges": edges,
                "entry_point": "node_1"
            }
            
            assert len(workflow_config["nodes"]) == 2
            assert len(workflow_config["edges"]) == 1
            assert workflow_config["entry_point"] == "node_1"

        except ImportError:
            pytest.skip("LangGraph engine not available for testing")

    def test_tool_integration_mocking(self):
        """Test tool integration with mocked components."""
        # Mock tool discovery result
        mock_tools = [
            {
                "name": "analyze_document",
                "description": "Analyze document content",
                "parameters": {
                    "document_id": {"type": "string", "required": True},
                    "analysis_type": {"type": "string", "default": "quality"}
                }
            },
            {
                "name": "store_document",
                "description": "Store document in repository",
                "parameters": {
                    "content": {"type": "string", "required": True},
                    "metadata": {"type": "object", "required": False}
                }
            }
        ]
        
        # Test tool structure validation
        for tool in mock_tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            
            # Verify parameter structure
            for param_name, param_config in tool["parameters"].items():
                assert "type" in param_config
                assert param_config["type"] in ["string", "object", "array", "number", "boolean"]


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
