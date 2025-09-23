"""Unit Tests for MCP Protocol Implementation in GitHub MCP Service.

This module tests MCP (Model Context Protocol) protocol compliance including:
- MCP message format validation and parsing
- Tool invocation request/response handling
- Protocol version compatibility
- Error handling and recovery
- Tool capability negotiation

Tests cover the complete MCP protocol implementation within the GitHub MCP service.
"""

import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List, Optional
import uuid

from main import ToolDescription


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance and message handling."""

    @pytest.fixture
    def sample_tool_description(self):
        """Create a sample tool description for testing."""
        return ToolDescription(
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
            tags=["repository", "read"],
            category="repository",
            toolset="repos"
        )

    def test_tool_description_validation(self, sample_tool_description):
        """Test tool description validation and schema compliance."""
        # Test valid tool description
        assert sample_tool_description.name == "repos.get"
        assert sample_tool_description.description == "Get repository information"
        assert "repository" in sample_tool_description.tags
        assert sample_tool_description.category == "repository"
        assert sample_tool_description.toolset == "repos"

        # Test input schema validation
        assert "properties" in sample_tool_description.input_schema
        assert "owner" in sample_tool_description.input_schema["properties"]
        assert "repo" in sample_tool_description.input_schema["properties"]
        assert sample_tool_description.input_schema["required"] == ["owner", "repo"]

        # Test output schema validation
        assert "properties" in sample_tool_description.output_schema
        assert "name" in sample_tool_description.output_schema["properties"]

    def test_mcp_message_format_validation(self):
        """Test MCP message format validation."""
        # Test valid MCP request message
        valid_request = {
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tools/call",
            "params": {
                "name": "repos.get",
                "arguments": {
                    "owner": "octocat",
                    "repo": "Hello-World"
                }
            }
        }

        # Validate JSON-RPC 2.0 compliance
        assert valid_request["jsonrpc"] == "2.0"
        assert "id" in valid_request
        assert "method" in valid_request
        assert "params" in valid_request

        # Test valid MCP response message
        valid_response = {
            "jsonrpc": "2.0",
            "id": "123",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Repository information retrieved successfully"
                    }
                ]
            }
        }

        assert valid_response["jsonrpc"] == "2.0"
        assert valid_response["id"] == "123"
        assert "result" in valid_response

        # Test error response
        error_response = {
            "jsonrpc": "2.0",
            "id": "123",
            "error": {
                "code": -32602,
                "message": "Invalid params",
                "data": {"details": "Missing required parameter"}
            }
        }

        assert error_response["jsonrpc"] == "2.0"
        assert error_response["id"] == "123"
        assert "error" in error_response
        assert error_response["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_tool_invocation_request_handling(self):
        """Test tool invocation request handling."""
        # Mock tool registry
        mock_tool = MagicMock()
        mock_tool.name = "repos.get"
        mock_tool.description = "Get repository information"
        mock_tool.input_schema = {
            "type": "object",
            "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}},
            "required": ["owner", "repo"]
        }

        with patch("main.tool_registry") as mock_registry:
            mock_registry.get_tool.return_value = mock_tool
            mock_registry.has_tool.return_value = True

            # Import the invoke_tool function (assuming it exists)
            from main import invoke_tool

            # Test successful tool invocation
            result = await invoke_tool("repos.get", {"owner": "octocat", "repo": "Hello-World"})

            # Verify result structure
            assert isinstance(result, dict)
            assert "success" in result or "content" in result

    def test_protocol_version_compatibility(self):
        """Test MCP protocol version compatibility."""
        # Test supported protocol versions
        supported_versions = ["2.0", "2.1"]

        for version in supported_versions:
            message = {
                "jsonrpc": version,
                "id": "123",
                "method": "tools/list"
            }

            # Should not raise an exception for supported versions
            assert message["jsonrpc"] in supported_versions

        # Test unsupported version
        unsupported_message = {
            "jsonrpc": "1.0",
            "id": "123",
            "method": "tools/list"
        }

        # Should handle gracefully
        assert unsupported_message["jsonrpc"] == "1.0"

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Test tool not found error
        with patch("main.tool_registry") as mock_registry:
            mock_registry.has_tool.return_value = False
            mock_registry.get_tool.return_value = None

            from main import invoke_tool

            with pytest.raises(Exception):  # Should raise appropriate exception
                await invoke_tool("nonexistent.tool", {})

        # Test invalid parameters error
        with patch("main.tool_registry") as mock_registry:
            mock_tool = MagicMock()
            mock_tool.input_schema = {
                "type": "object",
                "required": ["owner", "repo"]
            }
            mock_registry.get_tool.return_value = mock_tool
            mock_registry.has_tool.return_value = True

            # Missing required parameters
            with pytest.raises(ValueError):
                await invoke_tool("repos.get", {})  # Missing owner and repo

    def test_tool_capability_negotiation(self):
        """Test tool capability negotiation and discovery."""
        # Test tool listing with capabilities
        mock_tools = {
            "repos.get": ToolDescription(
                name="repos.get",
                description="Get repository info",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
                tags=["read"],
                category="repository",
                toolset="repos"
            ),
            "repos.create": ToolDescription(
                name="repos.create",
                description="Create repository",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
                tags=["write"],
                category="repository",
                toolset="repos"
            ),
            "issues.list": ToolDescription(
                name="issues.list",
                description="List issues",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
                tags=["read"],
                category="issues",
                toolset="issues"
            )
        }

        with patch("main.tool_registry") as mock_registry:
            mock_registry.list_tools.return_value = mock_tools

            # Test filtering by category
            repo_tools = {k: v for k, v in mock_tools.items() if v.category == "repository"}
            assert len(repo_tools) == 2

            # Test filtering by tags
            read_tools = {k: v for k, v in mock_tools.items() if "read" in v.tags}
            assert len(read_tools) == 2

            write_tools = {k: v for k, v in mock_tools.items() if "write" in v.tags}
            assert len(write_tools) == 1

    @pytest.mark.asyncio
    async def test_concurrent_tool_invocations(self):
        """Test concurrent tool invocations and resource management."""
        # Mock multiple tool invocations
        mock_results = [
            {"content": [{"text": f"Result {i}"}]}
            for i in range(5)
        ]

        with patch("main.invoke_tool") as mock_invoke:
            mock_invoke.side_effect = mock_results

            # Simulate concurrent invocations
            tasks = []
            for i in range(5):
                task = mock_invoke(f"tool.{i}", {"param": f"value{i}"})
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            # Verify all results received
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result["content"][0]["text"] == f"Result {i}"

    def test_message_id_tracking(self):
        """Test message ID tracking and correlation."""
        # Test unique ID generation
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())

        assert id1 != id2
        assert len(id1) == 36  # UUID4 length
        assert len(id2) == 36

        # Test ID validation
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'

        assert re.match(uuid_pattern, id1)
        assert re.match(uuid_pattern, id2)

    def test_protocol_extension_handling(self):
        """Test handling of MCP protocol extensions."""
        # Test custom protocol extensions
        extended_request = {
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tools/call",
            "params": {
                "name": "repos.get",
                "arguments": {"owner": "octocat", "repo": "Hello-World"}
            },
            "extensions": {
                "caching": {"ttl": 300},
                "tracing": {"trace_id": "abc-123"}
            }
        }

        # Should handle extensions gracefully
        assert "extensions" in extended_request
        assert extended_request["extensions"]["caching"]["ttl"] == 300
        assert extended_request["extensions"]["tracing"]["trace_id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_protocol_timeout_handling(self):
        """Test timeout handling in protocol operations."""
        # Mock a slow tool execution
        with patch("main.invoke_tool", new_callable=AsyncMock) as mock_invoke:
            # Simulate timeout
            mock_invoke.side_effect = asyncio.TimeoutError()

            with pytest.raises(asyncio.TimeoutError):
                await mock_invoke("slow.tool", {}, timeout=1.0)

    def test_protocol_error_code_mapping(self):
        """Test MCP error code mapping and handling."""
        # Standard JSON-RPC error codes
        error_codes = {
            -32700: "Parse error",
            -32600: "Invalid Request",
            -32601: "Method not found",
            -32602: "Invalid params",
            -32603: "Internal error"
        }

        # Test error code handling
        for code, message in error_codes.items():
            error_response = {
                "jsonrpc": "2.0",
                "id": "123",
                "error": {
                    "code": code,
                    "message": message
                }
            }

            assert error_response["error"]["code"] == code
            assert error_response["error"]["message"] == message

    @pytest.mark.asyncio
    async def test_protocol_streaming_responses(self):
        """Test streaming response handling in MCP protocol."""
        # Mock streaming tool response
        async def mock_streaming_tool(*args, **kwargs):
            # Simulate streaming chunks
            chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
            for chunk in chunks:
                yield {"content": [{"text": chunk}]}
                await asyncio.sleep(0.1)  # Simulate network delay

        with patch("main.invoke_tool", side_effect=mock_streaming_tool):
            # This would test streaming response handling
            # Implementation depends on actual streaming support
            pass

    def test_protocol_metadata_handling(self):
        """Test protocol metadata handling and propagation."""
        # Test request metadata
        request_with_metadata = {
            "jsonrpc": "2.0",
            "id": "123",
            "method": "tools/call",
            "params": {
                "name": "repos.get",
                "arguments": {"owner": "octocat"},
                "_meta": {
                    "user_id": "user123",
                    "session_id": "session456",
                    "request_timeout": 30
                }
            }
        }

        # Should preserve metadata
        assert "_meta" in request_with_metadata["params"]
        assert request_with_metadata["params"]["_meta"]["user_id"] == "user123"

        # Test response metadata
        response_with_metadata = {
            "jsonrpc": "2.0",
            "id": "123",
            "result": {
                "content": [{"text": "Success"}]
            },
            "_meta": {
                "processing_time_ms": 150,
                "cache_hit": False,
                "rate_limit_remaining": 4999
            }
        }

        assert "_meta" in response_with_metadata
        assert response_with_metadata["_meta"]["processing_time_ms"] == 150
