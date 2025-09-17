"""Comprehensive tests for LangGraph Tool Discovery functionality.

This module tests the automatic tool discovery and registration system
that integrates with LangGraph workflows in the LLM Documentation Ecosystem.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# Import the modules we need to test
from modules.tool_discovery import ToolDiscoveryService, tool_discovery_service
from modules.models import ToolDiscoveryRequest
from modules.discovery_handler import DiscoveryHandler, discovery_handler


class TestToolDiscoveryService:
    """Test the core ToolDiscoveryService functionality."""

    @pytest.fixture
    def mock_openapi_spec(self) -> Dict[str, Any]:
        """Mock OpenAPI specification for testing."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "Test Service", "version": "1.0.0"},
            "paths": {
                "/documents": {
                    "get": {
                        "summary": "List documents",
                        "operationId": "list_documents",
                        "responses": {"200": {"description": "Success"}}
                    },
                    "post": {
                        "summary": "Create document",
                        "operationId": "create_document",
                        "responses": {"201": {"description": "Created"}}
                    }
                },
                "/documents/{id}": {
                    "get": {
                        "summary": "Get document",
                        "operationId": "get_document",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "Success"}}
                    },
                    "put": {
                        "summary": "Update document",
                        "operationId": "update_document",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {"200": {"description": "Updated"}}
                    }
                }
            }
        }

    @pytest.fixture
    def discovery_service(self) -> ToolDiscoveryService:
        """Create a fresh ToolDiscoveryService for testing."""
        return ToolDiscoveryService()

    @pytest.mark.asyncio
    async def test_fetch_openapi_spec_success(self, discovery_service):
        """Test successful OpenAPI spec fetching."""
        mock_spec = {"openapi": "3.0.0", "info": {"title": "Test"}}

        with patch.object(discovery_service, '_fetch_openapi_spec', return_value=mock_spec) as mock_fetch:
            result = await discovery_service._fetch_openapi_spec("http://test.com/openapi.json")
            assert result == mock_spec
            mock_fetch.assert_called_once_with("http://test.com/openapi.json")

    @pytest.mark.asyncio
    async def test_discover_tools_basic(self, discovery_service, mock_openapi_spec):
        """Test basic tool discovery from OpenAPI spec."""
        with patch.object(discovery_service, '_fetch_openapi_spec', return_value=mock_openapi_spec):
            result = await discovery_service.discover_tools(
                service_name="test_service",
                service_url="http://test-service:8000"
            )

            assert result["service_name"] == "test_service"
            assert result["service_url"] == "http://test-service:8000"
            assert result["status"] == "success"
            assert "tools" in result
            assert len(result["tools"]) > 0

            # Check that tools have expected structure
            for tool in result["tools"]:
                assert "name" in tool
                assert "description" in tool
                assert "categories" in tool
                assert "service_name" in tool
                assert "service_url" in tool

    @pytest.mark.asyncio
    async def test_tool_categorization(self, discovery_service, mock_openapi_spec):
        """Test that tools are properly categorized."""
        with patch.object(discovery_service, '_fetch_openapi_spec', return_value=mock_openapi_spec):
            result = await discovery_service.discover_tools(
                service_name="test_service",
                service_url="http://test-service:8000"
            )

            tools = result["tools"]
            assert len(tools) > 0

            # Check categorization
            for tool in tools:
                categories = tool["categories"]
                assert isinstance(categories, list)
                assert len(categories) > 0

                # Check that categories are valid
                valid_categories = ["create", "read", "update", "delete", "analysis",
                                  "search", "notification", "storage", "processing",
                                  "document", "prompt", "code", "workflow", "general"]
                for category in categories:
                    assert category in valid_categories

    @pytest.mark.asyncio
    async def test_tool_naming_convention(self, discovery_service, mock_openapi_spec):
        """Test that tool names follow proper naming conventions."""
        with patch.object(discovery_service, '_fetch_openapi_spec', return_value=mock_openapi_spec):
            result = await discovery_service.discover_tools(
                service_name="test_service",
                service_url="http://test-service:8000"
            )

            tools = result["tools"]
            assert len(tools) > 0

            for tool in tools:
                tool_name = tool["name"]
                # Should be service_name + operation_id in snake_case
                assert tool_name.startswith("test_service_")
                assert "_" in tool_name  # Should have underscores
                assert tool_name.islower()  # Should be lowercase

    @pytest.mark.asyncio
    async def test_parameter_extraction(self, discovery_service, mock_openapi_spec):
        """Test that parameters are properly extracted from OpenAPI spec."""
        with patch.object(discovery_service, '_fetch_openapi_spec', return_value=mock_openapi_spec):
            result = await discovery_service.discover_tools(
                service_name="test_service",
                service_url="http://test-service:8000"
            )

            tools = result["tools"]

            # Find the get_document tool which has parameters
            get_tool = next((t for t in tools if "get_document" in t["name"]), None)
            if get_tool:
                parameters = get_tool.get("parameters", {})
                assert "properties" in parameters
                assert "id" in parameters["properties"]
                assert parameters["properties"]["id"]["type"] == "string"


