"""Tests for CLI manager structure and DRY patterns.

Tests the new manager organization and base class integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from services.cli.modules.managers import (
    ConfigManager, AnalysisServiceManager, AdvancedMonitoringManager,
    OrchestratorManager, WorkflowManager, PromptManager
)
from services.cli.modules.base.base_manager import BaseManager
from tests.unit.cli.test_base import (
    BaseManagerTestMixin, ManagerAssertionMixin,
    assert_class_inheritance, assert_method_exists
)


class TestManagerStructure(BaseManagerTestMixin, ManagerAssertionMixin):
    """Test manager structure and organization."""

    def test_manager_imports(self):
        """Test that all managers can be imported successfully."""
        # This test ensures the import structure works
        managers = [
            ConfigManager, AnalysisServiceManager, AdvancedMonitoringManager,
            OrchestratorManager, WorkflowManager, PromptManager
        ]

        for manager in managers:
            assert manager is not None

    def test_service_manager_inheritance(self):
        """Test that service managers inherit from BaseManager."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)
        assert_class_inheritance(manager, BaseManager)
        self.assert_manager_inheritance(manager)

    def test_config_manager_inheritance(self):
        """Test that specialized managers inherit from BaseManager."""
        manager = ConfigManager(self.mock_console, self.mock_clients)
        assert_class_inheritance(manager, BaseManager)

    def test_manager_initialization(self):
        """Test manager initialization with proper base class setup."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)
        self.assert_manager_initialization(manager, self.mock_console, self.mock_clients)

    @pytest.mark.asyncio
    async def test_menu_loop_integration(self):
        """Test that managers integrate with the new menu loop system."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)
        await self.assert_menu_loop_works(manager)

    @pytest.mark.asyncio
    async def test_orchestrator_menu_integration(self):
        """Test orchestrator manager menu integration."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Mock the submenu methods to avoid full execution
        with patch.object(manager, 'workflow_management_menu') as mock_workflow:
            with patch.object(manager, 'handle_choice', return_value=True):
                with patch('rich.prompt.Prompt.ask', side_effect=["1", "", "b"]):
                    await manager.orchestrator_management_menu()

                    # Should call the workflow menu
                    mock_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_manager_cache_integration(self):
        """Test manager cache integration."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)
        await self.assert_cache_operations_work(manager)

    def test_manager_display_integration(self):
        """Test manager display integration."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)
        self.assert_display_methods_work(manager)

    @pytest.mark.asyncio
    async def test_manager_error_handling(self):
        """Test manager error handling through base class."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Mock a failing operation
        async def failing_operation():
            raise ValueError("Test error")

        # Should handle error gracefully through base manager
        with pytest.raises(ValueError):
            await manager.run_with_progress(failing_operation(), "Test operation")

    def test_workflow_manager_standalone(self):
        """Test workflow manager as standalone component."""
        manager = WorkflowManager(self.mock_console, self.mock_clients)

        assert isinstance(manager, BaseManager)
        assert hasattr(manager, 'workflow_orchestration_menu')

    def test_prompt_manager_standalone(self):
        """Test prompt manager as standalone component."""
        manager = PromptManager(self.mock_console, self.mock_clients)

        assert isinstance(manager, BaseManager)
        assert hasattr(manager, 'prompt_management_menu')


class TestDRYPatterns(BaseManagerTestMixin):
    """Test DRY patterns across managers."""

    def test_common_menu_structure(self):
        """Test that managers follow common menu patterns."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should have standard menu loop method from BaseManager
        assert_method_exists(manager, 'run_menu_loop')

        # Should have handle_choice method
        assert_method_exists(manager, 'handle_choice')

    @pytest.mark.asyncio
    async def test_consistent_error_handling(self):
        """Test consistent error handling across managers."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Test that all managers handle errors through the same base mechanism
        async def test_operation():
            return "success"

        result = await manager.run_with_progress(test_operation(), "Test")
        assert result == "success"

    def test_shared_utility_access(self):
        """Test that managers have access to shared utilities."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should have access to cache manager
        assert hasattr(manager, 'cache_manager')

        # Should have access to display manager
        assert hasattr(manager, 'display')

        # Should have access to base utility methods
        assert_method_exists(manager, 'confirm_action')
        assert_method_exists(manager, 'get_user_input')
        assert_method_exists(manager, 'select_from_list')

    @pytest.mark.asyncio
    async def test_menu_loop_reusability(self):
        """Test that menu loop can be reused across different contexts."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Test with different menu configurations
        simple_menu = [("1", "Option 1")]
        complex_menu = [("1", "Option 1"), ("2", "Option 2"), ("3", "Option 3")]

        # Should work with both simple and complex menus
        with patch('rich.prompt.Prompt.ask', return_value="b"):
            await manager.run_menu_loop("Simple Menu", simple_menu)
            await manager.run_menu_loop("Complex Menu", complex_menu)


