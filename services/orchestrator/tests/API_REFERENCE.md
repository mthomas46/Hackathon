# 📚 Orchestrator Test API Reference

**Complete API Reference for Orchestrator Service Testing**

This document provides comprehensive documentation for all orchestrator service API endpoints, including request/response formats, authentication, error handling, and testing examples.

## 📋 Table of Contents

- [🌐 Base Information](#-base-information)
- [🔐 Authentication](#-authentication)
- [📝 Workflow Management APIs](#-workflow-management-apis)
- [🚀 Workflow Execution APIs](#-workflow-execution-apis)
- [🎯 Advanced APIs](#-advanced-apis)
- [📊 Analytics & Monitoring APIs](#-analytics--monitoring-apis)
- [🧪 Test-Specific APIs](#-test-specific-apis)
- [❌ Error Handling](#-error-handling)
- [🔧 Testing Examples](#-testing-examples)

## 🌐 Base Information

### Service URL
```
Base URL: http://localhost:5080
Test URL: http://localhost:5080 (same as production for testing)
```

### Content Types
```
Request: application/json
Response: application/json
```

### HTTP Status Codes
```
200 OK - Success
201 Created - Resource created
400 Bad Request - Invalid request
401 Unauthorized - Authentication required
403 Forbidden - Insufficient permissions
404 Not Found - Resource not found
409 Conflict - Resource conflict
422 Unprocessable Entity - Validation error
500 Internal Server Error - Server error
```

### Rate Limiting
```
Test Environment: No rate limiting
Production: 100 requests/minute per user
```

## 🔐 Authentication

### Authentication Methods

#### 1. Bearer Token (Recommended)
```http
Authorization: Bearer <jwt_token>
```

#### 2. API Key
```http
X-API-Key: <api_key>
```

#### 3. User ID Header (Test Environment)
```http
X-User-ID: <user_id>
```

### Authentication Examples

#### Python Requests
```python
import requests

# Method 1: Bearer token
headers = {
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
    'Content-Type': 'application/json'
}

# Method 2: API key
headers = {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
}

# Method 3: User ID (test environment)
headers = {
    'X-User-ID': 'test-user-123',
    'Content-Type': 'application/json'
}

response = requests.get('http://localhost:5080/workflows', headers=headers)
```

#### cURL Examples
```bash
# Bearer token
curl -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     http://localhost:5080/workflows

# API key
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     http://localhost:5080/workflows

# User ID (test environment)
curl -H "X-User-ID: test-user-123" \
     -H "Content-Type: application/json" \
     http://localhost:5080/workflows
```

#### Test Authentication Setup
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_authenticated_request():
    """Test authenticated API request."""
    async with AsyncClient(base_url="http://localhost:5080") as client:
        # Test environment authentication
        headers = {"X-User-ID": "test-user-123"}

        response = await client.get("/workflows", headers=headers)
        assert response.status_code == 200
```

## 📝 Workflow Management APIs

### Create Workflow

**Endpoint:** `POST /workflows`

**Description:** Create a new workflow with parameters and actions.

**Request Body:**
```json
{
  "name": "Document Analysis Workflow",
  "description": "Analyze documents for quality and insights",
  "parameters": [
    {
      "name": "document_url",
      "type": "string",
      "description": "URL of document to analyze",
      "required": true
    },
    {
      "name": "analysis_type",
      "type": "string",
      "description": "Type of analysis to perform",
      "required": false,
      "default_value": "comprehensive",
      "allowed_values": ["basic", "comprehensive", "detailed"]
    }
  ],
  "actions": [
    {
      "action_id": "fetch_document",
      "action_type": "service_call",
      "name": "Fetch Document",
      "description": "Retrieve document from URL",
      "config": {
        "service": "source_agent",
        "endpoint": "/fetch",
        "method": "POST",
        "parameters": {
          "url": "{{document_url}}"
        }
      }
    },
    {
      "action_id": "analyze_content",
      "action_type": "service_call",
      "name": "Analyze Content",
      "description": "Analyze document content",
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
    }
  ],
  "tags": ["analysis", "document"],
  "timeout_seconds": 300
}
```

**Response (201 Created):**
```json
{
  "workflow_id": "wf_1234567890abcdef",
  "name": "Document Analysis Workflow",
  "description": "Analyze documents for quality and insights",
  "status": "active",
  "version": "1.0",
  "created_by": "test-user-123",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "parameters": [...],
  "actions": [...],
  "tags": ["analysis", "document"],
  "timeout_seconds": 300
}
```

**Test Examples:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_workflow():
    """Test workflow creation via API."""
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "parameters": [
            {
                "name": "input_text",
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
                    "message": "{{input_text}}"
                }
            }
        ]
    }

    async with AsyncClient(base_url="http://localhost:5080") as client:
        response = await client.post(
            "/workflows",
            json=workflow_data,
            headers={"X-User-ID": "test-user-123"}
        )

        assert response.status_code == 201
        data = response.json()

        assert "workflow_id" in data
        assert data["name"] == "Test Workflow"
        assert data["status"] == "active"
        assert data["created_by"] == "test-user-123"

@pytest.mark.asyncio
async def test_create_workflow_validation_error():
    """Test workflow creation with validation errors."""
    invalid_data = {
        "name": "",  # Invalid: empty name
        "parameters": [],
        "actions": []
    }

    async with AsyncClient(base_url="http://localhost:5080") as client:
        response = await client.post(
            "/workflows",
            json=invalid_data,
            headers={"X-User-ID": "test-user-123"}
        )

        assert response.status_code == 422
        data = response.json()

        assert "detail" in data
        assert "name" in str(data["detail"]).lower()
```

### List Workflows

**Endpoint:** `GET /workflows`

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 50, max: 100)
- `status` (string, optional): Filter by status ("active", "inactive", "draft")
- `created_by` (string, optional): Filter by creator
- `tags` (string, optional): Filter by tags (comma-separated)
- `search` (string, optional): Search in name and description

**Response (200 OK):**
```json
{
  "workflows": [
    {
      "workflow_id": "wf_1234567890abcdef",
      "name": "Document Analysis Workflow",
      "description": "Analyze documents for quality and insights",
      "status": "active",
      "created_by": "test-user-123",
      "created_at": "2024-01-15T10:30:00Z",
      "tags": ["analysis", "document"],
      "version": "1.0"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

**Test Examples:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_workflows():
    """Test listing workflows."""
    async with AsyncClient(base_url="http://localhost:5080") as client:
        response = await client.get(
            "/workflows",
            headers={"X-User-ID": "test-user-123"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "workflows" in data
        assert "pagination" in data
        assert isinstance(data["workflows"], list)

@pytest.mark.asyncio
async def test_list_workflows_with_filters():
    """Test listing workflows with filters."""
    async with AsyncClient(base_url="http://localhost:5080") as client:
        response = await client.get(
            "/workflows?page=1&page_size=10&status=active&created_by=test-user-123",
            headers={"X-User-ID": "test-user-123"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10

        # All returned workflows should match filters
        for workflow in data["workflows"]:
            assert workflow["status"] == "active"
            assert workflow["created_by"] == "test-user-123"
```

### Get Workflow Details

**Endpoint:** `GET /workflows/{workflow_id}`

**Path Parameters:**
- `workflow_id` (string, required): Workflow ID

**Response (200 OK):**
```json
{
  "workflow_id": "wf_1234567890abcdef",
  "name": "Document Analysis Workflow",
  "description": "Analyze documents for quality and insights",
  "status": "active",
  "version": "1.0",
  "created_by": "test-user-123",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "parameters": [
    {
      "name": "document_url",
      "type": "string",
      "description": "URL of document to analyze",
      "required": true
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
        "parameters": {
          "url": "{{document_url}}"
        }
      }
    }
  ],
  "tags": ["analysis", "document"],
  "timeout_seconds": 300,
  "execution_count": 5,
  "last_execution": "2024-01-15T11:00:00Z"
}
```

**Test Examples:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_workflow_details():
    """Test getting workflow details."""
    # First create a workflow
    workflow_data = {
        "name": "Test Workflow Details",
        "description": "Workflow for testing details retrieval",
        "parameters": [],
        "actions": []
    }

    async with AsyncClient(base_url="http://localhost:5080") as client:
        # Create workflow
        create_response = await client.post(
            "/workflows",
            json=workflow_data,
            headers={"X-User-ID": "test-user-123"}
        )
        assert create_response.status_code == 201
        workflow_id = create_response.json()["workflow_id"]

        # Get workflow details
        response = await client.get(
            f"/workflows/{workflow_id}",
            headers={"X-User-ID": "test-user-123"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["workflow_id"] == workflow_id
        assert data["name"] == "Test Workflow Details"
        assert "parameters" in data
        assert "actions" in data
        assert "created_at" in data

@pytest.mark.asyncio
async def test_get_nonexistent_workflow():
    """Test getting details of non-existent workflow."""
    async with AsyncClient(base_url="http://localhost:5080") as client:
        response = await client.get(
            "/workflows/nonexistent_workflow_id",
            headers={"X-User-ID": "test-user-123"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
```

### Update Workflow

**Endpoint:** `PUT /workflows/{workflow_id}`

**Path Parameters:**
- `workflow_id` (string, required): Workflow ID

**Request Body:**
```json
{
  "description": "Updated description",
  "status": "inactive",
  "tags": ["updated", "v2"],
  "timeout_seconds": 600
}
```

**Response (200 OK):**
```json
{
  "workflow_id": "wf_1234567890abcdef",
  "name": "Document Analysis Workflow",
  "description": "Updated description",
  "status": "inactive",
  "updated_at": "2024-01-15T11:30:00Z",
  "tags": ["updated", "v2"],
  "timeout_seconds": 600
}
```

### Delete Workflow

**Endpoint:** `DELETE /workflows/{workflow_id}`

**Path Parameters:**
- `workflow_id` (string, required): Workflow ID

**Response (204 No Content):**
```http
HTTP/1.1 204 No Content
```

## 🚀 Workflow Execution APIs

### Execute Workflow

**Endpoint:** `POST /workflows/{workflow_id}/execute`

**Path Parameters:**
- `workflow_id` (string, required): Workflow ID

**Request Body:**
```json
{
  "parameters": {
    "document_url": "https://example.com/doc.pdf",
    "analysis_type": "comprehensive"
  },
  "async_execution": true,
  "callback_url": "https://example.com/webhook"
}
```

**Response (202 Accepted) - Async Execution:**
```json
{
  "execution_id": "exec_1234567890abcdef",
  "workflow_id": "wf_1234567890abcdef",
  "status": "queued",
  "created_at": "2024-01-15T11:30:00Z",
  "parameters": {
    "document_url": "https://example.com/doc.pdf",
    "analysis_type": "comprehensive"
  }
}
```

**Response (200 OK) - Sync Execution:**
```json
{
  "execution_id": "exec_1234567890abcdef",
  "workflow_id": "wf_1234567890abcdef",
  "status": "completed",
  "created_at": "2024-01-15T11:30:00Z",
  "completed_at": "2024-01-15T11:31:15Z",
  "parameters": {
    "document_url": "https://example.com/doc.pdf",
    "analysis_type": "comprehensive"
  },
  "result": {
    "fetch_document": {
      "status": "success",
      "response": {
        "content": "Document content...",
        "metadata": {"size": 1024}
      }
    },
    "analyze_content": {
      "status": "success",
      "response": {
        "quality_score": 0.85,
        "issues": []
      }
    }
  }
}
```

### Get Execution Status

**Endpoint:** `GET /workflows/executions/{execution_id}`

**Path Parameters:**
- `execution_id` (string, required): Execution ID

**Response (200 OK):**
```json
{
  "execution_id": "exec_1234567890abcdef",
  "workflow_id": "wf_1234567890abcdef",
  "status": "running",
  "created_at": "2024-01-15T11:30:00Z",
  "started_at": "2024-01-15T11:30:05Z",
  "parameters": {...},
  "progress": {
    "completed_actions": 1,
    "total_actions": 3,
    "current_action": "analyze_content",
    "percentage": 33.33
  },
  "current_step": "analyze_content",
  "logs": [
    {
      "timestamp": "2024-01-15T11:30:05Z",
      "level": "INFO",
      "message": "Starting workflow execution",
      "action_id": null
    },
    {
      "timestamp": "2024-01-15T11:30:10Z",
      "level": "INFO",
      "message": "Completed action: fetch_document",
      "action_id": "fetch_document"
    }
  ]
}
```

### List Workflow Executions

**Endpoint:** `GET /workflows/{workflow_id}/executions`

**Path Parameters:**
- `workflow_id` (string, required): Workflow ID

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 50)
- `status` (string, optional): Filter by status

**Response (200 OK):**
```json
{
  "executions": [
    {
      "execution_id": "exec_1234567890abcdef",
      "status": "completed",
      "created_at": "2024-01-15T11:30:00Z",
      "completed_at": "2024-01-15T11:31:15Z",
      "duration_seconds": 75
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 1,
    "total_pages": 1
  }
}
```

### Cancel Execution

**Endpoint:** `POST /workflows/executions/{execution_id}/cancel`

**Path Parameters:**
- `execution_id` (string, required): Execution ID

**Response (200 OK):**
```json
{
  "execution_id": "exec_1234567890abcdef",
  "status": "cancelled",
  "cancelled_at": "2024-01-15T11:35:00Z",
  "message": "Execution cancelled by user"
}
```

## 🎯 Advanced APIs

### Create from Template

**Endpoint:** `POST /workflows/from-template`

**Request Body:**
```json
{
  "template_name": "document_analysis",
  "customizations": {
    "name": "Custom Document Analysis",
    "description": "Customized workflow",
    "parameters": [
      {
        "name": "custom_param",
        "type": "string",
        "required": true
      }
    ]
  }
}
```

### Search Workflows

**Endpoint:** `GET /workflows/search`

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (integer, optional): Maximum results (default: 50)

### Get Statistics

**Endpoint:** `GET /workflows/statistics`

**Response (200 OK):**
```json
{
  "total_workflows": 25,
  "active_workflows": 20,
  "total_executions": 150,
  "successful_executions": 140,
  "failed_executions": 10,
  "average_execution_time": 45.2,
  "popular_tags": [
    {"tag": "analysis", "count": 15},
    {"tag": "document", "count": 12}
  ]
}
```

### Health Check

**Endpoint:** `GET /workflows/health`

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "external_services": {
      "analysis_service": "healthy",
      "source_agent": "healthy"
    }
  },
  "metrics": {
    "uptime_seconds": 3600,
    "active_executions": 3,
    "queued_executions": 2
  }
}
```

## 📊 Analytics & Monitoring APIs

### Get Activity Feed

**Endpoint:** `GET /workflows/activity`

**Query Parameters:**
- `limit` (integer, optional): Maximum activities (default: 20)
- `since` (string, optional): ISO 8601 timestamp

**Response (200 OK):**
```json
{
  "activities": [
    {
      "id": "act_1234567890abcdef",
      "type": "workflow_created",
      "timestamp": "2024-01-15T12:00:00Z",
      "user_id": "test-user-123",
      "details": {
        "workflow_id": "wf_1234567890abcdef",
        "workflow_name": "Document Analysis"
      }
    },
    {
      "id": "act_1234567890abcdf0",
      "type": "workflow_executed",
      "timestamp": "2024-01-15T12:05:00Z",
      "user_id": "test-user-123",
      "details": {
        "workflow_id": "wf_1234567890abcdef",
        "execution_id": "exec_1234567890abcdf0"
      }
    }
  ]
}
```

### Get System Metrics

**Endpoint:** `GET /metrics`

**Response (200 OK):**
```json
{
  "timestamp": "2024-01-15T12:00:00Z",
  "system": {
    "cpu_usage_percent": 45.2,
    "memory_usage_mb": 256,
    "disk_usage_percent": 23.5
  },
  "application": {
    "active_connections": 15,
    "requests_per_second": 12.5,
    "average_response_time_ms": 125.3
  },
  "workflows": {
    "active_executions": 3,
    "queued_executions": 2,
    "completed_today": 45,
    "failed_today": 2
  }
}
```

## 🧪 Test-Specific APIs

### Test Data Setup

**Endpoint:** `POST /test/setup`

**Description:** Initialize test data for testing scenarios.

**Request Body:**
```json
{
  "scenario": "document_analysis",
  "user_id": "test-user-123",
  "cleanup_existing": true
}
```

### Test Data Cleanup

**Endpoint:** `POST /test/cleanup`

**Description:** Clean up test data.

**Request Body:**
```json
{
  "user_id": "test-user-123",
  "cleanup_all": false
}
```

### Mock Service Configuration

**Endpoint:** `POST /test/mock-service`

**Description:** Configure mock responses for external services.

**Request Body:**
```json
{
  "service_name": "analysis_service",
  "endpoint": "/analyze",
  "response": {
    "status": "success",
    "data": {
      "quality_score": 0.85,
      "issues": []
    }
  },
  "delay_ms": 100
}
```

## ❌ Error Handling

### Common Error Responses

#### Validation Error (422)
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### Not Found Error (404)
```json
{
  "detail": "Workflow not found: wf_nonexistent"
}
```

#### Conflict Error (409)
```json
{
  "detail": "Workflow with name 'Duplicate Name' already exists"
}
```

#### Server Error (500)
```json
{
  "detail": "Internal server error",
  "error_id": "err_1234567890abcdef"
}
```

### Error Response Format
```json
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T12:00:00Z",
  "request_id": "req_1234567890abcdef",
  "path": "/workflows",
  "method": "POST"
}
```

## 🔧 Testing Examples

### Complete Test Suite Example
```python
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any

class TestOrchestratorAPI:
    """Complete API test suite for orchestrator service."""

    @pytest_asyncio.fixture
    async def client(self):
        """HTTP client fixture."""
        async with AsyncClient(base_url="http://localhost:5080") as client:
            yield client

    @pytest_asyncio.fixture
    async def test_user_headers(self):
        """Test user authentication headers."""
        return {"X-User-ID": "test-user-123"}

    @pytest_asyncio.fixture
    async def sample_workflow(self, client, test_user_headers):
        """Create a sample workflow for testing."""
        workflow_data = {
            "name": "API Test Workflow",
            "description": "Workflow for API testing",
            "parameters": [
                {
                    "name": "test_input",
                    "type": "string",
                    "required": True
                }
            ],
            "actions": [
                {
                    "action_id": "process_input",
                    "action_type": "notification",
                    "name": "Process Input",
                    "config": {
                        "message": "{{test_input}}"
                    }
                }
            ]
        }

        response = await client.post(
            "/workflows",
            json=workflow_data,
            headers=test_user_headers
        )

        assert response.status_code == 201
        return response.json()

    @pytest.mark.asyncio
    async def test_workflow_lifecycle(self, client, test_user_headers, sample_workflow):
        """Test complete workflow lifecycle via API."""
        workflow_id = sample_workflow["workflow_id"]

        # 1. Get workflow details
        response = await client.get(
            f"/workflows/{workflow_id}",
            headers=test_user_headers
        )
        assert response.status_code == 200

        # 2. Execute workflow
        execution_data = {
            "parameters": {"test_input": "Hello API Test"}
        }
        response = await client.post(
            f"/workflows/{workflow_id}/execute",
            json=execution_data,
            headers=test_user_headers
        )
        assert response.status_code in [200, 202]

        # 3. Check execution status (if async)
        if response.status_code == 202:
            execution_id = response.json()["execution_id"]
            response = await client.get(
                f"/workflows/executions/{execution_id}",
                headers=test_user_headers
            )
            assert response.status_code == 200

        # 4. List executions
        response = await client.get(
            f"/workflows/{workflow_id}/executions",
            headers=test_user_headers
        )
        assert response.status_code == 200

        # 5. Update workflow
        update_data = {"description": "Updated via API test"}
        response = await client.put(
            f"/workflows/{workflow_id}",
            json=update_data,
            headers=test_user_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_error_scenarios(self, client, test_user_headers):
        """Test various error scenarios."""
        # Test non-existent workflow
        response = await client.get(
            "/workflows/nonexistent_id",
            headers=test_user_headers
        )
        assert response.status_code == 404

        # Test invalid workflow creation
        invalid_data = {"name": "", "parameters": [], "actions": []}
        response = await client.post(
            "/workflows",
            json=invalid_data,
            headers=test_user_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_pagination_and_filtering(self, client, test_user_headers):
        """Test pagination and filtering functionality."""
        # Create multiple workflows
        for i in range(5):
            workflow_data = {
                "name": f"Test Workflow {i}",
                "description": f"Workflow {i} for pagination testing",
                "parameters": [],
                "actions": []
            }
            response = await client.post(
                "/workflows",
                json=workflow_data,
                headers=test_user_headers
            )
            assert response.status_code == 201

        # Test pagination
        response = await client.get(
            "/workflows?page=1&page_size=2",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["workflows"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["total_pages"] >= 3

        # Test filtering by status
        response = await client.get(
            "/workflows?status=active",
            headers=test_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        for workflow in data["workflows"]:
            assert workflow["status"] == "active"
```

### Performance Testing Example
```python
import pytest
import pytest_asyncio
import asyncio
import time
from typing import List
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_performance():
    """Test API performance under load."""
    async with AsyncClient(base_url="http://localhost:5080") as client:
        # Create test workflow
        workflow_data = {
            "name": "Performance Test Workflow",
            "description": "Workflow for performance testing",
            "parameters": [{"name": "input", "type": "string", "required": True}],
            "actions": [{
                "action_id": "echo",
                "action_type": "notification",
                "name": "Echo Input",
                "config": {"message": "{{input}}"}
            }]
        }

        response = await client.post(
            "/workflows",
            json=workflow_data,
            headers={"X-User-ID": "perf-test-user"}
        )
        workflow_id = response.json()["workflow_id"]

        # Performance test
        num_requests = 50
        execution_times: List[float] = []

        start_time = time.time()

        for i in range(num_requests):
            request_start = time.time()

            response = await client.post(
                f"/workflows/{workflow_id}/execute",
                json={"parameters": {"input": f"Test input {i}"}},
                headers={"X-User-ID": "perf-test-user"}
            )

            request_end = time.time()
            execution_times.append(request_end - request_start)

            assert response.status_code in [200, 202]

        total_time = time.time() - start_time

        # Calculate metrics
        avg_time = sum(execution_times) / len(execution_times)
        throughput = num_requests / total_time

        print(f"Performance Results:")
        print(f"  Requests: {num_requests}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average response time: {avg_time:.3f}s")
        print(f"  Throughput: {throughput:.2f} req/s")

        # Performance assertions
        assert avg_time < 2.0, f"Average response time too slow: {avg_time:.3f}s"
        assert throughput > 5.0, f"Throughput too low: {throughput:.2f} req/s"
```

---

## 📚 API Reference Summary

### Endpoints Summary
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workflows` | Create workflow |
| GET | `/workflows` | List workflows |
| GET | `/workflows/{id}` | Get workflow details |
| PUT | `/workflows/{id}` | Update workflow |
| DELETE | `/workflows/{id}` | Delete workflow |
| POST | `/workflows/{id}/execute` | Execute workflow |
| GET | `/workflows/executions/{id}` | Get execution status |
| GET | `/workflows/{id}/executions` | List executions |
| POST | `/workflows/executions/{id}/cancel` | Cancel execution |
| POST | `/workflows/from-template` | Create from template |
| GET | `/workflows/search` | Search workflows |
| GET | `/workflows/statistics` | Get statistics |
| GET | `/workflows/health` | Health check |

### Authentication Methods
- **Bearer Token**: `Authorization: Bearer <token>`
- **API Key**: `X-API-Key: <key>`
- **User ID**: `X-User-ID: <user_id>` (test environment)

### Response Status Codes
- **200 OK**: Success
- **201 Created**: Resource created
- **202 Accepted**: Async operation accepted
- **204 No Content**: Success with no content
- **400 Bad Request**: Invalid request
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

---

**Complete API Reference! 📚🚀**

This comprehensive API reference provides everything needed to effectively test and integrate with the orchestrator service APIs.
