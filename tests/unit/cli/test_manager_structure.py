"""Tests for CLI manager structure and DRY patterns.

Tests the new manager organization and base class integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from rich.console import Console

from services.cli.modules.managers import (
    ConfigManager, AnalysisServiceManager, AdvancedMonitoringManager,
    OrchestratorManager, WorkflowManager, PromptManager
)
from services.cli.modules.base.base_manager import BaseManager


class TestManagerStructure:
    """Test manager structure and organization."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    @pytest.fixture
    def mock_clients(self):
        """Mock service clients."""
        return Mock()

    def test_manager_imports(self):
        """Test that all managers can be imported successfully."""
        # This test ensures the import structure works
        assert ConfigManager is not None
        assert AnalysisServiceManager is not None
        assert AdvancedMonitoringManager is not None
        assert OrchestratorManager is not None
        assert WorkflowManager is not None
        assert PromptManager is not None

    def test_service_manager_inheritance(self, mock_console, mock_clients):
        """Test that service managers inherit from BaseManager."""
        manager = OrchestratorManager(mock_console, mock_clients)
        assert isinstance(manager, BaseManager)
        assert hasattr(manager, 'console')
        assert hasattr(manager, 'clients')
        assert hasattr(manager, 'cache_manager')
        assert hasattr(manager, 'display')

    def test_config_manager_inheritance(self, mock_console, mock_clients):
        """Test that specialized managers inherit from BaseManager."""
        manager = ConfigManager(mock_console, mock_clients)
        assert isinstance(manager, BaseManager)

    def test_manager_initialization(self, mock_console, mock_clients):
        """Test manager initialization with proper base class setup."""
        manager = OrchestratorManager(mock_console, mock_clients)

        assert manager.console == mock_console
        assert manager.clients == mock_clients
        assert manager.cache_manager is not None
        assert manager.display is not None

    @pytest.mark.asyncio
    async def test_menu_loop_integration(self, mock_console, mock_clients):
        """Test that managers integrate with the new menu loop system."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Mock the menu loop to avoid actual user interaction
        menu_items = [("1", "Test Option")]

        with patch.object(manager, 'handle_choice', return_value=True) as mock_handle:
            with patch('rich.prompt.Prompt.ask', side_effect=["1", "b"]) as mock_prompt:
                await manager.run_menu_loop("Test Menu", menu_items)

                # Should call handle_choice with "1"
                mock_handle.assert_called_once_with("1")

    @pytest.mark.asyncio
    async def test_orchestrator_menu_integration(self, mock_console, mock_clients):
        """Test orchestrator manager menu integration."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Mock the submenu methods to avoid full execution
        with patch.object(manager, 'workflow_management_menu') as mock_workflow:
            with patch.object(manager, 'handle_choice', return_value=True):
                with patch('rich.prompt.Prompt.ask', side_effect=["1", "b"]):
                    await manager.orchestrator_management_menu()

                    # Should call the workflow menu
                    mock_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_cache_integration(self, mock_console, mock_clients):
        """Test manager cache integration."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Test cache operations through base manager
        await manager.cache_set("test_key", "test_value")
        result = await manager.cache_get("test_key")

        assert result == "test_value"

    def test_manager_display_integration(self, mock_console, mock_clients):
        """Test manager display integration."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Test display methods through base manager
        manager.display.show_success("Test success")
        manager.display.show_error("Test error")
        manager.display.show_warning("Test warning")
        manager.display.show_info("Test info")

        # Verify console was called (mock verification would be more complex)
        # For now, just ensure the display object exists
        assert manager.display is not None

    @pytest.mark.asyncio
    async def test_manager_error_handling(self, mock_console, mock_clients):
        """Test manager error handling through base class."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Mock a failing operation
        async def failing_operation():
            raise ValueError("Test error")

        # Should handle error gracefully through base manager
        with pytest.raises(ValueError):
            await manager.run_with_progress(failing_operation(), "Test operation")

    def test_workflow_manager_standalone(self, mock_console, mock_clients):
        """Test workflow manager as standalone component."""
        manager = WorkflowManager(mock_console, mock_clients)

        assert isinstance(manager, BaseManager)
        assert hasattr(manager, 'workflow_orchestration_menu')

    def test_prompt_manager_standalone(self, mock_console, mock_clients):
        """Test prompt manager as standalone component."""
        manager = PromptManager(mock_console, mock_clients)

        assert isinstance(manager, BaseManager)
        assert hasattr(manager, 'prompt_management_menu')


class TestDRYPatterns:
    """Test DRY patterns across managers."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    @pytest.fixture
    def mock_clients(self):
        """Mock service clients."""
        return Mock()

    def test_common_menu_structure(self, mock_console, mock_clients):
        """Test that managers follow common menu patterns."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should have standard menu loop method from BaseManager
        assert hasattr(manager, 'run_menu_loop')

        # Should have handle_choice method
        assert hasattr(manager, 'handle_choice')

    @pytest.mark.asyncio
    async def test_consistent_error_handling(self, mock_console, mock_clients):
        """Test consistent error handling across managers."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Test that all managers handle errors through the same base mechanism
        async def test_operation():
            return "success"

        result = await manager.run_with_progress(test_operation(), "Test")
        assert result == "success"

    def test_shared_utility_access(self, mock_console, mock_clients):
        """Test that managers have access to shared utilities."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should have access to cache manager
        assert hasattr(manager, 'cache_manager')

        # Should have access to display manager
        assert hasattr(manager, 'display')

        # Should have access to base utility methods
        assert hasattr(manager, 'confirm_action')
        assert hasattr(manager, 'get_user_input')
        assert hasattr(manager, 'select_from_list')

    @pytest.mark.asyncio
    async def test_menu_loop_reusability(self, mock_console, mock_clients):
        """Test that menu loop can be reused across different contexts."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Test with different menu configurations
        simple_menu = [("1", "Option 1")]
        complex_menu = [("1", "Option 1"), ("2", "Option 2"), ("3", "Option 3")]

        # Should work with both simple and complex menus
        with patch('rich.prompt.Prompt.ask', return_value="b"):
            await manager.run_menu_loop("Simple Menu", simple_menu)
            await manager.run_menu_loop("Complex Menu", complex_menu)


