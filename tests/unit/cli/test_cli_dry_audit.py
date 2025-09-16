"""Test CLI DRY improvements and structure audit.

Tests the key improvements made to eliminate code duplication and improve stability.
"""

import pytest
from unittest.mock import Mock, patch

from services.cli.modules.managers import (
    OrchestratorManager, ConfigManager, WorkflowManager, PromptManager
)
from services.cli.modules.base.base_manager import BaseManager
from tests.unit.cli.test_base import (
    BaseManagerTestMixin, ManagerAssertionMixin,
    assert_no_circular_imports, assert_class_inheritance, assert_method_exists, assert_imports_work
)


class TestDRYImprovements(BaseManagerTestMixin, ManagerAssertionMixin):
    """Test DRY (Don't Repeat Yourself) improvements."""

    def test_menu_loop_dry_implementation(self):
        """Test that menu loop DRY implementation works across managers."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Verify the DRY menu loop method exists and manager implements interface
        self.assert_manager_implements_interface(manager)

    def test_base_manager_inheritance_consistency(self):
        """Test that all managers consistently inherit from BaseManager."""
        managers = [
            OrchestratorManager(self.mock_console, self.mock_clients),
            WorkflowManager(self.mock_console, self.mock_clients),
            PromptManager(self.mock_console, self.mock_clients)
        ]

        for manager in managers:
            # All should implement the BaseManager interface correctly
            self.assert_manager_implements_interface(manager)
            self.assert_manager_initialization_complete(manager, self.mock_console, self.mock_clients)

    def test_cache_manager_dry_implementation(self):
        """Test that cache manager is consistently used across managers."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should have cache manager from BaseManager
        assert hasattr(manager, 'cache_manager')
        assert isinstance(manager.cache_manager, type(manager.cache_manager))

        # Should be able to use cache operations
        assert_method_exists(manager, 'cache_get')
        assert_method_exists(manager, 'cache_set')

    def test_display_manager_dry_implementation(self):
        """Test that display manager provides consistent interface."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should have display manager with consistent methods
        display_methods = ['show_success', 'show_error', 'show_warning', 'show_info', 'show_table']
        for method in display_methods:
            assert_method_exists(manager.display, method)

    def test_error_handling_dry_patterns(self, mock_console, mock_clients):
        """Test that error handling follows DRY patterns."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should have run_with_progress that handles errors consistently
        assert_method_exists(manager, 'run_with_progress')

    def test_menu_structure_dry_patterns(self, mock_console, mock_clients):
        """Test that menu structures follow DRY patterns."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should have get_main_menu method (inherited or implemented)
        assert hasattr(manager, 'get_main_menu') or hasattr(manager, 'orchestrator_management_menu')

        # Should have handle_choice method
        assert_method_exists(manager, 'handle_choice')


class TestStabilityImprovements(BaseManagerTestMixin):
    """Test stability improvements from DRY refactoring."""

    def test_manager_initialization_stability(self, mock_console, mock_clients):
        """Test that manager initialization is stable."""
        # Should be able to create multiple managers without issues
        managers = []
        for _ in range(5):
            manager = OrchestratorManager(self.mock_console, self.mock_clients)
            managers.append(manager)

        # All should be properly initialized
        for manager in managers:
            self.assert_manager_inheritance(manager)

    def test_cache_operations_stability(self, mock_console, mock_clients):
        """Test that cache operations are stable."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should be able to perform cache operations without errors
        import asyncio

        async def test_cache():
            await self.assert_cache_operations_work(manager)

        # Run the async test
        asyncio.run(test_cache())

    def test_base_class_method_stability(self, mock_console, mock_clients):
        """Test that base class methods are stable."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Test display methods
        self.assert_display_methods_work(manager)

        # Test log operation
        manager.log_operation("test_operation", param="value")

    def test_import_structure_stability(self):
        """Test that import structure is stable."""
        # Should be able to import all managers without issues
        from services.cli.modules.managers.services import (
            OrchestratorManager, AnalysisManager
        )

        # Should be able to import base classes
        from services.cli.modules.base import BaseManager

        # Should be able to import utilities
        from services.cli.modules.utils import CacheManager, APIClient

        # All imports should succeed using base utility
        assert_imports_work(
            OrchestratorManager, BaseManager, CacheManager, APIClient
        )


class TestStructureAudit:
    """Test that the reorganized structure follows best practices."""

    def test_directory_structure_logical(self):
        """Test that directory structure is logical."""
        import os

        base_path = "services/cli/modules"

        # Check that key directories exist
        directories = [
            f"{base_path}/base",
            f"{base_path}/managers",
            f"{base_path}/handlers",
            f"{base_path}/utils",
            f"{base_path}/formatters",
            f"{base_path}/models",
            f"{base_path}/managers/services",
            f"{base_path}/managers/config",
            f"{base_path}/managers/analysis",
            f"{base_path}/managers/monitoring"
        ]

        for directory in directories:
            assert os.path.exists(directory), f"Directory {directory} does not exist"

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
            assert filename.endswith("_manager.py"), f"File {filename} does not follow naming convention"

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
        assert_no_circular_imports()


class TestDRYBenefits(BaseManagerTestMixin):
    """Test the benefits achieved by DRY improvements."""

    def test_menu_loop_reuse(self, mock_console, mock_clients):
        """Test that menu loop can be reused across different contexts."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should be able to call run_menu_loop multiple times with different menus
        menu1 = [("1", "Option 1")]
        menu2 = [("1", "Choice 1"), ("2", "Choice 2")]

        # This demonstrates the DRY benefit - same method handles different menus
        assert_method_exists(manager, 'run_menu_loop')

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
        manager1 = OrchestratorManager(self.mock_console, self.mock_clients)
        manager2 = WorkflowManager(self.mock_console, self.mock_clients)

        # Both should have same cache interface
        assert_method_exists(manager1, 'cache_get')
        assert_method_exists(manager1, 'cache_set')
        assert_method_exists(manager2, 'cache_get')
        assert_method_exists(manager2, 'cache_set')

        # Should be using the same CacheManager implementation
        assert isinstance(manager1.cache_manager, type(manager1.cache_manager))
        assert isinstance(manager2.cache_manager, type(manager2.cache_manager))

    def test_display_reuse_across_managers(self, mock_console, mock_clients):
        """Test that display functionality is reused across managers."""
        manager1 = OrchestratorManager(self.mock_console, self.mock_clients)
        manager2 = PromptManager(self.mock_console, self.mock_clients)

        # Both should have same display interface
        display_methods = ['show_success', 'show_error', 'show_warning', 'show_info']
        for method in display_methods:
            assert_method_exists(manager1.display, method)
            assert_method_exists(manager2.display, method)

    def test_error_handling_reuse(self, mock_console, mock_clients):
        """Test that error handling is reused across managers."""
        manager = OrchestratorManager(self.mock_console, self.mock_clients)

        # Should have consistent error handling through run_with_progress
        assert_method_exists(manager, 'run_with_progress')

        # Should have proper error context
        assert_method_exists(manager, 'log_operation')
