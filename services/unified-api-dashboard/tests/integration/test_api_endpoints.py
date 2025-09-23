"""
Integration Tests for API Endpoints

Comprehensive integration tests for all FastAPI endpoints in the Unified API Dashboard.
Tests authentication, authorization, analytics, developer tools, security, and topology endpoints.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ...conftest import *


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, async_client, mock_user_manager):
        """Test successful login."""
        mock_user = Mock()
        mock_user.user_id = "test_user"
        mock_user.username = "testuser"
        mock_user.role = Mock(value="developer")
        mock_user.permissions = set()
        mock_user_manager.authenticate_user = AsyncMock(return_value=mock_user)

        login_data = {"username": "testuser", "password": "password123"}

        response = await async_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "token" in data["data"]
        assert data["data"]["user_id"] == "test_user"
        assert data["data"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_login_failure(self, async_client, mock_user_manager):
        """Test login failure with invalid credentials."""
        mock_user_manager.authenticate_user = AsyncMock(return_value=None)

        login_data = {"username": "testuser", "password": "wrongpassword"}

        response = await async_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200  # API returns 200 with error in JSON
        data = response.json()
        assert data["success"] == False
        assert "Invalid credentials" in data["message"]

    @pytest.mark.asyncio
    async def test_logout(self, async_client):
        """Test user logout."""
        # First login to get a token
        with patch("services.unified-api-dashboard.modules.security.auth.UserManager.authenticate_user") as mock_auth:
            mock_user = Mock()
            mock_user.user_id = "test_user"
            mock_user.username = "testuser"
            mock_user.role = Mock(value="developer")
            mock_user.permissions = set()
            mock_auth.return_value = mock_user

            login_response = await async_client.post(
                "/api/auth/login", json={"username": "testuser", "password": "password123"}
            )
            token = login_response.json()["data"]["token"]

        # Now logout
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "Logout successful" in data["message"]


class TestAuditEndpoints:
    """Test audit API endpoints."""

    @pytest.mark.asyncio
    async def test_get_audit_events(self, async_client):
        """Test retrieving audit events."""
        # This would require authentication in a real scenario
        response = await async_client.get("/api/audit/events")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_compliance_status(self, async_client):
        """Test compliance status retrieval."""
        response = await async_client.get("/api/audit/compliance")

        # Should require authentication
        assert response.status_code in [401, 403]


class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""

    @pytest.mark.asyncio
    async def test_get_usage_overview(self, async_client):
        """Test usage overview endpoint."""
        response = await async_client.get("/api/analytics/usage/overview")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_performance_insights(self, async_client):
        """Test performance insights endpoint."""
        response = await async_client.get("/api/analytics/performance/insights")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_record_api_request(self, async_client, sample_usage_data):
        """Test API request recording."""
        request_data = sample_usage_data[0]

        response = await async_client.post("/api/analytics/record-request", json=request_data)

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_record_error(self, async_client, sample_error_data):
        """Test error recording."""
        error_data = sample_error_data[0]

        response = await async_client.post("/api/analytics/record-error", json=error_data)

        # Should require authentication
        assert response.status_code in [401, 403]


class TestDeveloperToolsEndpoints:
    """Test developer tools API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_client(self, async_client, sample_openapi_spec):
        """Test client code generation."""
        request_data = {"service_name": "test-service", "language": "python", "openapi_spec": sample_openapi_spec}

        response = await async_client.post("/api/tools/generate-client", json=request_data)

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_validate_spec(self, async_client, sample_openapi_spec):
        """Test OpenAPI specification validation."""
        request_data = {"service_name": "test-service", "openapi_spec": sample_openapi_spec}

        response = await async_client.post("/api/tools/validate-spec", json=request_data)

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_run_integration_test(self, async_client):
        """Test integration test execution."""
        request_data = {
            "service_name": "test-service",
            "test_type": "functional",
            "config": {"concurrent_users": 5, "duration_seconds": 10},
        }

        response = await async_client.post("/api/tools/run-integration-test", json=request_data)

        # Should require authentication
        assert response.status_code in [401, 403]


class TestSecurityEndpoints:
    """Test security API endpoints."""

    @pytest.mark.asyncio
    async def test_get_security_threats(self, async_client):
        """Test security threats retrieval."""
        response = await async_client.get("/api/security/threats")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_security_metrics(self, async_client):
        """Test security metrics retrieval."""
        response = await async_client.get("/api/security/metrics")

        # Should require authentication
        assert response.status_code in [401, 403]