class TestManagerIntegration:
    """Test integration between different managers."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    @pytest.fixture
    def mock_clients(self):
        """Mock service clients."""
        return Mock()

    def test_manager_type_hierarchy(self, mock_console, mock_clients):
        """Test manager type hierarchy and relationships."""
        # Test that different manager types work together
        orchestrator = OrchestratorManager(mock_console, mock_clients)
        config = ConfigManager(mock_console, mock_clients)
        analysis = AnalysisServiceManager(mock_console, mock_clients)

        managers = [orchestrator, config, analysis]

        # All should be BaseManager instances
        for manager in managers:
            assert isinstance(manager, BaseManager)

        # All should have common interface
        for manager in managers:
            assert hasattr(manager, 'console')
            assert hasattr(manager, 'clients')
            assert hasattr(manager, 'run_menu_loop')

    @pytest.mark.asyncio
    async def test_shared_cache_between_managers(self, mock_console, mock_clients):
        """Test that managers can share cache when needed."""
        manager1 = OrchestratorManager(mock_console, mock_clients)
        manager2 = OrchestratorManager(mock_console, mock_clients)

        # Set cache on one manager
        await manager1.cache_set("shared_key", "shared_value")

        # Other manager should be able to access it (if using same cache instance)
        # Note: In this test setup, they have separate cache instances
        result1 = await manager1.cache_get("shared_key")
        result2 = await manager2.cache_get("shared_key")

        assert result1 == "shared_value"
        assert result2 is None  # Different cache instances

    def test_manager_method_consistency(self, mock_console, mock_clients):
        """Test that managers have consistent method signatures."""
        managers = [
            OrchestratorManager(mock_console, mock_clients),
            WorkflowManager(mock_console, mock_clients),
            PromptManager(mock_console, mock_clients)
        ]

        # All managers should have common BaseManager methods
        common_methods = ['confirm_action', 'get_user_input', 'select_from_list', 'run_menu_loop']

        for manager in managers:
            for method in common_methods:
                assert hasattr(manager, method), f"Manager {manager.__class__.__name__} missing method {method}"
