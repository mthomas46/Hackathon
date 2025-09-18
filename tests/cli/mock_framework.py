"""
CLI Mock Testing Framework

Provides comprehensive mocking capabilities for CLI testing including:
- Mock HTTP clients for service responses
- Docker command mocking
- Environment simulation
- Response timing and error injection
- Test data generation and validation
"""

import asyncio
import json
import time
import subprocess
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
import urllib.request
import urllib.error
import urllib.parse

from .test_fixtures import CLITestFixtures, MockServiceResponse


@dataclass
class MockHTTPRequest:
    """Mock HTTP request for testing"""
    url: str
    method: str = "GET"
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: float = 10.0


@dataclass
class MockHTTPResponse:
    """Mock HTTP response for testing"""
    status_code: int
    data: Optional[Union[str, Dict[str, Any]]] = None
    headers: Optional[Dict[str, str]] = None
    delay: float = 0.0  # Response delay in seconds
    exception: Optional[Exception] = None


class MockHTTPClient:
    """Mock HTTP client for CLI testing"""

    def __init__(self):
        self.requests: List[MockHTTPRequest] = []
        self.responses: Dict[str, MockHTTPResponse] = {}
        self.default_response = MockHTTPResponse(status_code=200, data={"status": "ok"})

    def add_response(self, url_pattern: str, response: MockHTTPResponse):
        """Add a mock response for a URL pattern"""
        self.responses[url_pattern] = response

    def get_response(self, url: str) -> MockHTTPResponse:
        """Get mock response for a URL"""
        # Try exact match first
        if url in self.responses:
            return self.responses[url]

        # Try pattern matching
        for pattern, response in self.responses.items():
            if pattern in url:
                return response

        return self.default_response

    def record_request(self, request: MockHTTPRequest):
        """Record a request for verification"""
        self.requests.append(request)

    def get_requests_for_url(self, url_pattern: str) -> List[MockHTTPRequest]:
        """Get all requests made to a URL pattern"""
        return [req for req in self.requests if url_pattern in req.url]

    def clear_requests(self):
        """Clear recorded requests"""
        self.requests.clear()

    async def mock_get_json(self, url: str) -> Optional[Dict]:
        """Mock async get_json method"""
        self.record_request(MockHTTPRequest(url=url, method="GET"))

        response = self.get_response(url)

        # Simulate delay
        if response.delay > 0:
            await asyncio.sleep(response.delay)

        # Simulate exception
        if response.exception:
            raise response.exception

        if response.status_code != 200:
            return None

        if isinstance(response.data, dict):
            return response.data
        elif isinstance(response.data, str):
            try:
                return json.loads(response.data)
            except json.JSONDecodeError:
                return None

        return response.data

    async def mock_post_json(self, url: str, data: Dict) -> Optional[Dict]:
        """Mock async post_json method"""
        self.record_request(MockHTTPRequest(url=url, method="POST", data=data))

        response = self.get_response(url)

        # Simulate delay
        if response.delay > 0:
            await asyncio.sleep(response.delay)

        # Simulate exception
        if response.exception:
            raise response.exception

        if response.status_code not in [200, 201]:
            return None

        if isinstance(response.data, dict):
            return response.data
        elif isinstance(response.data, str):
            try:
                return json.loads(response.data)
            except json.JSONDecodeError:
                return None

        return response.data


