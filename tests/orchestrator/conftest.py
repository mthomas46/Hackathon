#!/usr/bin/env python3
"""
Orchestrator Test Configuration and Fixtures

Shared test configuration, fixtures, and utilities for orchestrator tests.
"""

import pytest
import pytest_asyncio
import asyncio
import sys
import os
import tempfile
import shutil
from typing import Dict, Any, List, Optional, AsyncGenerator
from unittest.mock import Mock, AsyncMock, MagicMock
import aiohttp
from fastapi.testclient import TestClient

# Add services to path
sys.path.insert(0, '/Users/mykalthomas/Documents/work/Hackathon/services')

from orchestrator.main import app
from orchestrator.modules.workflow_management.service import WorkflowManagementService
from orchestrator.modules.workflow_management.models import WorkflowDefinition, WorkflowStatus
from shared.event_streaming import EventStreamProcessor, StreamEvent, EventType, EventPriority
from shared.enterprise_service_mesh import EnterpriseServiceMesh, ServiceIdentity
from shared.health import HealthStatus, DependencyHealth, SystemHealth


# Test Configuration
TEST_CONFIG = {
    "database_url": ":memory:",  # Use in-memory SQLite for tests
    "service_timeout": 5,  # 5 second timeout for service calls
    "max_concurrent_tests": 10,  # Maximum concurrent test execution
    "test_data_retention": 300,  # Keep test data for 5 minutes
    "mock_service_responses": True,  # Use mocked service responses
    "enable_event_logging": False,  # Disable event logging in tests
    "performance_thresholds": {
        "max_workflow_creation_time": 2.0,  # seconds
        "max_workflow_execution_time": 10.0,  # seconds
        "min_requests_per_second": 5,  # for load tests
        "max_memory_usage": 100 * 1024 * 1024,  # 100MB
    }
}


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_client() -> AsyncGenerator[TestClient, None]:
    """Create FastAPI test client."""
    async with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def workflow_service():
    """Create workflow service instance for testing."""
    service = WorkflowManagementService()

    # Clean up any existing test data
    await cleanup_test_workflows(service)

    return service


@pytest_asyncio.fixture(scope="function")
async def event_stream():
    """Create event stream processor for testing."""
    stream = EventStreamProcessor()
    return stream


@pytest_asyncio.fixture(scope="function")
async def service_mesh():
    """Create service mesh instance for testing."""
    mesh = EnterpriseServiceMesh()
    return mesh


@pytest.fixture(scope="function")
def sample_workflow_data() -> Dict[str, Any]:
    """Create sample workflow data for testing."""
    return {
        "name": "Sample Test Workflow",
        "description": "A sample workflow for testing purposes",
        "tags": ["test", "sample"],
        "parameters": [
            {
                "name": "input_text",
                "type": "string",
                "description": "Input text to process",
                "required": True
            },
            {
                "name": "processing_mode",
                "type": "string",
                "description": "Processing mode",
                "required": False,
                "default_value": "standard",
                "allowed_values": ["fast", "standard", "detailed"]
            }
        ],
        "actions": [
            {
                "action_id": "process_input",
                "action_type": "service_call",
                "name": "Process Input",
                "description": "Process the input text",
                "config": {
                    "service": "interpreter",
                    "endpoint": "/process",
                    "method": "POST",
                    "parameters": {
                        "text": "{{input_text}}",
                        "mode": "{{processing_mode}}"
                    }
                }
            },
            {
                "action_id": "generate_output",
                "action_type": "service_call",
                "name": "Generate Output",
                "description": "Generate final output",
                "config": {
                    "service": "summarizer_hub",
                    "endpoint": "/summarize",
                    "method": "POST",
                    "parameters": {
                        "content": "{{process_input.response.content}}",
                        "max_length": 200
                    }
                },
                "depends_on": ["process_input"]
            },
            {
                "action_id": "notify_completion",
                "action_type": "notification",
                "name": "Notify Completion",
                "description": "Send completion notification",
                "config": {
                    "message": "Workflow completed successfully",
                    "channels": ["log"]
                },
                "depends_on": ["generate_output"]
            }
        ]
    }


