#!/usr/bin/env python3
"""
API Endpoint Tests for Orchestrator Service

Tests all REST API endpoints and their functionality.
"""

import pytest
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient
import sys
import os

# Add services to path
sys.path.insert(0, '/Users/mykalthomas/Documents/work/Hackathon/services')

from orchestrator.main import app
from orchestrator.modules.workflow_management.service import WorkflowManagementService
from orchestrator.modules.workflow_management.models import WorkflowStatus


class TestWorkflowAPICreate:
    """Test workflow creation API endpoints."""

    def test_create_workflow_success(self, client: TestClient):
        """Test successful workflow creation via API."""
        workflow_data = {
            "name": "API Test Workflow",
            "description": "Workflow created via API test",
            "tags": ["api", "test"],
            "parameters": [
                {
                    "name": "input_text",
                    "type": "string",
                    "description": "Text input for processing",
                    "required": True
                },
                {
                    "name": "priority",
                    "type": "string",
                    "description": "Processing priority",
                    "required": False,
                    "default_value": "normal",
                    "allowed_values": ["low", "normal", "high"]
                }
            ],
            "actions": [
                {
                    "action_id": "process_text",
                    "action_type": "service_call",
                    "name": "Process Text",
                    "description": "Process the input text",
                    "config": {
                        "service": "interpreter",
                        "endpoint": "/process",
                        "method": "POST",
                        "parameters": {
                            "text": "{{input_text}}",
                            "priority": "{{priority}}"
                        }
                    }
                },
                {
                    "action_id": "notify_completion",
                    "action_type": "notification",
                    "name": "Notify Completion",
                    "description": "Send completion notification",
                    "config": {
                        "message": "Text processing completed for: {{input_text}}",
                        "channels": ["log"]
                    },
                    "depends_on": ["process_text"]
                }
            ]
        }

        response = client.post("/workflows", json=workflow_data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == True
        assert "workflow" in response_data

        workflow = response_data["workflow"]
        assert workflow["name"] == "API Test Workflow"
        assert workflow["description"] == "Workflow created via API test"
        assert workflow["parameters_count"] == 2
        assert workflow["actions_count"] == 2
        assert "workflow_id" in workflow

    def test_create_workflow_validation_error(self, client: TestClient):
        """Test workflow creation with validation errors."""
        # Test missing name
        invalid_workflow = {
            "description": "Missing name field",
            "parameters": [],
            "actions": []
        }

        response = client.post("/workflows", json=invalid_workflow)
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["success"] == False
        assert "name" in response_data["message"].lower()

    def test_create_workflow_from_template(self, client: TestClient):
        """Test workflow creation from predefined template."""
        template_request = {
            "template_name": "document_analysis",
            "customizations": {
                "name": "Custom Document Analysis",
                "description": "Customized document analysis workflow"
            }
        }

        response = client.post("/workflows/from-template", json=template_request)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == True
        assert "workflow" in response_data

        workflow = response_data["workflow"]
        assert workflow["name"] == "Custom Document Analysis"
        assert workflow["description"] == "Customized document analysis workflow"


class TestWorkflowAPIRead:
    """Test workflow read/list API endpoints."""

    def test_list_workflows(self, client: TestClient):
        """Test listing workflows via API."""
        response = client.get("/workflows")

        assert response.status_code == 200
        response_data = response.json()
        assert "workflows" in response_data
        assert "total" in response_data
        assert "page" in response_data
        assert "page_size" in response_data

        assert isinstance(response_data["workflows"], list)
        assert response_data["total"] >= 0

    def test_list_workflows_with_filters(self, client: TestClient):
        """Test listing workflows with filters."""
        # Create test workflow first
        workflow_data = {
            "name": "Filter Test Workflow",
            "description": "Workflow for filter testing",
            "tags": ["test", "filter"],
            "parameters": [],
            "actions": [{
                "action_id": "test_action",
                "action_type": "notification",
                "name": "Test Action",
                "config": {"message": "Filter test"}
            }]
        }

        create_response = client.post("/workflows", json=workflow_data)
        assert create_response.status_code == 200

        # Test filtering by name
        response = client.get("/workflows?name_contains=Filter")
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["workflows"]) >= 1

        # Verify workflow is in results
        workflow_names = [w["name"] for w in response_data["workflows"]]
        assert "Filter Test Workflow" in workflow_names

    def test_get_workflow_details(self, client: TestClient):
        """Test getting specific workflow details."""
        # Create test workflow
        workflow_data = {
            "name": "Details Test Workflow",
            "description": "Workflow for details testing",
            "parameters": [
                {
                    "name": "test_param",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "details_action",
                    "action_type": "notification",
                    "name": "Details Action",
                    "config": {"message": "Details test"}
                }
            ]
        }

        create_response = client.post("/workflows", json=workflow_data)
        assert create_response.status_code == 200

        workflow_id = create_response.json()["workflow"]["workflow_id"]

        # Get workflow details
        response = client.get(f"/workflows/{workflow_id}")
        assert response.status_code == 200

        workflow_details = response.json()
        assert workflow_details["workflow_id"] == workflow_id
        assert workflow_details["name"] == "Details Test Workflow"
        assert "parameters" in workflow_details
        assert "actions" in workflow_details
        assert "execution_statistics" in workflow_details

    def test_get_nonexistent_workflow(self, client: TestClient):
        """Test getting a non-existent workflow."""
        response = client.get("/workflows/non-existent-workflow-id")
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["detail"] == "Workflow not found"


