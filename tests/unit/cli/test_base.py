"""Base test utilities and fixtures for CLI tests.

This module provides common test fixtures, helper classes, and utilities
to eliminate code duplication across CLI test files.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from rich.console import Console
from typing import Dict, Any, Optional, List

from services.cli.modules.base.base_manager import BaseManager


# ===== COMMON FIXTURES =====
# Common fixtures are now defined in conftest.py


# ===== HELPER CLASSES =====

class MockManager(BaseManager):
    """Mock implementation of BaseManager for testing."""

    def __init__(self, console=None, clients=None, cache=None):
        self._console = console or Mock(spec=Console)
        self._clients = clients or Mock()
        self._cache = cache or {}
        super().__init__(self._console, self._clients, self._cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        return [("1", "Test Option 1"), ("2", "Test Option 2")]

    async def handle_choice(self, choice: str) -> bool:
        return True


class AsyncTestHelper:
    """Helper for common async test patterns."""

    @staticmethod
    def mock_prompt_sequence(*responses):
        """Create a mock that returns a sequence of prompt responses."""
        return Mock(side_effect=responses)

    @staticmethod
    def create_async_mock(return_value=None, side_effect=None):
        """Create an AsyncMock with common configuration."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock


# ===== COMMON TEST PATTERNS =====

class BaseManagerTestMixin:
    """Mixin providing common test methods for BaseManager subclasses."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mock_console, mock_clients):
        """Set up fixtures for the test class."""
        self.mock_console = mock_console
        self.mock_clients = mock_clients

    def assert_manager_inheritance(self, manager):
        """Assert that a manager properly inherits from BaseManager."""
        assert isinstance(manager, BaseManager)
        assert hasattr(manager, 'console')
        assert hasattr(manager, 'clients')
        assert hasattr(manager, 'cache_manager')
        assert hasattr(manager, 'display')

    def assert_manager_initialization(self, manager, expected_console, expected_clients):
        """Assert that a manager is properly initialized."""
        assert manager.console == expected_console
        assert manager.clients == expected_clients
        assert manager.cache_manager is not None
        assert manager.display is not None

    async def assert_menu_loop_works(self, manager, menu_items=None):
        """Assert that the menu loop works with a manager."""
        menu_items = menu_items or [("1", "Test Option")]

        with patch.object(manager, 'handle_choice', return_value=True) as mock_handle:
            with patch('rich.prompt.Prompt.ask', side_effect=["1", "", "b"]):
                await manager.run_menu_loop("Test Menu", menu_items)

                mock_handle.assert_called_once_with("1")

    async def assert_cache_operations_work(self, manager):
        """Assert that cache operations work on a manager."""
        test_key = "test_key"
        test_value = "test_value"

        await manager.cache_set(test_key, test_value)
        result = await manager.cache_get(test_key)

        assert result == test_value

    def assert_display_methods_work(self, manager):
        """Assert that display methods work on a manager."""
        manager.display.show_success("Test success")
        manager.display.show_error("Test error")
        manager.display.show_warning("Test warning")
        manager.display.show_info("Test info")

        # Verify the display object exists and has the methods
        assert manager.display is not None
        assert hasattr(manager.display, 'show_success')
        assert hasattr(manager.display, 'show_error')
        assert hasattr(manager.display, 'show_warning')
        assert hasattr(manager.display, 'show_info')


class APITestMixin:
    """Mixin providing common API testing patterns."""

    async def assert_api_call_with_status(self, manager, endpoint, description, expected_status_call=None):
        """Assert that an API call with status works."""
        mock_response = {"test": "data"}

        with patch.object(manager.clients, 'get_json', new_callable=AsyncMock, return_value=mock_response) as mock_get:
            result = await manager.api_get_with_status(endpoint, description)

            assert result == mock_response
            mock_get.assert_called_once_with(endpoint)

    async def assert_api_operation_with_confirm(self, manager, endpoint, data, description, confirm_msg, success_msg):
        """Assert that an API operation with confirmation works."""
        mock_response = {"success": True}

        with patch('rich.prompt.Confirm.ask', return_value=True) as mock_confirm:
            with patch.object(manager.clients, 'post_json', new_callable=AsyncMock, return_value=mock_response) as mock_post:
                result = await manager.api_operation_with_confirm(
                    endpoint, data, description, confirm_msg, success_msg
                )

                assert result is True
                mock_confirm.assert_called_once_with(f"[yellow]{confirm_msg}[/yellow]", default=False)
                mock_post.assert_called_once_with(endpoint, data)


# ===== UTILITY FUNCTIONS =====

def create_test_manager(manager_class, console=None, clients=None, cache=None):
    """Create a test instance of a manager class."""
    console = console or Mock(spec=Console)
    clients = clients or Mock()
    cache = cache or {}

    return manager_class(console, clients, cache)


async def run_async_test(coro):
    """Helper to run async test functions."""
    import asyncio
    return await asyncio.create_task(coro)


def mock_rich_console():
    """Create a properly mocked Rich console."""
    console = Mock(spec=Console)
    console.print = Mock()
    console.status = Mock()
    console.status.return_value.__enter__ = Mock(return_value=Mock())
    console.status.return_value.__exit__ = Mock(return_value=None)
    return console


def patch_multiple(*patches):
    """Helper to apply multiple patches at once."""
    def decorator(func):
        for patch_args in reversed(patches):
            if isinstance(patch_args, tuple):
                func = patch(*patch_args)(func)
            else:
                func = patch(patch_args)(func)
        return func
    return decorator


# ===== COMMON ASSERTIONS =====

def assert_imports_work(*imports):
    """Assert that a list of imports work without errors."""
    for import_item in imports:
        assert import_item is not None, f"Import failed: {import_item}"


def assert_no_circular_imports():
    """Assert that there are no circular import issues in the CLI module."""
    try:
        # Try importing various CLI modules to detect circular imports
        from services.cli.modules.base import BaseManager
        from services.cli.modules.managers import OrchestratorManager
        from services.cli.modules.utils import CacheManager, APIClient
        from services.cli.modules.formatters import DisplayManager

        # If we get here without ImportError, no circular imports
        assert BaseManager is not None
        assert OrchestratorManager is not None
        assert CacheManager is not None
        assert APIClient is not None
        assert DisplayManager is not None

    except ImportError as e:
        pytest.fail(f"Circular import detected: {e}")


def assert_class_inheritance(obj, base_class):
    """Assert that an object's class properly inherits from a base class."""
    assert isinstance(obj, base_class), f"{obj.__class__.__name__} does not inherit from {base_class.__name__}"