@pytest.fixture(scope="function")
def complex_workflow_data() -> Dict[str, Any]:
    """Create complex workflow data for advanced testing."""
    return {
        "name": "Complex Integration Workflow",
        "description": "Complex workflow with multiple services and dependencies",
        "tags": ["complex", "integration", "multi-service"],
        "parameters": [
            {
                "name": "github_repo",
                "type": "string",
                "description": "GitHub repository URL",
                "required": True
            },
            {
                "name": "jira_ticket",
                "type": "string",
                "description": "Jira ticket key",
                "required": True
            },
            {
                "name": "analysis_depth",
                "type": "string",
                "description": "Depth of analysis",
                "required": False,
                "default_value": "comprehensive"
            }
        ],
        "actions": [
            {
                "action_id": "parse_github_url",
                "action_type": "transform_data",
                "name": "Parse GitHub URL",
                "description": "Extract repository info from URL",
                "config": {
                    "transformation_type": "parse_github_url",
                    "input_field": "github_repo"
                }
            },
            {
                "action_id": "fetch_github_data",
                "action_type": "service_call",
                "name": "Fetch GitHub Data",
                "description": "Fetch PR data from GitHub",
                "config": {
                    "service": "source_agent",
                    "endpoint": "/github/pr",
                    "method": "GET",
                    "parameters": {
                        "repository": "{{parse_github_url.repository}}",
                        "pr_number": "{{parse_github_url.pr_number}}"
                    }
                },
                "depends_on": ["parse_github_url"]
            },
            {
                "action_id": "fetch_jira_data",
                "action_type": "service_call",
                "name": "Fetch Jira Data",
                "description": "Fetch ticket data from Jira",
                "config": {
                    "service": "source_agent",
                    "endpoint": "/jira/issue",
                    "method": "GET",
                    "parameters": {
                        "issue_key": "{{jira_ticket}}"
                    }
                }
            },
            {
                "action_id": "analyze_code",
                "action_type": "service_call",
                "name": "Analyze Code",
                "description": "Analyze code changes",
                "config": {
                    "service": "code_analyzer",
                    "endpoint": "/analyze",
                    "method": "POST",
                    "parameters": {
                        "code_data": "{{fetch_github_data.response}}",
                        "analysis_depth": "{{analysis_depth}}"
                    }
                },
                "depends_on": ["fetch_github_data"]
            },
            {
                "action_id": "cross_reference",
                "action_type": "service_call",
                "name": "Cross Reference",
                "description": "Cross-reference PR with Jira requirements",
                "config": {
                    "service": "analysis_service",
                    "endpoint": "/cross_reference",
                    "method": "POST",
                    "parameters": {
                        "pr_data": "{{fetch_github_data.response}}",
                        "jira_data": "{{fetch_jira_data.response}}",
                        "code_analysis": "{{analyze_code.response}}"
                    }
                },
                "depends_on": ["fetch_github_data", "fetch_jira_data", "analyze_code"]
            },
            {
                "action_id": "generate_report",
                "action_type": "service_call",
                "name": "Generate Report",
                "description": "Generate comprehensive report",
                "config": {
                    "service": "analysis_service",
                    "endpoint": "/generate_report",
                    "method": "POST",
                    "parameters": {
                        "analysis_results": "{{cross_reference.response}}",
                        "format": "comprehensive"
                    }
                },
                "depends_on": ["cross_reference"]
            },
            {
                "action_id": "notify_stakeholders",
                "action_type": "notification",
                "name": "Notify Stakeholders",
                "description": "Notify relevant stakeholders",
                "config": {
                    "message": "Analysis complete: {{generate_report.response.summary}}",
                    "channels": ["notification_service", "log"],
                    "priority": "normal"
                },
                "depends_on": ["generate_report"]
            }
        ]
    }


@pytest.fixture(scope="function")
def mock_service_responses():
    """Mock service responses for testing."""
    return {
        "source_agent": {
            "/github/pr": {
                "status": "success",
                "data": {
                    "title": "Test PR",
                    "description": "Test pull request",
                    "changes": ["file1.py", "file2.py"],
                    "author": "test_user"
                }
            },
            "/jira/issue": {
                "status": "success",
                "data": {
                    "key": "PROJ-123",
                    "summary": "Test ticket",
                    "description": "Test description",
                    "priority": "high"
                }
            }
        },
        "analysis_service": {
            "/analyze": {
                "status": "success",
                "data": {
                    "quality_score": 0.85,
                    "issues": ["Issue 1", "Issue 2"],
                    "recommendations": ["Fix 1", "Fix 2"]
                }
            },
            "/cross_reference": {
                "status": "success",
                "data": {
                    "confidence_score": 0.75,
                    "matches": ["Requirement A", "Requirement B"],
                    "gaps": ["Missing test coverage"]
                }
            }
        },
        "code_analyzer": {
            "/analyze": {
                "status": "success",
                "data": {
                    "complexity_score": 0.6,
                    "test_coverage": 0.8,
                    "issues": ["Code style issue"]
                }
            }
        },
        "summarizer_hub": {
            "/summarize": {
                "status": "success",
                "data": {
                    "summary": "This is a generated summary of the provided content.",
                    "key_points": ["Point 1", "Point 2", "Point 3"]
                }
            }
        }
    }


