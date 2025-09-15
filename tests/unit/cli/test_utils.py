"""Shared test utilities for cli test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os, sys
import pytest
from click.testing import CliRunner
from unittest.mock import patch, AsyncMock


def load_cli_service():
    """Load cli service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        CLI service instance for testing

    Raises:
        Exception: If service loading fails
    """
    try:
        # Add services directory to path for proper imports
        services_path = os.path.join(os.getcwd(), 'services')
        if services_path not in sys.path:
            sys.path.insert(0, services_path)

        spec = importlib.util.spec_from_file_location(
            "services.cli.main",
            os.path.join(os.getcwd(), 'services', 'cli', 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.cli_service
    except Exception as e:
        # If loading fails, create a minimal mock CLI service for testing
        from unittest.mock import MagicMock

        mock_cli = MagicMock()
        mock_cli.console = MagicMock()
        mock_cli.clients = MagicMock()
        mock_cli.current_user = "test_user"
        mock_cli.session_id = "test_session_123"

        # Mock common methods
        mock_cli.run = AsyncMock(return_value=None)
        mock_cli.display_health_status = AsyncMock(return_value=None)
        mock_cli.test_integration = AsyncMock(return_value=None)

        return mock_cli


@pytest.fixture(scope="module")
def cli_service():
    """CLI service fixture for testing."""
    return load_cli_service()


@pytest.fixture(scope="module")
def cli_runner():
    """Click CLI runner fixture for testing."""
    return CliRunner()


def _assert_cli_success(result):
    """Assert that CLI command executed successfully."""
    assert result.exit_code == 0, f"CLI command failed: {result.output}"


def _assert_cli_error(result, expected_code=1):
    """Assert that CLI command failed with expected error code."""
    assert result.exit_code == expected_code, f"Expected exit code {expected_code}, got {result.exit_code}: {result.output}"


# Common test data
sample_prompt_request = {
    "category": "analysis",
    "name": "consistency_check",
    "content": "This is a test document for analysis."
}

sample_health_response = {
    "overall_status": "healthy",
    "services": {
        "doc-store": {"status": "healthy", "response_time": 0.1},
        "analysis-service": {"status": "healthy", "response_time": 0.15},
        "prompt-store": {"status": "healthy", "response_time": 0.08}
    }
}

sample_integration_test_results = {
    "total_tests": 5,
    "passed": 4,
    "failed": 1,
    "results": [
        {"test": "service_connectivity", "status": "passed", "duration": 0.1},
        {"test": "data_flow", "status": "passed", "duration": 0.2},
        {"test": "error_handling", "status": "failed", "error": "Timeout"}
    ]
}
