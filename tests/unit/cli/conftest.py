"""CLI Test Configuration and Fixtures.

Provides common fixtures and configuration for CLI unit tests.
"""

import pytest
from unittest.mock import Mock, patch
from rich.console import Console


@pytest.fixture
def mock_console():
    """Standard mock console fixture used across all CLI tests."""
    console = Mock()
    console.print = Mock()
    # Mock the status method to return a context manager
    status_mock = Mock()
    status_mock.__enter__ = Mock(return_value=Mock())
    status_mock.__exit__ = Mock(return_value=None)
    console.status = Mock(return_value=status_mock)
    return console


@pytest.fixture
def mock_clients():
    """Standard mock service clients fixture used across all CLI tests."""
    from unittest.mock import AsyncMock
    clients = Mock()
    # Common async methods used in tests
    clients.get_json = AsyncMock()
    clients.post_json = AsyncMock()
    clients.put_json = AsyncMock()
    clients.delete_json = AsyncMock()
    return clients


@pytest.fixture
def mock_cache():
    """Standard mock cache fixture for testing."""
    return {}


@pytest.fixture
def cli_service(mock_console, mock_clients, mock_cache):
    """CLICommands service instance for testing."""
    from services.cli.modules.cli_commands import CLICommands

    # Patch get_cli_clients to return our mock
    with patch('services.cli.modules.cli_commands.get_cli_clients', return_value=mock_clients):
        # Patch Console() to return our mock
        with patch('services.cli.modules.cli_commands.Console', return_value=mock_console):
            service = CLICommands()
            service._cache = mock_cache  # Override the cache
            yield service


# Removed autouse fixture to avoid conflicts with test-specific mocking