class TestWorkflowAPIUpdate:
    """Test workflow update API endpoints."""

    def test_update_workflow_success(self, client: TestClient):
        """Test successful workflow update."""
        # Create test workflow
        workflow_data = {
            "name": "Update Test Workflow",
            "description": "Original description",
            "parameters": [],
            "actions": [{
                "action_id": "update_action",
                "action_type": "notification",
                "name": "Update Action",
                "config": {"message": "Original message"}
            }]
        }

        create_response = client.post("/workflows", json=workflow_data)
        assert create_response.status_code == 200

        workflow_id = create_response.json()["workflow"]["workflow_id"]

        # Update workflow
        update_data = {
            "description": "Updated description",
            "tags": ["updated", "test"]
        }

        response = client.put(f"/workflows/{workflow_id}", json=update_data)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] == True
        assert "Updated workflow" in response_data["message"]

        # Verify update
        get_response = client.get(f"/workflows/{workflow_id}")
        assert get_response.status_code == 200

        updated_workflow = get_response.json()
        assert updated_workflow["description"] == "Updated description"
        assert "updated" in updated_workflow["tags"]

    def test_update_nonexistent_workflow(self, client: TestClient):
        """Test updating a non-existent workflow."""
        update_data = {
            "description": "This should fail"
        }

        response = client.put("/workflows/non-existent-workflow-id", json=update_data)
        assert response.status_code == 404
        response_data = response.json()
        assert "Workflow not found" in response_data["detail"]


