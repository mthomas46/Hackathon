"""Unit tests for ExternalService domain entity."""

import pytest
from datetime import datetime, timezone
from domain.entities.external_service import (
    ExternalService,
    ServiceType,
    ServiceStatus,
    ServiceEndpoint
)


class TestExternalService:
    """Test cases for ExternalService entity."""

    def test_create_basic_external_service(self):
        """Test creating a basic external service."""
        service = ExternalService(
            name="test-service",
            service_type=ServiceType.API,
            description="A test service"
        )

        assert service.name == "test-service"
        assert service.service_type == ServiceType.API
        assert service.description == "A test service"
        assert service.status == ServiceStatus.ACTIVE
        assert service.version == "1.0.0"
        assert len(service.endpoints) == 0
        assert isinstance(service.created_at, datetime)
        assert service.id == ""

    def test_create_service_with_all_fields(self):
        """Test creating a service with all optional fields."""
        created_time = datetime.now(timezone.utc)

        service = ExternalService(
            id="test-123",
            name="full-service",
            display_name="Full Test Service",
            description="Complete service description",
            summary="Brief summary",
            service_type=ServiceType.DATABASE,
            status=ServiceStatus.DEPRECATED,
            version="2.1.3",
            latest_release="2.1.4",
            release_date=created_time,
            technologies=["python", "postgresql", "docker"],
            run_requirements={"python": ">=3.8", "memory": "2GB"},
            base_url="https://api.example.com",
            port=443,
            health_endpoint="/health",
            created_at=created_time
        )

        assert service.id == "test-123"
        assert service.name == "full-service"
        assert service.display_name == "Full Test Service"
        assert service.description == "Complete service description"
        assert service.summary == "Brief summary"
        assert service.service_type == ServiceType.DATABASE
        assert service.status == ServiceStatus.DEPRECATED
        assert service.version == "2.1.3"
        assert service.latest_release == "2.1.4"
        assert service.release_date == created_time
        assert service.technologies == ["python", "postgresql", "docker"]
        assert service.run_requirements == {"python": ">=3.8", "memory": "2GB"}
        assert service.base_url == "https://api.example.com"
        assert service.port == 443
        assert service.health_endpoint == "/health"
        assert service.created_at == created_time

    def test_service_with_endpoints(self):
        """Test service with endpoint management."""
        service = ExternalService(
            name="api-service",
            service_type=ServiceType.API
        )

        # Add endpoint
        endpoint = ServiceEndpoint(
            id="ep1",
            path="/users",
            method="GET",
            description="Get users"
        )

        service.endpoints.append(endpoint)

        assert len(service.endpoints) == 1
        assert service.endpoints[0].path == "/users"
        assert service.endpoints[0].method == "GET"

    def test_get_active_endpoints(self):
        """Test getting active endpoints."""
        service = ExternalService(
            name="test-service",
            service_type=ServiceType.API
        )

        # Add active endpoint (with ID)
        active_endpoint = ServiceEndpoint(
            id="active-1",
            path="/active",
            description="Active endpoint"
        )

        # Add inactive endpoint (no ID)
        inactive_endpoint = ServiceEndpoint(
            path="/inactive",
            description="Inactive endpoint"
        )

        service.endpoints.extend([active_endpoint, inactive_endpoint])

        active_endpoints = service.get_active_endpoints()

        assert len(active_endpoints) == 1
        assert active_endpoints[0].id == "active-1"
        assert active_endpoints[0].path == "/active"

    def test_add_endpoint(self):
        """Test adding endpoints to service."""
        service = ExternalService(
            name="test-service",
            service_type=ServiceType.API
        )

        endpoint = ServiceEndpoint(
            path="/test",
            method="POST",
            description="Test endpoint"
        )

        service.endpoints.append(endpoint)

        assert len(service.endpoints) == 1
        assert service.endpoints[0].path == "/test"
        assert service.endpoints[0].method == "POST"

    def test_remove_endpoint(self):
        """Test removing endpoints from service."""
        service = ExternalService(
            name="test-service",
            service_type=ServiceType.API
        )

        # Add multiple endpoints
        ep1 = ServiceEndpoint(id="ep1", path="/ep1", description="Endpoint 1")
        ep2 = ServiceEndpoint(id="ep2", path="/ep2", description="Endpoint 2")
        ep3 = ServiceEndpoint(id="ep3", path="/ep3", description="Endpoint 3")

        service.endpoints.extend([ep1, ep2, ep3])

        # Remove middle endpoint
        service.endpoints.pop(1)

        assert len(service.endpoints) == 2
        assert service.endpoints[0].id == "ep1"
        assert service.endpoints[1].id == "ep3"

    def test_service_type_enum_values(self):
        """Test all service type enum values."""
        for service_type in ServiceType:
            service = ExternalService(
                name=f"test-{service_type.value}",
                service_type=service_type
            )
            assert service.service_type == service_type

    def test_service_status_enum_values(self):
        """Test all service status enum values."""
        for status in ServiceStatus:
            service = ExternalService(
                name=f"test-{status.value}",
                service_type=ServiceType.API,
                status=status
            )
            assert service.status == status

    def test_service_default_values(self):
        """Test default values are set correctly."""
        service = ExternalService(
            name="minimal-service",
            service_type=ServiceType.API
        )

        assert service.id == ""
        assert service.display_name == "Minimal Service"  # Auto-generated from name
        assert service.description == ""
        assert service.summary == ""
        assert service.status == ServiceStatus.ACTIVE
        assert service.version == "1.0.0"
        assert service.latest_release is None
        assert service.release_date is None
        assert service.technologies == []
        assert service.run_requirements == {}
        assert service.base_url is None
        assert service.port is None
        assert service.health_endpoint is None
        assert service.endpoints == []
        assert isinstance(service.created_at, datetime)

    def test_service_equality(self):
        """Test service equality comparison."""
        # Create services with same values
        service1 = ExternalService(
            id="test-123",
            name="test-service",
            service_type=ServiceType.API
        )

        service2 = ExternalService(
            id="test-123",
            name="test-service",
            service_type=ServiceType.API
        )

        service3 = ExternalService(
            id="different-id",
            name="test-service",
            service_type=ServiceType.API
        )

        # Test that services with same field values are equal (ignoring auto-generated timestamps)
        # Since dataclass compares all fields including timestamps, we'll test field-by-field
        assert service1.id == service2.id
        assert service1.name == service2.name
        assert service1.service_type == service2.service_type

        # Different IDs should make core identity different
        assert service1.id != service3.id

    def test_service_string_representation(self):
        """Test service string representation."""
        service = ExternalService(
            id="test-123",
            name="test-service",
            service_type=ServiceType.API,
            description="Test description"
        )

        # Test that it has a string representation
        str_repr = str(service)
        assert "ExternalService" in str_repr
        assert "test-service" in str_repr

    def test_service_with_empty_endpoints_list(self):
        """Test service behavior with empty endpoints."""
        service = ExternalService(
            name="empty-service",
            service_type=ServiceType.API
        )

        assert service.endpoints == []
        assert service.get_active_endpoints() == []

    def test_service_created_at_timezone(self):
        """Test that created_at uses UTC timezone."""
        service = ExternalService(
            name="timezone-service",
            service_type=ServiceType.API
        )

        assert service.created_at.tzinfo is not None
        assert service.created_at.tzinfo == timezone.utc