class MockDockerClient:
    """Mock Docker client for CLI testing"""

    def __init__(self):
        self.commands: List[List[str]] = []
        self.responses: Dict[str, str] = {}
        self.exceptions: Dict[str, Exception] = {}
        self.delays: Dict[str, float] = {}

    def add_command_response(self, command_key: str, response: str, delay: float = 0.0):
        """Add a mock response for a command"""
        self.responses[command_key] = response
        self.delays[command_key] = delay

    def add_command_exception(self, command_key: str, exception: Exception):
        """Add an exception for a command"""
        self.exceptions[command_key] = exception

    def get_command_key(self, cmd: List[str]) -> str:
        """Generate a key for command matching"""
        return " ".join(cmd)

    def mock_subprocess_run(self, cmd: List[str], **kwargs) -> Mock:
        """Mock subprocess.run for Docker commands"""
        command_key = self.get_command_key(cmd)
        self.commands.append(cmd)

        # Create mock result
        result = Mock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""

        # Check for exceptions
        if command_key in self.exceptions:
            result.returncode = 1
            result.stderr = str(self.exceptions[command_key])
            return result

        # Check for responses
        if command_key in self.responses:
            result.stdout = self.responses[command_key]
            result.returncode = 0
        else:
            # Default responses based on command type
            if "ps" in cmd:
                result.stdout = CLITestFixtures.get_mock_container_status()
            elif "stats" in cmd:
                result.stdout = CLITestFixtures.get_mock_container_stats()
            elif "logs" in cmd:
                service_name = cmd[-1] if cmd else "test-service"
                result.stdout = CLITestFixtures.get_mock_container_logs(service_name)
            elif "restart" in cmd or "stop" in cmd or "start" in cmd:
                result.stdout = f"Command executed successfully"
            else:
                result.returncode = 1
                result.stderr = "Command not mocked"

        # Simulate delay
        if command_key in self.delays:
            time.sleep(self.delays[command_key])

        return result

    def get_executed_commands(self) -> List[List[str]]:
        """Get list of executed commands"""
        return self.commands.copy()

    def clear_commands(self):
        """Clear executed commands history"""
        self.commands.clear()


