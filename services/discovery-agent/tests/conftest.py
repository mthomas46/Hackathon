"""Test configuration for discovery-agent service.

This module provides shared fixtures and configuration for all tests.
Fixtures are organized by category for easy discovery.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

# Add service path for imports
service_path = Path(__file__).parent.parent
sys.path.insert(0, str(service_path))

# Add shared services path
shared_path = Path(__file__).parent.parent.parent.parent / "services" / "shared"
if shared_path.exists():
    sys.path.insert(0, str(shared_path))


# ============================================================================
# Domain Entity Fixtures
# ============================================================================

@pytest.fixture
def sample_endpoint():
    """Create a sample endpoint entity for testing."""
    from domain.entities import Endpoint
    return Endpoint(
        path="/api/v1/analyze",
        method="POST",
        summary="Analyze code",
        description="Perform static code analysis",
        parameters=[
            {"name": "code", "in": "body", "required": True},
            {"name": "language", "in": "body", "required": True}
        ],
        responses={
            "200": {"description": "Analysis complete"},
            "400": {"description": "Invalid request"}
        },
        tags=["analysis"]
    )


@pytest.fixture
def sample_service():
    """Create a sample service entity for testing."""
    from domain.entities import Service
    return Service(
        name="code-analyzer",
        base_url="http://code-analyzer:6000",
        openapi_url="http://code-analyzer:6000/openapi.json",
        version="1.0.0",
        description="Code analysis service",
        status="discovered"
    )


@pytest.fixture
def sample_service_with_endpoints(sample_service, sample_endpoint):
    """Create a service with multiple endpoints."""
    endpoint2 = sample_endpoint
    endpoint2.path = "/health"
    endpoint2.method = "GET"
    
    sample_service.add_endpoint(sample_endpoint)
    sample_service.add_endpoint(endpoint2)
    return sample_service


@pytest.fixture
def sample_discovery_result(sample_service):
    """Create a sample discovery result."""
    from domain.entities import DiscoveryResult
    return DiscoveryResult(
        service=sample_service,
        success=True,
        error_message=None
    )


# ============================================================================
# Value Object Fixtures
# ============================================================================

@pytest.fixture
def sample_discovery_spec_url():
    """Create a discovery spec with URL."""
    from domain.value_objects import DiscoverySpec
    return DiscoverySpec(
        url="http://code-analyzer:6000/openapi.json",
        version="3.0.0"
    )


@pytest.fixture
def sample_discovery_spec_content():
    """Create a discovery spec with inline content."""
    from domain.value_objects import DiscoverySpec
    return DiscoverySpec(
        content={
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        },
        version="3.0.0"
    )


@pytest.fixture
def sample_http_method():
    """Create a sample HTTP method value object."""
    from domain.value_objects import HttpMethod
    return HttpMethod(method="GET")


@pytest.fixture
def sample_api_path():
    """Create a sample API path value object."""
    from domain.value_objects import ApiPath
    return ApiPath(path="/api/v1/resource/{id}")


# ============================================================================
# OpenAPI Specification Fixtures
# ============================================================================

@pytest.fixture
def simple_openapi_spec() -> Dict[str, Any]:
    """Simple OpenAPI 3.0 specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test Service API",
            "version": "1.0.0",
            "description": "Test service for discovery"
        },
        "servers": [
            {"url": "http://localhost:8000"}
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "operationId": "health_check",
                    "responses": {
                        "200": {"description": "Service is healthy"}
                    },
                    "tags": ["monitoring"]
                }
            },
            "/api/v1/items": {
                "get": {
                    "summary": "List items",
                    "operationId": "list_items",
                    "responses": {
                        "200": {"description": "Items list"}
                    },
                    "tags": ["items"]
                },
                "post": {
                    "summary": "Create item",
                    "operationId": "create_item",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Item created"}
                    },
                    "tags": ["items"]
                }
            }
        }
    }


@pytest.fixture
def complex_openapi_spec() -> Dict[str, Any]:
    """Complex OpenAPI 3.0 specification with multiple endpoints."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Complex Service API",
            "version": "2.0.0",
            "description": "Complex service with many endpoints"
        },
        "paths": {
            "/api/v1/analyze": {
                "post": {
                    "summary": "Analyze code",
                    "parameters": [
                        {
                            "name": "language",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "code": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Analysis complete"},
                        "400": {"description": "Invalid request"}
                    }
                }
            },
            "/api/v1/search": {
                "get": {
                    "summary": "Search items",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Search results"}
                    }
                }
            }
        }
    }


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator service."""
    mock = Mock()
    mock.register_service = AsyncMock(return_value={"success": True})
    mock.register_tools = AsyncMock(return_value={"success": True, "tools_registered": 5})
    mock.get_service = AsyncMock(return_value={"name": "test-service", "status": "active"})
    return mock


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external requests."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=Mock(
        status_code=200,
        json=lambda: {"openapi": "3.0.0", "info": {}, "paths": {}}
    ))
    mock.post = AsyncMock(return_value=Mock(status_code=201))
    return mock


@pytest.fixture
def mock_openapi_fetcher():
    """Mock OpenAPI specification fetcher."""
    async def fetch_spec(url: str) -> Dict[str, Any]:
        return {
            "openapi": "3.0.0",
            "info": {"title": "Mock API", "version": "1.0.0"},
            "paths": {}
        }
    return fetch_spec


# ============================================================================
# FastAPI Testing Fixtures
# ============================================================================

@pytest.fixture
def test_client():
    """FastAPI test client for API endpoint testing."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture
def test_app():
    """FastAPI application instance for testing."""
    from main import app
    return app


# ============================================================================
# Database/Repository Fixtures
# ============================================================================

@pytest.fixture
def in_memory_repository():
    """In-memory repository for testing (if needed)."""
    from typing import Dict, Optional
    
    class InMemoryRepo:
        def __init__(self):
            self.storage: Dict[str, Any] = {}
        
        async def save(self, entity_id: str, entity: Any) -> None:
            self.storage[entity_id] = entity
        
        async def get(self, entity_id: str) -> Optional[Any]:
            return self.storage.get(entity_id)
        
        async def delete(self, entity_id: str) -> bool:
            if entity_id in self.storage:
                del self.storage[entity_id]
                return True
            return False
        
        async def list_all(self):
            return list(self.storage.values())
    
    return InMemoryRepo()


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def current_timestamp():
    """Current timestamp for testing."""
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_service_urls():
    """Sample service URLs for testing."""
    return {
        "code-analyzer": "http://code-analyzer:6000",
        "orchestrator": "http://orchestrator:5099",
        "doc-store": "http://doc-store:8000",
        "analysis-service": "http://analysis-service:5010"
    }


@pytest.fixture
def sample_tool_definition():
    """Sample LangGraph tool definition."""
    return {
        "name": "code_analyzer_analyze_code",
        "description": "Analyze code for complexity and issues",
        "categories": ["analysis", "code"],
        "service_name": "code-analyzer",
        "service_url": "http://code-analyzer:6000",
        "http_method": "POST",
        "path": "/api/v1/analyze",
        "parameters": {
            "code": {"type": "string", "required": True},
            "language": {"type": "string", "required": True}
        }
    }


# ============================================================================
# Test Data Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically cleanup test data after each test."""
    yield
    # Add any cleanup logic here if needed
    pass


# ============================================================================
# Pytest Configuration Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (with dependencies)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (full workflow)"
    )
