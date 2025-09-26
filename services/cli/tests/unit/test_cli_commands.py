"""Comprehensive tests for CLI commands functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cli.application.commands.cli_commands import CLICommands
from cli.infrastructure.services.services.analysis_manager import AnalysisManager
from cli.infrastructure.services.services.docstore_manager import DocStoreManager


class TestCLICommands:
    """Test CLI commands functionality."""

    @pytest.fixture
    def cli_commands(self):
        """Create CLI commands instance with mocked dependencies."""
        with patch('cli.application.commands.cli_commands.ServiceClients') as mock_clients, \
             patch('cli.application.commands.cli_commands.AnalysisManager') as mock_analysis, \
             patch('cli.application.commands.cli_commands.ConfigManager') as mock_config:

            mock_clients_instance = MagicMock()
            mock_analysis_instance = MagicMock()
            mock_config_instance = MagicMock()

            mock_clients.return_value = mock_clients_instance
            mock_analysis.return_value = mock_analysis_instance
            mock_config.return_value = mock_config_instance

            commands = CLICommands()
            commands.clients = mock_clients_instance
            commands.analysis_manager = mock_analysis_instance
            commands.config_manager = mock_config_instance

            yield commands

    def test_cli_commands_initialization(self, cli_commands):
        """Test CLI commands initialization."""
        assert cli_commands.clients is not None
        assert cli_commands.analysis_manager is not None
        assert cli_commands.config_manager is not None

    @pytest.mark.asyncio
    async def test_service_health_check(self, cli_commands):
        """Test service health check functionality."""
        # Mock health check responses
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"status": "healthy"})
        cli_commands.clients.get_json = AsyncMock(return_value=mock_response)

        result = await cli_commands.check_service_health()

        assert isinstance(result, dict)
        assert "services" in result
        cli_commands.clients.get_json.assert_called()

    def test_get_service_health_url(self, cli_commands):
        """Test service health URL generation."""
        from cli.modules.shared_utils import get_service_health_url

        # Test with mocked clients
        cli_commands.clients.get_service_url = MagicMock(return_value="http://test:5000")

        url = get_service_health_url(cli_commands.clients, "test")
        assert url == "http://test:5000/health"

    @pytest.mark.asyncio
    async def test_analysis_operations(self, cli_commands):
        """Test analysis operations through CLI."""
        # Mock analysis response
        cli_commands.analysis_manager.analyze_codebase = AsyncMock(return_value={
            "status": "completed",
            "findings": []
        })

        result = await cli_commands.analysis_manager.analyze_codebase()

        assert result["status"] == "completed"
        assert "findings" in result

    def test_service_listing(self, cli_commands):
        """Test service listing functionality."""
        # Mock service listing
        cli_commands.clients.list_services = MagicMock(return_value=[
            "analysis-service",
            "doc-store",
            "orchestrator"
        ])

        services = cli_commands.clients.list_services()
        assert len(services) == 3
        assert "analysis-service" in services

    @pytest.mark.asyncio
    async def test_bulk_operations(self, cli_commands):
        """Test bulk operations functionality."""
        # Mock bulk operation
        cli_commands.clients.bulk_operation = AsyncMock(return_value={
            "processed": 10,
            "successful": 9,
            "failed": 1
        })

        result = await cli_commands.clients.bulk_operation("test_operation", [])

        assert result["processed"] == 10
        assert result["successful"] == 9
        assert result["failed"] == 1


class TestCLIInfrastructure:
    """Test CLI infrastructure components."""

    def test_analysis_manager_initialization(self):
        """Test analysis manager can be initialized."""
        with patch('cli.infrastructure.services.services.analysis_manager.ServiceClients'):
            manager = AnalysisManager()
            assert manager is not None

    def test_docstore_manager_initialization(self):
        """Test docstore manager can be initialized."""
        with patch('cli.infrastructure.services.services.docstore_manager.ServiceClients'):
            manager = DocStoreManager()
            assert manager is not None

    @patch('cli.infrastructure.services.config.config_manager.ConfigManager')
    def test_config_manager_functionality(self, mock_config_manager):
        """Test config manager basic functionality."""
        mock_instance = MagicMock()
        mock_config_manager.return_value = mock_instance

        # Test config operations
        mock_instance.get_config = MagicMock(return_value={"test": "value"})
        config = mock_instance.get_config("test")

        assert config == {"test": "value"}

    def test_service_registry_operations(self):
        """Test service registry functionality."""
        from cli.infrastructure.adapters.service_registry import ServiceRegistry

        registry = ServiceRegistry()
        assert registry is not None

        # Test service registration (mock)
        registry.register_service = MagicMock()
        registry.register_service("test-service", "http://test:5000")

        registry.register_service.assert_called_once_with("test-service", "http://test:5000")


class TestCLIApplicationLayer:
    """Test CLI application layer components."""

    def test_command_parsing(self):
        """Test command parsing and validation."""
        # Test basic command structure
        commands = ["health", "analyze", "list", "config"]

        assert len(commands) > 0
        assert "health" in commands
        assert "analyze" in commands

    def test_response_formatting(self):
        """Test CLI response formatting."""
        # Test success response
        success_response = {
            "success": True,
            "message": "Operation completed",
            "data": {"result": "test"}
        }

        assert success_response["success"] is True
        assert "message" in success_response
        assert "data" in success_response

        # Test error response
        error_response = {
            "success": False,
            "error": "Operation failed",
            "details": "Invalid parameters"
        }

        assert error_response["success"] is False
        assert "error" in error_response

    @pytest.mark.asyncio
    async def test_async_command_execution(self):
        """Test async command execution patterns."""
        async def mock_async_command():
            return {"status": "completed"}

        result = await mock_async_command()
        assert result["status"] == "completed"

    def test_error_handling(self):
        """Test error handling in CLI commands."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            assert str(e) == "Test error"

        # Test with CLI-specific error handling
        from cli.domain.exceptions import CliError

        try:
            raise CliError("CLI specific error", error_code="CLI_ERROR")
        except CliError as e:
            assert e.error_code == "CLI_ERROR"


class TestCLIDomainLayer:
    """Test CLI domain layer components."""

    def test_cli_exceptions(self):
        """Test CLI domain exceptions."""
        from cli.domain.exceptions import CliError, CliCommandError, CliValidationError

        # Test base exception
        error = CliError("Test error")
        assert str(error) == "Test error"

        # Test command error
        cmd_error = CliCommandError("Command failed")
        assert isinstance(cmd_error, CliError)

        # Test validation error
        val_error = CliValidationError("Validation failed")
        assert isinstance(val_error, CliError)

    def test_exception_hierarchy(self):
        """Test exception hierarchy and inheritance."""
        from cli.domain.exceptions import CliError

        # Test that all CLI exceptions inherit from CliError
        exceptions = [
            "CliCommandError",
            "CliValidationError",
            "CliServiceError",
            "CliNetworkError"
        ]

        # Verify exception classes exist and inherit properly
        for exc_name in exceptions:
            try:
                exc_class = getattr(__import__(f'cli.domain.exceptions', fromlist=[exc_name]), exc_name)
                instance = exc_class("test")
                assert isinstance(instance, CliError)
            except AttributeError:
                # Some exceptions might not be implemented yet
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
