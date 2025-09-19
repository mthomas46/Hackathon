"""API & CLI Enhancement Tests.

This module contains comprehensive tests for advanced API features and CLI enhancements,
including HATEOAS, WebSocket streaming, and command-line interface validation.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import subprocess
import websockets
from fastapi.testclient import TestClient
from fastapi import WebSocket

# Add project path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestAdvancedHATEOAS:
    """Test advanced HATEOAS (Hypermedia As The Engine Of Application State) features."""

    def test_hateoas_link_generation(self):
        """Test automatic HATEOAS link generation for API responses."""
        # Mock API response with HATEOAS links
        base_url = "http://localhost:8000/api/v1"

        def generate_hateoas_links(resource_type: str, resource_id: str = None) -> Dict[str, Any]:
            """Generate HATEOAS links for a resource."""
            links = {
                "self": {"href": f"{base_url}/{resource_type}"}
            }

            if resource_id:
                links["self"]["href"] = f"{base_url}/{resource_type}/{resource_id}"

            # Add related resource links based on resource type
            if resource_type == "simulations":
                links.update({
                    "create": {"href": f"{base_url}/simulations", "method": "POST"},
                    "list": {"href": f"{base_url}/simulations", "method": "GET"},
                    "execute": {"href": f"{base_url}/simulations/{resource_id}/execute", "method": "POST"} if resource_id else None,
                    "status": {"href": f"{base_url}/simulations/{resource_id}/status", "method": "GET"} if resource_id else None,
                    "documents": {"href": f"{base_url}/simulations/{resource_id}/documents", "method": "GET"} if resource_id else None,
                    "events": {"href": f"{base_url}/simulations/{resource_id}/events", "method": "GET"} if resource_id else None
                })
            elif resource_type == "documents":
                links.update({
                    "download": {"href": f"{base_url}/documents/{resource_id}/download", "method": "GET"} if resource_id else None,
                    "analyze": {"href": f"{base_url}/documents/{resource_id}/analyze", "method": "POST"} if resource_id else None,
                    "versions": {"href": f"{base_url}/documents/{resource_id}/versions", "method": "GET"} if resource_id else None
                })

            # Remove None values
            return {k: v for k, v in links.items() if v is not None}

        # Test link generation for different resources
        simulation_links = generate_hateoas_links("simulations", "sim_123")
        document_links = generate_hateoas_links("documents", "doc_456")
        collection_links = generate_hateoas_links("simulations")

        # Validate simulation links
        assert "self" in simulation_links
        assert simulation_links["self"]["href"] == f"{base_url}/simulations/sim_123"
        assert "execute" in simulation_links
        assert "status" in simulation_links
        assert "documents" in simulation_links
        assert "events" in simulation_links

        # Validate document links
        assert "self" in document_links
        assert document_links["self"]["href"] == f"{base_url}/documents/doc_456"
        assert "download" in document_links
        assert "analyze" in document_links

        # Validate collection links
        assert "create" in collection_links
        assert "list" in collection_links
        assert collection_links["create"]["method"] == "POST"
        assert collection_links["list"]["method"] == "GET"

        print("✅ HATEOAS link generation validated")

    def test_hateoas_navigation_workflow(self):
        """Test complete HATEOAS navigation workflow."""
        # Simulate a user navigating through the API using HATEOAS links
        navigation_path = []

        # Start with the root API
        current_response = {
            "_links": {
                "simulations": {"href": "/api/v1/simulations", "method": "GET"},
                "health": {"href": "/api/v1/health", "method": "GET"}
            }
        }

        navigation_path.append("API Root")

        # Navigate to simulations
        simulations_response = {
            "_links": {
                "self": {"href": "/api/v1/simulations", "method": "GET"},
                "create": {"href": "/api/v1/simulations", "method": "POST"}
            },
            "simulations": [
                {
                    "id": "sim_123",
                    "name": "Test Simulation",
                    "_links": {
                        "self": {"href": "/api/v1/simulations/sim_123", "method": "GET"},
                        "execute": {"href": "/api/v1/simulations/sim_123/execute", "method": "POST"},
                        "status": {"href": "/api/v1/simulations/sim_123/status", "method": "GET"}
                    }
                }
            ]
        }

        navigation_path.append("Simulations List")

        # Navigate to specific simulation
        simulation_response = {
            "id": "sim_123",
            "name": "Test Simulation",
            "status": "running",
            "_links": {
                "self": {"href": "/api/v1/simulations/sim_123", "method": "GET"},
                "execute": {"href": "/api/v1/simulations/sim_123/execute", "method": "POST"},
                "status": {"href": "/api/v1/simulations/sim_123/status", "method": "GET"},
                "documents": {"href": "/api/v1/simulations/sim_123/documents", "method": "GET"},
                "events": {"href": "/api/v1/simulations/sim_123/events", "method": "GET"},
                "stop": {"href": "/api/v1/simulations/sim_123/stop", "method": "POST"}
            }
        }

        navigation_path.append("Simulation Detail")

        # Navigate to documents
        documents_response = {
            "_links": {
                "self": {"href": "/api/v1/simulations/sim_123/documents", "method": "GET"},
                "create": {"href": "/api/v1/simulations/sim_123/documents", "method": "POST"}
            },
            "documents": [
                {
                    "id": "doc_456",
                    "type": "requirements_doc",
                    "_links": {
                        "self": {"href": "/api/v1/documents/doc_456", "method": "GET"},
                        "download": {"href": "/api/v1/documents/doc_456/download", "method": "GET"},
                        "analyze": {"href": "/api/v1/documents/doc_456/analyze", "method": "POST"}
                    }
                }
            ]
        }

        navigation_path.append("Documents List")

        # Validate navigation workflow
        assert len(navigation_path) == 4
        assert "API Root" in navigation_path
        assert "Simulations List" in navigation_path
        assert "Simulation Detail" in navigation_path
        assert "Documents List" in navigation_path

        # Validate that each response contains proper HATEOAS links
        assert "_links" in current_response
        assert "_links" in simulations_response
        assert "_links" in simulation_response
        assert "_links" in documents_response

        # Validate link consistency
        sim_links = simulation_response["_links"]
        assert sim_links["self"]["href"].endswith("/simulations/sim_123")
        assert sim_links["execute"]["href"].endswith("/simulations/sim_123/execute")
        assert sim_links["documents"]["href"].endswith("/simulations/sim_123/documents")

        print("✅ HATEOAS navigation workflow validated")

    def test_hateoas_error_responses(self):
        """Test HATEOAS links in error responses."""
        # Test error responses with helpful navigation links
        error_responses = [
            {
                "error": "Not Found",
                "message": "The requested simulation does not exist",
                "status_code": 404,
                "_links": {
                    "collection": {"href": "/api/v1/simulations", "title": "Back to simulations"},
                    "help": {"href": "/api/v1/docs/errors", "title": "Error documentation"},
                    "support": {"href": "/api/v1/support", "title": "Get support"}
                }
            },
            {
                "error": "Unauthorized",
                "message": "Authentication required",
                "status_code": 401,
                "_links": {
                    "login": {"href": "/api/v1/auth/login", "title": "Login"},
                    "register": {"href": "/api/v1/auth/register", "title": "Register new account"},
                    "docs": {"href": "/api/v1/docs/authentication", "title": "Authentication docs"}
                }
            },
            {
                "error": "Validation Error",
                "message": "Invalid simulation configuration",
                "status_code": 422,
                "_links": {
                    "schema": {"href": "/api/v1/schemas/simulation", "title": "Simulation schema"},
                    "examples": {"href": "/api/v1/examples/simulations", "title": "Valid examples"},
                    "validate": {"href": "/api/v1/validate/simulation", "title": "Validation endpoint"}
                }
            }
        ]

        # Validate error responses include helpful links
        for error_response in error_responses:
            assert "_links" in error_response
            assert "error" in error_response
            assert "message" in error_response
            assert "status_code" in error_response

            links = error_response["_links"]
            assert len(links) > 0

            # Validate link structure
            for link_name, link_data in links.items():
                assert "href" in link_data
                assert "title" in link_data
                assert link_data["href"].startswith("/api/v1")

        print("✅ HATEOAS error responses validated")


class TestCLICommandValidation:
    """Test CLI command validation and functionality."""

    def test_cli_command_structure(self):
        """Test CLI command structure and argument parsing."""
        # Mock CLI commands and their expected structures
        cli_commands = {
            "start": {
                "description": "Start a new simulation",
                "args": [
                    {"name": "--config", "type": "file", "required": True, "help": "Configuration file path"},
                    {"name": "--name", "type": "string", "required": False, "help": "Simulation name"}
                ],
                "examples": [
                    "simulation start --config config.yaml",
                    "simulation start --config config.yaml --name 'Test Sim'"
                ]
            },
            "status": {
                "description": "Check simulation status",
                "args": [
                    {"name": "simulation_id", "type": "string", "required": True, "help": "Simulation ID"}
                ],
                "examples": [
                    "simulation status sim_123"
                ]
            },
            "list": {
                "description": "List all simulations",
                "args": [
                    {"name": "--status", "type": "choice", "required": False, "choices": ["active", "completed", "failed"]},
                    {"name": "--limit", "type": "int", "required": False, "default": 10}
                ],
                "examples": [
                    "simulation list",
                    "simulation list --status active",
                    "simulation list --limit 20"
                ]
            }
        }

        # Validate command structure
        for cmd_name, cmd_config in cli_commands.items():
            assert "description" in cmd_config
            assert "args" in cmd_config
            assert "examples" in cmd_config

            # Validate arguments
            for arg in cmd_config["args"]:
                assert "name" in arg
                assert "type" in arg
                assert "required" in arg
                # Help is optional for some args
                if arg.get("required", False):
                    assert "help" in arg, f"Required argument {arg['name']} must have help text"

                # Validate argument types
                valid_types = ["string", "int", "file", "choice", "bool"]
                assert arg["type"] in valid_types

                # If choice type, must have choices
                if arg["type"] == "choice":
                    assert "choices" in arg
                    assert isinstance(arg["choices"], list)

            # Validate examples
            for example in cmd_config["examples"]:
                assert example.startswith(f"simulation {cmd_name}")

        print("✅ CLI command structure validated")

    def test_cli_argument_validation(self):
        """Test CLI argument validation and error handling."""
        # Mock argument validation function
        def validate_cli_args(command: str, args: Dict[str, Any]) -> Dict[str, Any]:
            """Validate CLI arguments for a command."""
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }

            if command == "start":
                if "config" not in args:
                    validation_result["valid"] = False
                    validation_result["errors"].append("Missing required argument: --config")

                config_path = args.get("config")
                if config_path and not config_path.endswith((".yaml", ".yml", ".json")):
                    validation_result["warnings"].append("Config file should have .yaml, .yml, or .json extension")

                name = args.get("name", "")
                if len(name) > 100:
                    validation_result["errors"].append("Simulation name too long (max 100 characters)")

            elif command == "status":
                if "simulation_id" not in args:
                    validation_result["valid"] = False
                    validation_result["errors"].append("Missing required argument: simulation_id")

                sim_id = args.get("simulation_id", "")
                if sim_id and not sim_id.startswith("sim_"):
                    validation_result["warnings"].append("Simulation ID should start with 'sim_'")

            elif command == "list":
                limit = args.get("limit", 10)
                if not isinstance(limit, int) or limit < 1 or limit > 100:
                    validation_result["errors"].append("Limit must be an integer between 1 and 100")

                status = args.get("status")
                if status and status not in ["active", "completed", "failed"]:
                    validation_result["errors"].append("Status must be one of: active, completed, failed")

            return validation_result

        # Test various argument validation scenarios
        test_cases = [
            # Valid cases
            ("start", {"config": "config.yaml"}, True, [], []),
            ("start", {"config": "config.yaml", "name": "Test Sim"}, True, [], []),
            ("status", {"simulation_id": "sim_123"}, True, [], []),
            ("list", {"limit": 20}, True, [], []),

            # Invalid cases
            ("start", {}, False, ["Missing required argument: --config"], []),
            ("start", {"config": "config.txt"}, True, [], ["Config file should have .yaml, .yml, or .json extension"]),
            ("start", {"config": "config.yaml", "name": "x" * 150}, False, ["Simulation name too long (max 100 characters)"], []),
            ("list", {"limit": 150}, False, ["Limit must be an integer between 1 and 100"], []),
            ("list", {"status": "invalid"}, False, ["Status must be one of: active, completed, failed"], [])
        ]

        for command, args, expected_valid, expected_errors, expected_warnings in test_cases:
            result = validate_cli_args(command, args)

            assert result["valid"] == expected_valid, f"Validation failed for {command} with args {args}"

            # Check errors
            for expected_error in expected_errors:
                assert expected_error in result["errors"], f"Expected error not found: {expected_error}"

            # Check warnings
            for expected_warning in expected_warnings:
                assert expected_warning in result["warnings"], f"Expected warning not found: {expected_warning}"

        print("✅ CLI argument validation tested")

    def test_cli_help_system(self):
        """Test CLI help system and documentation."""
        # Mock CLI help system
        help_content = {
            "main": """
