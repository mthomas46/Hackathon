"""
Unit tests for domain entities.

Tests cover:
- Endpoint entity
- Service entity (aggregate root)
- DiscoveryResult entity
"""

import pytest
from datetime import datetime, timezone


@pytest.mark.unit
@pytest.mark.domain
class TestEndpointEntity:
    """Test Endpoint entity."""
    
    def test_endpoint_creation(self):
        """Test creating an endpoint."""
        from domain.entities import Endpoint
        
        endpoint = Endpoint(
            path="/api/v1/test",
            method="GET",
            summary="Test endpoint",
            description="A test endpoint for testing",
            parameters=[],
            responses={"200": {"description": "Success"}},
            tags=["test"]
        )
        
        assert endpoint.path == "/api/v1/test"
        assert endpoint.method == "GET"
        assert endpoint.summary == "Test endpoint"
        assert endpoint.description == "A test endpoint for testing"
        assert endpoint.tags == ["test"]
    
    def test_endpoint_with_parameters(self, sample_endpoint):
        """Test endpoint with parameters."""
        assert len(sample_endpoint.parameters) == 2
        assert sample_endpoint.parameters[0]["name"] == "code"
        assert sample_endpoint.parameters[0]["required"] is True
    
    def test_endpoint_equality(self):
        """Test endpoint equality based on path and method."""
        from domain.entities import Endpoint
        
        endpoint1 = Endpoint(
            path="/api/test",
            method="GET",
            summary="Test",
            description="Test",
            parameters=[],
            responses={},
            tags=[]
        )
        
        endpoint2 = Endpoint(
            path="/api/test",
            method="GET",
            summary="Different summary",
            description="Different",
            parameters=[],
            responses={},
            tags=[]
        )
        
        endpoint3 = Endpoint(
            path="/api/test",
            method="POST",
            summary="Test",
            description="Test",
            parameters=[],
            responses={},
            tags=[]
        )
        
        # Same path and method should be equal
        assert endpoint1 == endpoint2
        # Different method should not be equal
        assert endpoint1 != endpoint3
    
    def test_endpoint_hash(self):
        """Test endpoint can be used in sets/dicts."""
        from domain.entities import Endpoint
        
        endpoint1 = Endpoint(
            path="/api/test",
            method="GET",
            summary="Test",
            description="Test",
            parameters=[],
            responses={},
            tags=[]
        )
        
        endpoint2 = Endpoint(
            path="/api/test",
            method="GET",
            summary="Different",
            description="Different",
            parameters=[],
            responses={},
            tags=[]
        )
        
        # Should be able to use in a set
        endpoint_set = {endpoint1, endpoint2}
        assert len(endpoint_set) == 1  # Same path+method
    
    def test_endpoint_to_dict(self, sample_endpoint):
        """Test converting endpoint to dictionary."""
        endpoint_dict = sample_endpoint.to_dict()
        
        assert endpoint_dict["path"] == sample_endpoint.path
        assert endpoint_dict["method"] == sample_endpoint.method
        assert endpoint_dict["summary"] == sample_endpoint.summary
        assert endpoint_dict["parameters"] == sample_endpoint.parameters