def assert_method_exists(obj, method_name):
    """Assert that an object has a specific method."""
    assert hasattr(obj, method_name), f"{obj.__class__.__name__} missing method: {method_name}"
    assert callable(getattr(obj, method_name)), f"{obj.__class__.__name__}.{method_name} is not callable"


# ===== TEST ASSERTION MIXINS =====

class CLIAssertionMixin:
    """Mixin providing common CLI-specific assertions."""

    def assert_cli_service_initialized(self, service):
        """Assert that a CLI service is properly initialized."""
        assert service is not None, "CLI service should not be None"
        assert hasattr(service, 'console'), "CLI service should have console attribute"
        assert hasattr(service, 'clients'), "CLI service should have clients attribute"
        assert hasattr(service, 'current_user'), "CLI service should have current_user attribute"
        assert hasattr(service, 'session_id'), "CLI service should have session_id attribute"
        assert service.current_user is not None, "CLI service current_user should not be None"
        assert service.session_id is not None, "CLI service session_id should not be None"
        assert service.console is not None, "CLI service console should not be None"
        assert service.clients is not None, "CLI service clients should not be None"

    def assert_health_response_structure(self, health_data):
        """Assert that health response has correct structure."""
        assert isinstance(health_data, dict), "Health data should be a dictionary"
        assert len(health_data) > 0, "Health data should not be empty"

        expected_services = ["orchestrator", "prompt-store", "source-agent", "analysis-service", "doc-store"]
        for service in expected_services:
            assert service in health_data, f"Health data should include {service}"

        for service, data in health_data.items():
            assert "status" in data, f"Service {service} should have status"
            assert "timestamp" in data, f"Service {service} should have timestamp"
            assert data["status"] in ["healthy", "unhealthy"], f"Service {service} status should be healthy or unhealthy"

    def assert_api_response_success(self, response, expected_keys=None):
        """Assert that an API response indicates success."""
        assert response is not None, "API response should not be None"
        assert isinstance(response, dict), "API response should be a dictionary"

        if expected_keys:
            for key in expected_keys:
                assert key in response, f"API response should contain key: {key}"

    def assert_menu_display_called(self, mock_console, expected_title=None):
        """Assert that menu display methods were called."""
        assert mock_console.print.called, "Console print should have been called for menu display"

        if expected_title:
            # Check that the title was included in one of the print calls
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any(expected_title in call for call in print_calls), f"Menu title '{expected_title}' should have been displayed"


