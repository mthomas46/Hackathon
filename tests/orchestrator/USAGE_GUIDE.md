# 🧪 Orchestrator Test Suite Usage Guide

**Practical Examples and Tutorials for Testing the Orchestrator Service**

This guide provides hands-on examples and tutorials for effectively using the orchestrator test suite to validate functionality, ensure quality, and maintain production readiness.

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📝 Writing Your First Test](#-writing-your-first-test)
- [🧪 Test Examples](#-test-examples)
- [🔧 Advanced Testing](#-advanced-testing)
- [🐛 Debugging Tests](#-debugging-tests)
- [📊 Performance Testing](#-performance-testing)
- [🚀 CI/CD Integration](#-ci-cd-integration)
- [📈 Best Practices](#-best-practices)

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Navigate to project directory
cd /Users/mykalthomas/Documents/work/Hackathon

# Set PYTHONPATH (required)
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-xdist

# Verify setup
python -c "import orchestrator; print('✅ Orchestrator import successful')"
```

### 2. Run Your First Test
```bash
# Run a simple test to verify setup
python -m pytest tests/orchestrator/test_orchestrator_features.py::TestOrchestratorWorkflowManagement::test_workflow_creation -v

# Expected output:
# tests/orchestrator/test_orchestrator_features.py::TestOrchestratorWorkflowManagement::test_workflow_creation PASSED
```

### 3. Run Full Test Suite
```bash
# Run all tests
python tests/orchestrator/test_runner.py

# Or run with pytest directly
python -m pytest tests/orchestrator/ -v
```

## 📝 Writing Your First Test

### Basic Test Structure
```python
import pytest
import pytest_asyncio
from orchestrator.modules.workflow_management.service import WorkflowManagementService

class TestMyFeature:
    """Test class for my new feature."""

    @pytest_asyncio.fixture
    async def workflow_service(self):
        """Create workflow service for testing."""
        service = WorkflowManagementService()
        return service

    @pytest.mark.asyncio
    async def test_basic_functionality(self, workflow_service):
        """Test basic functionality of my feature."""
        # Arrange - Set up test data
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "parameters": [
                {
                    "name": "input_text",
                    "type": "string",
                    "description": "Input text to process",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "process",
                    "action_type": "notification",
                    "name": "Process Input",
                    "config": {
                        "message": "{{input_text}}"
                    }
                }
            ]
        }

        # Act - Execute the functionality
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "test_user"
        )

        # Assert - Verify the results
        assert success == True
        assert workflow is not None
        assert workflow.name == "Test Workflow"
        assert len(workflow.parameters) == 1
        assert len(workflow.actions) == 1
```

### Running Your Test
```bash
# Save the test as test_my_feature.py in tests/orchestrator/
# Then run it
python -m pytest tests/orchestrator/test_my_feature.py -v
```

## 🧪 Test Examples

### Example 1: Workflow Creation Test
```python
import pytest
import pytest_asyncio

@pytest.mark.asyncio
async def test_workflow_creation_with_parameters(workflow_service):
    """Test workflow creation with complex parameters."""
    workflow_data = {
        "name": "Complex Parameter Test",
        "description": "Test workflow with multiple parameter types",
        "parameters": [
            {
                "name": "user_name",
                "type": "string",
                "description": "User's full name",
                "required": True
            },
            {
                "name": "user_age",
                "type": "integer",
                "description": "User's age in years",
                "required": False,
                "default_value": 25
            },
            {
                "name": "is_active",
                "type": "boolean",
                "description": "Whether user is active",
                "required": False,
                "default_value": True
            }
        ],
        "actions": [
            {
                "action_id": "validate_user",
                "action_type": "notification",
                "name": "Validate User",
                "config": {
                    "message": "Processing user: {{user_name}} (Age: {{user_age}}, Active: {{is_active}})"
                }
            }
        ]
    }

    success, message, workflow = await workflow_service.create_workflow(
        workflow_data, "test_user"
    )

    assert success == True
    assert workflow is not None
    assert len(workflow.parameters) == 3

    # Verify parameter details
    params = {p.name: p for p in workflow.parameters}
    assert params["user_name"].required == True
    assert params["user_age"].required == False
    assert params["user_age"].default_value == 25
    assert params["is_active"].type == "boolean"
```

### Example 2: Error Handling Test
```python
import pytest
import pytest_asyncio

@pytest.mark.asyncio
async def test_workflow_creation_invalid_data(workflow_service):
    """Test workflow creation with invalid data."""
    # Test missing required field
    invalid_workflow = {
        "description": "Missing name field",
        "parameters": [],
        "actions": []
    }

    success, message, workflow = await workflow_service.create_workflow(
        invalid_workflow, "test_user"
    )

    assert success == False
    assert "name" in message.lower()
    assert workflow is None

@pytest.mark.asyncio
async def test_workflow_creation_duplicate_actions(workflow_service):
    """Test workflow creation with duplicate action IDs."""
    workflow_data = {
        "name": "Duplicate Action Test",
        "description": "Test duplicate action IDs",
        "parameters": [],
        "actions": [
            {
                "action_id": "duplicate",
                "action_type": "notification",
                "name": "First Action",
                "config": {"message": "First"}
            },
            {
                "action_id": "duplicate",  # Duplicate ID
                "action_type": "notification",
                "name": "Second Action",
                "config": {"message": "Second"}
            }
        ]
    }

    success, message, workflow = await workflow_service.create_workflow(
        workflow_data, "test_user"
    )

    assert success == False
    assert "duplicate" in message.lower()
    assert "action_id" in message.lower()
```

### Example 3: Integration Test
```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_workflow_with_service_integration(workflow_service):
    """Test workflow that integrates with external services."""
    workflow_data = {
        "name": "Integration Test Workflow",
        "description": "Test integration with analysis service",
        "parameters": [
            {
                "name": "document_url",
                "type": "string",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "analyze_doc",
                "action_type": "service_call",
                "name": "Analyze Document",
                "config": {
                    "service": "analysis_service",
                    "endpoint": "/analyze",
                    "method": "POST",
                    "parameters": {
                        "url": "{{document_url}}",
                        "analysis_type": "comprehensive"
                    }
                }
            },
            {
                "action_id": "generate_report",
                "action_type": "service_call",
                "name": "Generate Report",
                "config": {
                    "service": "reporting_service",
                    "endpoint": "/generate",
                    "method": "POST",
                    "parameters": {
                        "analysis_result": "{{analyze_doc.response}}",
                        "format": "json"
                    }
                },
                "depends_on": ["analyze_doc"]
            }
        ]
    }

    # Mock the external service calls
    with patch('orchestrator.modules.workflow_management.service.ServiceClients') as mock_clients:
        mock_client = AsyncMock()
        mock_client.make_request.return_value = {
            "status": "success",
            "data": {"quality_score": 85, "issues": []}
        }
        mock_clients.return_value.get_client.return_value = mock_client

        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "test_user"
        )

        assert success == True
        assert len(workflow.actions) == 2

        # Verify dependency resolution
        actions = {a.action_id: a for a in workflow.actions}
        assert "analyze_doc" in actions
        assert "generate_report" in actions
        assert actions["generate_report"].depends_on == ["analyze_doc"]
```

### Example 4: Performance Test
```python
import pytest
import pytest_asyncio
import asyncio
import time
from typing import List

@pytest.mark.asyncio
async def test_concurrent_workflow_execution(workflow_service):
    """Test executing multiple workflows concurrently."""
    # Create a simple workflow
    workflow_data = {
        "name": "Performance Test Workflow",
        "description": "Simple workflow for performance testing",
        "parameters": [
            {
                "name": "input_value",
                "type": "string",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "process",
                "action_type": "notification",
                "name": "Process Input",
                "config": {
                    "message": "Processing: {{input_value}}"
                }
            }
        ]
    }

    # Create workflow
    success, message, workflow = await workflow_service.create_workflow(
        workflow_data, "test_user"
    )
    assert success == True

    # Execute multiple workflows concurrently
    async def execute_workflow(execution_id: int):
        """Execute a single workflow instance."""
        start_time = time.time()
        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id,
            {"input_value": f"Test input {execution_id}"},
            f"user_{execution_id}"
        )
        end_time = time.time()

        return {
            "execution_id": execution_id,
            "success": success,
            "execution_time": end_time - start_time,
            "execution": execution
        }

    # Run concurrent executions
    num_concurrent = 10
    start_time = time.time()

    tasks = [execute_workflow(i) for i in range(num_concurrent)]
    results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # Analyze results
    successful_executions = sum(1 for r in results if r["success"])
    avg_execution_time = sum(r["execution_time"] for r in results) / len(results)

    print(f"Concurrent executions: {num_concurrent}")
    print(f"Successful: {successful_executions}/{num_concurrent}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average execution time: {avg_execution_time:.2f}s")
    print(f"Executions per second: {num_concurrent/total_time:.2f}")

    # Assertions
    assert successful_executions == num_concurrent, "All executions should succeed"
    assert total_time < 30, "Concurrent execution should complete within 30 seconds"
    assert avg_execution_time < 5, "Average execution time should be under 5 seconds"
```

## 🔧 Advanced Testing

### Parameterized Tests
```python
import pytest

@pytest.mark.parametrize("input_text,expected_output", [
    ("Hello World", "HELLO WORLD"),
    ("pytest testing", "PYTEST TESTING"),
    ("", ""),
    ("aBcD", "ABCD"),
])
@pytest.mark.asyncio
async def test_parameterized_uppercase_conversion(workflow_service, input_text, expected_output):
    """Test uppercase conversion with multiple inputs."""
    workflow_data = {
        "name": "Uppercase Conversion",
        "description": "Convert text to uppercase",
        "parameters": [
            {
                "name": "input_text",
                "type": "string",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "uppercase",
                "action_type": "transform",
                "name": "Convert to Uppercase",
                "config": {
                    "transformation": "uppercase",
                    "input_field": "input_text"
                }
            }
        ]
    }

    success, message, workflow = await workflow_service.create_workflow(
        workflow_data, "test_user"
    )
    assert success == True

    # Execute with parameterized input
    success, message, execution = await workflow_service.execute_workflow(
        workflow.workflow_id,
        {"input_text": input_text},
        "test_user"
    )

    assert success == True
    # Verify the transformation result
    # (Implementation depends on your transform action)
```

### Fixture Examples
```python
import pytest
import pytest_asyncio
from typing import Dict, Any

@pytest.fixture
def simple_workflow_data() -> Dict[str, Any]:
    """Simple workflow data fixture."""
    return {
        "name": "Simple Test Workflow",
        "description": "A simple workflow for testing",
        "parameters": [
            {
                "name": "message",
                "type": "string",
                "description": "Message to process",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "notify",
                "action_type": "notification",
                "name": "Send Notification",
                "config": {
                    "message": "{{message}}"
                }
            }
        ]
    }

@pytest.fixture
def complex_workflow_data() -> Dict[str, Any]:
    """Complex workflow with multiple steps."""
    return {
        "name": "Complex Multi-Step Workflow",
        "description": "Workflow with dependencies and multiple services",
        "parameters": [
            {
                "name": "document_url",
                "type": "string",
                "required": True
            },
            {
                "name": "analysis_type",
                "type": "string",
                "required": False,
                "default_value": "comprehensive"
            }
        ],
        "actions": [
            {
                "action_id": "fetch_document",
                "action_type": "service_call",
                "name": "Fetch Document",
                "config": {
                    "service": "source_agent",
                    "endpoint": "/fetch",
                    "method": "POST",
                    "parameters": {"url": "{{document_url}}"}
                }
            },
            {
                "action_id": "analyze_content",
                "action_type": "service_call",
                "name": "Analyze Content",
                "config": {
                    "service": "analysis_service",
                    "endpoint": "/analyze",
                    "method": "POST",
                    "parameters": {
                        "content": "{{fetch_document.response.content}}",
                        "type": "{{analysis_type}}"
                    }
                },
                "depends_on": ["fetch_document"]
            },
            {
                "action_id": "generate_summary",
                "action_type": "service_call",
                "name": "Generate Summary",
                "config": {
                    "service": "summarizer_hub",
                    "endpoint": "/summarize",
                    "method": "POST",
                    "parameters": {
                        "text": "{{analyze_content.response.summary}}",
                        "max_length": 200
                    }
                },
                "depends_on": ["analyze_content"]
            }
        ]
    }

@pytest_asyncio.fixture
async def initialized_workflow_service():
    """Workflow service with test data cleanup."""
    service = WorkflowManagementService()

    # Clean up any existing test workflows
    await cleanup_test_workflows(service)

    yield service

    # Cleanup after tests
    await cleanup_test_workflows(service)

async def cleanup_test_workflows(service):
    """Clean up test workflows."""
    # Implementation to remove test workflows
    pass
```

### Mocking External Services
```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_workflow_with_mocked_services(workflow_service):
    """Test workflow execution with mocked external services."""

    # Create workflow that calls external services
    workflow_data = {
        "name": "Mocked Service Test",
        "description": "Test with mocked services",
        "parameters": [
            {
                "name": "input_data",
                "type": "string",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "call_analysis",
                "action_type": "service_call",
                "name": "Call Analysis Service",
                "config": {
                    "service": "analysis_service",
                    "endpoint": "/analyze",
                    "method": "POST",
                    "parameters": {
                        "data": "{{input_data}}"
                    }
                }
            }
        ]
    }

    # Mock the service client
    with patch('orchestrator.modules.workflow_management.service.ServiceClients') as mock_clients_class:
        # Create mock client instance
        mock_client_instance = MagicMock()
        mock_clients_class.return_value.get_client.return_value = mock_client_instance

        # Mock the response
        mock_response = {
            "status": "success",
            "data": {
                "analysis_result": "positive",
                "confidence_score": 0.95
            }
        }
        mock_client_instance.make_request = AsyncMock(return_value=mock_response)

        # Create and execute workflow
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "test_user"
        )
        assert success == True

        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id,
            {"input_data": "test input data"},
            "test_user"
        )

        # Verify the mock was called correctly
        assert success == True
        mock_client_instance.make_request.assert_called_once_with(
            "POST",
            "/analyze",
            {"data": "test input data"}
        )
```

## 🐛 Debugging Tests

### Common Debugging Techniques

#### 1. Print Debug Information
```python
@pytest.mark.asyncio
async def test_debug_workflow_creation(workflow_service):
    """Test with detailed debugging information."""
    workflow_data = {
        "name": "Debug Test Workflow",
        "description": "Workflow for debugging",
        "parameters": [],
        "actions": []
    }

    print("=== DEBUG: Creating workflow ===")
    print(f"Workflow data: {workflow_data}")

    success, message, workflow = await workflow_service.create_workflow(
        workflow_data, "test_user"
    )

    print(f"Success: {success}")
    print(f"Message: {message}")
    print(f"Workflow: {workflow}")

    if workflow:
        print(f"Workflow ID: {workflow.workflow_id}")
        print(f"Created at: {workflow.created_at}")

    assert success == True
```

#### 2. Step-by-Step Execution
```python
@pytest.mark.asyncio
async def test_step_by_step_execution(workflow_service):
    """Test execution step by step."""
    # Step 1: Create workflow
    print("Step 1: Creating workflow...")
    workflow_data = {
        "name": "Step Test Workflow",
        "description": "Step-by-step testing",
        "parameters": [
            {"name": "test_param", "type": "string", "required": True}
        ],
        "actions": [
            {
                "action_id": "test_action",
                "action_type": "notification",
                "name": "Test Action",
                "config": {"message": "Test: {{test_param}}"}
            }
        ]
    }

    success, message, workflow = await workflow_service.create_workflow(
        workflow_data, "test_user"
    )
    assert success == True, f"Step 1 failed: {message}"
    print("✅ Step 1: Workflow created successfully")

    # Step 2: Verify workflow structure
    print("Step 2: Verifying workflow structure...")
    assert workflow.name == "Step Test Workflow"
    assert len(workflow.parameters) == 1
    assert len(workflow.actions) == 1
    print("✅ Step 2: Workflow structure verified")

    # Step 3: Execute workflow
    print("Step 3: Executing workflow...")
    success, message, execution = await workflow_service.execute_workflow(
        workflow.workflow_id,
        {"test_param": "Hello Debug"},
        "test_user"
    )
    assert success == True, f"Step 3 failed: {message}"
    print("✅ Step 3: Workflow executed successfully")

    print("🎉 All steps completed successfully!")
```

#### 3. Exception Handling and Logging
```python
import logging

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_with_exception_handling(workflow_service):
    """Test with comprehensive exception handling."""
    try:
        workflow_data = {
            "name": "Exception Test Workflow",
            "description": "Test exception handling",
            "parameters": [],
            "actions": []
        }

        logger.info("Creating workflow...")
        success, message, workflow = await workflow_service.create_workflow(
            workflow_data, "test_user"
        )

        if not success:
            logger.error(f"Workflow creation failed: {message}")
            # Try to understand why it failed
            logger.debug(f"Workflow data: {workflow_data}")
            logger.debug(f"User: test_user")

        assert success == True, f"Workflow creation failed: {message}"
        logger.info("✅ Workflow created successfully")

    except Exception as e:
        logger.exception("Unexpected error during test")
        # Log additional context
        logger.debug(f"Workflow service: {workflow_service}")
        logger.debug(f"Python path: {__file__}")
        raise
```

#### 4. Using pytest Fixtures for Debugging
```python
@pytest.fixture(autouse=True)
def enable_debug_logging():
    """Enable debug logging for all tests."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

@pytest.fixture
def debug_workflow_service(workflow_service):
    """Workflow service with debug logging."""
    original_create = workflow_service.create_workflow

    async def debug_create_workflow(*args, **kwargs):
        print("🔍 DEBUG: create_workflow called")
        print(f"   Args: {args}")
        print(f"   Kwargs: {kwargs}")
        result = await original_create(*args, **kwargs)
        print(f"   Result: {result}")
        return result

    workflow_service.create_workflow = debug_create_workflow
    return workflow_service
```

### Debugging Commands

#### Run Tests with Verbose Output
```bash
# Maximum verbosity
python -m pytest tests/orchestrator/test_debug_example.py -vvv

# Show local variables on failure
python -m pytest tests/orchestrator/test_debug_example.py -vv --tb=long

# Stop at first failure
python -m pytest tests/orchestrator/test_debug_example.py -x
```

#### Run Specific Test with Debug
```bash
# Run single test with detailed output
python -m pytest tests/orchestrator/test_debug_example.py::TestDebug::test_specific_scenario -vv -s

# Run with Python debugger
python -m pytest tests/orchestrator/test_debug_example.py::TestDebug::test_specific_scenario --pdb
```

#### Profile Test Performance
```bash
# Show slowest tests
python -m pytest tests/orchestrator/ --durations=10

# Profile specific test
python -c "
import cProfile
import asyncio
from tests.orchestrator.test_debug_example import *
import pstats

async def profile_test():
    service = WorkflowManagementService()
    await test_specific_scenario(service)

cProfile.run('asyncio.run(profile_test())', 'test_profile.prof')
p = pstats.Stats('test_profile.prof')
p.sort_stats('cumulative').print_stats(20)
"
```

## 📊 Performance Testing

### Basic Performance Test
```python
import pytest
import pytest_asyncio
import time
import statistics
from typing import List, Dict

@pytest.mark.asyncio
async def test_workflow_execution_performance(workflow_service):
    """Test workflow execution performance metrics."""
    # Create a simple workflow for testing
    workflow_data = {
        "name": "Performance Test Workflow",
        "description": "Workflow for performance testing",
        "parameters": [
            {
                "name": "input_value",
                "type": "string",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "process",
                "action_type": "notification",
                "name": "Process Input",
                "config": {
                    "message": "{{input_value}}"
                }
            }
        ]
    }

    # Create workflow
    success, message, workflow = await workflow_service.create_workflow(
        workflow_data, "test_user"
    )
    assert success == True

    # Performance test configuration
    num_executions = 50
    execution_times: List[float] = []

    print(f"Running {num_executions} workflow executions for performance testing...")

    # Execute workflow multiple times
    for i in range(num_executions):
        start_time = time.perf_counter()

        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id,
            {"input_value": f"Performance test input {i}"},
            "test_user"
        )

        end_time = time.perf_counter()
        execution_time = end_time - start_time
        execution_times.append(execution_time)

        assert success == True, f"Execution {i} failed: {message}"

        if i % 10 == 0:
            print(f"Completed {i+1}/{num_executions} executions")

    # Calculate performance metrics
    total_time = sum(execution_times)
    avg_time = statistics.mean(execution_times)
    median_time = statistics.median(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)
    throughput = num_executions / total_time

    print("
📊 Performance Results:"    print(f"   Total executions: {num_executions}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time: {avg_time:.3f}s")
    print(f"   Median time: {median_time:.3f}s")
    print(f"   Min time: {min_time:.3f}s")
    print(f"   Max time: {max_time:.3f}s")
    print(f"   Throughput: {throughput:.2f} executions/second")

    # Performance assertions
    assert avg_time < 2.0, f"Average execution time too slow: {avg_time:.3f}s"
    assert throughput > 5.0, f"Throughput too low: {throughput:.2f} executions/s"
    assert max_time < 5.0, f"Maximum execution time too slow: {max_time:.3f}s"
```

### Load Testing with Multiple Concurrent Users
```python
import pytest
import pytest_asyncio
import asyncio
import time
from typing import List, Dict, Any

@pytest.mark.asyncio
async def test_concurrent_load_performance(workflow_service):
    """Test performance under concurrent load."""
    # Create workflow for load testing
    workflow_data = {
        "name": "Load Test Workflow",
        "description": "Workflow for load testing",
        "parameters": [
            {
                "name": "user_id",
                "type": "string",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "user_greeting",
                "action_type": "notification",
                "name": "User Greeting",
                "config": {
                    "message": "Hello {{user_id}}!"
                }
            }
        ]
    }

    # Create workflow
    success, message, workflow = await workflow_service.create_workflow(
        workflow_data, "admin"
    )
    assert success == True

    async def simulate_user(user_id: int) -> Dict[str, Any]:
        """Simulate a single user executing the workflow."""
        start_time = time.perf_counter()

        success, message, execution = await workflow_service.execute_workflow(
            workflow.workflow_id,
            {"user_id": f"user_{user_id}"},
            f"user_{user_id}"
        )

        end_time = time.perf_counter()

        return {
            "user_id": user_id,
            "success": success,
            "execution_time": end_time - start_time,
            "error_message": message if not success else None
        }

    # Load test configuration
    num_concurrent_users = 20
    users_per_batch = 5

    print(f"🚀 Starting load test with {num_concurrent_users} concurrent users...")

    start_time = time.perf_counter()
    all_results: List[Dict[str, Any]] = []

    # Execute in batches to control concurrency
    for batch_start in range(0, num_concurrent_users, users_per_batch):
        batch_end = min(batch_start + users_per_batch, num_concurrent_users)
        batch_size = batch_end - batch_start

        print(f"   Executing batch {batch_start//users_per_batch + 1}: users {batch_start}-{batch_end-1}")

        # Create tasks for this batch
        tasks = [
            simulate_user(user_id)
            for user_id in range(batch_start, batch_end)
        ]

        # Execute batch concurrently
        batch_results = await asyncio.gather(*tasks)
        all_results.extend(batch_results)

    total_time = time.perf_counter() - start_time

    # Analyze results
    successful_executions = sum(1 for r in all_results if r["success"])
    failed_executions = len(all_results) - successful_executions

    if successful_executions > 0:
        execution_times = [r["execution_time"] for r in all_results if r["success"]]
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)
        throughput = successful_executions / total_time
    else:
        avg_execution_time = max_execution_time = min_execution_time = throughput = 0

    print("
📊 Load Test Results:"    print(f"   Total users: {num_concurrent_users}")
    print(f"   Successful executions: {successful_executions}")
    print(f"   Failed executions: {failed_executions}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average execution time: {avg_execution_time:.3f}s")
    print(f"   Max execution time: {max_execution_time:.3f}s")
    print(f"   Min execution time: {min_execution_time:.3f}s")
    print(f"   Throughput: {throughput:.2f} executions/second")

    # Load test assertions
    success_rate = successful_executions / num_concurrent_users
    assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"
    assert avg_execution_time < 3.0, f"Average execution time too slow: {avg_execution_time:.3f}s"
    assert max_execution_time < 10.0, f"Max execution time too slow: {max_execution_time:.3f}s"
    assert throughput > 3.0, f"Throughput too low: {throughput:.2f} executions/s"

    # Log any failures for debugging
    if failed_executions > 0:
        print(f"\n❌ Failed executions:")
        for result in all_results:
            if not result["success"]:
                print(f"   User {result['user_id']}: {result['error_message']}")
```

## 🚀 CI/CD Integration

### GitHub Actions Example
```yaml
# .github/workflows/test-orchestrator.yml
name: Test Orchestrator Service

on:
  push:
    paths:
      - 'services/orchestrator/**'
      - 'tests/orchestrator/**'
  pull_request:
    paths:
      - 'services/orchestrator/**'
      - 'tests/orchestrator/**'

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov pytest-xdist

    - name: Set PYTHONPATH
      run: echo "PYTHONPATH=$PWD/services:$PYTHONPATH" >> $GITHUB_ENV

    - name: Run tests
      run: python -m pytest tests/orchestrator/ -v --cov=orchestrator --cov-report=xml

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: orchestrator
        name: orchestrator-coverage

    - name: Generate test report
      run: python tests/orchestrator/test_runner.py

    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: test-results.xml
```

### Jenkins Pipeline Example
```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        PYTHONPATH = "${WORKSPACE}/services:$PYTHONPATH"
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install pytest pytest-asyncio pytest-cov pytest-xdist'
            }
        }

        stage('Test') {
            steps {
                sh 'python -m pytest tests/orchestrator/ -v --cov=orchestrator --cov-report=xml --junitxml=test-results.xml'
            }
        }

        stage('Test Runner') {
            steps {
                sh 'python tests/orchestrator/test_runner.py'
            }
        }
    }

    post {
        always {
            junit 'test-results.xml'
            publishCoverage adapters: [coberturaAdapter('coverage.xml')]
        }
    }
}
```

### Local CI/CD Setup
```bash
# Run tests with CI-like conditions
export CI=true
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Run full test suite
python -m pytest tests/orchestrator/ \
    --cov=orchestrator \
    --cov-report=html \
    --cov-report=xml \
    --junitxml=test-results.xml \
    -v

# Generate test runner report
python tests/orchestrator/test_runner.py

# Check coverage threshold
python -m pytest tests/orchestrator/ --cov=orchestrator --cov-fail-under=90
```

## 📈 Best Practices

### Test Organization
```python
# ✅ Good: Clear test structure
class TestWorkflowManagement:
    """Test workflow management functionality."""

    @pytest.mark.asyncio
    async def test_create_simple_workflow(self, workflow_service):
        """Test creating a simple workflow."""

    @pytest.mark.asyncio
    async def test_create_complex_workflow(self, workflow_service):
        """Test creating a complex workflow with dependencies."""

# ❌ Bad: Unorganized tests
def test_workflow_creation():
    """Multiple scenarios in one test."""

def test_random_workflow_stuff():
    """Unclear test purpose."""
```

### Naming Conventions
```python
# ✅ Good: Descriptive names
def test_workflow_creation_with_valid_parameters()
def test_workflow_execution_fails_with_invalid_input()
def test_concurrent_workflow_execution_performance()

# ❌ Bad: Unclear names
def test_workflow()
def test_execution()
def test_performance()
```

### Test Isolation
```python
# ✅ Good: Independent tests
@pytest.mark.asyncio
async def test_create_workflow_isolated(workflow_service):
    """Test workflow creation in isolation."""
    # Test only creation, no side effects

@pytest.mark.asyncio
async def test_execute_workflow_isolated(workflow_service):
    """Test workflow execution in isolation."""
    # Test only execution, with controlled inputs

# ❌ Bad: Dependent tests
@pytest.mark.asyncio
async def test_workflow_lifecycle(workflow_service):
    """Test entire workflow lifecycle in one test."""
    # Creation, execution, cleanup all mixed together
```

### Mock Usage
```python
# ✅ Good: Appropriate mocking
@pytest.mark.asyncio
async def test_workflow_with_mocked_service(workflow_service):
    """Test workflow with properly mocked external service."""
    with patch('service_client.make_request') as mock_request:
        mock_request.return_value = {'status': 'success'}
        # Test logic

# ❌ Bad: Over-mocking
@pytest.mark.asyncio
async def test_workflow_over_mocked(workflow_service):
    """Test with excessive mocking."""
    with patch('everything') as mock_everything:
        # Can't test actual functionality
```

### Performance Testing
```python
# ✅ Good: Realistic performance tests
@pytest.mark.asyncio
async def test_realistic_performance(workflow_service):
    """Test performance with realistic load."""
    # Create realistic workflow
    # Test with realistic data volumes
    # Measure realistic metrics

# ❌ Bad: Unrealistic performance tests
@pytest.mark.asyncio
async def test_unrealistic_performance(workflow_service):
    """Test performance with unrealistic scenarios."""
    # Test with impossible data volumes
    # Measure irrelevant metrics
    # Set unrealistic expectations
```

### Documentation
```python
# ✅ Good: Well-documented tests
@pytest.mark.asyncio
async def test_workflow_parameter_validation(workflow_service):
    """Test that workflow parameters are properly validated.

    This test verifies that:
    - Required parameters must be provided
    - Parameter types are enforced
    - Default values are applied correctly
    - Invalid parameters are rejected

    Args:
        workflow_service: The workflow management service fixture

    Raises:
        AssertionError: If parameter validation fails
    """
    # Test implementation

# ❌ Bad: Poorly documented tests
@pytest.mark.asyncio
async def test_something(workflow_service):
    """Test something."""
    # Unclear what is being tested
```

### Cleanup and Maintenance
```python
# ✅ Good: Proper cleanup
@pytest_asyncio.fixture
async def clean_workflow_service():
    """Workflow service with automatic cleanup."""
    service = WorkflowManagementService()
    yield service
    # Cleanup test data

# ❌ Bad: No cleanup
@pytest.mark.asyncio
async def test_without_cleanup(workflow_service):
    """Test that leaves data behind."""
    # No cleanup, pollutes test environment
```

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Set PYTHONPATH (required)
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon/services:$PYTHONPATH

# Run all tests
python -m pytest tests/orchestrator/ -v

# Run specific test
python -m pytest tests/orchestrator/test_file.py::TestClass::test_method -v

# Run with coverage
python -m pytest tests/orchestrator/ --cov=orchestrator --cov-report=html

# Run test runner
python tests/orchestrator/test_runner.py

# Debug test
python -m pytest tests/orchestrator/test_file.py -vv --pdb
```

### Common Fixtures
- `workflow_service` - Workflow management service
- `event_stream` - Event streaming processor
- `service_mesh` - Service mesh integration
- `sample_workflow_data` - Pre-configured workflow data

### Test Structure
```python
import pytest
import pytest_asyncio

class TestFeatureName:
    @pytest_asyncio.fixture
    async def setup_fixture(self):
        # Setup code
        yield resource
        # Cleanup code

    @pytest.mark.asyncio
    async def test_scenario_name(self, setup_fixture):
        # Arrange
        # Act
        # Assert
```

### Performance Testing
```python
# Measure execution time
start_time = time.perf_counter()
result = await function_to_test()
end_time = time.perf_counter()
execution_time = end_time - start_time

# Assert performance
assert execution_time < 2.0  # Less than 2 seconds
```

---

**Happy Testing! 🧪🚀**

This usage guide provides everything you need to effectively test the orchestrator service. Start with the basic examples and progress to advanced testing techniques as your familiarity grows.