@pytest.mark.unit
@pytest.mark.domain
class TestServiceEntity:
    """Test Service entity (aggregate root)."""
    
    def test_service_creation(self):
        """Test creating a service."""
        from domain.entities import Service
        
        service = Service(
            name="test-service",
            base_url="http://test-service:8000",
            openapi_url="http://test-service:8000/openapi.json",
            version="1.0.0",
            description="Test service",
            status="discovered"
        )
        
        assert service.name == "test-service"
        assert service.base_url == "http://test-service:8000"
        assert service.version == "1.0.0"
        assert service.status == "discovered"
        assert len(service.endpoints) == 0
    
    def test_service_add_endpoint(self, sample_service, sample_endpoint):
        """Test adding endpoint to service."""
        sample_service.add_endpoint(sample_endpoint)
        
        assert len(sample_service.endpoints) == 1
        assert sample_endpoint in sample_service.endpoints
    
    def test_service_add_duplicate_endpoint(self, sample_service):
        """Test that adding duplicate endpoint doesn't create duplicates."""
        from domain.entities import Endpoint
        
        endpoint1 = Endpoint(
            path="/api/test",
            method="GET",
            summary="Test 1",
            description="Test",
            parameters=[],
            responses={},
            tags=[]
        )
        
        endpoint2 = Endpoint(
            path="/api/test",
            method="GET",
            summary="Test 2",
            description="Test",
            parameters=[],
            responses={},
            tags=[]
        )
        
        sample_service.add_endpoint(endpoint1)
        sample_service.add_endpoint(endpoint2)
        
        # Should only have one endpoint (same path+method)
        assert len(sample_service.endpoints) == 1
    
    def test_service_remove_endpoint(self, sample_service, sample_endpoint):
        """Test removing endpoint from service."""
        sample_service.add_endpoint(sample_endpoint)
        assert len(sample_service.endpoints) == 1
        
        sample_service.remove_endpoint(sample_endpoint.path, sample_endpoint.method)
        assert len(sample_service.endpoints) == 0
    
    def test_service_find_endpoint(self, sample_service, sample_endpoint):
        """Test finding endpoint in service."""
        sample_service.add_endpoint(sample_endpoint)
        
        found = sample_service.find_endpoint("/api/v1/analyze", "POST")
        assert found is not None
        assert found.path == "/api/v1/analyze"
        
        not_found = sample_service.find_endpoint("/nonexistent", "GET")
        assert not_found is None
    
    def test_service_get_endpoints_by_tag(self, sample_service_with_endpoints):
        """Test getting endpoints by tag."""
        analysis_endpoints = sample_service_with_endpoints.get_endpoints_by_tag("analysis")
        
        assert len(analysis_endpoints) >= 1
        assert all("analysis" in ep.tags for ep in analysis_endpoints)
    
    def test_service_get_endpoints_by_method(self, sample_service_with_endpoints):
        """Test getting endpoints by HTTP method."""
        get_endpoints = sample_service_with_endpoints.get_endpoints_by_method("GET")
        post_endpoints = sample_service_with_endpoints.get_endpoints_by_method("POST")
        
        assert all(ep.method == "GET" for ep in get_endpoints)
        assert all(ep.method == "POST" for ep in post_endpoints)
    
    def test_service_endpoint_count(self, sample_service_with_endpoints):
        """Test endpoint count property."""
        count = sample_service_with_endpoints.endpoint_count
        
        assert count == 2
        assert count == len(sample_service_with_endpoints.endpoints)
    
    def test_service_to_dict(self, sample_service):
        """Test converting service to dictionary."""
        service_dict = sample_service.to_dict()
        
        assert service_dict["name"] == sample_service.name
        assert service_dict["base_url"] == sample_service.base_url
        assert service_dict["version"] == sample_service.version
        assert service_dict["status"] == sample_service.status
        assert "endpoints" in service_dict
    
    def test_service_equality(self):
        """Test service equality based on name."""
        from domain.entities import Service
        
        service1 = Service(
            name="test-service",
            base_url="http://test:8000",
            openapi_url="http://test:8000/openapi.json",
            version="1.0.0",
            description="Test",
            status="discovered"
        )
        
        service2 = Service(
            name="test-service",
            base_url="http://different:8000",
            openapi_url="http://different:8000/openapi.json",
            version="2.0.0",
            description="Different",
            status="active"
        )
        
        service3 = Service(
            name="different-service",
            base_url="http://test:8000",
            openapi_url="http://test:8000/openapi.json",
            version="1.0.0",
            description="Test",
            status="discovered"
        )
        
        # Same name should be equal
        assert service1 == service2
        # Different name should not be equal
        assert service1 != service3


@pytest.mark.unit
@pytest.mark.domain
class TestDiscoveryResultEntity:
    """Test DiscoveryResult entity."""
    
    def test_discovery_result_success(self, sample_service):
        """Test successful discovery result."""
        from domain.entities import DiscoveryResult
        
        result = DiscoveryResult(
            service=sample_service,
            success=True,
            error_message=None
        )
        
        assert result.success is True
        assert result.error_message is None
        assert result.service == sample_service
        assert result.is_successful is True
    
    def test_discovery_result_failure(self):
        """Test failed discovery result."""
        from domain.entities import DiscoveryResult
        
        result = DiscoveryResult(
            service=None,
            success=False,
            error_message="Failed to fetch OpenAPI specification"
        )
        
        assert result.success is False
        assert result.error_message == "Failed to fetch OpenAPI specification"
        assert result.service is None
        assert result.is_successful is False
    
    def test_discovery_result_with_metadata(self, sample_service):
        """Test discovery result with metadata."""
        from domain.entities import DiscoveryResult
        
        result = DiscoveryResult(
            service=sample_service,
            success=True,
            error_message=None,
            discovered_at=datetime.now(timezone.utc),
            discovery_duration_ms=150.5,
            metadata={"source": "orchestrator", "version": "3.0.0"}
        )
        
        assert result.discovered_at is not None
        assert result.discovery_duration_ms == 150.5
        assert result.metadata["source"] == "orchestrator"
    
    def test_discovery_result_to_dict(self, sample_discovery_result):
        """Test converting discovery result to dictionary."""
        result_dict = sample_discovery_result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["error_message"] is None
        assert "service" in result_dict
        assert result_dict["service"]["name"] == "code-analyzer"
    
    def test_discovery_result_summary(self, sample_service):
        """Test discovery result summary property."""
        from domain.entities import DiscoveryResult
        
        result = DiscoveryResult(
            service=sample_service,
            success=True,
            error_message=None
        )
        
        summary = result.summary
        
        assert "success" in summary.lower() or "successful" in summary.lower()
        assert sample_service.name in summary

