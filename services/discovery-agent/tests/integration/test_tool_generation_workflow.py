"""
Integration tests for LangGraph tool generation workflows.

Tests the complete workflow of discovering services and generating LangGraph tools.
"""

import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.integration
@pytest.mark.tools
class TestToolGenerationWorkflow:
    """Test complete tool generation workflow."""
    
    @pytest.mark.asyncio
    async def test_generate_tools_from_service(self, sample_service_with_endpoints):
        """Test generating LangGraph tools from discovered service."""
        from domain.services.tool_discovery import ToolDiscovery
        
        tool_discovery = ToolDiscovery()
        
        tools = await tool_discovery.generate_tools(sample_service_with_endpoints)
        
        assert isinstance(tools, list)
        assert len(tools) >= 2  # At least 2 endpoints -> 2 tools
        
        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "service_name" in tool
            assert "http_method" in tool
            assert "path" in tool
    
    @pytest.mark.asyncio
    async def test_tool_names_follow_convention(self, sample_service_with_endpoints):
        """Test that tool names follow naming convention."""
        from domain.services.tool_discovery import ToolDiscovery
        
        tool_discovery = ToolDiscovery()
        tools = await tool_discovery.generate_tools(sample_service_with_endpoints)
        
        for tool in tools:
            # Tool names should be: service_name + _ + sanitized_path + _ + method
            assert tool["name"].startswith(sample_service_with_endpoints.name.replace("-", "_"))
            assert "_" in tool["name"]
            assert tool["name"].islower() or "_" in tool["name"]
    
    @pytest.mark.asyncio
    async def test_tools_include_parameters(self, sample_service_with_endpoints):
        """Test that tools include parameter information."""
        from domain.services.tool_discovery import ToolDiscovery
        
        tool_discovery = ToolDiscovery()
        tools = await tool_discovery.generate_tools(sample_service_with_endpoints)
        
        # Find tool with parameters (analyze endpoint)
        analyze_tool = next((t for t in tools if "analyze" in t["name"].lower()), None)
        
        if analyze_tool:
            assert "parameters" in analyze_tool
            assert isinstance(analyze_tool["parameters"], dict)
    
    @pytest.mark.asyncio
    async def test_tools_include_categories(self, sample_service_with_endpoints):
        """Test that tools include category information."""
        from domain.services.tool_discovery import ToolDiscovery
        
        tool_discovery = ToolDiscovery()
        tools = await tool_discovery.generate_tools(sample_service_with_endpoints)
        
        for tool in tools:
            assert "categories" in tool
            assert isinstance(tool["categories"], list)
    
    @pytest.mark.asyncio
    async def test_generate_tools_for_multiple_services(self, sample_service):
        """Test generating tools for multiple services."""
        from domain.services.tool_discovery import ToolDiscovery
        from domain.entities import Service, Endpoint
        
        tool_discovery = ToolDiscovery()
        
        # Create another service
        service2 = Service(
            name="service-2",
            base_url="http://service-2:8001",
            openapi_url="http://service-2:8001/openapi.json",
            version="1.0.0",
            description="Second service",
            status="discovered"
        )
        
        endpoint = Endpoint(
            path="/api/test",
            method="GET",
            summary="Test",
            description="Test",
            parameters=[],
            responses={},
            tags=[]
        )
        service2.add_endpoint(endpoint)
        
        # Generate tools for both services
        tools1 = await tool_discovery.generate_tools(sample_service)
        tools2 = await tool_discovery.generate_tools(service2)
        
        # Tool names should be different (different service names)
        tool_names1 = {t["name"] for t in tools1}
        tool_names2 = {t["name"] for t in tools2}
        assert tool_names1.isdisjoint(tool_names2)  # No overlap