@pytest.fixture(scope="function")
async def mock_http_client(mock_service_responses):
    """Create mock HTTP client for testing service calls."""
    class MockHTTPClient:
        def __init__(self, responses):
            self.responses = responses

        async def request(self, method, url, **kwargs):
            # Parse service and endpoint from URL
            # This is a simplified mock - in practice you'd parse the actual URL
            service = "mock_service"
            endpoint = "/test"

            if service in self.responses and endpoint in self.responses[service]:
                response_data = self.responses[service][endpoint]
                mock_response = Mock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value=response_data)
                mock_response.text = AsyncMock(return_value=json.dumps(response_data))
                return mock_response
            else:
                mock_response = Mock()
                mock_response.status = 404
                mock_response.json = AsyncMock(return_value={"error": "Service not found"})
                return mock_response

    return MockHTTPClient(mock_service_responses)


@pytest.fixture(scope="function")
async def test_workflow(workflow_service, sample_workflow_data):
    """Create a test workflow for use in tests."""
    success, message, workflow = await workflow_service.create_workflow(
        sample_workflow_data, "test_user"
    )
    assert success == True

    # Activate workflow
    workflow.status = WorkflowStatus.ACTIVE
    await workflow_service.repository.save_workflow_definition(workflow)

    yield workflow

    # Cleanup
    try:
        await workflow_service.repository.delete_workflow_definition(workflow.workflow_id)
    except:
        pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def performance_monitor():
    """Create performance monitoring fixture."""
    class PerformanceMonitor:
        def __init__(self):
            self.start_times = {}
            self.measurements = {}

        def start_timer(self, name: str):
            """Start timing a operation."""
            self.start_times[name] = asyncio.get_event_loop().time()

        def stop_timer(self, name: str) -> float:
            """Stop timing and return elapsed time."""
            if name in self.start_times:
                elapsed = asyncio.get_event_loop().time() - self.start_times[name]
                self.measurements[name] = elapsed
                return elapsed
            return 0.0

        def get_measurement(self, name: str) -> Optional[float]:
            """Get measurement for a named operation."""
            return self.measurements.get(name)

        def get_all_measurements(self) -> Dict[str, float]:
            """Get all measurements."""
            return self.measurements.copy()

        def assert_performance(self, name: str, max_time: float):
            """Assert that a measurement is within acceptable time."""
            measurement = self.get_measurement(name)
            assert measurement is not None, f"No measurement found for {name}"
            assert measurement <= max_time, f"{name} took {measurement:.3f}s, max allowed {max_time:.3f}s"

    return PerformanceMonitor()


@pytest.fixture(scope="session")
def temp_directory():
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="orchestrator_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


# Utility Functions

async def cleanup_test_workflows(workflow_service: WorkflowManagementService):
    """Clean up test workflows from previous test runs."""
    try:
        # List all workflows
        workflows = await workflow_service.list_workflows()

        # Delete test workflows
        for workflow in workflows:
            if (workflow.created_by == "test_user" or
                workflow.name.startswith("Test") or
                "test" in workflow.name.lower()):
                try:
                    await workflow_service.delete_workflow(workflow.workflow_id)
                except:
                    pass  # Ignore errors during cleanup
    except:
        pass  # Ignore cleanup errors


def assert_workflow_execution_success(execution_result):
    """Assert that workflow execution was successful."""
    success, message, execution = execution_result
    assert success == True, f"Workflow execution failed: {message}"
    assert execution is not None, "Execution result is None"
    assert execution.status.name == "RUNNING", f"Execution status is {execution.status}, expected RUNNING"


def assert_api_response_success(response, expected_status: int = 200):
    """Assert that API response indicates success."""
    assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"

    if response.status_code == 200:
        response_data = response.json()
        if isinstance(response_data, dict) and "success" in response_data:
            assert response_data["success"] == True, f"API call failed: {response_data.get('message', 'Unknown error')}"


def create_test_event(event_type: EventType = EventType.SYSTEM,
                     priority: EventPriority = EventPriority.MEDIUM,
                     payload: Optional[Dict[str, Any]] = None) -> StreamEvent:
    """Create a test event for testing."""
    if payload is None:
        payload = {"test": "data", "timestamp": "2024-01-01T00:00:00Z"}

    return StreamEvent(
        event_id=f"test-event-{asyncio.get_event_loop().time()}",
        event_type=event_type,
        priority=priority,
        source_service="test_orchestrator",
        payload=payload
    )


