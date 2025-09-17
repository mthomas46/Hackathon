#!/usr/bin/env python3
"""
Minimal Orchestrator Test

Basic test to verify orchestrator workflow management works.
"""

import sys
import os
import pytest
import pytest_asyncio

# Add services to path
sys.path.insert(0, '/Users/mykalthomas/Documents/work/Hackathon/services')

from orchestrator.modules.workflow_management.service import WorkflowManagementService


@pytest_asyncio.fixture(scope="function")
async def workflow_service():
    """Create workflow service instance for testing."""
    service = WorkflowManagementService()
    yield service


@pytest.mark.asyncio
async def test_basic_workflow_creation(workflow_service):
    """Test basic workflow creation."""
    workflow_data = {
        "name": "Minimal Test Workflow",
        "description": "Basic workflow for testing",
        "parameters": [
            {
                "name": "input_value",
                "type": "string",
                "required": True
            }
        ],
        "actions": [
            {
                "action_id": "test_action",
                "action_type": "notification",
                "name": "Test Action",
                "config": {
                    "message": "Processing input"
                }
            }
        ]
    }

    success, message, workflow = await workflow_service.create_workflow(workflow_data, "test_user")

    assert success == True, f"Workflow creation failed: {message}"
    assert workflow is not None
    assert workflow.name == "Minimal Test Workflow"
    assert len(workflow.parameters) == 1
    assert len(workflow.actions) == 1
    assert workflow.created_by == "test_user"

    print("✅ Basic workflow creation test passed!")


@pytest.mark.asyncio
async def test_workflow_retrieval(workflow_service):
    """Test workflow retrieval."""
    # Create a workflow first
    workflow_data = {
        "name": "Retrieval Test Workflow",
        "description": "Workflow for retrieval testing",
        "parameters": [],
        "actions": []
    }

    success, message, workflow = await workflow_service.create_workflow(workflow_data, "test_user")
    assert success == True

    workflow_id = workflow.workflow_id

    # Retrieve the workflow
    retrieved = await workflow_service.get_workflow(workflow_id)
    assert retrieved is not None
    assert retrieved.workflow_id == workflow_id
    assert retrieved.name == "Retrieval Test Workflow"

    print("✅ Workflow retrieval test passed!")


if __name__ == "__main__":
    print("🧪 Running minimal orchestrator tests...")
    pytest.main([__file__, "-v"])
