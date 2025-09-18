"""
Pytest Configuration for CLI Tests

Provides pytest fixtures and configuration for CLI testing including:
- Mock framework fixtures
- Test data fixtures
- Environment setup
- Test isolation
"""


import asyncio
import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from .mock_framework import CLIMockFramework, create_successful_service_test
from .test_fixtures import CLITestFixtures
from ecosystem_cli_executable import EcosystemCLI


@pytest.fixture
def cli_instance():
    """Fixture providing a CLI instance"""
    return EcosystemCLI()


@pytest.fixture
def mock_framework():
    """Fixture providing a mock framework instance"""
    return CLIMockFramework()


@pytest.fixture
def test_fixtures():
    """Fixture providing test fixtures instance"""
    return CLITestFixtures()


@pytest.fixture
def mock_cli_environment():
    """Fixture providing mocked CLI environment context manager"""
    framework = CLIMockFramework()
    return framework.mock_cli_environment()


@pytest.fixture
async def async_mock_environment():
    """Fixture for async mock environment testing"""
    framework = CLIMockFramework()

    with framework.mock_cli_environment():
        yield framework


@pytest.fixture
def successful_service_test():
    """Fixture for successful service test setup"""
    return create_successful_service_test("doc_store")


@pytest.fixture
def mock_stdout():
    """Fixture for capturing stdout"""
    return StringIO()


@pytest.fixture
def mock_stderr():
    """Fixture for capturing stderr"""
    return StringIO()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for all tests"""
    # Ensure clean environment
    os.environ.pop('DOCKER_CONTAINER', None)
    os.environ.pop('KUBERNETES_SERVICE_HOST', None)

    # Set test environment
    os.environ['TESTING'] = 'true'

    yield

    # Cleanup
    os.environ.pop('TESTING', None)


@pytest.fixture
def docker_environment():
    """Fixture for Docker environment testing"""
    with patch.dict('os.environ', {'DOCKER_CONTAINER': 'true'}):
        yield


@pytest.fixture
def kubernetes_environment():
    """Fixture for Kubernetes environment testing"""
    with patch.dict('os.environ', {'KUBERNETES_SERVICE_HOST': 'localhost'}):
        yield


@pytest.fixture
def local_environment():
    """Fixture for local environment testing"""
    with patch.dict('os.environ', {}, clear=True):
        yield


@pytest.fixture
def mock_docker_commands():
    """Fixture for mocking Docker commands"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Command executed", stderr="")
        yield mock_run


@pytest.fixture
def mock_http_requests():
    """Fixture for mocking HTTP requests"""
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = b'{"status": "ok"}'
        mock_response.__enter__.return_value.status = 200
        mock_urlopen.return_value = mock_response
        yield mock_urlopen


@pytest.fixture
def performance_test_setup():
    """Fixture for performance testing setup"""
    framework = CLIMockFramework()
    framework.setup_service_responses("doc_store", "health")
    return framework


@pytest.fixture
def load_test_setup():
    """Fixture for load testing setup"""
    framework = CLIMockFramework()
    # Setup multiple services for load testing
    services = ["doc_store", "analysis-service", "llm-gateway", "frontend"]
    for service in services:
        framework.setup_service_responses(service, "health")
    return framework


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Custom markers
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests for CLI functionality")
    config.addinivalue_line("markers", "integration: Integration tests for CLI workflows")
    config.addinivalue_line("markers", "performance: Performance tests for CLI operations")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "docker: Tests requiring Docker environment")
    config.addinivalue_line("markers", "network: Tests requiring network access")


# Test configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

        # Add slow marker for performance tests
        if "performance" in str(item.fspath) or "load" in item.name:
            item.add_marker(pytest.mark.slow)


# Setup and teardown
@pytest.fixture(scope="session", autouse=True)
def session_setup_teardown():
    """Session-level setup and teardown"""
    # Setup
    print("\n🚀 Starting CLI Test Session...")

    yield

    # Teardown
    print("\n✅ CLI Test Session Completed!")


@pytest.fixture(autouse=True)
def test_setup_teardown(request):
    """Test-level setup and teardown"""
    # Setup
    print(f"\n🔬 Running test: {request.node.name}")

    yield

    # Teardown
    print(f"✅ Completed test: {request.node.name}")


# Custom assertion helpers
def assert_response_time_less_than(actual_time, expected_time, operation_name="operation"):
    """Assert that response time is within acceptable limits"""
    assert actual_time < expected_time, \
        f"{operation_name} too slow: {actual_time:.4f}s (expected < {expected_time}s)"


def assert_memory_usage_less_than(actual_mb, expected_mb, operation_name="operation"):
    """Assert that memory usage is within acceptable limits"""
    assert actual_mb < expected_mb, \
        f"{operation_name} memory usage too high: {actual_mb:.2f}MB (expected < {expected_mb}MB)"


def assert_success_rate_above(actual_rate, expected_rate, test_name="test"):
    """Assert that success rate meets minimum requirements"""
    assert actual_rate >= expected_rate, \
        f"{test_name} success rate too low: {actual_rate:.1f}% (expected >= {expected_rate}%)"