class TestWorkflowAPIDelete:
    """Test workflow deletion API endpoints."""

    def test_delete_workflow_success(self, client: TestClient):
        """Test successful workflow deletion."""
        # Create test workflow
        workflow_data = {
            "name": "Delete Test Workflow",
            "description": "Workflow for deletion testing",
            "parameters": [],
            "actions": [{
                "action_id": "delete_action",
                "action_type": "notification",
                "name": "Delete Action",
                "config": {"message": "Delete test"}
            }]
        }

        create_response = client.post("/workflows", json=workflow_data)
        assert create_response.status_code == 200

        workflow_id = create_response.json()["workflow"]["workflow_id"]

        # Delete workflow
        response = client.delete(f"/workflows/{workflow_id}")
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] == True
        assert "deleted" in response_data["message"]

        # Verify deletion
        get_response = client.get(f"/workflows/{workflow_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_workflow(self, client: TestClient):
        """Test deleting a non-existent workflow."""
        response = client.delete("/workflows/non-existent-workflow-id")
        assert response.status_code == 404
        response_data = response.json()
        assert "Workflow not found" in response_data["detail"]


class TestWorkflowAPIExecution:
    """Test workflow execution API endpoints."""

    def test_execute_workflow_success(self, client: TestClient):
        """Test successful workflow execution."""
        # Create test workflow
        workflow_data = {
            "name": "Execution Test Workflow",
            "description": "Workflow for execution testing",
            "parameters": [
                {
                    "name": "input_value",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "execute_action",
                    "action_type": "notification",
                    "name": "Execute Action",
                    "description": "Action for execution testing",
                    "config": {
                        "message": "Processing: {{input_value}}"
                    }
                }
            ]
        }

        create_response = client.post("/workflows", json=workflow_data)
        assert create_response.status_code == 200

        workflow_id = create_response.json()["workflow"]["workflow_id"]

        # Activate workflow (required for execution)
        activate_response = client.put(f"/workflows/{workflow_id}", json={"status": "active"})
        assert activate_response.status_code == 200

        # Execute workflow
        execution_data = {
            "parameters": {
                "input_value": "test_execution_value"
            }
        }

        response = client.post(f"/workflows/{workflow_id}/execute", json=execution_data)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] == True
        assert "execution" in response_data

        execution = response_data["execution"]
        assert execution["workflow_id"] == workflow_id
        assert "execution_id" in execution
        assert execution["status"] == "running"

    def test_execute_workflow_validation_error(self, client: TestClient):
        """Test workflow execution with validation errors."""
        # Create workflow with required parameter
        workflow_data = {
            "name": "Validation Test Workflow",
            "description": "Workflow for validation testing",
            "parameters": [
                {
                    "name": "required_param",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "validation_action",
                    "action_type": "notification",
                    "name": "Validation Action",
                    "config": {"message": "Validation test"}
                }
            ]
        }

        create_response = client.post("/workflows", json=workflow_data)
        assert create_response.status_code == 200

        workflow_id = create_response.json()["workflow"]["workflow_id"]

        # Activate workflow
        client.put(f"/workflows/{workflow_id}", json={"status": "active"})

        # Try to execute without required parameter
        execution_data = {
            "parameters": {}  # Missing required parameter
        }

        response = client.post(f"/workflows/{workflow_id}/execute", json=execution_data)
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["success"] == False
        assert "validation failed" in response_data["message"].lower()

    def test_get_execution_status(self, client: TestClient):
        """Test getting workflow execution status."""
        # Create and execute workflow first
        workflow_data = {
            "name": "Status Test Workflow",
            "description": "Workflow for status testing",
            "parameters": [
                {
                    "name": "test_param",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "status_action",
                    "action_type": "notification",
                    "name": "Status Action",
                    "config": {"message": "Status test"}
                }
            ]
        }

        create_response = client.post("/workflows", json=workflow_data)
        workflow_id = create_response.json()["workflow"]["workflow_id"]

        # Activate and execute
        client.put(f"/workflows/{workflow_id}", json={"status": "active"})
        execution_data = {"parameters": {"test_param": "test_value"}}
        exec_response = client.post(f"/workflows/{workflow_id}/execute", json=execution_data)
        execution_id = exec_response.json()["execution"]["execution_id"]

        # Get execution status
        response = client.get(f"/workflows/executions/{execution_id}")
        assert response.status_code == 200

        execution_details = response.json()
        assert execution_details["execution_id"] == execution_id
        assert execution_details["workflow_id"] == workflow_id
        assert "status" in execution_details
        assert "started_at" in execution_details

    def test_cancel_execution(self, client: TestClient):
        """Test cancelling a workflow execution."""
        # Create and start execution
        workflow_data = {
            "name": "Cancel Test Workflow",
            "description": "Workflow for cancellation testing",
            "parameters": [
                {
                    "name": "test_param",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "cancel_action",
                    "action_type": "notification",
                    "name": "Cancel Action",
                    "config": {"message": "Cancel test"}
                }
            ]
        }

        create_response = client.post("/workflows", json=workflow_data)
        workflow_id = create_response.json()["workflow"]["workflow_id"]

        # Activate and execute
        client.put(f"/workflows/{workflow_id}", json={"status": "active"})
        execution_data = {"parameters": {"test_param": "test_value"}}
        exec_response = client.post(f"/workflows/{workflow_id}/execute", json=execution_data)
        execution_id = exec_response.json()["execution"]["execution_id"]

        # Cancel execution
        response = client.post(f"/workflows/executions/{execution_id}/cancel")
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] == True
        assert "cancelled" in response_data["message"]