def create_test_service_identity(service_name: str = "test_service",
                               service_version: str = "1.0.0",
                               environment: str = "test") -> ServiceIdentity:
    """Create a test service identity."""
    return ServiceIdentity(
        service_name=service_name,
        service_version=service_version,
        environment=environment
    )


# Test Data Factories

def create_minimal_workflow_data(name: str = "Minimal Test Workflow") -> Dict[str, Any]:
    """Create minimal workflow data for basic testing."""
    return {
        "name": name,
        "description": "Minimal workflow for testing",
        "parameters": [],
        "actions": [{
            "action_id": "minimal_action",
            "action_type": "notification",
            "name": "Minimal Action",
            "config": {"message": "Minimal test completed"}
        }]
    }


def create_parameterized_workflow_data() -> Dict[str, Any]:
    """Create workflow data with parameters for testing."""
    return {
        "name": "Parameterized Test Workflow",
        "description": "Workflow with parameters for testing",
        "parameters": [
            {
                "name": "required_param",
                "type": "string",
                "required": True,
                "description": "A required parameter"
            },
            {
                "name": "optional_param",
                "type": "integer",
                "required": False,
                "default_value": 42,
                "description": "An optional parameter"
            }
        ],
        "actions": [
            {
                "action_id": "param_action",
                "action_type": "notification",
                "name": "Parameter Action",
                "config": {
                    "message": "Required: {{required_param}}, Optional: {{optional_param}}"
                }
            }
        ]
    }


def create_workflow_with_dependencies() -> Dict[str, Any]:
    """Create workflow data with action dependencies."""
    return {
        "name": "Dependency Test Workflow",
        "description": "Workflow with action dependencies",
        "parameters": [
            {
                "name": "input_data",
                "type": "string",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "step1",
                "action_type": "transform_data",
                "name": "Step 1",
                "description": "First processing step",
                "config": {
                    "transformation_type": "uppercase",
                    "input_data": "{{input_data}}"
                }
            },
            {
                "action_id": "step2",
                "action_type": "transform_data",
                "name": "Step 2",
                "description": "Second processing step",
                "config": {
                    "transformation_type": "reverse",
                    "input_data": "{{step1.output}}"
                },
                "depends_on": ["step1"]
            },
            {
                "action_id": "step3",
                "action_type": "notification",
                "name": "Step 3",
                "description": "Final notification step",
                "config": {
                    "message": "Processing complete: {{step2.output}}"
                },
                "depends_on": ["step2"]
            }
        ]
    }


# Performance Testing Utilities

class LoadTestRunner:
    """Utility for running load tests."""

    def __init__(self, base_url: str = "http://localhost:5080"):
        self.base_url = base_url
        self.session = None

    async def setup(self):
        """Setup load testing environment."""
        self.session = aiohttp.ClientSession()

    async def teardown(self):
        """Cleanup load testing environment."""
        if self.session:
            await self.session.close()

    async def run_load_test(self, endpoint: str, num_requests: int,
                          payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run load test on specified endpoint."""
        start_time = time.time()
        tasks = []

        for i in range(num_requests):
            task = self._make_request(endpoint, payload)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        successful_requests = sum(1 for r in results if not isinstance(r, Exception) and r.status == 200)
        failed_requests = len(results) - successful_requests
        total_time = end_time - start_time
        requests_per_second = len(results) / total_time

        return {
            "total_requests": len(results),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time": total_time,
            "requests_per_second": requests_per_second,
            "average_response_time": total_time / len(results)
        }

    async def _make_request(self, endpoint: str, payload: Optional[Dict[str, Any]]):
        """Make individual request for load testing."""
        async with self.session.post(f"{self.base_url}{endpoint}", json=payload or {}) as response:
            return response


# Test Configuration Validation

def validate_test_configuration():
    """Validate test configuration."""
    required_keys = ["database_url", "service_timeout", "max_concurrent_tests"]

    for key in required_keys:
        assert key in TEST_CONFIG, f"Missing required test configuration: {key}"

    # Validate performance thresholds
    thresholds = TEST_CONFIG.get("performance_thresholds", {})
    assert "max_workflow_creation_time" in thresholds, "Missing workflow creation time threshold"
    assert "max_workflow_execution_time" in thresholds, "Missing workflow execution time threshold"

    print("✅ Test configuration validated successfully")


# Initialize test configuration validation
validate_test_configuration()