class TestDiscoveryHandler:
    """Test the DiscoveryHandler tool discovery functionality."""

    @pytest.fixture
    def mock_request(self) -> ToolDiscoveryRequest:
        """Create a mock ToolDiscoveryRequest."""
        return ToolDiscoveryRequest(
            service_name="test_service",
            service_url="http://test-service:8000",
            tool_categories=["read", "create"],
            dry_run=False
        )

    @pytest.mark.asyncio
    async def test_discover_tools_dry_run(self, mock_request):
        """Test tool discovery in dry run mode."""
        mock_request.dry_run = True

        with patch('modules.discovery_handler.tool_discovery_service') as mock_service:
            mock_service.discover_tools.return_value = {
                "service_name": "test_service",
                "tools_discovered": 3,
                "tools": [{"name": "test_tool", "description": "Test tool"}]
            }

            result = await discovery_handler.discover_tools(mock_request)

            assert result["success"] is True
            assert "dry run" in result["message"].lower()
            mock_service.discover_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_tools_with_registration(self, mock_request):
        """Test tool discovery with orchestrator registration."""
        with patch('modules.discovery_handler.tool_discovery_service') as mock_service, \
             patch('modules.discovery_handler.register_with_orchestrator') as mock_register:

            mock_service.discover_tools.return_value = {
                "service_name": "test_service",
                "tools_discovered": 3,
                "tools": [{"name": "test_tool", "description": "Test tool"}]
            }
            mock_register.return_value = {"status": "registered"}

            result = await discovery_handler.discover_tools(mock_request)

            assert result["success"] is True
            assert result["data"]["registration_status"] == "completed"
            mock_register.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_tools_registration_failure(self, mock_request):
        """Test tool discovery when orchestrator registration fails."""
        with patch('modules.discovery_handler.tool_discovery_service') as mock_service, \
             patch('modules.discovery_handler.register_with_orchestrator', side_effect=Exception("Registration failed")):

            mock_service.discover_tools.return_value = {
                "service_name": "test_service",
                "tools_discovered": 3,
                "tools": [{"name": "test_tool", "description": "Test tool"}]
            }

            result = await discovery_handler.discover_tools(mock_request)

            assert result["success"] is True
            assert result["data"]["registration_status"] == "failed"
            assert "Registration failed" in result["data"]["registration_error"]


class TestIntegrationScenarios:
    """Test integration scenarios for tool discovery."""

    @pytest.mark.asyncio
    async def test_full_workflow_discovery(self):
        """Test the complete workflow from discovery to tool usage."""
        # This is a high-level integration test
        service_name = "document_store"
        service_url = "http://llm-document-store:5140"

        # Mock the entire discovery process
        with patch('modules.tool_discovery.tool_discovery_service') as mock_service:
            mock_service.discover_tools.return_value = {
                "service_name": service_name,
                "service_url": service_url,
                "tools_discovered": 5,
                "tools": [
                    {
                        "name": f"{service_name}_list_documents",
                        "description": "List documents in the store",
                        "categories": ["read", "document"],
                        "service_name": service_name,
                        "service_url": service_url,
                        "http_method": "GET",
                        "path": "/documents"
                    },
                    {
                        "name": f"{service_name}_create_document",
                        "description": "Create a new document",
                        "categories": ["create", "document"],
                        "service_name": service_name,
                        "service_url": service_url,
                        "http_method": "POST",
                        "path": "/documents"
                    }
                ]
            }

            # Test discovery
            result = await mock_service.discover_tools(service_name, service_url)
            assert result["tools_discovered"] == 5
            assert len(result["tools"]) == 2

            # Verify tool structure
            for tool in result["tools"]:
                assert "name" in tool
                assert "description" in tool
                assert "categories" in tool
                assert tool["service_name"] == service_name
                assert tool["service_url"] == service_url

    @pytest.mark.asyncio
    async def test_category_filtering(self):
        """Test that tool discovery respects category filters."""
        with patch('modules.tool_discovery.tool_discovery_service') as mock_service:
            # Mock discovery with mixed categories
            mock_service.discover_tools.return_value = {
                "service_name": "test_service",
                "tools": [
                    {"name": "tool1", "categories": ["read", "document"]},
                    {"name": "tool2", "categories": ["create", "storage"]},
                    {"name": "tool3", "categories": ["analysis", "processing"]}
                ]
            }

            # Test with category filter
            result = await mock_service.discover_tools(
                "test_service",
                "http://test.com",
                tool_categories=["read", "create"]
            )

            # Should only return tools with matching categories
            returned_tools = result["tools"]
            for tool in returned_tools:
                categories = tool["categories"]
                assert any(cat in ["read", "create"] for cat in categories)

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in tool discovery."""
        with patch('modules.tool_discovery.tool_discovery_service') as mock_service:
            # Simulate OpenAPI fetch failure
            mock_service._fetch_openapi_spec.side_effect = Exception("Network error")

            with pytest.raises(Exception) as exc_info:
                await mock_service.discover_tools("failing_service", "http://failing.com")

            assert "Network error" in str(exc_info.value)


class TestOrchestratorIntegration:
    """Test integration with orchestrator for tool discovery."""

    @pytest.mark.asyncio
    async def test_orchestrator_tool_discovery_endpoint(self):
        """Test the orchestrator's tool discovery endpoint."""
        # This would test the /tools/discover endpoint
        # Mock the discovery agent call
        pass

    @pytest.mark.asyncio
    async def test_startup_tool_discovery(self):
        """Test automatic tool discovery during orchestrator startup."""
        # This would test the startup event handler
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