@pytest.mark.integration
@pytest.mark.tools
class TestToolRegistry:
    """Test tool registry functionality."""
    
    @pytest.mark.asyncio
    async def test_register_tool(self, sample_tool_definition):
        """Test registering a tool in the registry."""
        from domain.services.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        await registry.register_tool(sample_tool_definition)
        
        # Verify tool is registered
        assert registry.has_tool(sample_tool_definition["name"])
    
    @pytest.mark.asyncio
    async def test_get_registered_tool(self, sample_tool_definition):
        """Test retrieving a registered tool."""
        from domain.services.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        await registry.register_tool(sample_tool_definition)
        
        retrieved_tool = await registry.get_tool(sample_tool_definition["name"])
        
        assert retrieved_tool is not None
        assert retrieved_tool["name"] == sample_tool_definition["name"]
        assert retrieved_tool["service_name"] == sample_tool_definition["service_name"]
    
    @pytest.mark.asyncio
    async def test_list_all_tools(self, sample_tool_definition):
        """Test listing all registered tools."""
        from domain.services.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Register multiple tools
        tool1 = sample_tool_definition
        tool2 = {**sample_tool_definition, "name": "another_tool"}
        
        await registry.register_tool(tool1)
        await registry.register_tool(tool2)
        
        all_tools = await registry.list_all_tools()
        
        assert len(all_tools) >= 2
        tool_names = {t["name"] for t in all_tools}
        assert "code_analyzer_analyze_code" in tool_names
        assert "another_tool" in tool_names
    
    @pytest.mark.asyncio
    async def test_get_tools_by_service(self, sample_tool_definition):
        """Test getting tools by service name."""
        from domain.services.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        await registry.register_tool(sample_tool_definition)
        
        service_tools = await registry.get_tools_by_service("code-analyzer")
        
        assert len(service_tools) >= 1
        assert all(t["service_name"] == "code-analyzer" for t in service_tools)
    
    @pytest.mark.asyncio
    async def test_get_tools_by_category(self, sample_tool_definition):
        """Test getting tools by category."""
        from domain.services.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        await registry.register_tool(sample_tool_definition)
        
        analysis_tools = await registry.get_tools_by_category("analysis")
        
        assert len(analysis_tools) >= 1
        assert all("analysis" in t["categories"] for t in analysis_tools)
    
    @pytest.mark.asyncio
    async def test_update_tool(self, sample_tool_definition):
        """Test updating a registered tool."""
        from domain.services.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        await registry.register_tool(sample_tool_definition)
        
        # Update tool description
        updated_tool = {**sample_tool_definition, "description": "Updated description"}
        await registry.update_tool(updated_tool["name"], updated_tool)
        
        retrieved_tool = await registry.get_tool(updated_tool["name"])
        assert retrieved_tool["description"] == "Updated description"
    
    @pytest.mark.asyncio
    async def test_unregister_tool(self, sample_tool_definition):
        """Test unregistering a tool."""
        from domain.services.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        await registry.register_tool(sample_tool_definition)
        
        assert registry.has_tool(sample_tool_definition["name"])
        
        await registry.unregister_tool(sample_tool_definition["name"])
        
        assert not registry.has_tool(sample_tool_definition["name"])
    
    @pytest.mark.asyncio
    async def test_clear_tools_by_service(self, sample_tool_definition):
        """Test clearing all tools for a service."""
        from domain.services.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Register multiple tools for same service
        tool1 = sample_tool_definition
        tool2 = {**sample_tool_definition, "name": "code_analyzer_another_tool"}
        
        await registry.register_tool(tool1)
        await registry.register_tool(tool2)
        
        # Clear all tools for code-analyzer
        await registry.clear_service_tools("code-analyzer")
        
        service_tools = await registry.get_tools_by_service("code-analyzer")
        assert len(service_tools) == 0