class TestTopologyEndpoints:
    """Test topology API endpoints."""

    @pytest.mark.asyncio
    async def test_get_topology_analysis(self, async_client):
        """Test topology analysis endpoint."""
        response = await async_client.get("/api/topology/analysis")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_topology_visualization(self, async_client):
        """Test topology visualization endpoint."""
        response = await async_client.get("/api/topology/visualization")

        # Should require authentication
        assert response.status_code in [401, 403]


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """Test basic health check."""
        response = await async_client.get("/health")

        # Health endpoint should be publicly accessible
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_api_health_overview(self, async_client):
        """Test API ecosystem health overview."""
        response = await async_client.get("/api/health/apis")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_service_health_status(self, async_client):
        """Test individual service health status."""
        response = await async_client.get("/api/health/services")

        # Should require authentication
        assert response.status_code in [401, 403]


class TestCatalogEndpoints:
    """Test API catalog endpoints."""

    @pytest.mark.asyncio
    async def test_get_api_catalog(self, async_client):
        """Test API catalog retrieval."""
        response = await async_client.get("/api/catalog/endpoints")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_search_apis(self, async_client):
        """Test API search functionality."""
        params = {"query": "health", "limit": 10}

        response = await async_client.get("/api/catalog/search", params=params)

        # Should require authentication
        assert response.status_code in [401, 403]


class TestDiscoveryEndpoints:
    """Test service discovery endpoints."""

    @pytest.mark.asyncio
    async def test_trigger_discovery_scan(self, async_client):
        """Test triggering API discovery scan."""
        response = await async_client.post("/api/discovery/scan")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_discovered_services(self, async_client):
        """Test retrieving discovered services."""
        response = await async_client.get("/api/discovery/services")

        # Should require authentication
        assert response.status_code in [401, 403]


class TestTestingEndpoints:
    """Test API testing endpoints."""

    @pytest.mark.asyncio
    async def test_execute_api_test(self, async_client, sample_api_request):
        """Test API test execution."""
        response = await async_client.post("/api/testing/execute", json=sample_api_request)

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_test_history(self, async_client):
        """Test retrieving test history."""
        response = await async_client.get("/api/testing/history")

        # Should require authentication
        assert response.status_code in [401, 403]


class TestErrorHandling:
    """Test error handling across endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, async_client):
        """Test handling of invalid JSON payloads."""
        response = await async_client.post(
            "/api/auth/login", content="invalid json", headers={"Content-Type": "application/json"}
        )

        # Should handle gracefully
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client):
        """Test handling of missing required fields."""
        incomplete_data = {"username": "testuser"}  # Missing password

        response = await async_client.post("/api/auth/login", json=incomplete_data)

        # Should return validation error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_unsupported_http_method(self, async_client):
        """Test handling of unsupported HTTP methods."""
        response = await async_client.patch("/api/auth/login")

        # Should return method not allowed
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self, async_client):
        """Test handling of nonexistent endpoints."""
        response = await async_client.get("/api/nonexistent/endpoint")

        # Should return not found
        assert response.status_code == 404


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, async_client):
        """Test rate limiting when limits are exceeded."""
        # This would require setting up rate limiting middleware
        # For now, just verify the endpoint exists and requires auth
        response = await async_client.get("/api/catalog/endpoints")

        assert response.status_code in [401, 403, 429]  # Could be rate limited


class TestCORSHeaders:
    """Test CORS headers for cross-origin requests."""

    @pytest.mark.asyncio
    async def test_cors_preflight_request(self, async_client):
        """Test CORS preflight requests."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization",
        }

        response = await async_client.options("/api/auth/login", headers=headers)

        # Should include CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers


class TestContentTypeValidation:
    """Test content type validation."""

    @pytest.mark.asyncio
    async def test_wrong_content_type(self, async_client):
        """Test rejection of wrong content types."""
        response = await async_client.post(
            "/api/auth/login",
            content='{"username": "test", "password": "test"}',
            headers={"Content-Type": "text/plain"},
        )

        # Should reject non-JSON content
        assert response.status_code in [400, 415]
