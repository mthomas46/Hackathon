"""Comprehensive unit tests for ToolDiscoveryService.

Tests all methods including the newly refactored categorization logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path for imports
current_dir = Path(__file__).parent  # tests/unit
tests_dir = current_dir.parent       # tests
service_dir = tests_dir.parent       # discovery-agent
services_dir = service_dir.parent    # services
project_root = services_dir.parent   # project root

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(services_dir))

from services.discovery_agent.domain.services.tool_discovery import ToolDiscoveryService  # type: ignore


class TestToolDiscoveryService:
    """Test suite for ToolDiscoveryService."""

    @pytest.fixture
    def service(self):
        """Create a ToolDiscoveryService instance."""
        return ToolDiscoveryService()

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        return AsyncMock()

    def test_initialization(self, service):
        """Test service initialization."""
        assert service.discovered_tools == {}
        assert service.service_client is not None
        assert service.security_scanner is None
        assert service.monitoring_service is None
        assert service.registry_storage is None

    def test_set_security_scanner(self, service):
        """Test setting security scanner."""
        scanner = MagicMock()
        service.set_security_scanner(scanner)
        assert service.security_scanner == scanner

    def test_set_monitoring_service(self, service):
        """Test setting monitoring service."""
        monitoring = MagicMock()
        service.set_monitoring_service(monitoring)
        assert service.monitoring_service == monitoring

    def test_set_registry_storage(self, service):
        """Test setting registry storage."""
        storage = MagicMock()
        service.set_registry_storage(storage)
        assert service.registry_storage == storage

    @pytest.mark.asyncio
    async def test_discover_tools_success(self, service):
        """Test successful tool discovery."""
        mock_spec = {
            "paths": {
                "/api/test": {
                    "get": {
                        "operationId": "getTest",
                        "summary": "Get test data"
                    }
                }
            }
        }

        with patch.object(service, '_fetch_openapi_spec', return_value=mock_spec) as mock_fetch:
            with patch.object(service, '_extract_endpoints') as mock_extract:
                with patch.object(service, '_analyze_endpoints_for_tools') as mock_analyze:
                    mock_extract.return_value = [{"path": "/api/test", "method": "GET", "operation_id": "getTest"}]
                    mock_analyze.return_value = [{"name": "test_tool", "description": "Test tool"}]

                    result = await service.discover_tools("test-service", "http://test.com")

                    assert result["service_name"] == "test-service"
                    assert result["endpoints_discovered"] == 1
                    assert result["tools_discovered"] == 1
                    assert "test-service" in service.discovered_tools

    @pytest.mark.asyncio
    async def test_discover_tools_fetch_failure(self, service):
        """Test tool discovery when OpenAPI fetch fails."""
        with patch.object(service, '_fetch_openapi_spec', side_effect=Exception("Fetch failed")):
            with pytest.raises(Exception, match="Failed to discover tools"):
                await service.discover_tools("test-service", "http://test.com")

    def test_extract_endpoints(self, service):
        """Test endpoint extraction from OpenAPI spec."""
        spec = {
            "paths": {
                "/api/users": {
                    "get": {
                        "operationId": "getUsers",
                        "summary": "Get users",
                        "description": "Retrieve users",
                        "tags": ["users"],
                        "parameters": [{"name": "limit", "in": "query"}],
                        "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                        "responses": {"200": {"description": "Success"}}
                    },
                    "post": {
                        "operationId": "createUser",
                        "summary": "Create user"
                    }
                }
            }
        }

        endpoints = service._extract_endpoints(spec)

        assert len(endpoints) == 2
        assert endpoints[0]["path"] == "/api/users"
        assert endpoints[0]["method"] == "GET"
        assert endpoints[0]["operation_id"] == "getUsers"
        assert endpoints[1]["method"] == "POST"
        assert endpoints[1]["operation_id"] == "createUser"

    def test_extract_endpoints_empty_spec(self, service):
        """Test endpoint extraction with empty spec."""
        spec = {"paths": {}}
        endpoints = service._extract_endpoints(spec)
        assert endpoints == []

    def test_extract_endpoints_invalid_data(self, service):
        """Test endpoint extraction with invalid data."""
        spec = {
            "paths": {
                "/api/test": {
                    "get": "invalid",  # Should be dict
                    "post": None       # Should be dict
                }
            }
        }
        endpoints = service._extract_endpoints(spec)
        assert len(endpoints) == 0

    def test_categorize_operation_crud_create(self, service):
        """Test CRUD create operation categorization."""
        endpoint = {"operation_id": "createUser", "method": "POST"}
        categories = service._categorize_operation(endpoint)
        assert "create" in categories

    def test_categorize_operation_crud_read(self, service):
        """Test CRUD read operations categorization."""
        test_cases = [
            {"operation_id": "getUser", "method": "GET"},
            {"operation_id": "listUsers", "method": "GET"},
            {"operation_id": "findUser", "method": "GET"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "read" in categories

    def test_categorize_operation_crud_update(self, service):
        """Test CRUD update operations categorization."""
        test_cases = [
            {"operation_id": "updateUser", "method": "PUT"},
            {"operation_id": "updateUser", "method": "PATCH"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "update" in categories

    def test_categorize_operation_crud_delete(self, service):
        """Test CRUD delete operation categorization."""
        endpoint = {"operation_id": "deleteUser", "method": "DELETE"}
        categories = service._categorize_operation(endpoint)
        assert "delete" in categories

    def test_categorize_operation_business_analysis(self, service):
        """Test business analysis operations categorization."""
        test_cases = [
            {"operation_id": "analyzeUser"},
            {"operation_id": "validateUser"},
            {"operation_id": "checkUserStatus"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "analysis" in categories

    def test_categorize_operation_business_search(self, service):
        """Test business search operations categorization."""
        test_cases = [
            {"operation_id": "searchUsers"},
            {"operation_id": "findUsers"},
            {"operation_id": "queryUsers"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "search" in categories

    def test_categorize_operation_business_notification(self, service):
        """Test business notification operations categorization."""
        test_cases = [
            {"operation_id": "notifyUser"},
            {"operation_id": "alertUser"},
            {"operation_id": "sendNotification"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "notification" in categories

    def test_categorize_operation_business_storage(self, service):
        """Test business storage operations categorization."""
        test_cases = [
            {"operation_id": "storeUser"},
            {"operation_id": "saveUser"},
            {"operation_id": "persistUser"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "storage" in categories

    def test_categorize_operation_business_processing(self, service):
        """Test business processing operations categorization."""
        test_cases = [
            {"operation_id": "processUser"},
            {"operation_id": "executeUserTask"},
            {"operation_id": "runUserAnalysis"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "processing" in categories

    def test_categorize_operation_service_specific_document(self, service):
        """Test service-specific document operations categorization."""
        test_cases = [
            {"operation_id": "createDocument"},
            {"operation_id": "getDoc"},
            {"operation_id": "processDocument"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "document" in categories

    def test_categorize_operation_service_specific_prompt(self, service):
        """Test service-specific prompt operations categorization."""
        endpoint = {"operation_id": "generatePrompt"}
        categories = service._categorize_operation(endpoint)
        assert "prompt" in categories

    def test_categorize_operation_service_specific_code(self, service):
        """Test service-specific code operations categorization."""
        test_cases = [
            {"operation_id": "analyzeCode"},
            {"operation_id": "processRepo"},
        ]

        for endpoint in test_cases:
            categories = service._categorize_operation(endpoint)
            assert "code" in categories

    def test_categorize_operation_service_specific_workflow(self, service):
        """Test service-specific workflow operations categorization."""
        endpoint = {"operation_id": "executeWorkflow"}
        categories = service._categorize_operation(endpoint)
        assert "workflow" in categories

    def test_categorize_operation_fallback(self, service):
        """Test categorization fallback to general category."""
        endpoint = {"operation_id": "unknownOperation"}
        categories = service._categorize_operation(endpoint)
        assert categories == ["general"]

    def test_categorize_operation_case_insensitive(self, service):
        """Test that categorization is case insensitive."""
        endpoint = {"operation_id": "CREATEUSER", "method": "post"}
        categories = service._categorize_operation(endpoint)
        assert "create" in categories

    def test_categorize_crud_operations_method_only(self, service):
        """Test CRUD categorization based on HTTP method alone."""
        test_cases = [
            ({"method": "POST"}, ["create"]),
            ({"method": "GET"}, ["read"]),
            ({"method": "PUT"}, ["update"]),
            ({"method": "DELETE"}, ["delete"]),
        ]

        for endpoint, expected in test_cases:
            categories = service._categorize_crud_operations("", endpoint.get("method", ""))
            assert expected[0] in categories

    def test_categorize_business_operations(self, service):
        """Test business operations categorization logic."""
        # Test analysis operations
        assert "analysis" in service._categorize_business_operations("analyzeData")
        assert "search" in service._categorize_business_operations("searchItems")
        assert "notification" in service._categorize_business_operations("notifyUser")
        assert "storage" in service._categorize_business_operations("storeData")
        assert "processing" in service._categorize_business_operations("processData")

    def test_categorize_service_specific_operations(self, service):
        """Test service-specific operations categorization logic."""
        # Test document operations
        assert "document" in service._categorize_service_specific_operations("createDocument")
        assert "document" in service._categorize_service_specific_operations("getDoc")

        # Test other service-specific categories
        assert "prompt" in service._categorize_service_specific_operations("generatePrompt")
        assert "code" in service._categorize_service_specific_operations("analyzeCode")
        assert "workflow" in service._categorize_service_specific_operations("executeWorkflow")

    def test_generate_tool_name(self, service):
        """Test tool name generation."""
        name = service._generate_tool_name("test-service", "getUsers")
        assert name == "test_service_get_users"

        # Test PascalCase conversion
        name = service._generate_tool_name("test-service", "GetUsersById")
        assert name == "test_service_get_users_by_id"

    def test_generate_tool_description(self, service):
        """Test tool description generation."""
        endpoint = {
            "method": "GET",
            "operation_id": "getUsers",
            "summary": "Retrieve users"
        }
        categories = ["read", "user"]

        description = service._generate_tool_description(endpoint, categories)
        assert "GET getUsers: Retrieve users" in description
        assert "Categories: read, user" in description

    def test_generate_tool_description_no_summary(self, service):
        """Test tool description generation without summary."""
        endpoint = {
            "method": "POST",
            "operation_id": "createUser"
        }
        categories = ["create"]

        description = service._generate_tool_description(endpoint, categories)
        assert "POST createUser" in description
        assert "Categories: create" in description

    def test_extract_tool_parameters(self, service):
        """Test tool parameter extraction."""
        endpoint = {
            "parameters": [
                {"name": "userId", "in": "path", "schema": {"type": "string"}, "required": True},
                {"name": "limit", "in": "query", "schema": {"type": "integer"}, "required": False},
            ],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }

        parameters = service._extract_tool_parameters(endpoint)

        assert "userId" in parameters["properties"]
        assert "limit" in parameters["properties"]
        assert "name" in parameters["properties"]
        assert "email" in parameters["properties"]
        assert "userId" in parameters["required"]
        assert "limit" not in parameters["required"]

    def test_extract_tool_parameters_no_parameters(self, service):
        """Test parameter extraction with no parameters."""
        endpoint = {}
        parameters = service._extract_tool_parameters(endpoint)

        assert parameters["type"] == "object"
        assert parameters["properties"] == {}
        assert parameters["required"] == []

    def test_generate_tool_for_endpoint_valid(self, service):
        """Test tool generation for valid endpoint."""
        endpoint = {
            "path": "/api/users",
            "method": "GET",
            "operation_id": "getUsers",
            "summary": "Get users",
            "tags": ["users"]
        }

        with patch.object(service, '_categorize_operation', return_value=["read", "user"]):
            with patch.object(service, '_generate_tool_name', return_value="test_service_get_users"):
                with patch.object(service, '_generate_tool_description') as mock_desc:
                    with patch.object(service, '_extract_tool_parameters', return_value={"type": "object", "properties": {}}):
                        mock_desc.return_value = "GET getUsers: Get users (Categories: read, user)"

                        tool = service._generate_tool_for_endpoint("test-service", "http://test.com", endpoint)

                        assert tool is not None
                        assert tool["name"] == "test_service_get_users"
                        assert tool["service_name"] == "test-service"
                        assert tool["operation_id"] == "getUsers"
                        assert tool["categories"] == ["read", "user"]

    def test_generate_tool_for_endpoint_no_operation_id(self, service):
        """Test tool generation for endpoint without operation ID."""
        endpoint = {
            "path": "/api/users",
            "method": "GET",
            "summary": "Get users"
        }

        tool = service._generate_tool_for_endpoint("test-service", "http://test.com", endpoint)
        assert tool is None

    def test_analyze_endpoints_for_tools(self, service):
        """Test endpoint analysis for tool generation."""
        endpoints = [
            {
                "path": "/api/users",
                "method": "GET",
                "operation_id": "getUsers",
                "summary": "Get users"
            },
            {
                "path": "/api/users",
                "method": "POST",
                "operation_id": "createUser",
                "summary": "Create user"
            }
        ]

        tool_categories = ["read"]

        with patch.object(service, '_generate_tool_for_endpoint') as mock_generate:
            mock_generate.side_effect = [
                {"name": "get_users", "categories": ["read"]},
                {"name": "create_user", "categories": ["create"]},
            ]

            tools = service._analyze_endpoints_for_tools("test-service", "http://test.com", endpoints, tool_categories)

            assert len(tools) == 1  # Only read category should be included
            assert tools[0]["name"] == "get_users"

    def test_analyze_endpoints_for_tools_no_filter(self, service):
        """Test endpoint analysis without category filtering."""
        endpoints = [
            {
                "path": "/api/users",
                "method": "GET",
                "operation_id": "getUsers"
            }
        ]

        with patch.object(service, '_generate_tool_for_endpoint') as mock_generate:
            mock_generate.return_value = {"name": "get_users", "categories": ["read"]}

            tools = service._analyze_endpoints_for_tools("test-service", "http://test.com", endpoints, None)

            assert len(tools) == 1
            assert tools[0]["name"] == "get_users"

    def test_clear_discovered_tools_all(self, service):
        """Test clearing all discovered tools."""
        service.discovered_tools = {
            "service1": {"tools": [], "spec_url": "", "endpoint_count": 0, "tool_count": 0},
            "service2": {"tools": [], "spec_url": "", "endpoint_count": 0, "tool_count": 0},
        }

        service.clear_discovered_tools()
        assert service.discovered_tools == {}

    def test_clear_discovered_tools_specific_service(self, service):
        """Test clearing tools for specific service."""
        service.discovered_tools = {
            "service1": {"tools": [], "spec_url": "", "endpoint_count": 0, "tool_count": 0},
            "service2": {"tools": [], "spec_url": "", "endpoint_count": 0, "tool_count": 0},
        }

        service.clear_discovered_tools("service1")
        assert "service1" not in service.discovered_tools
        assert "service2" in service.discovered_tools

    @pytest.mark.asyncio
    async def test_monitor_discovery_performance(self, service):
        """Test discovery performance monitoring."""
        discovery_results = {
            "service_name": "test-service",
            "endpoints_discovered": 10,
            "tools_discovered": 5,
            "processing_time": 1.5
        }

        with patch.object(service, 'monitoring_service') as mock_monitoring:
            mock_monitoring.record_metric = AsyncMock()
            await service.monitor_discovery_performance(discovery_results)

            mock_monitoring.record_metric.assert_called()

    @pytest.mark.asyncio
    async def test_monitor_discovery_performance_no_monitoring(self, service):
        """Test discovery performance monitoring when monitoring service not set."""
        discovery_results = {"service_name": "test-service"}

        # Should not raise exception when monitoring service is None
        await service.monitor_discovery_performance(discovery_results)