class TestWorkflowAPISearch:
    """Test workflow search API endpoints."""

    def test_search_workflows(self, client: TestClient):
        """Test workflow search functionality."""
        # Create test workflows with searchable content
        workflows_data = [
            {
                "name": "Document Analysis Search Test",
                "description": "Document analysis workflow for search testing",
                "tags": ["search", "document"],
                "parameters": [],
                "actions": []
            },
            {
                "name": "Code Review Search Test",
                "description": "Code review workflow for search testing",
                "tags": ["search", "code"],
                "parameters": [],
                "actions": []
            }
        ]

        created_workflows = []
        for workflow_data in workflows_data:
            response = client.post("/workflows", json=workflow_data)
            assert response.status_code == 200
            created_workflows.append(response.json()["workflow"]["workflow_id"])

        # Search for workflows
        response = client.get("/workflows/search?q=document")
        assert response.status_code == 200

        search_results = response.json()
        assert "workflows" in search_results
        assert len(search_results["workflows"]) >= 1

        # Verify search results contain expected workflow
        result_names = [w["name"] for w in search_results["workflows"]]
        assert "Document Analysis Search Test" in result_names


class TestWorkflowAPIStatistics:
    """Test workflow statistics API endpoints."""

    def test_get_workflow_statistics(self, client: TestClient):
        """Test getting workflow statistics."""
        response = client.get("/workflows/statistics")
        assert response.status_code == 200

        stats = response.json()
        assert "summary" in stats
        assert "generated_at" in stats

        summary = stats["summary"]
        assert "workflows" in summary
        assert "executions" in summary
        assert "success_rate" in summary
        assert "most_active_workflows" in summary

    def test_get_recent_activity(self, client: TestClient):
        """Test getting recent workflow activity."""
        response = client.get("/workflows/activity")
        assert response.status_code == 200

        activity = response.json()
        assert "activity" in activity
        assert "total" in activity
        assert "generated_at" in activity
        assert isinstance(activity["activity"], list)


class TestWorkflowAPIHealth:
    """Test workflow API health endpoints."""

    def test_health_check(self, client: TestClient):
        """Test workflow service health check."""
        response = client.get("/workflows/health")
        assert response.status_code == 200

        health_data = response.json()
        assert "status" in health_data
        assert "service" in health_data
        assert "timestamp" in health_data

        # Should be healthy for basic functionality
        assert health_data["status"] in ["healthy", "degraded"]

    def test_create_sample_workflow(self, client: TestClient):
        """Test creating a sample workflow for demonstration."""
        response = client.post("/workflows/examples/create-sample-workflow")
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["success"] == True
        assert "workflow" in response_data

        workflow = response_data["workflow"]
        assert "workflow_id" in workflow
        assert "Sample" in workflow["name"]


class TestWorkflowAPITemplates:
    """Test workflow template API endpoints."""

    def test_get_workflow_templates(self, client: TestClient):
        """Test getting available workflow templates."""
        response = client.get("/workflows/templates")
        assert response.status_code == 200

        templates_data = response.json()
        assert "templates" in templates_data
        assert "total_templates" in templates_data
        assert isinstance(templates_data["templates"], dict)

    def test_get_template_details(self, client: TestClient):
        """Test getting specific template details."""
        response = client.get("/workflows/templates/document_analysis")
        assert response.status_code == 200

        template_details = response.json()
        assert "template_name" in template_details
        assert "name" in template_details
        assert "description" in template_details
        assert "parameters" in template_details
        assert "actions" in template_details


# Test fixtures
@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Cleanup would go here if needed
    # For now, tests are designed to be isolated


if __name__ == "__main__":
    # Run basic API smoke tests
    client = TestClient(app)

    print("🧪 Running API Endpoint Smoke Tests...")

    # Test health endpoint
    response = client.get("/workflows/health")
    if response.status_code == 200:
        print("✅ Health endpoint working")
    else:
        print("❌ Health endpoint failed")

    # Test list workflows
    response = client.get("/workflows")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ List workflows working - found {data.get('total', 0)} workflows")
    else:
        print("❌ List workflows failed")

    # Test create sample workflow
    response = client.post("/workflows/examples/create-sample-workflow")
    if response.status_code == 200:
        print("✅ Create sample workflow working")
    else:
        print("❌ Create sample workflow failed")

    print("🏁 API Smoke Tests Complete")