class TestManagerIntegration(BaseManagerTestMixin):
    """Test integration between different managers."""

    def test_manager_type_hierarchy(self):
        """Test manager type hierarchy and relationships."""
        # Test that different manager types work together
        orchestrator = OrchestratorManager(self.mock_console, self.mock_clients)
        config = ConfigManager(self.mock_console, self.mock_clients)
        analysis = AnalysisServiceManager(self.mock_console, self.mock_clients)

        managers = [orchestrator, config, analysis]

        # All should be BaseManager instances
        for manager in managers:
            assert_class_inheritance(manager, BaseManager)

    @pytest.mark.asyncio
    async def test_shared_cache_between_managers(self):
        """Test that managers can share cache when needed."""
        manager1 = OrchestratorManager(self.mock_console, self.mock_clients)
        manager2 = OrchestratorManager(self.mock_console, self.mock_clients)

        # Set cache on one manager
        await manager1.cache_set("shared_key", "shared_value")

        # Other manager should be able to access it (if using same cache instance)
        # Note: In this test setup, they have separate cache instances
        result1 = await manager1.cache_get("shared_key")
        result2 = await manager2.cache_get("shared_key")

        assert result1 == "shared_value"
        assert result2 is None  # Different cache instances

    def test_manager_method_consistency(self):
        """Test that managers have consistent method signatures."""
        managers = [
            OrchestratorManager(self.mock_console, self.mock_clients),
            WorkflowManager(self.mock_console, self.mock_clients),
            PromptManager(self.mock_console, self.mock_clients)
        ]

        # All managers should have common BaseManager methods
        common_methods = ['confirm_action', 'get_user_input', 'select_from_list', 'run_menu_loop']

        for manager in managers:
            for method in common_methods:
                assert_method_exists(manager, method)

    def test_manager_type_hierarchy(self):
        """Test manager type hierarchy and relationships."""
        # Test that different manager types work together
        orchestrator = OrchestratorManager(self.mock_console, self.mock_clients)
        config = ConfigManager(self.mock_console, self.mock_clients)
        analysis = AnalysisServiceManager(self.mock_console, self.mock_clients)

        managers = [orchestrator, config, analysis]

        # All should be BaseManager instances
        for manager in managers:
            assert_class_inheritance(manager, BaseManager)

        # All should have common interface
        for manager in managers:
            assert_method_exists(manager, 'console')
            assert_method_exists(manager, 'clients')
            assert_method_exists(manager, 'run_menu_loop')

    @pytest.mark.asyncio
    async def test_shared_cache_between_managers(self):
        """Test that managers can share cache when needed."""
        manager1 = OrchestratorManager(self.mock_console, self.mock_clients)
        manager2 = OrchestratorManager(self.mock_console, self.mock_clients)

        # Set cache on one manager
        await manager1.cache_set("shared_key", "shared_value")

        # Other manager should be able to access it (if using same cache instance)
        # Note: In this test setup, they have separate cache instances
        result1 = await manager1.cache_get("shared_key")
        result2 = await manager2.cache_get("shared_key")

        assert result1 == "shared_value"
        assert result2 is None  # Different cache instances

    def test_manager_method_consistency(self):
        """Test that managers have consistent method signatures."""
        managers = [
            OrchestratorManager(self.mock_console, self.mock_clients),
            WorkflowManager(self.mock_console, self.mock_clients),
            PromptManager(self.mock_console, self.mock_clients)
        ]

        # All managers should have common BaseManager methods
        common_methods = ['confirm_action', 'get_user_input', 'select_from_list', 'run_menu_loop']

        for manager in managers:
            for method in common_methods:
                assert hasattr(manager, method), f"Manager {manager.__class__.__name__} missing method {method}"
