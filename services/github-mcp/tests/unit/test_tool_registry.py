"""Unit Tests for Tool Registry in GitHub MCP Service.

This module tests tool registry capabilities including:
- Tool registration and discovery
- Tool filtering and categorization
- Tool metadata validation
- Dynamic toolset management
- Tool capability assessment

Tests cover the complete tool registry infrastructure within the GitHub MCP service.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Set

from main import ToolDescription


class TestToolRegistry:
    """Test Tool Registry functionality."""

    @pytest.fixture
    def tool_registry(self):
        """Create tool registry instance with test data."""
        from main import tool_registry

        # Reset registry for clean testing
        tool_registry._tools = {}
        tool_registry._categories = set()
        tool_registry._toolsets = {}

        # Register test tools
        test_tools = self._get_test_tools()
        for tool_name, tool_desc in test_tools.items():
            tool_registry.register_tool(tool_name, tool_desc)

        return tool_registry

    def _get_test_tools(self) -> Dict[str, ToolDescription]:
        """Get test tools for registry testing."""
        return {
            "repos.get": ToolDescription(
                name="repos.get",
                description="Get repository information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"}
                    },
                    "required": ["owner", "repo"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "stars": {"type": "integer"}
                    }
                },
                category="repositories",
                tags=["read", "repository", "info"],
                version="1.0.0",
                deprecated=False,
                experimental=False,
                requires_auth=True,
                rate_limit=5000,
                timeout_seconds=30
            ),
            "issues.create": ToolDescription(
                name="issues.create",
                description="Create a new issue",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["owner", "repo", "title"]
                },
                category="issues",
                tags=["write", "issue", "create"],
                version="1.0.0",
                deprecated=False,
                experimental=False,
                requires_auth=True,
                rate_limit=1000,
                timeout_seconds=60
            ),
            "pulls.list": ToolDescription(
                name="pulls.list",
                description="List pull requests",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "state": {"type": "string", "enum": ["open", "closed", "all"]}
                    },
                    "required": ["owner", "repo"]
                },
                category="pull_requests",
                tags=["read", "pull_request", "list"],
                version="1.0.0",
                deprecated=False,
                experimental=False,
                requires_auth=True,
                rate_limit=2000,
                timeout_seconds=45
            ),
            "actions.workflows": ToolDescription(
                name="actions.workflows",
                description="Get workflow information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"}
                    },
                    "required": ["owner", "repo"]
                },
                category="actions",
                tags=["read", "workflow", "ci_cd"],
                version="1.1.0",
                deprecated=False,
                experimental=True,
                requires_auth=True,
                rate_limit=1000,
                timeout_seconds=30
            ),
            "legacy.search": ToolDescription(
                name="legacy.search",
                description="Legacy search functionality",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                },
                category="search",
                tags=["read", "search", "legacy"],
                version="0.9.0",
                deprecated=True,
                experimental=False,
                requires_auth=False,
                rate_limit=100,
                timeout_seconds=120
            )
        }

    def test_tool_registration(self, tool_registry):
        """Test tool registration functionality."""
        # Verify tools are registered
        assert "repos.get" in tool_registry._tools
        assert "issues.create" in tool_registry._tools
        assert "pulls.list" in tool_registry._tools

        # Verify categories are tracked
        assert "repositories" in tool_registry._categories
        assert "issues" in tool_registry._categories
        assert "pull_requests" in tool_registry._categories

    def test_tool_discovery_all(self, tool_registry):
        """Test discovering all tools."""
        tools = tool_registry.list_tools()

        assert len(tools) == 5
        tool_names = [tool["name"] for tool in tools]
        assert "repos.get" in tool_names
        assert "issues.create" in tool_names
        assert "pulls.list" in tool_names

    def test_tool_discovery_by_category(self, tool_registry):
        """Test discovering tools by category."""
        # Test repositories category
        repo_tools = tool_registry.list_tools(category="repositories")
        assert len(repo_tools) == 1
        assert repo_tools[0]["name"] == "repos.get"

        # Test issues category
        issue_tools = tool_registry.list_tools(category="issues")
        assert len(issue_tools) == 1
        assert issue_tools[0]["name"] == "issues.create"

        # Test non-existent category
        empty_tools = tool_registry.list_tools(category="nonexistent")
        assert len(empty_tools) == 0

    def test_tool_filtering_by_tags(self, tool_registry):
        """Test tool filtering by tags."""
        # Test read-only tools
        read_tools = tool_registry.list_tools(tags=["read"])
        assert len(read_tools) >= 3  # repos.get, pulls.list, actions.workflows, legacy.search

        # Test write tools
        write_tools = tool_registry.list_tools(tags=["write"])
        assert len(write_tools) == 1
        assert write_tools[0]["name"] == "issues.create"

        # Test multiple tags (AND logic)
        read_repo_tools = tool_registry.list_tools(tags=["read", "repository"])
        assert len(read_repo_tools) == 1
        assert read_repo_tools[0]["name"] == "repos.get"

    def test_tool_filtering_experimental(self, tool_registry):
        """Test filtering experimental tools."""
        # Include experimental
        all_tools = tool_registry.list_tools(include_experimental=True)
        assert len(all_tools) == 5

        # Exclude experimental (default)
        stable_tools = tool_registry.list_tools(include_experimental=False)
        assert len(stable_tools) == 4  # Excludes actions.workflows

        experimental_tools = [t for t in all_tools if t not in stable_tools]
        assert len(experimental_tools) == 1
        assert experimental_tools[0]["name"] == "actions.workflows"

    def test_tool_filtering_deprecated(self, tool_registry):
        """Test filtering deprecated tools."""
        # Include deprecated
        all_tools = tool_registry.list_tools(include_deprecated=True)
        assert len(all_tools) == 5

        # Exclude deprecated (default)
        current_tools = tool_registry.list_tools(include_deprecated=False)
        assert len(current_tools) == 4  # Excludes legacy.search

        deprecated_tools = [t for t in all_tools if t not in current_tools]
        assert len(deprecated_tools) == 1
        assert deprecated_tools[0]["name"] == "legacy.search"

    def test_tool_metadata_validation(self, tool_registry):
        """Test tool metadata validation."""
        tool = tool_registry.get_tool("repos.get")

        assert tool is not None
        assert tool.name == "repos.get"
        assert tool.category == "repositories"
        assert tool.version == "1.0.0"
        assert tool.requires_auth is True
        assert tool.rate_limit == 5000
        assert tool.timeout_seconds == 30

    def test_tool_schema_validation(self, tool_registry):
        """Test tool input/output schema validation."""
        tool = tool_registry.get_tool("repos.get")

        # Validate input schema
        input_schema = tool.input_schema
        assert input_schema["type"] == "object"
        assert "properties" in input_schema
        assert "owner" in input_schema["properties"]
        assert "repo" in input_schema["properties"]
        assert input_schema["required"] == ["owner", "repo"]

        # Validate output schema
        output_schema = tool.output_schema
        assert output_schema["type"] == "object"
        assert "properties" in output_schema

    def test_tool_capability_assessment(self, tool_registry):
        """Test tool capability assessment."""
        # Test authentication requirements
        auth_required = tool_registry.get_tools_requiring_auth()
        assert "repos.get" in auth_required
        assert "issues.create" in auth_required

        auth_optional = tool_registry.get_tools_without_auth()
        assert "legacy.search" in auth_optional

        # Test rate limits
        high_rate_tools = tool_registry.get_tools_by_rate_limit(min_limit=2000)
        assert "repos.get" in high_rate_tools
        assert "pulls.list" in high_rate_tools

        low_rate_tools = tool_registry.get_tools_by_rate_limit(max_limit=500)
        assert "legacy.search" in low_rate_tools

    def test_toolset_management(self, tool_registry):
        """Test dynamic toolset management."""
        # Create toolsets
        tool_registry.create_toolset("basic", ["repos.get", "issues.create"])
        tool_registry.create_toolset("ci_cd", ["actions.workflows", "pulls.list"])

        # Test toolset retrieval
        basic_tools = tool_registry.get_toolset("basic")
        assert len(basic_tools) == 2
        assert "repos.get" in [t.name for t in basic_tools]
        assert "issues.create" in [t.name for t in basic_tools]

        ci_cd_tools = tool_registry.get_toolset("ci_cd")
        assert len(ci_cd_tools) == 2
        assert "actions.workflows" in [t.name for t in ci_cd_tools]

        # Test toolset listing
        toolsets = tool_registry.list_toolsets()
        assert "basic" in toolsets
        assert "ci_cd" in toolsets

    def test_tool_search_functionality(self, tool_registry):
        """Test tool search and discovery functionality."""
        # Search by name
        repo_tools = tool_registry.search_tools("repo")
        assert len(repo_tools) >= 1
        assert any("repos.get" in tool.name for tool in repo_tools)

        # Search by description
        issue_tools = tool_registry.search_tools("issue")
        assert len(issue_tools) >= 1
        assert any("issues.create" in tool.name for tool in issue_tools)

        # Search with no results
        no_results = tool_registry.search_tools("nonexistent")
        assert len(no_results) == 0

    def test_tool_statistics(self, tool_registry):
        """Test tool registry statistics."""
        stats = tool_registry.get_statistics()

        assert "total_tools" in stats
        assert "categories" in stats
        assert "experimental_tools" in stats
        assert "deprecated_tools" in stats
        assert "auth_required_tools" in stats

        assert stats["total_tools"] == 5
        assert len(stats["categories"]) >= 4  # repositories, issues, pull_requests, actions, search
        assert stats["experimental_tools"] == 1  # actions.workflows
        assert stats["deprecated_tools"] == 1  # legacy.search
        assert stats["auth_required_tools"] == 4  # All except legacy.search

    def test_tool_validation_comprehensive(self, tool_registry):
        """Test comprehensive tool validation."""
        # Test valid tool retrieval
        tool = tool_registry.get_tool("repos.get")
        assert tool is not None
        assert tool.name == "repos.get"

        # Test invalid tool retrieval
        invalid_tool = tool_registry.get_tool("nonexistent.tool")
        assert invalid_tool is None

        # Test tool existence checking
        assert tool_registry.has_tool("repos.get") is True
        assert tool_registry.has_tool("nonexistent.tool") is False

    def test_tool_category_management(self, tool_registry):
        """Test tool category management."""
        categories = tool_registry.list_categories()
        assert "repositories" in categories
        assert "issues" in categories
        assert "pull_requests" in categories
        assert "actions" in categories

        # Test category statistics
        category_stats = tool_registry.get_category_statistics()
        assert "repositories" in category_stats
        assert category_stats["repositories"] >= 1

    def test_tool_bulk_operations(self, tool_registry):
        """Test bulk tool operations."""
        # Bulk tool retrieval
        tool_names = ["repos.get", "issues.create", "pulls.list"]
        tools = tool_registry.get_tools_bulk(tool_names)

        assert len(tools) == 3
        assert all(tool is not None for tool in tools)
        assert all(tool.name in tool_names for tool in tools)

        # Bulk tool validation
        validation_results = tool_registry.validate_tools_bulk(tool_names)
        assert all(result["valid"] for result in validation_results)

    def test_tool_configuration_management(self, tool_registry):
        """Test tool configuration management."""
        # Test tool configuration retrieval
        config = tool_registry.get_tool_config("repos.get")
        assert config is not None
        assert "rate_limit" in config
        assert "timeout_seconds" in config
        assert "requires_auth" in config

        # Test bulk configuration retrieval
        configs = tool_registry.get_tools_config(["repos.get", "issues.create"])
        assert len(configs) == 2
        assert all("rate_limit" in config for config in configs.values())

    @pytest.mark.parametrize("tool_name,expected_category", [
        ("repos.get", "repositories"),
        ("issues.create", "issues"),
        ("pulls.list", "pull_requests"),
        ("actions.workflows", "actions"),
        ("legacy.search", "search")
    ])
    def test_tool_categories_parametrized(self, tool_registry, tool_name, expected_category):
        """Test tool categories with parametrized tests."""
        tool = tool_registry.get_tool(tool_name)
        assert tool is not None
        assert tool.category == expected_category

    def test_tool_lifecycle_management(self, tool_registry):
        """Test tool lifecycle management."""
        # Test tool enabling/disabling (if supported)
        enabled_tools = tool_registry.get_enabled_tools()
        assert len(enabled_tools) == 5  # All tools enabled by default

        # Test tool health status
        health_status = tool_registry.get_tools_health()
        assert len(health_status) == 5
        assert all(status["healthy"] for status in health_status.values())

    def test_tool_dependency_resolution(self, tool_registry):
        """Test tool dependency resolution."""
        # Test tool prerequisites
        prereqs = tool_registry.get_tool_prerequisites("repos.get")
        # Repos tool might require certain permissions or other tools

        # Test tool compatibility
        compatible_tools = tool_registry.get_compatible_tools("repos.get")
        # Should return tools that work well with repos.get

    def test_tool_performance_metrics(self, tool_registry):
        """Test tool performance metrics tracking."""
        # Simulate tool usage
        tool_registry.record_tool_usage("repos.get", 1.5, True)
        tool_registry.record_tool_usage("issues.create", 2.1, True)
        tool_registry.record_tool_usage("repos.get", 0.8, False)  # Failed call

        # Check performance metrics
        metrics = tool_registry.get_performance_metrics()

        assert "repos.get" in metrics
        assert "issues.create" in metrics

        repo_metrics = metrics["repos.get"]
        assert repo_metrics["total_calls"] == 2
        assert repo_metrics["successful_calls"] == 1
        assert repo_metrics["failed_calls"] == 1
        assert "average_response_time" in repo_metrics

    def test_tool_error_handling(self, tool_registry):
        """Test tool error handling and recovery."""
        # Test invalid tool registration
        with pytest.raises(ValueError):
            tool_registry.register_tool("invalid.tool", None)

        # Test duplicate tool registration
        duplicate_tool = ToolDescription(
            name="repos.get",
            description="Duplicate tool",
            category="test"
        )

        with pytest.raises(ValueError):
            tool_registry.register_tool("repos.get", duplicate_tool)

    def test_tool_export_import(self, tool_registry):
        """Test tool registry export and import functionality."""
        # Export tool registry
        exported_data = tool_registry.export_tools()
        assert "tools" in exported_data
        assert "categories" in exported_data
        assert "metadata" in exported_data

        assert len(exported_data["tools"]) == 5

        # Create new registry and import
        from main import tool_registry as new_registry
        new_registry._tools = {}
        new_registry._categories = set()

        new_registry.import_tools(exported_data)

        # Verify import
        assert len(new_registry._tools) == 5
        assert new_registry.has_tool("repos.get")
        assert new_registry.has_tool("issues.create")

    def test_tool_caching_and_performance(self, tool_registry):
        """Test tool registry caching and performance optimizations."""
        import time

        # Measure performance of repeated lookups
        start_time = time.time()

        for _ in range(100):
            tool = tool_registry.get_tool("repos.get")
            assert tool is not None

        end_time = time.time()
        lookup_time = end_time - start_time

        # Should be very fast due to caching
        assert lookup_time < 1.0  # Less than 1 second for 100 lookups

        # Verify caching effectiveness
        cache_stats = tool_registry.get_cache_statistics()
        assert "hit_rate" in cache_stats
        assert cache_stats["hit_rate"] > 0.9  # High cache hit rate