class CLIMockFramework:
    """Comprehensive CLI testing framework"""

    def __init__(self):
        self.http_client = MockHTTPClient()
        self.docker_client = MockDockerClient()
        self.fixtures = CLITestFixtures()
        self.patches: List[Any] = []

    @contextmanager
    def mock_cli_environment(self, environment: str = "test"):
        """Context manager for mocking CLI environment"""
        patches = []

        try:
            # Mock HTTP client
            http_patch = patch('urllib.request.urlopen')
            mock_urlopen = http_patch.start()
            mock_urlopen.return_value.__enter__.return_value.read.return_value = b'{"status": "ok"}'
            mock_urlopen.return_value.__enter__.return_value.status = 200
            patches.append(http_patch)

            # Mock subprocess for Docker commands
            subprocess_patch = patch('subprocess.run')
            mock_subprocess = subprocess_patch.start()
            mock_subprocess.side_effect = self.docker_client.mock_subprocess_run
            patches.append(subprocess_patch)

            # Mock os.environ for environment detection
            os_patch = patch.dict('os.environ', {
                'DOCKER_CONTAINER': 'true' if environment == 'docker' else '',
                'KUBERNETES_SERVICE_HOST': 'localhost' if environment == 'kubernetes' else ''
            })
            os_patch.start()
            patches.append(os_patch)

            self.patches = patches

            yield self

        finally:
            # Stop all patches
            for patch_obj in patches:
                patch_obj.stop()
            self.patches = []

    def setup_service_responses(self, service_name: str, operation: str, response: Optional[MockServiceResponse] = None):
        """Setup mock responses for a service operation"""
        base_urls = self.fixtures.get_test_service_urls()
        base_url = base_urls.get(service_name, f"http://localhost:8080")

        if response is None:
            if service_name == "doc_store":
                response = self.fixtures.get_mock_doc_store_response(operation)
            elif service_name == "prompt_store":
                response = self.fixtures.get_mock_prompt_store_response(operation)
            elif service_name == "notification-service":
                response = self.fixtures.get_mock_notification_response(operation)
            else:
                response = self.fixtures.get_mock_health_response(service_name)

        # Setup HTTP response
        url_pattern = f"{base_url}/api/v1"
        http_response = MockHTTPResponse(
            status_code=response.status_code,
            data=response.json_data or response.text_data,
            headers=response.headers
        )
        self.http_client.add_response(url_pattern, http_response)

    def setup_container_responses(self, service_name: str, operation: str):
        """Setup mock responses for container operations"""
        command_responses = {
            "list": CLITestFixtures.get_mock_container_status(service_name),
            "stats": CLITestFixtures.get_mock_container_stats(),
            "logs": CLITestFixtures.get_mock_container_logs(service_name),
            "restart": f"Container {service_name} restarted successfully",
            "stop": f"Container {service_name} stopped successfully",
            "start": f"Container {service_name} started successfully",
            "rebuild": f"Container {service_name} rebuilt successfully"
        }

        response = command_responses.get(operation, "Command executed")
        self.docker_client.add_command_response(f"docker-compose {operation} {service_name}", response)

    def setup_error_scenario(self, service_name: str, error_type: str):
        """Setup error scenarios for testing"""
        error_responses = self.fixtures.get_error_responses()
        error_response = error_responses.get(error_type)

        if error_response:
            base_urls = self.fixtures.get_test_service_urls()
            base_url = base_urls.get(service_name, f"http://localhost:8080")
            url_pattern = f"{base_url}/api/v1"

            http_response = MockHTTPResponse(
                status_code=error_response.status_code,
                data=error_response.json_data or error_response.text_data,
                headers=error_response.headers
            )
            self.http_client.add_response(url_pattern, http_response)

    def setup_performance_scenario(self, service_name: str, delay: float = 2.0):
        """Setup performance testing scenario with delays"""
        base_urls = self.fixtures.get_test_service_urls()
        base_url = base_urls.get(service_name, f"http://localhost:8080")
        url_pattern = f"{base_url}/api/v1"

        response = self.fixtures.get_mock_health_response(service_name)
        http_response = MockHTTPResponse(
            status_code=response.status_code,
            data=response.json_data,
            delay=delay
        )
        self.http_client.add_response(url_pattern, http_response)

    def setup_concurrent_scenario(self, service_name: str, num_requests: int = 5):
        """Setup concurrent request scenario"""
        base_urls = self.fixtures.get_test_service_urls()
        base_url = base_urls.get(service_name, f"http://localhost:8080")

        # Setup multiple responses with slight delays
        for i in range(num_requests):
            delay = i * 0.1  # Stagger responses
            url_pattern = f"{base_url}/api/v1/request_{i}"
            response = self.fixtures.get_mock_health_response(service_name)
            http_response = MockHTTPResponse(
                status_code=response.status_code,
                data=response.json_data,
                delay=delay
            )
            self.http_client.add_response(url_pattern, http_response)

    def verify_requests(self, expected_requests: List[Dict[str, Any]]) -> bool:
        """Verify that expected requests were made"""
        actual_requests = self.http_client.requests

        if len(actual_requests) != len(expected_requests):
            return False

        for i, expected in enumerate(expected_requests):
            actual = actual_requests[i]
            if actual.url != expected.get("url"):
                return False
            if actual.method != expected.get("method", "GET"):
                return False
            if expected.get("data") and actual.data != expected["data"]:
                return False

        return True

    def verify_docker_commands(self, expected_commands: List[List[str]]) -> bool:
        """Verify that expected Docker commands were executed"""
        actual_commands = self.docker_client.get_executed_commands()

        if len(actual_commands) != len(expected_commands):
            return False

        for actual, expected in zip(actual_commands, expected_commands):
            if actual != expected:
                return False

        return True

    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of test execution"""
        return {
            "http_requests": len(self.http_client.requests),
            "docker_commands": len(self.docker_client.commands),
            "responses_configured": len(self.http_client.responses),
            "command_responses_configured": len(self.docker_client.responses),
            "exceptions_configured": len(self.docker_client.exceptions)
        }

    def reset(self):
        """Reset all mock state"""
        self.http_client.clear_requests()
        self.docker_client.clear_commands()
        self.http_client.responses.clear()
        self.docker_client.responses.clear()
        self.docker_client.exceptions.clear()


# Convenience functions for common test scenarios

def create_successful_service_test(service_name: str, operation: str = "health") -> CLIMockFramework:
    """Create a mock framework for successful service testing"""
    framework = CLIMockFramework()
    framework.setup_service_responses(service_name, operation)
    return framework


def create_error_service_test(service_name: str, error_type: str = "connection_error") -> CLIMockFramework:
    """Create a mock framework for error service testing"""
    framework = CLIMockFramework()
    framework.setup_error_scenario(service_name, error_type)
    return framework


def create_container_test(service_name: str, operation: str = "list") -> CLIMockFramework:
    """Create a mock framework for container testing"""
    framework = CLIMockFramework()
    framework.setup_container_responses(service_name, operation)
    return framework


def create_performance_test(service_name: str, delay: float = 1.0) -> CLIMockFramework:
    """Create a mock framework for performance testing"""
    framework = CLIMockFramework()
    framework.setup_performance_scenario(service_name, delay)
    return framework


def create_integration_test(services: List[str]) -> CLIMockFramework:
    """Create a mock framework for integration testing"""
    framework = CLIMockFramework()

    for service in services:
        framework.setup_service_responses(service, "health")

    return framework
