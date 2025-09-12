"""Documentation Consistency Fixtures - Focused fixtures for documentation consistency testing.

This module provides pytest fixtures specifically for testing the documentation consistency
ecosystem, including realistic data for GitHub, Jira, Confluence, and OpenAPI sources.
"""

import pytest
from typing import Dict, List, Any


@pytest.fixture
def sample_github_repo_data() -> Dict[str, Any]:
    """Sample GitHub repository data for testing."""
    return {
        "id": 123456,
        "name": "my-api-service",
        "full_name": "company/my-api-service",
        "description": "REST API service for user management",
        "readme_content": """
# My API Service

A REST API service for managing users and authentication.

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh access token

### Users
- `GET /users` - List users
- `POST /users` - Create user
- `GET /users/{id}` - Get user details
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

## Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error
        """,
        "open_api_content": {
            "openapi": "3.0.3",
            "info": {"title": "My API Service", "version": "1.0.0"},
            "paths": {
                "/auth/login": {
                    "post": {
                        "responses": {
                            "200": {"description": "Success"},
                            "400": {"description": "Bad Request"},
                            "401": {"description": "Unauthorized"},
                            "422": {"description": "Validation Error"}
                        }
                    }
                },
                "/users": {
                    "get": {
                        "responses": {
                            "200": {"description": "Success"},
                            "401": {"description": "Unauthorized"}
                        }
                    },
                    "post": {
                        "responses": {
                            "201": {"description": "Created"},
                            "400": {"description": "Bad Request"},
                            "401": {"description": "Unauthorized"}
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_jira_ticket_data() -> Dict[str, Any]:
    """Sample Jira ticket data for testing."""
    return {
        "key": "PROJ-123",
        "summary": "Implement user authentication API",
        "description": """As a user, I want to be able to authenticate via API so that I can access protected resources.

Acceptance Criteria:
- API should support JWT token-based authentication
- Login endpoint should validate credentials and return JWT
- Protected endpoints should validate JWT tokens
- Invalid tokens should return 401 Unauthorized
- Token expiration should be handled gracefully

Technical Details:
- Use bcrypt for password hashing
- JWT expiration: 1 hour
- Refresh token: 24 hours
        """,
        "status": "In Progress",
        "assignee": "developer@company.com",
        "created": "2024-01-15T10:00:00Z",
        "updated": "2024-01-16T14:30:00Z"
    }


@pytest.fixture
def sample_confluence_page_data() -> Dict[str, Any]:
    """Sample Confluence page data for testing."""
    return {
        "id": "12345678",
        "title": "API Authentication Guide",
        "content": """
# API Authentication Guide

## Overview
This guide covers authentication mechanisms for our API services.

## JWT Authentication
Our API uses JWT (JSON Web Tokens) for authentication.

### Login Process
1. Send POST request to `/auth/login` with credentials
2. Receive JWT token in response
3. Include token in Authorization header for subsequent requests

### Token Format
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Error Handling
- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: Valid token but insufficient permissions
- **422 Validation Error**: Malformed request

## Best Practices
- Store tokens securely (not in localStorage for production)
- Implement token refresh logic
- Handle token expiration gracefully
- Validate tokens on both client and server side
        """,
        "space": "Engineering",
        "created": "2024-01-10T09:00:00Z",
        "updated": "2024-01-15T16:00:00Z",
        "author": "tech-writer@company.com"
    }


@pytest.fixture
def consistency_finding_data() -> Dict[str, Any]:
    """Sample consistency finding data."""
    return {
        "id": "finding-123",
        "type": "error_code_mismatch",
        "severity": "high",
        "title": "API Error Code Mismatch",
        "description": "README documents error code 422 but OpenAPI spec defines 400",
        "sources": [
            {
                "type": "github_readme",
                "location": "README.md:25",
                "content": "422 - Validation Error"
            },
            {
                "type": "openapi_spec",
                "location": "/auth/login:responses:400",
                "content": "400 - Bad Request"
            }
        ],
        "suggested_fix": "Update README to use error code 400 instead of 422",
        "owners": ["api-team@company.com"],
        "confidence_score": 0.95
    }


@pytest.fixture
def documentation_consistency_scenario() -> Dict[str, Any]:
    """Complete documentation consistency test scenario."""
    return {
        "name": "authentication_api_consistency",
        "description": "Test consistency between README, OpenAPI spec, and Jira ticket for authentication API",
        "sources": {
            "github": {
                "repo": "company/my-api-service",
                "readme_content": "# Authentication API\n\nSupports JWT tokens with error codes 400, 401, 404, 500",
                "openapi_spec": {
                    "paths": {
                        "/auth/login": {
                            "post": {
                                "responses": {
                                    "200": {"description": "Success"},
                                    "401": {"description": "Unauthorized"},
                                    "422": {"description": "Validation Error"}
                                }
                            }
                        }
                    }
                }
            },
            "jira": {
                "ticket": "PROJ-123",
                "acceptance_criteria": "API should return 422 for validation errors, 401 for auth failures"
            },
            "confluence": {
                "page": "API Error Handling",
                "content": "Authentication API returns 400 for bad requests, 401 for unauthorized access"
            }
        },
        "expected_findings": [
            {
                "type": "error_code_inconsistency",
                "description": "Jira specifies 422 but Confluence documents 400",
                "severity": "medium"
            },
            {
                "type": "spec_readme_mismatch",
                "description": "OpenAPI defines 422 but README only lists 400",
                "severity": "low"
            }
        ]
    }


@pytest.fixture
def service_health_data() -> Dict[str, Any]:
    """Sample service health check data."""
    return {
        "orchestrator": {
            "status": "healthy",
            "uptime": "2d 4h 30m",
            "last_check": "2024-01-16T10:00:00Z"
        },
        "doc_store": {
            "status": "healthy",
            "documents_count": 1247,
            "last_ingestion": "2024-01-16T09:45:00Z"
        },
        "consistency_engine": {
            "status": "healthy",
            "findings_count": 23,
            "last_analysis": "2024-01-16T09:30:00Z"
        },
        "reporting": {
            "status": "healthy",
            "reports_generated": 5,
            "last_report": "2024-01-16T08:00:00Z"
        }
    }


@pytest.fixture
def api_contract_data() -> Dict[str, Any]:
    """Sample API contract test data."""
    return {
        "service_name": "user-service",
        "version": "1.0.0",
        "endpoints": [
            {
                "path": "/users",
                "method": "GET",
                "expected_status": 200,
                "expected_response_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "array"},
                        "pagination": {"type": "object"}
                    }
                }
            },
            {
                "path": "/users",
                "method": "POST",
                "request_body": {"name": "John Doe", "email": "john@example.com"},
                "expected_status": 201
            }
        ],
        "auth_required": True,
        "rate_limit": "1000/hour"
    }