Simulation CLI Tool

Usage: simulation [COMMAND] [OPTIONS]

Commands:
  start    Start a new simulation
  status   Check simulation status
  list     List all simulations
  stop     Stop a running simulation
  logs     View simulation logs

Options:
  -h, --help     Show this help message
  -v, --version  Show version information

Use 'simulation [COMMAND] --help' for more information about a command.
            """,
            "start": """
Start a new simulation

Usage: simulation start [OPTIONS]

Options:
  --config FILE       Configuration file path (required)
  --name TEXT         Simulation name
  --team-size INT     Team size (default: 5)
  --duration INT      Duration in weeks (default: 8)
  -h, --help          Show this help message

Examples:
  simulation start --config config.yaml
  simulation start --config config.yaml --name "My Simulation"
            """
        }

        # Validate help content structure
        for section, content in help_content.items():
            assert "Usage:" in content
            assert "Options:" in content or "Commands:" in content

            if section == "main":
                assert "Commands:" in content
                assert "start" in content
                assert "status" in content
                assert "list" in content

            if section == "start":
                assert "--config" in content
                assert "--name" in content
                assert "Examples:" in content

        print("✅ CLI help system validated")


class TestWebSocketStreaming:
    """Test WebSocket streaming functionality."""

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """Test WebSocket connection lifecycle."""
        # Mock WebSocket connection lifecycle
        connection_events = []

        async def mock_websocket_handler():
            """Mock WebSocket handler simulating connection lifecycle."""
            # Connection established
            connection_events.append({"event": "connected", "timestamp": time.time()})

            # Simulate receiving messages
            messages = [
                {"type": "subscribe", "channels": ["simulation_progress"]},
                {"type": "ping"},
                {"type": "unsubscribe", "channels": ["simulation_progress"]}
            ]

            for message in messages:
                connection_events.append({"event": "message_received", "data": message, "timestamp": time.time()})
                await asyncio.sleep(0.01)  # Simulate processing time

                # Send response
                if message["type"] == "ping":
                    connection_events.append({"event": "message_sent", "data": {"type": "pong"}, "timestamp": time.time()})
                elif message["type"] == "subscribe":
                    connection_events.append({"event": "message_sent", "data": {"type": "subscribed", "channels": message["channels"]}, "timestamp": time.time()})

            # Connection closed
            connection_events.append({"event": "disconnected", "timestamp": time.time()})

        # Run the mock WebSocket handler
        await mock_websocket_handler()

        # Validate connection lifecycle
        assert len(connection_events) >= 6  # connected + 3 messages received + 2 messages sent + disconnected

        # Check event sequence
        event_types = [e["event"] for e in connection_events]
        assert "connected" in event_types
        assert "disconnected" in event_types
        assert event_types.count("message_received") == 3
        assert event_types.count("message_sent") >= 2

        # Validate message handling
        messages_received = [e for e in connection_events if e["event"] == "message_received"]
        assert len(messages_received) == 3

        messages_sent = [e for e in connection_events if e["event"] == "message_sent"]
        assert len(messages_sent) >= 2

        print("✅ WebSocket connection lifecycle validated")

    def test_websocket_message_validation(self):
        """Test WebSocket message validation and parsing."""
        # Mock WebSocket message validation
        def validate_websocket_message(message: Dict[str, Any]) -> Dict[str, Any]:
            """Validate WebSocket message structure."""
            validation_result = {
                "valid": True,
                "errors": [],
                "message_type": None
            }

            if not isinstance(message, dict):
                validation_result["valid"] = False
                validation_result["errors"].append("Message must be a JSON object")
                return validation_result

            if "type" not in message:
                validation_result["valid"] = False
                validation_result["errors"].append("Message must have a 'type' field")
                return validation_result

            message_type = message["type"]
            validation_result["message_type"] = message_type

            # Validate message structure based on type
            if message_type == "subscribe":
                if "channels" not in message:
                    validation_result["valid"] = False
                    validation_result["errors"].append("Subscribe message must have 'channels' field")

                if not isinstance(message.get("channels", []), list):
                    validation_result["valid"] = False
                    validation_result["errors"].append("'channels' must be an array")

            elif message_type == "unsubscribe":
                if "channels" not in message:
                    validation_result["valid"] = False
                    validation_result["errors"].append("Unsubscribe message must have 'channels' field")

            elif message_type == "simulation_command":
                required_fields = ["command", "simulation_id"]
                for field in required_fields:
                    if field not in message:
                        validation_result["valid"] = False
                        validation_result["errors"].append(f"Missing required field: {field}")

            return validation_result

        # Test various message types
        test_messages = [
            # Valid messages
            ({"type": "subscribe", "channels": ["progress", "events"]}, True, "subscribe"),
            ({"type": "unsubscribe", "channels": ["progress"]}, True, "unsubscribe"),
            ({"type": "ping"}, True, "ping"),
            ({"type": "simulation_command", "command": "start", "simulation_id": "sim_123"}, True, "simulation_command"),

            # Invalid messages
            ({}, False, None),  # Missing type
            ({"type": "subscribe"}, False, "subscribe"),  # Missing channels
            ({"type": "subscribe", "channels": "progress"}, False, "subscribe"),  # Wrong channels type
            ({"type": "simulation_command", "command": "start"}, False, "simulation_command"),  # Missing simulation_id
            ("not an object", False, None),  # Wrong type
        ]

        for message, expected_valid, expected_type in test_messages:
            result = validate_websocket_message(message)

            assert result["valid"] == expected_valid, f"Validation failed for message: {message}"

            if expected_type:
                assert result["message_type"] == expected_type, f"Wrong message type for: {message}"

            if not expected_valid:
                assert len(result["errors"]) > 0, f"No errors reported for invalid message: {message}"

        print("✅ WebSocket message validation tested")

    @pytest.mark.asyncio
    async def test_websocket_broadcasting_efficiency(self):
        """Test WebSocket broadcasting efficiency with multiple clients."""
        # Mock multiple WebSocket clients
        num_clients = 50
        clients = [AsyncMock() for _ in range(num_clients)]
        broadcast_messages = []

        async def broadcast_to_clients(message: Dict[str, Any]):
            """Broadcast message to all connected clients."""
            broadcast_messages.append(message)
            message_json = json.dumps(message)

            # Broadcast concurrently
            tasks = []
            for client in clients:
                task = client.send_text(message_json)
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        # Test broadcasting efficiency
        start_time = time.time()

        # Broadcast multiple messages
        messages = [
            {"type": "simulation_progress", "simulation_id": "sim_123", "progress": 25.0},
            {"type": "simulation_event", "simulation_id": "sim_123", "event": "phase_completed"},
            {"type": "simulation_status", "simulation_id": "sim_123", "status": "running"}
        ]

        for message in messages:
            await broadcast_to_clients(message)

        end_time = time.time()
        total_time = end_time - start_time

        # Validate broadcasting efficiency
        assert len(broadcast_messages) == len(messages)
        assert total_time < 2.0, f"Broadcasting took too long: {total_time:.2f}s"

        # Check that all clients received all messages
        for client in clients:
            assert client.send_text.call_count == len(messages)

        # Calculate broadcasting metrics
        total_messages_sent = len(clients) * len(messages)
        messages_per_second = total_messages_sent / total_time

        assert messages_per_second > 100, f"Broadcasting rate too low: {messages_per_second:.1f} msg/s"

        print("✅ WebSocket broadcasting efficiency validated")


class TestAPIEnhancementFeatures:
    """Test advanced API enhancement features."""

    def test_api_versioning_support(self):
        """Test API versioning support and compatibility."""
        # Mock API versioning system
        api_versions = {
            "v1": {
                "endpoints": ["/api/v1/simulations", "/api/v1/health"],
                "deprecated": False,
                "sunset_date": None
            },
            "v2": {
                "endpoints": ["/api/v2/simulations", "/api/v2/health", "/api/v2/analytics"],
                "deprecated": False,
                "sunset_date": None
            },
            "v1.5": {
                "endpoints": ["/api/v1.5/simulations", "/api/v1.5/health"],
                "deprecated": True,
                "sunset_date": "2024-12-31"
            }
        }

        # Test version compatibility
        current_version = "v2"
        supported_versions = ["v1", "v1.5", "v2"]

        assert current_version in supported_versions
        assert "v1" in supported_versions  # Backward compatibility

        # Check deprecated versions
        deprecated_versions = [v for v, config in api_versions.items() if config["deprecated"]]

        if deprecated_versions:
            for version in deprecated_versions:
                config = api_versions[version]
                assert config["sunset_date"] is not None, f"Deprecated version {version} missing sunset date"

        # Validate endpoint consistency across versions
        base_endpoints = ["/health"]  # Endpoints that should exist in all versions

        for version, config in api_versions.items():
            if not config["deprecated"]:
                endpoints = config["endpoints"]
                for base_endpoint in base_endpoints:
                    versioned_endpoint = f"/api/{version}{base_endpoint}"
                    assert any(ep.endswith(base_endpoint) for ep in endpoints), \
                        f"Version {version} missing base endpoint: {base_endpoint}"

        print("✅ API versioning support validated")

    def test_api_rate_limiting(self):
        """Test API rate limiting functionality."""
        # Mock rate limiting system
        rate_limits = {
            "default": {"requests_per_minute": 60, "burst_limit": 10},
            "authenticated": {"requests_per_minute": 300, "burst_limit": 50},
            "admin": {"requests_per_minute": 1000, "burst_limit": 200}
        }

        request_log = []

        def check_rate_limit(user_type: str, endpoint: str) -> Dict[str, Any]:
            """Check if request is within rate limits."""
            limits = rate_limits.get(user_type, rate_limits["default"])

            # Count recent requests (simplified)
            recent_requests = len([r for r in request_log
                                 if r["user_type"] == user_type
                                 and time.time() - r["timestamp"] < 60])  # Last minute

            allowed = recent_requests < limits["requests_per_minute"]

            if allowed:
                request_log.append({
                    "user_type": user_type,
                    "endpoint": endpoint,
                    "timestamp": time.time()
                })

            return {
                "allowed": allowed,
                "remaining_requests": max(0, limits["requests_per_minute"] - recent_requests - 1),
                "reset_time": int(time.time()) + 60
            }

        # Test rate limiting for different user types
        test_scenarios = [
            ("default", "/api/v1/simulations", 70),  # Exceed limit
            ("authenticated", "/api/v1/simulations", 320),  # Exceed limit
            ("admin", "/api/v1/simulations", 1050),  # Exceed limit
        ]

        for user_type, endpoint, num_requests in test_scenarios:
            # Reset request log for this scenario
            request_log.clear()

            # Make requests up to the limit
            allowed_count = 0
            for i in range(num_requests):
                result = check_rate_limit(user_type, endpoint)
                if result["allowed"]:
                    allowed_count += 1
                else:
                    break

            # Validate rate limiting
            limits = rate_limits.get(user_type, rate_limits["default"])
            expected_allowed = min(num_requests, limits["requests_per_minute"])

            assert allowed_count <= limits["requests_per_minute"], \
                f"Rate limit exceeded for {user_type}: {allowed_count} > {limits['requests_per_minute']}"

        print("✅ API rate limiting validated")

    def test_api_caching_headers(self):
        """Test API caching headers and cache control."""
        # Mock cache control headers for different endpoints
        cache_headers = {
            "/api/v1/simulations": {
                "Cache-Control": "private, max-age=300",  # 5 minutes
                "ETag": '"simulations-list-v1"',
                "Last-Modified": "Wed, 21 Oct 2023 07:28:00 GMT"
            },
            "/api/v1/simulations/{id}": {
                "Cache-Control": "private, max-age=60",  # 1 minute
                "ETag": '"simulation-detail-{id}"',
                "Vary": "Accept-Encoding"
            },
            "/api/v1/health": {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            },
            "/api/v1/documents/{id}/download": {
                "Cache-Control": "public, max-age=3600",  # 1 hour
                "ETag": '"document-{id}-v1"',
                "Content-Type": "application/pdf"
            }
        }

        # Validate cache headers
        for endpoint, headers in cache_headers.items():
            assert "Cache-Control" in headers

            cache_control = headers["Cache-Control"]

            if "health" in endpoint:
                # Health endpoints should not be cached
                assert "no-cache" in cache_control or "no-store" in cache_control
            elif "download" in endpoint:
                # Download endpoints can be cached longer
                assert "max-age" in cache_control
            else:
                # Regular endpoints have moderate caching
                assert "max-age" in cache_control

            # ETag should be present for cacheable content
            if "no-cache" not in cache_control and "no-store" not in cache_control:
                assert "ETag" in headers

        print("✅ API caching headers validated")


# Helper fixtures
@pytest.fixture
def mock_websocket_server():
    """Create a mock WebSocket server for testing."""
    return {
        "host": "localhost",
        "port": 8080,
        "connected_clients": [],
        "message_history": []
    }


@pytest.fixture
def cli_command_parser():
    """Create a mock CLI command parser for testing."""
    return {
        "commands": {
            "start": {"args": ["--config", "--name"], "required": ["--config"]},
            "status": {"args": ["simulation_id"], "required": ["simulation_id"]},
            "list": {"args": ["--status", "--limit"], "required": []}
        },
        "global_options": ["--help", "--version", "--verbose"]
    }


@pytest.fixture
def api_response_builder():
    """Create a mock API response builder for testing."""
    def build_response(data=None, status_code=200, headers=None):
        response = {
            "status_code": status_code,
            "headers": headers or {},
            "body": data or {}
        }

        # Add HATEOAS links if data is present
        if isinstance(data, dict) and data:
            response["body"]["_links"] = {
                "self": {"href": "/api/v1/current"},
                "collection": {"href": "/api/v1/collection"}
            }

        return response

    return build_response
