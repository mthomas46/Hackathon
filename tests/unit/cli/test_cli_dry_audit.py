"""Test CLI DRY improvements and structure audit.

Tests the key improvements made to eliminate code duplication and improve stability.
"""

import pytest
from unittest.mock import Mock, patch
from rich.console import Console

from services.cli.modules.managers import (
    OrchestratorManager, ConfigManager, WorkflowManager, PromptManager
)
from services.cli.modules.base.base_manager import BaseManager
from services.cli.modules.utils.cache_utils import CacheManager
from services.cli.modules.utils.api_utils import APIClient


class TestDRYImprovements:
    """Test DRY (Don't Repeat Yourself) improvements."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    @pytest.fixture
    def mock_clients(self):
        """Mock service clients."""
        return Mock()

    def test_menu_loop_dry_implementation(self, mock_console, mock_clients):
        """Test that menu loop DRY implementation works across managers."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Verify the DRY menu loop method exists
        assert hasattr(manager, 'run_menu_loop')
        assert callable(manager.run_menu_loop)

        # Verify it inherits from BaseManager
        assert isinstance(manager, BaseManager)

    def test_base_manager_inheritance_consistency(self, mock_console, mock_clients):
        """Test that all managers consistently inherit from BaseManager."""
        managers = [
            OrchestratorManager(mock_console, mock_clients),
            WorkflowManager(mock_console, mock_clients),
            PromptManager(mock_console, mock_clients)
        ]

        for manager in managers:
            # All should inherit from BaseManager
            assert isinstance(manager, BaseManager)

            # All should have the DRY methods
            assert hasattr(manager, 'run_menu_loop')
            assert hasattr(manager, 'confirm_action')
            assert hasattr(manager, 'get_user_input')
            assert hasattr(manager, 'select_from_list')
            assert hasattr(manager, 'cache_manager')
            assert hasattr(manager, 'display')

            # All should have proper initialization
            assert manager.console == mock_console
            assert manager.clients == mock_clients

    def test_cache_manager_dry_implementation(self, mock_console, mock_clients):
        """Test that cache manager is consistently used across managers."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should have cache manager from BaseManager
        assert isinstance(manager.cache_manager, CacheManager)

        # Should be able to use cache operations
        assert hasattr(manager, 'cache_get')
        assert hasattr(manager, 'cache_set')

    def test_display_manager_dry_implementation(self, mock_console, mock_clients):
        """Test that display manager provides consistent interface."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should have display manager with consistent methods
        display_methods = ['show_success', 'show_error', 'show_warning', 'show_info', 'show_table']
        for method in display_methods:
            assert hasattr(manager.display, method)

    def test_error_handling_dry_patterns(self, mock_console, mock_clients):
        """Test that error handling follows DRY patterns."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should have run_with_progress that handles errors consistently
        assert hasattr(manager, 'run_with_progress')

    def test_menu_structure_dry_patterns(self, mock_console, mock_clients):
        """Test that menu structures follow DRY patterns."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should have get_main_menu method (inherited or implemented)
        assert hasattr(manager, 'get_main_menu') or hasattr(manager, 'orchestrator_management_menu')

        # Should have handle_choice method
        assert hasattr(manager, 'handle_choice')


