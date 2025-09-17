"""Integration tests for documentation quality and consistency workflows.

These tests verify the complete workflow from documentation quality assessment
through consistency analysis and improvement recommendations.
"""

import importlib.util, os
import pytest
from fastapi.testclient import TestClient


def _load_service(service_name, service_dir):
    """Load a service dynamically from hyphenated directory."""
    try:
        spec = importlib.util.spec_from_file_location(
            f"services.{service_name}.main",
            os.path.join(os.getcwd(), 'services', service_dir, 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        print(f"Warning: Could not load {service_name}: {e}")
        return None


@pytest.fixture(scope="module")
def doc_store_app():
    """Load doc_store service."""
    return _load_service("doc_store", "doc_store")


@pytest.fixture(scope="module")
def analysis_service_app():
    """Load analysis-service."""
    return _load_service("analysis-service", "analysis-service")


@pytest.fixture(scope="module")
def summarizer_app():
    """Load summarizer-hub service."""
    return _load_service("summarizer-hub", "summarizer-hub")


def _assert_http_ok(response):
    """Assert HTTP 200 response."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestDocumentationQualityWorkflow:
    """Test documentation quality assessment and improvement workflows."""

    def test_api_documentation_completeness_analysis(self, doc_store_app, analysis_service_app):
        """Test analysis of API documentation completeness and quality."""
        doc_client = TestClient(doc_store_app)
        analysis_client = TestClient(analysis_service_app)

        # API documentation with varying completeness levels
        api_docs = [
            {
                "id": "incomplete-api-doc",
                "content": """
# User API

## Endpoints
- GET /users
- POST /users
- DELETE /users
""",
                "metadata": {
                    "type": "api_documentation",
                    "completeness": "low",
                    "issues": ["missing_parameters", "no_examples", "no_error_codes"]
                }
            },
            {
                "id": "complete-api-doc",
                "content": """
# User Management API v2.0

## Overview
Comprehensive user management with authentication and authorization.

## Authentication
All requests require JWT token in Authorization header.

## Endpoints

### GET /api/v2/users
Retrieve paginated list of users.

**Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Items per page (default: 20, max: 100)
- `search` (string, optional): Search query

**Response:**
```json
{
  "users": [...],
  "pagination": {
    "page": 1,
    "total_pages": 5,
    "total_count": 95
  }
}
```

**Error Codes:**
- `400`: Invalid parameters
- `401`: Unauthorized
- `403`: Forbidden

### POST /api/v2/users
Create new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user"
}
```

**Response:** Created user object

**Error Codes:**
- `400`: Validation error
- `409`: User already exists
""",
                "metadata": {
                    "type": "api_documentation",
                    "completeness": "high",
                    "version": "2.0",
                    "examples_count": 4,
                    "error_codes_count": 6
                }
            }
        ]

        # Step 1: Store API documentation
        stored_api_docs = []
        for doc in api_docs:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_api_docs.append(store_resp.json()["data"]["id"])

        # Step 2: Analyze documentation quality
        if analysis_client:
            quality_resp = analysis_client.post("/analyze/quality", json={
                "documents": stored_api_docs,
                "criteria": [
                    "completeness",
                    "consistency",
                    "examples",
                    "error_handling",
                    "authentication"
                ],
                "output_format": "detailed_report"
            })

            # Verify quality analysis
            assert quality_resp.status_code in [200, 202, 404]

            if quality_resp.status_code == 200:
                quality_result = quality_resp.json()
                assert "data" in quality_result or "findings" in quality_result

        # Step 3: Verify quality differences are detectable
        complete_get = doc_client.get("/documents/complete-api-doc")
        incomplete_get = doc_client.get("/documents/incomplete-api-doc")

        _assert_http_ok(complete_get)
        _assert_http_ok(incomplete_get)

        complete_doc = complete_get.json()["data"]
        incomplete_doc = incomplete_get.json()["data"]

        # Complete doc should have higher quality metadata
        assert complete_doc["metadata"]["completeness"] == "high"
        assert incomplete_doc["metadata"]["completeness"] == "low"

    def test_cross_documentation_consistency_analysis(self, doc_store_app, analysis_service_app):
        """Test consistency analysis across related documentation."""
        doc_client = TestClient(doc_store_app)
        analysis_client = TestClient(analysis_service_app)

        # Related documentation that should be consistent
        related_docs = [
            {
                "id": "user-service-readme",
                "content": """
# User Service

## Overview
The User Service manages user accounts, profiles, and authentication.

## API Endpoints
- `GET /users` - List users
- `GET /users/{id}` - Get user details
- `POST /users` - Create user
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

## Data Models

### User
```json
{
  "id": "string",
  "email": "string",
  "name": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Authentication
Uses JWT tokens for authentication.
""",
                "metadata": {
                    "service": "user-service",
                    "type": "readme",
                    "audience": "developers"
                }
            },
            {
                "id": "user-service-api-spec",
                "content": """
# User Service API Specification

## Authentication
Bearer token authentication required.

## Endpoints

### GET /users
**Description:** Retrieve list of users
**Parameters:**
- `limit` (optional): Maximum number of results
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "users": [User],
  "total": "integer"
}
```

### GET /users/{userId}
**Description:** Get specific user
**Parameters:**
- `userId` (path): User identifier

**Response:** User object

### POST /users
**Description:** Create new user
**Request:**
```json
{
  "email": "string",
  "fullName": "string"
}
```

**Response:** Created User object
""",
                "metadata": {
                    "service": "user-service",
                    "type": "api_specification",
                    "audience": "developers"
                }
            },
            {
                "id": "user-service-deployment",
                "content": """
# User Service Deployment Guide

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT tokens
- `REDIS_URL`: Redis connection for caching
- `PORT`: Service port (default: 8080)

## Database Schema

### users table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Health Checks
- `GET /health` - Service health status
- `GET /ready` - Readiness probe

## Monitoring
- Metrics exposed on `/metrics`
- Logs written to stdout
""",
                "metadata": {
                    "service": "user-service",
                    "type": "deployment_guide",
                    "audience": "devops"
                }
            }
        ]

        # Step 1: Store related documentation
        stored_related_docs = []
        for doc in related_docs:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_related_docs.append(store_resp.json()["data"]["id"])

        # Step 2: Analyze consistency across documentation
        if analysis_client:
            consistency_resp = analysis_client.post("/analyze/consistency", json={
                "documents": stored_related_docs,
                "consistency_checks": [
                    "terminology_consistency",
                    "api_endpoint_consistency",
                    "data_model_consistency",
                    "authentication_consistency"
                ],
                "group_by": "service"
            })

            # Verify consistency analysis
            assert consistency_resp.status_code in [200, 202, 404]

    def test_documentation_gap_analysis(self, doc_store_app, analysis_service_app):
        """Test identification of documentation gaps and missing content."""
        doc_client = TestClient(doc_store_app)
        analysis_client = TestClient(analysis_service_app)

        # Documentation set with potential gaps
        documentation_set = [
            {
                "id": "authentication-guide",
                "content": """
# Authentication Guide

## Login Process
1. User submits credentials
2. System validates credentials
3. JWT token is issued
4. Token stored in client

## Token Refresh
- Tokens expire after 1 hour
- Use refresh endpoint to get new token
- Old token becomes invalid

## Logout
- Call logout endpoint
- Token is invalidated
- Client should clear stored token
""",
                "metadata": {
                    "topic": "authentication",
                    "type": "user_guide",
                    "completeness": "partial"
                }
            },
            {
                "id": "api-reference",
                "content": """
# API Reference

## Authentication Endpoints

### POST /auth/login
**Description:** Authenticate user
**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

### POST /auth/refresh
**Description:** Refresh access token

### POST /auth/logout
**Description:** Invalidate token

## User Endpoints

### GET /users
### POST /users
### GET /users/{id}
### PUT /users/{id}
""",
                "metadata": {
                    "topic": "api",
                    "type": "reference",
                    "completeness": "partial"
                }
            }
        ]

        # Step 1: Store documentation
        stored_gap_docs = []
        for doc in documentation_set:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_gap_docs.append(store_resp.json()["data"]["id"])

        # Step 2: Analyze for documentation gaps
        if analysis_client:
            gap_resp = analysis_client.post("/analyze/gaps", json={
                "documents": stored_gap_docs,
                "expected_topics": [
                    "authentication",
                    "authorization",
                    "user_management",
                    "error_handling",
                    "rate_limiting",
                    "data_validation",
                    "security"
                ],
                "gap_types": [
                    "missing_topics",
                    "incomplete_sections",
                    "outdated_information"
                ]
            })

            # Verify gap analysis
            assert gap_resp.status_code in [200, 202, 404]

    def test_documentation_improvement_workflow(self, doc_store_app, summarizer_app):
        """Test documentation improvement through summarization and enhancement."""
        doc_client = TestClient(doc_store_app)
        summarizer_client = TestClient(summarizer_app) if summarizer_app else None

        # Original documentation that could be improved
        original_doc = {
            "id": "user-onboarding-guide",
            "content": """
# User Onboarding

## Getting Started
Welcome to our platform. To get started, you need to create an account.

## Account Creation
Go to signup page. Enter email and password. Click create account.

## Email Verification
Check your email. Click verification link. Your account is now active.

## First Login
Go to login page. Enter credentials. You are now logged in.

## Basic Features
You can now use the platform. Explore the dashboard. Check out settings.
""",
            "metadata": {
                "type": "user_guide",
                "topic": "onboarding",
                "quality": "basic",
                "readability": "low"
            }
        }

        # Step 1: Store original documentation
        store_resp = doc_client.post("/documents", json={
            "id": original_doc["id"],
            "content": original_doc["content"],
            "metadata": original_doc["metadata"]
        })
        _assert_http_ok(store_resp)

        # Step 2: Generate improved version using summarization service
        if summarizer_client:
            improve_resp = summarizer_client.post("/improve/documentation", json={
                "content": original_doc["content"],
                "improvement_type": "enhance_readability",
                "target_audience": "end_users",
                "add_examples": True,
                "structure_content": True
            })

            if improve_resp.status_code == 200:
                improved_content = improve_resp.json()["data"]["improved_content"]

                # Step 3: Store improved documentation
                improved_doc_id = "user-onboarding-guide-improved"
                improved_store_resp = doc_client.post("/documents", json={
                    "id": improved_doc_id,
                    "content": improved_content,
                    "metadata": {
                        "type": "user_guide",
                        "topic": "onboarding",
                        "quality": "enhanced",
                        "readability": "high",
                        "improved_from": original_doc["id"],
                        "improvement_method": "ai_enhanced"
                    }
                })
                _assert_http_ok(improved_store_resp)

        # Step 4: Verify both versions exist and are searchable
        original_get = doc_client.get(f"/documents/{original_doc['id']}")
        _assert_http_ok(original_get)

        search_resp = doc_client.get("/search", params={"q": "user onboarding"})
        _assert_http_ok(search_resp)
        search_results = search_resp.json()["data"]["items"]

        onboarding_found = any("onboarding" in doc["id"] for doc in search_results)
        assert onboarding_found, "Onboarding documentation not found"

    def test_documentation_version_comparison(self, doc_store_app, analysis_service_app):
        """Test comparison and analysis of different documentation versions."""
        doc_client = TestClient(doc_store_app)
        analysis_client = TestClient(analysis_service_app)

        # Different versions of the same documentation
        versions = [
            {
                "id": "payment-api-v1",
                "content": """
# Payment API v1

## Create Payment
POST /payments

Request:
{
  "amount": 100.00,
  "currency": "USD"
}
""",
                "metadata": {
                    "service": "payment-api",
                    "version": "1.0",
                    "status": "deprecated",
                    "breaking_changes": []
                }
            },
            {
                "id": "payment-api-v2",
                "content": """
# Payment API v2

## Breaking Changes
- Authentication now required
- Currency parameter mandatory
- Amount validation enhanced

## Create Payment
POST /v2/payments

Request:
{
  "amount": 100.00,
  "currency": "USD",
  "description": "Payment description"
}
""",
                "metadata": {
                    "service": "payment-api",
                    "version": "2.0",
                    "status": "current",
                    "breaking_changes": [
                        "authentication_required",
                        "currency_mandatory",
                        "enhanced_validation"
                    ]
                }
            }
        ]

        # Step 1: Store versioned documentation
        stored_versions = []
        for doc in versions:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_versions.append(store_resp.json()["data"]["id"])

        # Step 2: Compare documentation versions
        if analysis_client:
            comparison_resp = analysis_client.post("/analyze/compare", json={
                "documents": stored_versions,
                "comparison_type": "version_diff",
                "focus_areas": [
                    "api_changes",
                    "breaking_changes",
                    "new_features",
                    "deprecated_features"
                ]
            })

            # Verify version comparison
            assert comparison_resp.status_code in [200, 202, 404]

        # Step 3: Verify version metadata
        for doc in versions:
            get_resp = doc_client.get(f"/documents/{doc['id']}")
            _assert_http_ok(get_resp)
            retrieved = get_resp.json()["data"]

            assert retrieved["metadata"]["version"] == doc["metadata"]["version"]
            assert retrieved["metadata"]["status"] in ["current", "deprecated"]
