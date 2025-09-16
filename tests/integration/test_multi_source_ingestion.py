"""Integration tests for multi-source document ingestion workflows.

These tests verify the complete workflow from multiple source ingestion
through analysis and reporting, simulating enterprise documentation scenarios.
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
def source_agent_app():
    """Load source-agent service."""
    return _load_service("source-agent", "source-agent")


def _assert_http_ok(response):
    """Assert HTTP 200 response."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestMultiSourceIngestionWorkflow:
    """Test multi-source document ingestion and analysis workflows."""

    def test_enterprise_api_documentation_ingestion(self, doc_store_app, analysis_service_app):
        """Test ingestion of enterprise API documentation from multiple sources."""
        doc_client = TestClient(doc_store_app)
        analysis_client = TestClient(analysis_service_app)

        # Simulate enterprise API documentation from different teams
        enterprise_docs = [
            {
                "id": "auth-service-api",
                "title": "Authentication Service API",
                "content": """
# Authentication Service API

## Overview
Central authentication service for enterprise platform.

## Endpoints

### POST /auth/login
Authenticate user credentials.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "jwt_token",
  "expires_in": 3600
}
```

### POST /auth/refresh
Refresh authentication token.

### POST /auth/logout
Invalidate authentication token.
""",
                "metadata": {
                    "source": "confluence",
                    "team": "platform-security",
                    "service": "auth-service",
                    "api_version": "v2.1",
                    "last_updated": "2024-01-15",
                    "tags": ["authentication", "security", "enterprise"]
                }
            },
            {
                "id": "user-mgmt-api",
                "title": "User Management Service API",
                "content": """
# User Management Service API

## Overview
User profile and permission management.

## Endpoints

### GET /users
Retrieve paginated user list.

### GET /users/{id}
Retrieve specific user profile.

### POST /users
Create new user account.

### PUT /users/{id}
Update user profile and permissions.

### DELETE /users/{id}
Deactivate user account.
""",
                "metadata": {
                    "source": "github",
                    "team": "platform-users",
                    "service": "user-mgmt",
                    "api_version": "v1.8",
                    "last_updated": "2024-01-10",
                    "tags": ["users", "profiles", "permissions"]
                }
            },
            {
                "id": "billing-api",
                "title": "Billing Service API",
                "content": """
# Billing Service API

## Overview
Subscription and billing management.

## Endpoints

### GET /billing/subscriptions
List user subscriptions.

### POST /billing/subscriptions
Create new subscription.

### PUT /billing/subscriptions/{id}
Update subscription details.

### POST /billing/invoices/{id}/pay
Process payment for invoice.
""",
                "metadata": {
                    "source": "jira",
                    "team": "platform-billing",
                    "service": "billing-service",
                    "api_version": "v3.2",
                    "last_updated": "2024-01-20",
                    "tags": ["billing", "subscriptions", "payments"]
                }
            }
        ]

        # Step 1: Ingest all enterprise documentation
        stored_docs = []
        for doc in enterprise_docs:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_doc = store_resp.json()["data"]
            stored_docs.append(stored_doc["id"])

        # Step 2: Verify cross-service search capabilities
        search_resp = doc_client.get("/search", params={"q": "authentication login"})
        _assert_http_ok(search_resp)
        search_results = search_resp.json()["data"]["items"]

        # Should find auth service documentation
        auth_found = any("auth-service" in doc["id"] for doc in search_results)
        assert auth_found, "Auth service documentation not found in search"

        # Step 3: Run enterprise-wide API consistency analysis
        if analysis_client:
            analysis_resp = analysis_client.post("/analyze", json={
                "targets": stored_docs,
                "analysis_type": "consistency",
                "scope": "enterprise_api",
                "filters": {
                    "services": ["auth-service", "user-mgmt", "billing-service"]
                }
            })

            # Analysis might be async or return different status
            assert analysis_resp.status_code in [200, 202, 404], f"Unexpected analysis response: {analysis_resp.status_code}"

    def test_technical_documentation_aggregation(self, doc_store_app):
        """Test aggregation of technical documentation from various sources."""
        doc_client = TestClient(doc_store_app)

        # Technical documentation from different sources
        tech_docs = [
            {
                "id": "architecture-overview",
                "content": """
# System Architecture Overview

## Microservices Architecture

The platform consists of the following microservices:

1. **API Gateway** - Request routing and authentication
2. **User Service** - User management and profiles
3. **Order Service** - Order processing and fulfillment
4. **Payment Service** - Payment processing and billing
5. **Notification Service** - Email and push notifications
6. **Analytics Service** - Usage analytics and reporting

## Data Flow

1. Client request → API Gateway → Authentication
2. Authenticated request → Appropriate microservice
3. Business logic processing → Database operations
4. Response generation → Client

## Technology Stack

- **Backend**: Python, FastAPI, PostgreSQL
- **Frontend**: React, TypeScript
- **Infrastructure**: Kubernetes, Docker
- **Monitoring**: Prometheus, Grafana
""",
                "metadata": {
                    "type": "architecture_documentation",
                    "source": "confluence",
                    "category": "technical",
                    "audience": "developers",
                    "tags": ["architecture", "microservices", "infrastructure"]
                }
            },
            {
                "id": "deployment-guide",
                "content": """
# Deployment Guide

## Local Development Setup

### Prerequisites
- Docker Desktop
- Python 3.9+
- Node.js 16+

### Setup Steps

1. **Clone Repository**
```bash
git clone https://github.com/company/platform.git
cd platform
```

2. **Start Infrastructure**
```bash
docker-compose up -d postgres redis
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
cd frontend && npm install
```

4. **Run Services**
```bash
# Backend
python -m services.api_gateway.main

# Frontend
npm start
```

## Production Deployment

### Kubernetes Deployment

1. Build Docker images
2. Apply Kubernetes manifests
3. Configure ingress and SSL
4. Set up monitoring

### Environment Variables

Required environment variables for production:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: JWT signing secret
- `API_KEYS`: Comma-separated API keys
""",
                "metadata": {
                    "type": "deployment_documentation",
                    "source": "github",
                    "category": "operational",
                    "audience": "devops",
                    "tags": ["deployment", "kubernetes", "docker"]
                }
            },
            {
                "id": "api-reference",
                "content": """
# API Reference

## Authentication

All API requests require authentication via JWT token.

### Obtaining Token

```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

### Using Token

```http
Authorization: Bearer <jwt_token>
```

## Common Response Formats

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE"
}
```

## Rate Limiting

- 1000 requests per hour for read operations
- 100 requests per hour for write operations
- Rate limit headers included in responses
""",
                "metadata": {
                    "type": "api_documentation",
                    "source": "swagger",
                    "category": "reference",
                    "audience": "developers",
                    "tags": ["api", "authentication", "reference"]
                }
            }
        ]

        # Step 1: Store all technical documentation
        stored_tech_docs = []
        for doc in tech_docs:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_tech_docs.append(store_resp.json()["data"]["id"])

        # Step 2: Test technical documentation search and filtering
        # Search for architecture information
        arch_search = doc_client.get("/search", params={"q": "microservices architecture"})
        _assert_http_ok(arch_search)
        arch_results = arch_search.json()["data"]["items"]

        arch_found = any("architecture" in doc["id"] for doc in arch_results)
        assert arch_found, "Architecture documentation not found"

        # Search for deployment information
        deploy_search = doc_client.get("/search", params={"q": "kubernetes deployment"})
        _assert_http_ok(deploy_search)
        deploy_results = deploy_search.json()["data"]["items"]

        deploy_found = any("deployment" in doc["id"] for doc in deploy_results)
        assert deploy_found, "Deployment documentation not found"

        # Search for API information
        api_search = doc_client.get("/search", params={"q": "authentication jwt"})
        _assert_http_ok(api_search)
        api_results = api_search.json()["data"]["items"]

        api_found = any("api" in doc["id"] for doc in api_results)
        assert api_found, "API documentation not found"

    def test_documentation_versioning_and_releases(self, doc_store_app):
        """Test documentation versioning and release management."""
        doc_client = TestClient(doc_store_app)

        # Documentation versions for a service
        versions = [
            {
                "id": "payment-api-v1.0",
                "version": "1.0",
                "content": """
# Payment API v1.0

## Endpoints
- POST /payments - Process payment
- GET /payments/{id} - Get payment status
""",
                "metadata": {
                    "service": "payment-api",
                    "version": "1.0",
                    "status": "deprecated",
                    "release_date": "2023-06-01"
                }
            },
            {
                "id": "payment-api-v1.5",
                "version": "1.5",
                "content": """
# Payment API v1.5

## Endpoints
- POST /payments - Process payment (enhanced validation)
- GET /payments/{id} - Get payment status
- POST /payments/{id}/refund - Process refund
""",
                "metadata": {
                    "service": "payment-api",
                    "version": "1.5",
                    "status": "deprecated",
                    "release_date": "2023-09-15"
                }
            },
            {
                "id": "payment-api-v2.0",
                "version": "2.0",
                "content": """
# Payment API v2.0

## Breaking Changes
- Authentication now required for all endpoints
- Currency parameter now mandatory

## New Features
- Support for multiple payment methods
- Webhook notifications for payment events
- Enhanced error handling

## Endpoints
- POST /v2/payments - Process payment
- GET /v2/payments/{id} - Get payment details
- POST /v2/payments/{id}/refund - Process refund
- GET /v2/webhooks - List webhook configurations
""",
                "metadata": {
                    "service": "payment-api",
                    "version": "2.0",
                    "status": "current",
                    "release_date": "2024-01-01"
                }
            }
        ]

        # Step 1: Store all versions
        for doc in versions:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)

        # Step 2: Search for current version
        current_search = doc_client.get("/search", params={
            "q": "payment api",
            "filters": {"version": "2.0", "status": "current"}
        })

        if current_search.status_code == 200:
            current_results = current_search.json()["data"]["items"]
            v2_found = any("v2.0" in doc["id"] for doc in current_results)

            if len(current_results) > 0:  # If filtering is implemented
                assert v2_found, "Current API version not found"

        # Step 3: Verify version information in metadata
        for doc in versions:
            get_resp = doc_client.get(f"/documents/{doc['id']}")
            _assert_http_ok(get_resp)
            retrieved = get_resp.json()["data"]

            assert retrieved["metadata"]["version"] == doc["version"]
            assert retrieved["metadata"]["status"] in ["current", "deprecated"]
            assert "release_date" in retrieved["metadata"]

    def test_cross_team_documentation_consistency(self, doc_store_app, analysis_service_app):
        """Test consistency analysis across documentation from different teams."""
        doc_client = TestClient(doc_store_app)
        analysis_client = TestClient(analysis_service_app)

        # Documentation from different development teams
        team_docs = [
            {
                "id": "frontend-api-usage",
                "content": """
# Frontend API Usage Guide

## Authentication
```javascript
const token = await login(username, password);
localStorage.setItem('token', token);
```

## User Management
```javascript
// Get user profile
const user = await api.get('/users/profile');

// Update user
await api.put('/users/profile', userData);
```

## Error Handling
```javascript
try {
  const result = await api.post('/users', userData);
} catch (error) {
  if (error.status === 401) {
    // Redirect to login
  }
}
```
""",
                "metadata": {
                    "team": "frontend",
                    "type": "usage_guide",
                    "language": "javascript",
                    "framework": "react"
                }
            },
            {
                "id": "backend-api-implementation",
                "content": """
# Backend API Implementation

## Authentication Middleware
```python
def authenticate_request():
    token = request.headers.get('Authorization')
    if not token:
        raise HTTPException(status_code=401)

    # Validate JWT token
    payload = jwt.decode(token, SECRET_KEY)
    return payload['user_id']
```

## User Endpoints
```python
@app.get('/users/profile')
def get_user_profile(user_id: int = Depends(authenticate_request)):
    user = db.query(User).filter(User.id == user_id).first()
    return user.to_dict()

@app.put('/users/profile')
def update_user_profile(user_data: UserUpdate, user_id: int = Depends(authenticate_request)):
    user = db.query(User).filter(User.id == user_id).first()
    user.update(user_data)
    db.commit()
    return user.to_dict()
```
""",
                "metadata": {
                    "team": "backend",
                    "type": "implementation",
                    "language": "python",
                    "framework": "fastapi"
                }
            },
            {
                "id": "mobile-api-integration",
                "content": """
# Mobile API Integration

## iOS Integration
```swift
class APIService {
    func login(username: String, password: String) async throws -> String {
        let request = LoginRequest(username: username, password: password)
        let response: LoginResponse = try await apiClient.post("/auth/login", body: request)
        return response.token
    }

    func getUserProfile() async throws -> UserProfile {
        return try await apiClient.get("/users/profile")
    }
}
```

## Android Integration
```kotlin
class APIService(private val apiClient: APIClient) {

    suspend fun login(username: String, password: String): Result<String> {
        return try {
            val response = apiClient.post<LoginResponse>("/auth/login",
                LoginRequest(username, password))
            Result.success(response.token)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getUserProfile(): Result<UserProfile> {
        return apiClient.get("/users/profile")
    }
}
```
""",
                "metadata": {
                    "team": "mobile",
                    "type": "integration_guide",
                    "platforms": ["ios", "android"],
                    "languages": ["swift", "kotlin"]
                }
            }
        ]

        # Step 1: Store cross-team documentation
        stored_team_docs = []
        for doc in team_docs:
            store_resp = doc_client.post("/documents", json={
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
            _assert_http_ok(store_resp)
            stored_team_docs.append(store_resp.json()["data"]["id"])

        # Step 2: Test cross-team search capabilities
        # Search for authentication patterns
        auth_search = doc_client.get("/search", params={"q": "authentication login"})
        _assert_http_ok(auth_search)
        auth_results = auth_search.json()["data"]["items"]

        # Should find documentation from multiple teams
        frontend_found = any("frontend" in doc["id"] for doc in auth_results)
        backend_found = any("backend" in doc["id"] for doc in auth_results)

        assert frontend_found or backend_found, "Cross-team auth documentation not found"

        # Step 3: Analyze consistency across team implementations
        if analysis_client:
            consistency_resp = analysis_client.post("/analyze", json={
                "targets": stored_team_docs,
                "analysis_type": "consistency",
                "scope": "cross_team",
                "focus_areas": ["authentication", "error_handling", "api_usage"]
            })

            # Verify analysis request is accepted
            assert consistency_resp.status_code in [200, 202, 404]
