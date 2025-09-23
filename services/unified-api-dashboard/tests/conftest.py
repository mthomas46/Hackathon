"""
Test Configuration and Fixtures

Comprehensive test fixtures for the Unified API Dashboard testing infrastructure.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from ..config import config
from ..modules.api.catalog import APICatalogManager
from ..modules.discovery.client import DiscoveryClient
from ..modules.monitoring.health import HealthMonitor
from ..modules.security import (
    AuditLogger,
    UserManager,
)

# ============================================================================
# MOCK DATA AND FIXTURES
# ============================================================================


@pytest.fixture
def mock_discovery_client():
    """Mock DiscoveryClient for testing."""
    client = Mock(spec=DiscoveryClient)
    client.discover_services = AsyncMock(
        return_value=[
            {
                "service_name": "test-service",
                "service_url": "http://test-service:8000",
                "openapi_spec": {
                    "openapi": "3.0.0",
                    "info": {"title": "Test Service", "version": "1.0.0"},
                    "paths": {
                        "/health": {"get": {"summary": "Health check", "responses": {"200": {"description": "OK"}}}}
                    },
                },
                "health_endpoint": "/health",
                "last_discovered": datetime.now().isoformat(),
            }
        ]
    )
    client.get_service_spec = AsyncMock(
        return_value={"openapi": "3.0.0", "info": {"title": "Test Service", "version": "1.0.0"}}
    )
    return client


@pytest.fixture
def mock_health_monitor():
    """Mock HealthMonitor for testing."""
    monitor = Mock(spec=HealthMonitor)
    monitor.get_health_status = AsyncMock(
        return_value={
            "overall_health": "healthy",
            "services": {
                "test-service": {"status": "healthy", "response_time": 150, "last_check": datetime.now().isoformat()}
            },
        }
    )
    monitor.check_service_health = AsyncMock(
        return_value={"status": "healthy", "response_time": 120, "timestamp": datetime.now().isoformat()}
    )
    return monitor


@pytest.fixture
def mock_api_catalog():
    """Mock APICatalogManager for testing."""
    catalog = Mock(spec=APICatalogManager)
    catalog.get_catalog = AsyncMock(
        return_value={"services": ["test-service"], "total_endpoints": 5, "last_updated": datetime.now().isoformat()}
    )
    catalog.search_apis = AsyncMock(
        return_value=[{"service": "test-service", "endpoint": "/api/test", "method": "GET", "summary": "Test endpoint"}]
    )
    return catalog


@pytest.fixture
def mock_user_manager():
    """Mock UserManager for testing."""
    manager = Mock(spec=UserManager)
    manager.authenticate_user = AsyncMock(
        return_value=Mock(user_id="test_user", username="testuser", role=Mock(value="developer"))
    )
    manager.get_user = AsyncMock(
        return_value=Mock(user_id="test_user", username="testuser", role=Mock(value="developer"))
    )
    return manager


@pytest.fixture
def mock_audit_logger():
    """Mock AuditLogger for testing."""
    logger = Mock(spec=AuditLogger)
    logger.log_event = AsyncMock(return_value="event_123")
    logger.get_events = AsyncMock(return_value=[])
    return logger


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0", "description": "Test API for unit testing"},
        "servers": [{"url": "http://localhost:8000"}],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "Healthy",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        }
                    },
                }
            },
            "/users": {
                "get": {
                    "summary": "Get users",
                    "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 10}}],
                    "responses": {
                        "200": {
                            "description": "Users list",
                            "content": {"application/json": {"schema": {"type": "array", "items": {"type": "object"}}}},
                        }
                    },
                },
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "User created"}},
                },
            },
        },
    }


@pytest.fixture
def sample_api_request():
    """Sample API request for testing."""
    return {
        "service_name": "test-service",
        "endpoint_path": "/api/test",
        "method": "GET",
        "headers": {"Authorization": "Bearer test-token"},
        "params": {"limit": 10},
        "body": None,
    }


@pytest.fixture
def sample_usage_data():
    """Sample usage data for analytics testing."""
    return [
        {
            "timestamp": datetime.now() - timedelta(hours=i),
            "service": "test-service",
            "endpoint": "/api/test",
            "method": "GET",
            "response_time": 150 + i * 10,
            "status_code": 200,
            "user_id": f"user_{i}",
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_error_data():
    """Sample error data for testing."""
    return [
        {
            "timestamp": datetime.now() - timedelta(hours=i),
            "service": "test-service",
            "endpoint": "/api/error",
            "method": "POST",
            "error_type": "validation_error",
            "error_message": f"Validation error {i}",
            "status_code": 400,
            "user_id": f"user_{i}",
        }
        for i in range(5)
    ]


@pytest.fixture
def sample_service_topology():
    """Sample service topology data for testing."""
    return {
        "services": ["api-gateway", "user-service", "auth-service", "data-service"],
        "relationships": [
            {"from": "api-gateway", "to": "user-service", "calls": 150},
            {"from": "api-gateway", "to": "auth-service", "calls": 200},
            {"from": "user-service", "to": "data-service", "calls": 100},
            {"from": "auth-service", "to": "data-service", "calls": 50},
        ],
        "health_status": {
            "api-gateway": "healthy",
            "user-service": "healthy",
            "auth-service": "degraded",
            "data-service": "healthy",
        },
    }


@pytest.fixture
def sample_security_events():
    """Sample security events for testing."""
    return [
        {
            "event_id": f"event_{i}",
            "threat_type": "suspicious_traffic" if i % 2 == 0 else "unauthorized_access",
            "threat_level": "medium",
            "source_ip": f"192.168.1.{i}",
            "user_id": f"user_{i}" if i % 3 == 0 else None,
            "description": f"Security event {i}",
            "timestamp": datetime.now() - timedelta(minutes=i * 5),
            "confidence_score": 0.8,
        }
        for i in range(10)
    ]


# ============================================================================
# ASYNC TEST UTILITIES
# ============================================================================


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    """Async HTTP client for integration tests."""
    # This would be replaced with actual test client in integration tests
    client = Mock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    yield client


# ============================================================================
# TEST CONFIGURATION
# ============================================================================


@pytest.fixture
def test_config():
    """Test configuration override."""
    # Create a test config that doesn't interfere with production
    test_config = config.copy()
    test_config.service.name = "test-unified-api-dashboard"
    test_config.service.port = 8080
    test_config.database.url = "sqlite:///:memory:"
    test_config.cache.enabled = False
    return test_config


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Add any cleanup logic here


@pytest.fixture(scope="session", autouse=True)
async def session_cleanup():
    """Cleanup after test session."""
    yield
    # Add session cleanup logic here