@pytest.mark.integration
@pytest.mark.tools
class TestSemanticAnalyzer:
    """Test semantic analyzer for tool categorization."""
    
    @pytest.mark.asyncio
    async def test_analyze_endpoint_semantics(self, sample_endpoint):
        """Test semantic analysis of endpoint."""
        from domain.services.semantic_analyzer import SemanticAnalyzer
        
        analyzer = SemanticAnalyzer()
        
        semantics = await analyzer.analyze_endpoint(sample_endpoint)
        
        assert "categories" in semantics
        assert isinstance(semantics["categories"], list)
        assert len(semantics["categories"]) > 0
    
    @pytest.mark.asyncio
    async def test_categorize_crud_operations(self):
        """Test categorization of CRUD operations."""
        from domain.services.semantic_analyzer import SemanticAnalyzer
        from domain.entities import Endpoint
        
        analyzer = SemanticAnalyzer()
        
        # Create endpoint
        create_endpoint = Endpoint(
            path="/api/users",
            method="POST",
            summary="Create user",
            description="Create a new user",
            parameters=[],
            responses={},
            tags=[]
        )
        
        semantics = await analyzer.analyze_endpoint(create_endpoint)
        categories = semantics["categories"]
        
        assert "create" in categories or "crud" in categories
    
    @pytest.mark.asyncio
    async def test_categorize_read_operations(self):
        """Test categorization of read operations."""
        from domain.services.semantic_analyzer import SemanticAnalyzer
        from domain.entities import Endpoint
        
        analyzer = SemanticAnalyzer()
        
        # Read endpoint
        read_endpoint = Endpoint(
            path="/api/users/{id}",
            method="GET",
            summary="Get user",
            description="Retrieve user by ID",
            parameters=[],
            responses={},
            tags=[]
        )
        
        semantics = await analyzer.analyze_endpoint(read_endpoint)
        categories = semantics["categories"]
        
        assert "read" in categories or "retrieve" in categories or "crud" in categories
    
    @pytest.mark.asyncio
    async def test_detect_search_endpoints(self):
        """Test detection of search endpoints."""
        from domain.services.semantic_analyzer import SemanticAnalyzer
        from domain.entities import Endpoint
        
        analyzer = SemanticAnalyzer()
        
        search_endpoint = Endpoint(
            path="/api/search",
            method="GET",
            summary="Search items",
            description="Search for items by query",
            parameters=[{"name": "q", "in": "query"}],
            responses={},
            tags=[]
        )
        
        semantics = await analyzer.analyze_endpoint(search_endpoint)
        categories = semantics["categories"]
        
        assert "search" in categories or "query" in categories
    
    @pytest.mark.asyncio
    async def test_detect_health_endpoints(self):
        """Test detection of health/monitoring endpoints."""
        from domain.services.semantic_analyzer import SemanticAnalyzer
        from domain.entities import Endpoint
        
        analyzer = SemanticAnalyzer()
        
        health_endpoint = Endpoint(
            path="/health",
            method="GET",
            summary="Health check",
            description="Check service health",
            parameters=[],
            responses={},
            tags=["monitoring"]
        )
        
        semantics = await analyzer.analyze_endpoint(health_endpoint)
        categories = semantics["categories"]
        
        assert "monitoring" in categories or "health" in categories


@pytest.mark.integration
@pytest.mark.tools
class TestToolGenerationEdgeCases:
    """Test edge cases in tool generation."""
    
    @pytest.mark.asyncio
    async def test_generate_tools_from_empty_service(self, sample_service):
        """Test generating tools from service with no endpoints."""
        from domain.services.tool_discovery import ToolDiscovery
        
        tool_discovery = ToolDiscovery()
        
        # Service has no endpoints
        tools = await tool_discovery.generate_tools(sample_service)
        
        assert isinstance(tools, list)
        assert len(tools) == 0
    
    @pytest.mark.asyncio
    async def test_handle_special_characters_in_paths(self):
        """Test handling special characters in endpoint paths."""
        from domain.services.tool_discovery import ToolDiscovery
        from domain.entities import Service, Endpoint
        
        tool_discovery = ToolDiscovery()
        
        service = Service(
            name="test-service",
            base_url="http://test:8000",
            openapi_url="http://test:8000/openapi.json",
            version="1.0.0",
            description="Test",
            status="discovered"
        )
        
        # Endpoint with special characters
        endpoint = Endpoint(
            path="/api/v1/items/{item_id}/sub-items/{sub_id}",
            method="GET",
            summary="Get sub-item",
            description="Get sub-item by ID",
            parameters=[],
            responses={},
            tags=[]
        )
        service.add_endpoint(endpoint)
        
        tools = await tool_discovery.generate_tools(service)
        
        assert len(tools) == 1
        # Tool name should sanitize special characters
        assert "{" not in tools[0]["name"]
        assert "}" not in tools[0]["name"]
        assert tools[0]["name"].replace("_", "").isalnum()
    
    @pytest.mark.asyncio
    async def test_handle_duplicate_tool_names(self):
        """Test handling potential duplicate tool names."""
        from domain.services.tool_discovery import ToolDiscovery
        from domain.entities import Service, Endpoint
        
        tool_discovery = ToolDiscovery()
        
        service = Service(
            name="test-service",
            base_url="http://test:8000",
            openapi_url="http://test:8000/openapi.json",
            version="1.0.0",
            description="Test",
            status="discovered"
        )
        
        # Two similar endpoints that might generate same tool name
        endpoint1 = Endpoint(
            path="/api/test",
            method="GET",
            summary="Test GET",
            description="Test",
            parameters=[],
            responses={},
            tags=[]
        )
        
        endpoint2 = Endpoint(
            path="/api/test",
            method="POST",
            summary="Test POST",
            description="Test",
            parameters=[],
            responses={},
            tags=[]
        )
        
        service.add_endpoint(endpoint1)
        service.add_endpoint(endpoint2)
        
        tools = await tool_discovery.generate_tools(service)
        
        # Should generate 2 tools with different names
        assert len(tools) == 2
        tool_names = [t["name"] for t in tools]
        assert len(set(tool_names)) == 2  # All names are unique

