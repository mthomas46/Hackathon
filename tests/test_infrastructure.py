"""Testing Infrastructure - In-memory databases and service mocking.

This module provides comprehensive testing infrastructure for the documentation
consistency ecosystem including in-memory databases, service mocks, and
realistic data fixtures for all services.
"""

import pytest
import sqlite3
import tempfile
import os
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, MagicMock
import json
from datetime import datetime, timedelta


class InMemoryDatabase:
    """In-memory SQLite database for testing all services."""

    def __init__(self):
        self.db_path = ":memory:"
        self.connection = None
        self._initialize_schema()

    def _initialize_schema(self):
        """Initialize database schema for all services."""
        # isolation for xdist: a dedicated connection per test function/process
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        self.connection.row_factory = sqlite3.Row

        # Create tables for all services
        self._create_doc_store_tables()
        self._create_analysis_service_tables()
        self._create_prompt_store_tables()
        self._create_orchestrator_tables()
        self._create_frontend_tables()

    def _create_doc_store_tables(self):
        """Create Doc Store tables."""
        self.connection.execute("""
            CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_id TEXT,
                content TEXT NOT NULL,
                metadata TEXT,
                quality_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE analyses (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                analysis_type TEXT,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)

        self.connection.execute("""
            CREATE VIRTUAL TABLE documents_fts USING fts5(
                id, content, metadata,
                content=documents,
                content_rowid=rowid
            )
        """)

    def _create_analysis_service_tables(self):
        """Create Analysis Service tables."""
        self.connection.execute("""
            CREATE TABLE findings (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                source TEXT,
                location TEXT,
                owners TEXT,
                confidence REAL DEFAULT 0.0,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE reports (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                data TEXT,
                format TEXT DEFAULT 'json',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _create_prompt_store_tables(self):
        """Create Prompt Store tables."""
        self.connection.execute("""
            CREATE TABLE prompts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                version TEXT DEFAULT '1.0.0',
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE ab_tests (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                prompts TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _create_orchestrator_tables(self):
        """Create Orchestrator tables."""
        self.connection.execute("""
            CREATE TABLE workflows (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                config TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE services (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT DEFAULT 'unknown',
                last_health_check TIMESTAMP,
                capabilities TEXT
            )
        """)

    def _create_frontend_tables(self):
        """Create Frontend tables."""
        self.connection.execute("""
            CREATE TABLE ui_state (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                component TEXT,
                state TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def execute(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a query and return results as dicts."""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        self.connection.commit()
        return results

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


@pytest.fixture(scope="function")
def in_memory_db():
    """Provide in-memory database for all tests."""
    db = InMemoryDatabase()
    yield db
    db.close()


class ServiceMocks:
    """Mock implementations for all services."""

    @staticmethod
    def create_doc_store_mock():
        """Create mock for Doc Store service."""
        mock = Mock(name="DocStoreMock")
        mock.get_document.return_value = {
            "id": "doc-123",
            "content": "# Sample Document\n\nContent here.",
            "source": "github",
            "metadata": {"quality_score": 0.85}
        }
        mock.search_documents.return_value = [
            {"id": "doc-1", "content": "Authentication guide", "score": 0.95},
            {"id": "doc-2", "content": "API documentation", "score": 0.87}
        ]
        mock.store_document.return_value = "doc-456"
        return mock

    @staticmethod
    def create_analysis_service_mock():
        """Create mock for Analysis Service."""
        mock = Mock(name="AnalysisServiceMock")
        mock.analyze_document.return_value = {
            "findings": [
                {
                    "type": "consistency_error",
                    "severity": "high",
                    "description": "Error code mismatch detected"
                }
            ],
            "quality_score": 0.78
        }
        mock.get_findings.return_value = [
            {
                "id": "finding-1",
                "type": "error_code_mismatch",
                "severity": "high",
                "title": "API Error Code Inconsistency",
                "description": "Error codes differ between documentation sources"
            }
        ]
        return mock

    @staticmethod
    def create_source_agent_mock():
        """Create mock for Source Agent."""
        mock = Mock(name="SourceAgentMock")
        mock.fetch_github.return_value = {
            "documents": [
                {
                    "source": "github",
                    "path": "README.md",
                    "content": "# API Documentation\n\nREST API for user management."
                }
            ]
        }
        mock.fetch_jira.return_value = {
            "documents": [
                {
                    "source": "jira",
                    "key": "PROJ-123",
                    "content": "Implement JWT authentication",
                    "type": "Story"
                }
            ]
        }
        mock.normalize_content.return_value = {
            "normalized_content": "# API Documentation\n\nNormalized content.",
            "metadata": {"format": "markdown", "headings": ["API Documentation"]}
        }
        return mock

    @staticmethod
    def create_orchestrator_mock():
        """Create mock for Orchestrator."""
        mock = Mock(name="OrchestratorMock")
        mock.execute_workflow.return_value = {
            "workflow_id": "workflow-123",
            "status": "completed",
            "result": {"documents_processed": 5, "findings_generated": 3}
        }
        mock.get_service_health.return_value = {
            "doc_store": "healthy",
            "analysis-service": "healthy",
            "source-agent": "healthy"
        }
        return mock

    @staticmethod
    def create_frontend_mock():
        """Create mock for Frontend."""
        mock = Mock(name="FrontendMock")
        mock.get_findings_view.return_value = {
            "findings": [],
            "total_count": 0,
            "severity_breakdown": {"high": 0, "medium": 0, "low": 0}
        }
        mock.search_documents.return_value = {
            "results": [],
            "total_count": 0,
            "query": "test"
        }
        return mock


@pytest.fixture
def service_mocks():
    """Provide service mocks for testing."""
    return {
        "doc_store": ServiceMocks.create_doc_store_mock(),
        "analysis_service": ServiceMocks.create_analysis_service_mock(),
        "source_agent": ServiceMocks.create_source_agent_mock(),
        "orchestrator": ServiceMocks.create_orchestrator_mock(),
        "frontend": ServiceMocks.create_frontend_mock()
    }


class RealisticDataFixtures:
    """Realistic data fixtures for all services."""

    @staticmethod
    def github_document():
        """Realistic GitHub document fixture."""
        return {
            "id": "github-doc-123",
            "source": "github",
            "source_id": "company/my-api-service/README.md",
            "content": """# User Management API

A comprehensive REST API for managing users and authentication in our platform.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. All requests require a valid JWT token in the Authorization header.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Endpoints

### GET /users
Retrieve a list of users.

**Query Parameters:**
- `page` (integer, optional): Page number for pagination
- `limit` (integer, optional): Number of users per page (max 100)

**Response:**
```json
{
  "data": [
    {
      "id": "user-123",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "admin",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150
  }
}
```

### POST /users
Create a new user.

**Request:**
```json
{
  "email": "newuser@example.com",
  "name": "Jane Smith",
  "password": "securepassword123",
  "role": "user"
}
```

**Response Codes:**
- `201` - User created successfully
- `400` - Invalid request data
- `409` - User already exists
- `422` - Validation error

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  }
}
```

## Rate Limiting

API requests are limited to:
- 1000 requests per hour for authenticated users
- 100 requests per hour for anonymous users

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1640995200
```""",
            "metadata": {
                "repository": "company/my-api-service",
                "path": "README.md",
                "branch": "main",
                "author": "api-team",
                "last_commit": "2024-01-15T14:30:00Z",
                "language": "Markdown",
                "size": 2048,
                "quality_score": 0.92
            },
            "quality_score": 0.92,
            "created_at": "2024-01-15T14:30:00Z"
        }

    @staticmethod
    def jira_ticket():
        """Realistic Jira ticket fixture."""
        return {
            "id": "jira-ticket-456",
            "source": "jira",
            "source_id": "PROJ-123",
            "content": """## User Authentication System Implementation

### Description
As a platform user, I want to be able to securely authenticate using industry-standard methods so that I can access protected resources and maintain account security.

### Acceptance Criteria
- [ ] Implement JWT-based authentication with refresh tokens
- [ ] Support password-based login with bcrypt hashing
- [ ] Provide password reset functionality via email
- [ ] Implement session management with configurable timeouts
- [ ] Support OAuth2 integration with Google and GitHub
- [ ] Add rate limiting to prevent brute force attacks
- [ ] Implement account lockout after failed attempts
- [ ] Provide audit logging for security events
- [ ] Support multi-factor authentication (MFA)
- [ ] Implement secure password policies

### Technical Requirements
- Use RS256 algorithm for JWT signing
- Implement token refresh with sliding expiration
- Store password hashes using bcrypt with salt rounds >= 12
- Implement secure random token generation
- Use HTTPS for all authentication endpoints
- Implement CSRF protection
- Add security headers (HSTS, CSP, X-Frame-Options)
- Support JWT blacklisting for logout
- Implement secure cookie settings

### Security Considerations
- Prevent timing attacks in password comparison
- Implement secure password reset token generation
- Add request rate limiting per IP and user
- Implement account lockout after 5 failed attempts
- Add audit logging for all authentication events
- Implement secure session management
- Add protection against common attacks (XSS, CSRF, injection)

### API Endpoints
- POST /auth/login - User login
- POST /auth/logout - User logout
- POST /auth/refresh - Token refresh
- POST /auth/forgot-password - Password reset request
- POST /auth/reset-password - Password reset confirmation
- GET /auth/me - Current user info
- POST /auth/change-password - Password change

### Error Codes
- 400 - Bad Request (invalid input)
- 401 - Unauthorized (invalid credentials)
- 403 - Forbidden (insufficient permissions)
- 422 - Validation Error (input validation failed)
- 429 - Too Many Requests (rate limited)
- 500 - Internal Server Error

### Dependencies
- bcrypt for password hashing
- PyJWT for JWT token handling
- redis for token blacklisting
- email service for password reset
- rate limiting middleware

### Testing Requirements
- Unit tests for password hashing and JWT generation
- Integration tests for complete authentication flow
- Security tests for common vulnerabilities
- Load tests for concurrent authentication requests
- End-to-end tests for password reset flow""",
            "metadata": {
                "project": "PROJ",
                "key": "PROJ-123",
                "type": "Story",
                "status": "In Progress",
                "priority": "High",
                "assignee": "backend-team",
                "reporter": "product-manager",
                "created": "2024-01-10T09:15:00Z",
                "updated": "2024-01-15T11:20:00Z",
                "labels": ["authentication", "security", "api"],
                "components": ["Backend", "Security"],
                "story_points": 13,
                "epic": "User Management System"
            },
            "quality_score": 0.88,
            "created_at": "2024-01-15T11:20:00Z"
        }

    @staticmethod
    def confluence_page():
        """Realistic Confluence page fixture."""
        return {
            "id": "confluence-page-789",
            "source": "confluence",
            "source_id": "page-789",
            "content": """# API Error Code Reference

## Overview

This document provides a comprehensive reference for all API error codes used across our platform. Consistent error handling is crucial for providing a good developer experience and debugging issues effectively.

## Error Code Categories

### Authentication Errors (4xx)

#### 4001 - Invalid Credentials
**Description:** The provided username or password is incorrect.

**HTTP Status:** 401 Unauthorized

**Example Response:**
```json
{
  "error": {
    "code": "4001",
    "message": "Invalid credentials provided",
    "details": {
      "reason": "username_password_mismatch"
    }
  }
}
```

**Troubleshooting:**
- Verify username and password are correct
- Check if account is locked due to failed attempts
- Ensure password hasn't expired

#### 4002 - Token Expired
**Description:** The JWT token has expired and needs to be refreshed.

**HTTP Status:** 401 Unauthorized

**Example Response:**
```json
{
  "error": {
    "code": "4002",
    "message": "Authentication token has expired",
    "details": {
      "expired_at": "2024-01-15T10:30:00Z",
      "can_refresh": true
    }
  }
}
```

**Resolution:**
- Use refresh token to get new access token
- Implement automatic token refresh in client applications

#### 4003 - Insufficient Permissions
**Description:** User doesn't have required permissions for the operation.

**HTTP Status:** 403 Forbidden

**Example Response:**
```json
{
  "error": {
    "code": "4003",
    "message": "Insufficient permissions for this operation",
    "details": {
      "required_role": "admin",
      "user_role": "user",
      "missing_permissions": ["user.delete", "system.config"]
    }
  }
}
```

### Validation Errors (4xx)

#### 4101 - Missing Required Field
**Description:** A required field is missing from the request.

**HTTP Status:** 400 Bad Request

**Example Response:**
```json
{
  "error": {
    "code": "4101",
    "message": "Required field is missing",
    "details": {
      "field": "email",
      "location": "request.body"
    }
  }
}
```

#### 4102 - Invalid Field Format
**Description:** A field value doesn't match the expected format.

**HTTP Status:** 400 Bad Request

**Example Response:**
```json
{
  "error": {
    "code": "4102",
    "message": "Field format is invalid",
    "details": {
      "field": "email",
      "value": "invalid-email",
      "expected_format": "RFC 5322 email address",
      "suggestion": "user@domain.com"
    }
  }
}
```

### System Errors (5xx)

#### 5001 - Database Connection Error
**Description:** Unable to connect to the database.

**HTTP Status:** 500 Internal Server Error

**Example Response:**
```json
{
  "error": {
    "code": "5001",
    "message": "Database connection failed",
    "details": {
      "retry_after": 30,
      "incident_id": "db-conn-20240115-001"
    }
  }
}
```

#### 5002 - External Service Unavailable
**Description:** A required external service is currently unavailable.

**HTTP Status:** 502 Bad Gateway

**Example Response:**
```json
{
  "error": {
    "code": "5002",
    "message": "External service temporarily unavailable",
    "details": {
      "service": "payment-gateway",
      "estimated_recovery": "5 minutes",
      "alternative_available": false
    }
  }
}
```

## Error Code Mapping

| Error Code | HTTP Status | Category | Retryable |
|------------|-------------|----------|-----------|
| 4001 | 401 | Authentication | No |
| 4002 | 401 | Authentication | No (use refresh) |
| 4003 | 403 | Authorization | No |
| 4101 | 400 | Validation | No |
| 4102 | 400 | Validation | No |
| 5001 | 500 | System | Yes |
| 5002 | 502 | System | Yes |

## Best Practices

### For API Consumers
1. Always check error codes in addition to HTTP status codes
2. Implement proper error handling for each error type
3. Use exponential backoff for retryable errors
4. Log errors with sufficient context for debugging

### For API Developers
1. Use consistent error code ranges for different categories
2. Include actionable error messages
3. Provide suggestions for fixing validation errors
4. Include retry information for transient errors

## Monitoring and Alerting

Error rates should be monitored:
- Overall error rate should be < 1%
- Authentication errors should be < 5% of total requests
- Individual error codes should be tracked for anomalies

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-01 | Initial error code reference |
| 1.1 | 2024-01-10 | Added validation errors section |
| 1.2 | 2024-01-15 | Added monitoring guidelines |""",
            "metadata": {
                "space": "Engineering",
                "title": "API Error Code Reference",
                "page_id": "789",
                "author": "api-team",
                "created": "2024-01-01T00:00:00Z",
                "updated": "2024-01-15T09:45:00Z",
                "labels": ["api", "error-codes", "reference", "documentation"],
                "parent_page": "API Documentation",
                "version": 3,
                "comments_count": 5
            },
            "quality_score": 0.95,
            "created_at": "2024-01-15T09:45:00Z"
        }

    @staticmethod
    def openapi_spec():
        """Realistic OpenAPI specification fixture."""
        return {
            "id": "openapi-spec-101",
            "source": "openapi",
            "source_id": "company/my-api/v1/spec.yaml",
            "content": """openapi: 3.0.3
info:
  title: User Management API
  description: A comprehensive REST API for managing users and authentication
  version: 1.0.0
  contact:
    name: API Support
    email: api-support@company.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.company.com/v1
    description: Production server
  - url: https://staging-api.company.com/v1
    description: Staging server
  - url: https://dev-api.company.com/v1
    description: Development server

security:
  - bearerAuth: []
  - apiKeyAuth: []

paths:
  /auth/login:
    post:
      summary: Authenticate user
      description: Authenticate a user with email and password
      tags:
        - Authentication
      security: []  # No auth required for login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - email
                - password
              properties:
                email:
                  type: string
                  format: email
                  example: user@example.com
                password:
                  type: string
                  format: password
                  minLength: 8
                  example: securepassword123
      responses:
        '200':
          description: Authentication successful
          content:
            application/json:
              schema:
                type: object
                required:
                  - access_token
                  - token_type
                  - expires_in
                properties:
                  access_token:
                    type: string
                    example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                  token_type:
                    type: string
                    example: bearer
                  expires_in:
                    type: integer
                    example: 3600
                  refresh_token:
                    type: string
                    example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        '400':
          description: Bad request - invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Authentication failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Too many requests
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /users:
    get:
      summary: List users
      description: Retrieve a paginated list of users
      tags:
        - Users
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
          description: Page number for pagination
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
          description: Number of users per page
        - name: search
          in: query
          schema:
            type: string
          description: Search query for filtering users
      responses:
        '200':
          description: Users retrieved successfully
          content:
            application/json:
              schema:
                type: object
                required:
                  - data
                  - pagination
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
        '401':
          description: Authentication required
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

    post:
      summary: Create user
      description: Create a new user account
      tags:
        - Users
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                type: object
                required:
                  - data
                properties:
                  data:
                    $ref: '#/components/schemas/User'
        '400':
          description: Bad request - invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: User already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /users/{userId}:
    get:
      summary: Get user
      description: Retrieve a specific user by ID
      tags:
        - Users
      security:
        - bearerAuth: []
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
            format: uuid
          description: Unique identifier of the user
      responses:
        '200':
          description: User retrieved successfully
          content:
            application/json:
              schema:
                type: object
                required:
                  - data
                properties:
                  data:
                    $ref: '#/components/schemas/User'
        '401':
          description: Authentication required
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: User not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token for authentication
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key for authentication

  schemas:
    User:
      type: object
      required:
        - id
        - email
        - name
        - role
        - created_at
      properties:
        id:
          type: string
          format: uuid
          example: 123e4567-e89b-12d3-a456-426614174000
        email:
          type: string
          format: email
          example: user@example.com
        name:
          type: string
          example: John Doe
        role:
          type: string
          enum: [admin, user, guest]
          example: user
        created_at:
          type: string
          format: date-time
          example: 2024-01-15T10:00:00Z
        updated_at:
          type: string
          format: date-time
          example: 2024-01-15T10:00:00Z

    CreateUserRequest:
      type: object
      required:
        - email
        - name
        - password
      properties:
        email:
          type: string
          format: email
          example: newuser@example.com
        name:
          type: string
          example: Jane Smith
        password:
          type: string
          format: password
          minLength: 8
          example: securepassword123
        role:
          type: string
          enum: [admin, user, guest]
          default: user
          example: user

    Pagination:
      type: object
      required:
        - page
        - limit
        - total
      properties:
        page:
          type: integer
          example: 1
        limit:
          type: integer
          example: 20
        total:
          type: integer
          example: 150
        total_pages:
          type: integer
          example: 8

    Error:
      type: object
      required:
        - error
      properties:
        error:
          type: object
          required:
            - code
            - message
          properties:
            code:
              type: string
              example: VALIDATION_ERROR
            message:
              type: string
              example: Invalid request parameters
            details:
              type: object
              example:
                field: email
                issue: Invalid email format""",
            "metadata": {
                "title": "User Management API",
                "version": "1.0.0",
                "format": "openapi",
                "endpoints_count": 3,
                "schemas_count": 5,
                "last_updated": "2024-01-15T12:00:00Z",
                "generated_from": "company/my-api"
            },
            "quality_score": 0.90,
            "created_at": "2024-01-15T12:00:00Z"
        }

    @staticmethod
    def consistency_finding():
        """Realistic consistency finding fixture."""
        return {
            "id": "finding-123",
            "type": "error_code_mismatch",
            "severity": "high",
            "title": "API Error Code Inconsistency Detected",
            "description": "Error codes between OpenAPI spec and README documentation don't match",
            "source": "consistency_analysis",
            "location": "API documentation comparison",
            "evidence": [
                {
                    "document_type": "openapi_spec",
                    "location": "/auth/login:responses:422",
                    "content": "422 - Validation Error",
                    "confidence": 0.95
                },
                {
                    "document_type": "readme",
                    "location": "README.md:45",
                    "content": "400 - Bad Request for validation errors",
                    "confidence": 0.92
                }
            ],
            "suggested_fix": "Update README.md to use error code 422 instead of 400 for validation errors",
            "owners": ["api-team@company.com", "docs-team@company.com"],
            "confidence": 0.94,
            "category": "api_consistency",
            "tags": ["error_codes", "validation", "documentation_drift"],
            "created_at": "2024-01-15T13:30:00Z",
            "status": "open"
        }

    @staticmethod
    def workflow_execution():
        """Realistic workflow execution fixture."""
        return {
            "workflow_id": "workflow-456",
            "type": "documentation_consistency_analysis",
            "status": "completed",
            "config": {
                "sources": ["github", "jira", "confluence", "openapi"],
                "analysis_types": ["error_code_consistency", "terminology_consistency"],
                "include_llm_analysis": True,
                "parallel_processing": True
            },
            "steps": [
                {
                    "step_id": "ingest-github",
                    "name": "Ingest GitHub Documentation",
                    "status": "completed",
                    "duration_ms": 2340,
                    "documents_processed": 15,
                    "started_at": "2024-01-15T13:00:00Z",
                    "completed_at": "2024-01-15T13:00:02Z"
                },
                {
                    "step_id": "ingest-jira",
                    "name": "Ingest Jira Tickets",
                    "status": "completed",
                    "duration_ms": 1890,
                    "documents_processed": 8,
                    "started_at": "2024-01-15T13:00:02Z",
                    "completed_at": "2024-01-15T13:00:04Z"
                },
                {
                    "step_id": "ingest-confluence",
                    "name": "Ingest Confluence Pages",
                    "status": "completed",
                    "duration_ms": 3450,
                    "documents_processed": 12,
                    "started_at": "2024-01-15T13:00:04Z",
                    "completed_at": "2024-01-15T13:00:07Z"
                },
                {
                    "step_id": "consistency-analysis",
                    "name": "Run Consistency Analysis",
                    "status": "completed",
                    "duration_ms": 5670,
                    "findings_generated": 23,
                    "started_at": "2024-01-15T13:00:07Z",
                    "completed_at": "2024-01-15T13:00:13Z"
                },
                {
                    "step_id": "generate-report",
                    "name": "Generate Findings Report",
                    "status": "completed",
                    "duration_ms": 890,
                    "reports_generated": 1,
                    "started_at": "2024-01-15T13:00:13Z",
                    "completed_at": "2024-01-15T13:00:14Z"
                }
            ],
            "result": {
                "total_documents_processed": 35,
                "findings_generated": 23,
                "high_severity_findings": 5,
                "medium_severity_findings": 12,
                "low_severity_findings": 6,
                "processing_time_ms": 14250,
                "success_rate": 1.0
            },
            "created_at": "2024-01-15T13:00:00Z",
            "completed_at": "2024-01-15T13:00:14Z",
            "duration_ms": 14250
        }


@pytest.fixture
def realistic_fixtures():
    """Provide realistic data fixtures for all services."""
    return {
        "github_document": RealisticDataFixtures.github_document(),
        "jira_ticket": RealisticDataFixtures.jira_ticket(),
        "confluence_page": RealisticDataFixtures.confluence_page(),
        "openapi_spec": RealisticDataFixtures.openapi_spec(),
        "consistency_finding": RealisticDataFixtures.consistency_finding(),
        "workflow_execution": RealisticDataFixtures.workflow_execution()
    }