class ManagerAssertionMixin:
    """Mixin providing common manager-specific assertions."""

    def assert_manager_implements_interface(self, manager):
        """Assert that a manager implements the BaseManager interface."""
        from services.cli.modules.base.base_manager import BaseManager
        assert_class_inheritance(manager, BaseManager)

        # Check required attributes
        assert hasattr(manager, 'console'), "Manager should have console attribute"
        assert hasattr(manager, 'clients'), "Manager should have clients attribute"
        assert hasattr(manager, 'cache_manager'), "Manager should have cache_manager attribute"
        assert hasattr(manager, 'display'), "Manager should have display attribute"

        # Check required methods
        assert_method_exists(manager, 'get_main_menu')
        assert_method_exists(manager, 'handle_choice')
        assert_method_exists(manager, 'run_menu_loop')

    def assert_manager_initialization_complete(self, manager, console, clients, cache=None):
        """Assert that manager initialization is complete."""
        assert manager.console is console, "Manager console should be set correctly"
        assert manager.clients is clients, "Manager clients should be set correctly"
        assert manager.cache_manager is not None, "Manager should have cache_manager"
        assert manager.display is not None, "Manager should have display"
        assert manager.api_client is not None, "Manager should have api_client"

        if cache is not None:
            assert manager.cache is cache, "Manager cache should be set correctly"

    def assert_menu_structure_valid(self, menu_items):
        """Assert that menu items have valid structure."""
        assert isinstance(menu_items, list), "Menu items should be a list"
        assert len(menu_items) > 0, "Menu should have at least one item"

        for item in menu_items:
            assert isinstance(item, tuple), "Menu item should be a tuple"
            assert len(item) == 2, "Menu item should have exactly 2 elements"
            assert isinstance(item[0], str), "Menu item option should be a string"
            assert isinstance(item[1], str), "Menu item description should be a string"
            assert len(item[0]) > 0, "Menu item option should not be empty"
            assert len(item[1]) > 0, "Menu item description should not be empty"


class ValidationAssertionMixin:
    """Mixin providing common validation assertions."""

    def assert_validation_error_raised(self, func, *args, expected_error=None, **kwargs):
        """Assert that a validation error is raised."""
        with pytest.raises((ValueError, AssertionError, TypeError)) as exc_info:
            func(*args, **kwargs)

        if expected_error:
            assert expected_error in str(exc_info.value), f"Error message should contain: {expected_error}"

    def assert_parameter_validation(self, func, invalid_params, expected_error_contains=None):
        """Assert that parameter validation works correctly."""
        for invalid_param in invalid_params:
            with pytest.raises((ValueError, TypeError, AssertionError)) as exc_info:
                func(**invalid_param)

            if expected_error_contains:
                assert expected_error_contains in str(exc_info.value), f"Error should contain: {expected_error_contains}"

    def assert_required_params_validated(self, func, required_params):
        """Assert that required parameters are validated."""
        for param in required_params:
            # Test with parameter missing
            incomplete_params = {k: v for k, v in required_params.items() if k != param}
            with pytest.raises((ValueError, AssertionError)) as exc_info:
                func(**incomplete_params)

            assert "Missing required parameters" in str(exc_info.value) or "required" in str(exc_info.value).lower()


class AsyncTestMixin:
    """Mixin providing common async test patterns."""

    async def assert_async_operation_completes(self, coro, timeout=5.0):
        """Assert that an async operation completes within timeout."""
        import asyncio

        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            pytest.fail(f"Async operation did not complete within {timeout} seconds")

    async def assert_async_method_called(self, mock_obj, method_name, expected_calls=1):
        """Assert that an async method was called the expected number of times."""
        assert getattr(mock_obj, method_name).call_count == expected_calls, \
            f"Method {method_name} should have been called {expected_calls} times, " \
            f"but was called {getattr(mock_obj, method_name).call_count} times"


# mock_console is now in conftest.py