class TestStabilityImprovements:
    """Test stability improvements from DRY refactoring."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    @pytest.fixture
    def mock_clients(self):
        """Mock service clients."""
        return Mock()

    def test_manager_initialization_stability(self, mock_console, mock_clients):
        """Test that manager initialization is stable."""
        # Should be able to create multiple managers without issues
        managers = []
        for _ in range(5):
            manager = OrchestratorManager(mock_console, mock_clients)
            managers.append(manager)

        # All should be properly initialized
        for manager in managers:
            assert isinstance(manager, BaseManager)
            assert manager.console == mock_console
            assert manager.clients == mock_clients

    def test_cache_operations_stability(self, mock_console, mock_clients):
        """Test that cache operations are stable."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should be able to perform cache operations without errors
        import asyncio

        async def test_cache():
            await manager.cache_set("test_key", "test_value")
            result = await manager.cache_get("test_key")
            assert result == "test_value"

        # Run the async test
        asyncio.run(test_cache())

    def test_base_class_method_stability(self, mock_console, mock_clients):
        """Test that base class methods are stable."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Test synchronous methods don't crash
        manager.display.show_info("Test message")
        manager.display.show_success("Test success")
        manager.display.show_error("Test error")
        manager.display.show_warning("Test warning")

        # Test log operation
        manager.log_operation("test_operation", param="value")

    def test_import_structure_stability(self):
        """Test that import structure is stable."""
        # Should be able to import all managers without issues
        from services.cli.modules.managers.services import (
            OrchestratorManager, AnalysisManager, DocStoreManager
        )

        # Should be able to import base classes
        from services.cli.modules.base import BaseManager

        # Should be able to import utilities
        from services.cli.modules.utils import CacheManager, APIClient

        # All imports should succeed
        assert OrchestratorManager is not None
        assert BaseManager is not None
        assert CacheManager is not None
        assert APIClient is not None


class TestStructureAudit:
    """Test that the reorganized structure follows best practices."""

    def test_directory_structure_logical(self):
        """Test that directory structure is logical."""
        import os

        base_path = "services/cli/modules"

        # Check that key directories exist
        assert os.path.exists(f"{base_path}/base")
        assert os.path.exists(f"{base_path}/managers")
        assert os.path.exists(f"{base_path}/handlers")
        assert os.path.exists(f"{base_path}/utils")
        assert os.path.exists(f"{base_path}/formatters")
        assert os.path.exists(f"{base_path}/models")

        # Check subdirectories
        assert os.path.exists(f"{base_path}/managers/services")
        assert os.path.exists(f"{base_path}/managers/config")
        assert os.path.exists(f"{base_path}/managers/analysis")
        assert os.path.exists(f"{base_path}/managers/monitoring")

    def test_file_naming_consistency(self):
        """Test that file naming follows consistent patterns."""
        import os
        import glob

        base_path = "services/cli/modules"

        # Check that manager files follow naming convention
        manager_files = glob.glob(f"{base_path}/managers/services/*_manager.py")
        assert len(manager_files) > 0

        for file_path in manager_files:
            filename = os.path.basename(file_path)
            # Should end with _manager.py
            assert filename.endswith("_manager.py")

    def test_import_hierarchy_clean(self):
        """Test that import hierarchy is clean and follows DRY principles."""
        # Should be able to import from top level
        from services.cli.modules.managers import OrchestratorManager

        # Should be able to import from submodules
        from services.cli.modules.managers.services import OrchestratorManager as DirectOrchestrator

        # Both should be the same class
        assert OrchestratorManager is DirectOrchestrator

    def test_no_circular_imports(self):
        """Test that there are no circular import issues."""
        # This test will fail if there are circular imports
        try:
            from services.cli.modules.cli_commands import CLICommands
            from services.cli.modules.managers import ConfigManager, WorkflowManager
            from services.cli.modules.utils import CacheManager, APIClient

            # If we get here without ImportError, no circular imports
            assert CLICommands is not None
            assert ConfigManager is not None
            assert WorkflowManager is not None
            assert CacheManager is not None
            assert APIClient is not None

        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")


class TestDRYBenefits:
    """Test the benefits achieved by DRY improvements."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    @pytest.fixture
    def mock_clients(self):
        """Mock service clients."""
        return Mock()

    def test_menu_loop_reuse(self, mock_console, mock_clients):
        """Test that menu loop can be reused across different contexts."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should be able to call run_menu_loop multiple times with different menus
        menu1 = [("1", "Option 1")]
        menu2 = [("1", "Choice 1"), ("2", "Choice 2")]

        # This demonstrates the DRY benefit - same method handles different menus
        assert hasattr(manager, 'run_menu_loop')

        # Method should accept different menu configurations
        import inspect
        sig = inspect.signature(manager.run_menu_loop)
        params = list(sig.parameters.keys())

        # Should accept title, menu_items, back_option
        assert 'title' in params
        assert 'menu_items' in params
        assert 'back_option' in params

    def test_cache_reuse_across_managers(self, mock_console, mock_clients):
        """Test that cache functionality is reused across managers."""
        manager1 = OrchestratorManager(mock_console, mock_clients)
        manager2 = WorkflowManager(mock_console, mock_clients)

        # Both should have same cache interface
        assert hasattr(manager1, 'cache_get')
        assert hasattr(manager1, 'cache_set')
        assert hasattr(manager2, 'cache_get')
        assert hasattr(manager2, 'cache_set')

        # Should be using the same CacheManager implementation
        assert isinstance(manager1.cache_manager, CacheManager)
        assert isinstance(manager2.cache_manager, CacheManager)

    def test_display_reuse_across_managers(self, mock_console, mock_clients):
        """Test that display functionality is reused across managers."""
        manager1 = OrchestratorManager(mock_console, mock_clients)
        manager2 = PromptManager(mock_console, mock_clients)

        # Both should have same display interface
        display_methods = ['show_success', 'show_error', 'show_warning', 'show_info']
        for method in display_methods:
            assert hasattr(manager1.display, method)
            assert hasattr(manager2.display, method)

    def test_error_handling_reuse(self, mock_console, mock_clients):
        """Test that error handling is reused across managers."""
        manager = OrchestratorManager(mock_console, mock_clients)

        # Should have consistent error handling through run_with_progress
        assert hasattr(manager, 'run_with_progress')

        # Should have proper error context
        assert hasattr(manager, 'log_operation')