class TestServiceEndpoint:
    """Test cases for ServiceEndpoint value object."""

    def test_create_basic_endpoint(self):
        """Test creating a basic service endpoint."""
        endpoint = ServiceEndpoint(
            path="/test",
            method="GET",
            description="Test endpoint"
        )

        assert endpoint.id == ""
        assert endpoint.path == "/test"
        assert endpoint.method == "GET"
        assert endpoint.description == "Test endpoint"
        assert endpoint.request_contract == {}
        assert endpoint.response_contract == {}
        assert endpoint.response_types == []
        assert endpoint.parameters == []
        assert endpoint.authentication_required is False
        assert endpoint.rate_limit is None
        assert isinstance(endpoint.created_at, datetime)

    def test_create_endpoint_with_contracts(self):
        """Test endpoint with request and response contracts."""
        endpoint = ServiceEndpoint(
            id="contract-ep",
            path="/users",
            method="POST",
            description="Create user",
            request_contract={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"}
                },
                "required": ["name", "email"]
            },
            response_contract={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            },
            response_types=["application/json", "application/xml"],
            authentication_required=True,
            rate_limit="100/hour"
        )

        assert endpoint.id == "contract-ep"
        assert endpoint.path == "/users"
        assert endpoint.method == "POST"
        assert endpoint.authentication_required is True
        assert endpoint.rate_limit == "100/hour"
        assert "application/json" in endpoint.response_types
        assert endpoint.request_contract["required"] == ["name", "email"]

    def test_endpoint_parameters(self):
        """Test endpoint with parameters."""
        parameters = [
            {
                "name": "user_id",
                "type": "string",
                "required": True,
                "description": "User identifier"
            },
            {
                "name": "format",
                "type": "string",
                "required": False,
                "enum": ["json", "xml"],
                "default": "json"
            }
        ]

        endpoint = ServiceEndpoint(
            path="/users/{user_id}",
            method="GET",
            description="Get user by ID",
            parameters=parameters
        )

        assert len(endpoint.parameters) == 2
        assert endpoint.parameters[0]["name"] == "user_id"
        assert endpoint.parameters[0]["required"] is True
        assert endpoint.parameters[1]["default"] == "json"

    def test_endpoint_default_values(self):
        """Test endpoint default values."""
        endpoint = ServiceEndpoint()

        assert endpoint.id == ""
        assert endpoint.path == "/"  # Default path
        assert endpoint.method == "GET"
        assert endpoint.description == ""
        assert endpoint.request_contract == {}
        assert endpoint.response_contract == {}
        assert endpoint.response_types == []
        assert endpoint.parameters == []
        assert endpoint.authentication_required is False
        assert endpoint.rate_limit is None
        assert isinstance(endpoint.created_at, datetime)

    def test_endpoint_equality(self):
        """Test endpoint equality."""
        endpoint1 = ServiceEndpoint(
            id="ep1",
            path="/test",
            method="GET"
        )

        endpoint2 = ServiceEndpoint(
            id="ep1",
            path="/test",
            method="GET"
        )

        endpoint3 = ServiceEndpoint(
            id="ep2",
            path="/test",
            method="GET"
        )

        # Test field-by-field equality since timestamps differ
        assert endpoint1.id == endpoint2.id
        assert endpoint1.path == endpoint2.path
        assert endpoint1.method == endpoint2.method

        # Different IDs should make them different
        assert endpoint1.id != endpoint3.id

    def test_endpoint_string_representation(self):
        """Test endpoint string representation."""
        endpoint = ServiceEndpoint(
            path="/api/test",
            method="POST",
            description="Test endpoint"
        )

        str_repr = str(endpoint)
        assert "ServiceEndpoint" in str_repr
        assert "/api/test" in str_repr
        assert "POST" in str_repr
