"""CLI workflow integration tests.

Tests complete CLI workflows from user interaction to service operations.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from click.testing import CliRunner
from rich.console import Console

from services.cli.modules.cli_commands import CLICommands
from services.cli.modules.managers import (
    OrchestratorManager, ConfigManager, WorkflowManager
)


@pytest.fixture
def mock_console():
    """Mock console for testing."""
    return Mock(spec=Console)


@pytest.fixture
def mock_clients():
    """Mock service clients."""
    return Mock()


@pytest.fixture
def cli_commands(mock_console, mock_clients):
    """CLICommands instance for testing."""
    return CLICommands()


class TestCLIWorkflowIntegration:
    """Test complete CLI workflow integration."""

    def test_cli_initialization(self, cli_commands):
        """Test CLI initialization."""
        assert cli_commands.current_user is not None
        assert cli_commands.session_id is not None
        assert cli_commands.console is not None
        assert cli_commands.clients is not None

    @pytest.mark.asyncio
    async def test_health_check_workflow(self, cli_commands, mock_clients):
        """Test complete health check workflow."""
        cli_commands.clients = mock_clients

        # Mock all service health responses
        mock_clients.get_json.side_effect = [
            {"overall_healthy": True},  # orchestrator
            {"status": "healthy"},      # prompt-store
            {"status": "healthy"},      # source-agent
            {"status": "healthy"},      # analysis-service
            {"status": "healthy"}       # doc_store
        ]

        health_data = await cli_commands.check_service_health()

        assert len(health_data) == 5
        assert "orchestrator" in health_data
        assert "prompt-store" in health_data
        assert "source-agent" in health_data
        assert "analysis-service" in health_data
        assert "doc_store" in health_data

    @pytest.mark.asyncio
    async def test_service_integration_workflow(self, cli_commands, mock_clients):
        """Test service integration testing workflow."""
        cli_commands.clients = mock_clients

        # Mock successful integration test responses
        mock_clients.get_json.side_effect = [
            {"status": "healthy"},      # prompt-store health
            {"status": "healthy"},      # interpreter health
            {"overall_healthy": True},  # orchestrator health
            {"integrations": ["doc_store"]},  # analysis health
            {"prompts": [{"id": "1"}]}, # prompt-store prompts
        ]

        mock_clients.post_json.side_effect = [
            {"intent": "analyze"},      # interpreter interpret
            {"interpretation": "test"}  # orchestrator query
        ]

        results = await cli_commands.test_integration()

        assert isinstance(results, dict)
        assert len(results) == 5  # 5 test categories

    def test_manager_instantiation(self, cli_commands):
        """Test that all managers are properly instantiated."""
        # Test that CLI commands has all expected managers
        expected_managers = [
            'orchestrator_manager',
            'analysis_manager',
            'docstore_manager',
            'source_agent_manager',
            'infrastructure_manager',
            'bulk_operations_manager',
            'interpreter_manager',
            'discovery_agent_manager',
            'memory_agent_manager',
            'secure_analyzer_manager',
            'summarizer_hub_manager',
            'code_analyzer_manager',
            'notification_service_manager',
            'log_collector_manager',
            'bedrock_proxy_manager',
            'deployment_manager',
            'architecture_digitizer_manager',
            'analysis_service_manager',
            'config_manager',
            'advanced_monitoring_manager'
        ]

        for manager_name in expected_managers:
            assert hasattr(cli_commands, manager_name), f"Missing manager: {manager_name}"
            manager = getattr(cli_commands, manager_name)
            assert manager is not None, f"Manager {manager_name} is None"

    def test_manager_type_validation(self, cli_commands):
        """Test that managers are of correct types."""
        from services.cli.modules.base.base_manager import BaseManager
        from services.cli.modules.managers.config.config_manager import ConfigManager
        from services.cli.modules.managers.analysis.analysis_service_manager import AnalysisServiceManager
        from services.cli.modules.managers.monitoring.advanced_monitoring_manager import AdvancedMonitoringManager

        # Test specialized managers
        assert isinstance(cli_commands.config_manager, ConfigManager)
        assert isinstance(cli_commands.analysis_service_manager, AnalysisServiceManager)
        assert isinstance(cli_commands.advanced_monitoring_manager, AdvancedMonitoringManager)

        # Test service managers inherit from BaseManager
        service_managers = [
            cli_commands.orchestrator_manager,
            cli_commands.analysis_manager,
            cli_commands.docstore_manager,
            cli_commands.source_agent_manager
        ]

        for manager in service_managers:
            assert isinstance(manager, BaseManager), f"Manager {manager.__class__.__name__} is not BaseManager instance"

    @pytest.mark.asyncio
    async def test_menu_navigation_workflow(self, cli_commands):
        """Test menu navigation workflow."""
        # Mock the main menu selection and submenu
        with patch.object(cli_commands, 'get_choice', side_effect=['1', 'q']):
            with patch.object(cli_commands, 'print_header'):
                with patch.object(cli_commands, 'print_menu'):
                    with patch.object(cli_commands.orchestrator_manager, 'orchestrator_management_menu') as mock_orchestrator_menu:
                        # Mock the orchestrator menu to avoid full execution
                        async def mock_menu():
                            pass
                        mock_orchestrator_menu.side_effect = mock_menu

                        await cli_commands.run()

                        # Should have called orchestrator menu
                        mock_orchestrator_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, cli_commands, mock_clients):
        """Test error recovery in CLI workflows."""
        cli_commands.clients = mock_clients

        # Mock service failures
        mock_clients.get_json.side_effect = Exception("Service unavailable")

        # Should handle errors gracefully
        try:
            await cli_commands.check_service_health()
        except Exception:
            # CLI should handle errors gracefully
            pass

        # CLI should still be functional after errors
        assert cli_commands.current_user is not None
        assert cli_commands.session_id is not None

    def test_cli_state_persistence(self, cli_commands):
        """Test CLI state persistence across operations."""
        initial_user = cli_commands.current_user
        initial_session = cli_commands.session_id

        # Simulate multiple operations
        cli_commands.print_header()
        cli_commands.print_menu()
        cli_commands.ab_testing_menu()

        # State should remain consistent
        assert cli_commands.current_user == initial_user
        assert cli_commands.session_id == initial_session


class TestDRYIntegrationWorkflow:
    """Test DRY patterns in complete CLI workflows."""

    def test_base_class_inheritance_consistency(self, cli_commands):
        """Test that all managers consistently inherit from BaseManager."""
        from services.cli.modules.base.base_manager import BaseManager

        # Get all manager attributes
        manager_attrs = [attr for attr in dir(cli_commands) if attr.endswith('_manager')]

        for attr_name in manager_attrs:
            manager = getattr(cli_commands, attr_name)
            assert isinstance(manager, BaseManager), f"Manager {attr_name} does not inherit from BaseManager"

    def test_common_interface_consistency(self, cli_commands):
        """Test that all managers have consistent interfaces."""
        # Common methods that all managers should have
        common_methods = ['confirm_action', 'get_user_input', 'select_from_list', 'run_menu_loop']

        manager_attrs = [attr for attr in dir(cli_commands) if attr.endswith('_manager')]

        for attr_name in manager_attrs:
            manager = getattr(cli_commands, attr_name)
            for method in common_methods:
                assert hasattr(manager, method), f"Manager {attr_name} missing method {method}"

    @pytest.mark.asyncio
    async def test_cache_sharing_workflow(self, cli_commands):
        """Test cache sharing across managers."""
        # Set cache value on one manager
        await cli_commands.orchestrator_manager.cache_set("workflow_key", "workflow_data")

        # Different managers should have independent caches (for now)
        result1 = await cli_commands.orchestrator_manager.cache_get("workflow_key")
        result2 = await cli_commands.config_manager.cache_get("workflow_key")

        assert result1 == "workflow_data"
        assert result2 is None  # Independent caches

    def test_display_consistency_workflow(self, cli_commands):
        """Test display consistency across all managers."""
        # All managers should have the same display interface
        display_methods = ['show_success', 'show_error', 'show_warning', 'show_info', 'show_table']

        manager_attrs = [attr for attr in dir(cli_commands) if attr.endswith('_manager')]

        for attr_name in manager_attrs:
            manager = getattr(cli_commands, attr_name)
            for method in display_methods:
                assert hasattr(manager.display, method), f"Manager {attr_name} display missing method {method}"

    @pytest.mark.asyncio
    async def test_progress_reporting_consistency(self, cli_commands):
        """Test progress reporting consistency."""
        async def test_operation():
            return "completed"

        # Test progress reporting on different managers
        result1 = await cli_commands.orchestrator_manager.run_with_progress(test_operation(), "Test 1")
        result2 = await cli_commands.config_manager.run_with_progress(test_operation(), "Test 2")

        assert result1 == "completed"
        assert result2 == "completed"


class TestEndToEndWorkflow:
    """Test end-to-end CLI workflows."""

    @pytest.mark.asyncio
    async def test_full_health_check_cycle(self, cli_commands, mock_clients):
        """Test complete health check cycle."""
        cli_commands.clients = mock_clients

        # Mock complete health check cycle
        mock_clients.get_json.side_effect = [
            {"overall_healthy": True, "services": 5},  # orchestrator
            {"status": "healthy", "uptime": "2h"},     # prompt-store
            {"status": "healthy", "version": "1.0"},   # source-agent
            {"status": "healthy", "models": ["gpt-4"]}, # analysis
            {"status": "healthy", "docs": 1000}        # doc_store
        ]

        # Execute full health check
        health_data = await cli_commands.check_service_health()

        # Verify complete health data structure
        assert len(health_data) == 5
        for service, data in health_data.items():
            assert "status" in data
            assert "timestamp" in data
            if data["status"] == "healthy":
                assert "response" in data

    @pytest.mark.asyncio
    async def test_full_integration_test_cycle(self, cli_commands, mock_clients):
        """Test complete integration test cycle."""
        cli_commands.clients = mock_clients

        # Mock complex integration test scenario
        mock_clients.get_json.side_effect = [
            {"status": "healthy", "connections": 5},    # prompt-store
            {"status": "healthy", "intents": 10},       # interpreter
            {"overall_healthy": True, "workflows": 8},  # orchestrator
            {"status": "healthy", "integrations": ["doc_store", "source-agent"]}, # analysis
            {"prompts": [{"id": "1", "content": "test"}]} # prompts
        ]

        mock_clients.post_json.side_effect = [
            {"intent": "analyze", "confidence": 0.95},   # interpreter
            {"interpretation": "system analysis complete"} # orchestrator
        ]

        # Execute full integration test
        results = await cli_commands.test_integration()

        # Verify comprehensive test results
        assert isinstance(results, dict)
        assert len(results) >= 5  # At least 5 test categories

        # Should have test results for key integrations
        expected_tests = [
            "Prompt Store Health",
            "Interpreter Integration",
            "Orchestrator Integration",
            "Analysis Service Integration"
        ]

        for test_name in expected_tests:
            assert test_name in results, f"Missing test result: {test_name}"

    def test_cli_lifecycle_management(self, cli_commands):
        """Test CLI lifecycle management."""
        # Test initialization
        assert cli_commands.current_user is not None

        # Test that CLI can handle multiple operations without state corruption
        for i in range(10):
            cli_commands.print_header()
            cli_commands.print_menu()

        # State should remain consistent
        assert cli_commands.current_user is not None
        assert cli_commands.session_id is not None

        # Console should still be accessible
        assert cli_commands.console is not None
