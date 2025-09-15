"""Tests for CLI base classes (BaseManager, BaseFormatter, BaseHandler).

Tests core functionality, DRY patterns, and common behavior.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from rich.console import Console

from services.cli.modules.base.base_manager import BaseManager
from services.cli.modules.base.base_formatter import BaseFormatter
from services.cli.modules.base.base_handler import BaseHandler
from services.cli.modules.utils.cache_utils import CacheManager
from services.cli.modules.formatters.display_utils import DisplayManager


class TestBaseManager:
    """Test BaseManager core functionality."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    @pytest.fixture
    def mock_clients(self):
        """Mock service clients."""
        return Mock()

    class ConcreteBaseManager(BaseManager):
        """Concrete implementation of BaseManager for testing."""
        async def get_main_menu(self):
            return []

        async def handle_choice(self, choice: str) -> bool:
            return True

    @pytest.fixture
    def base_manager(self, mock_console, mock_clients):
        """BaseManager instance for testing."""
        return self.ConcreteBaseManager(mock_console, mock_clients)

    def test_initialization(self, base_manager, mock_console, mock_clients):
        """Test BaseManager initialization."""
        assert base_manager.console == mock_console
        assert base_manager.clients == mock_clients
        assert isinstance(base_manager.cache_manager, CacheManager)
        assert isinstance(base_manager.display, DisplayManager)

    @pytest.mark.asyncio
    async def test_confirm_action_default_false(self, base_manager):
        """Test confirm_action with default False."""
        with patch('rich.prompt.Confirm.ask', return_value=False) as mock_confirm:
            result = await base_manager.confirm_action("Test?")
            assert result is False
            mock_confirm.assert_called_once_with("[yellow]Test?[/yellow]", default=False)

    @pytest.mark.asyncio
    async def test_confirm_action_default_true(self, base_manager):
        """Test confirm_action with default True."""
        with patch('rich.prompt.Confirm.ask', return_value=True) as mock_confirm:
            result = await base_manager.confirm_action("Test?", default=True)
            assert result is True
            mock_confirm.assert_called_once_with("[yellow]Test?[/yellow]", default=True)

    @pytest.mark.asyncio
    async def test_get_user_input_simple(self, base_manager):
        """Test simple user input."""
        with patch('rich.prompt.Prompt.ask', return_value="test input") as mock_prompt:
            result = await base_manager.get_user_input("Enter text")
            assert result == "test input"
            mock_prompt.assert_called_once_with("Enter text")

    @pytest.mark.asyncio
    async def test_get_user_input_with_default(self, base_manager):
        """Test user input with default value."""
        with patch('rich.prompt.Prompt.ask', return_value="user input") as mock_prompt:
            result = await base_manager.get_user_input("Enter text", default="default")
            assert result == "user input"
            mock_prompt.assert_called_once_with("Enter text", default="default")

    @pytest.mark.asyncio
    async def test_get_user_input_password(self, base_manager):
        """Test password input."""
        with patch('rich.prompt.Prompt.ask', return_value="secret") as mock_prompt:
            result = await base_manager.get_user_input("Password", password=True)
            assert result == "secret"
            mock_prompt.assert_called_once_with("Password", password=True)

    @pytest.mark.asyncio
    async def test_select_from_list_empty(self, base_manager):
        """Test select_from_list with empty list."""
        result = await base_manager.select_from_list([], "Select item")
        assert result is None

    @pytest.mark.asyncio
    async def test_select_from_list_valid_selection(self, base_manager, mock_console):
        """Test valid selection from list."""
        items = ["item1", "item2", "item3"]

        with patch('rich.prompt.Prompt.ask', return_value="2") as mock_prompt:
            result = await base_manager.select_from_list(items, "Select item")
            assert result == "item2"

    @pytest.mark.asyncio
    async def test_select_from_list_cancel(self, base_manager):
        """Test canceling selection."""
        items = ["item1", "item2"]

        with patch('rich.prompt.Prompt.ask', return_value="c") as mock_prompt:
            result = await base_manager.select_from_list(items, "Select item")
            assert result is None

    @pytest.mark.asyncio
    async def test_select_from_list_invalid_input(self, base_manager):
        """Test invalid input handling."""
        items = ["item1", "item2"]

        with patch('rich.prompt.Prompt.ask', side_effect=["abc", "1"]) as mock_prompt:
            result = await base_manager.select_from_list(items, "Select item")
            assert result == "item1"

    @pytest.mark.asyncio
    async def test_run_with_progress_success(self, base_manager):
        """Test successful run_with_progress."""
        async def test_coro():
            return "success"

        result = await base_manager.run_with_progress(test_coro(), "Testing")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_run_with_progress_error(self, base_manager, mock_console):
        """Test run_with_progress with error."""
        async def failing_coro():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await base_manager.run_with_progress(failing_coro(), "Testing")

    def test_log_operation(self, base_manager):
        """Test operation logging."""
        with patch('services.cli.modules.utils.metrics_utils.log_cli_operation') as mock_log:
            base_manager.log_operation("test_operation", key="value")
            mock_log.assert_called_once_with("test_operation", key="value")

    @pytest.mark.asyncio
    async def test_cache_operations(self, base_manager):
        """Test cache get/set operations."""
        # Test cache set
        await base_manager.cache_set("test_key", "test_value", 300)

        # Test cache get
        result = await base_manager.cache_get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_menu_loop_exit(self, base_manager):
        """Test menu loop exit condition."""
        menu_items = [("1", "Option 1"), ("2", "Option 2")]

        with patch('rich.prompt.Prompt.ask', return_value="b") as mock_prompt:
            with patch.object(base_manager, 'handle_choice') as mock_handle:
                await base_manager.run_menu_loop("Test Menu", menu_items)

                # Should not call handle_choice since we exit immediately
                mock_handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_menu_loop_valid_choice(self, base_manager):
        """Test menu loop with valid choice."""
        menu_items = [("1", "Option 1")]

        # Mock handle_choice to return True and track calls
        with patch.object(base_manager, 'handle_choice', return_value=True) as mock_handle:
            with patch('rich.prompt.Prompt.ask', side_effect=["1", "b"]) as mock_prompt:
                await base_manager.run_menu_loop("Test Menu", menu_items)

                # Verify handle_choice was called with "1"
                mock_handle.assert_called_once_with("1")

    @pytest.mark.asyncio
    async def test_menu_loop_invalid_choice(self, base_manager):
        """Test menu loop with invalid choice."""
        menu_items = [("1", "Option 1")]

        with patch('rich.prompt.Prompt.ask', side_effect=["invalid", "b"]) as mock_prompt:
            with patch.object(base_manager, 'handle_choice', return_value=False):
                await base_manager.run_menu_loop("Test Menu", menu_items)

    @pytest.mark.asyncio
    async def test_menu_loop_keyboard_interrupt(self, base_manager):
        """Test menu loop keyboard interrupt handling."""
        menu_items = [("1", "Option 1")]

        with patch('rich.prompt.Prompt.ask', side_effect=KeyboardInterrupt()):
            await base_manager.run_menu_loop("Test Menu", menu_items)

    @pytest.mark.asyncio
    async def test_menu_loop_exception_handling(self, base_manager):
        """Test menu loop exception handling."""
        menu_items = [("1", "Option 1")]

        # Mock the first prompt to raise an exception, then "b" to exit
        with patch('rich.prompt.Prompt.ask', side_effect=[Exception("Test error"), "b"]) as mock_prompt:
            await base_manager.run_menu_loop("Test Menu", menu_items)

            # Should have been called twice: once for menu choice (exception), once for continue prompt
            assert mock_prompt.call_count >= 2


class TestBaseFormatter:
    """Test BaseFormatter functionality."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    class ConcreteBaseFormatter(BaseFormatter):
        """Concrete implementation of BaseFormatter for testing."""
        def format_operation_result(self, operation: str, result: dict) -> str:
            return f"Operation {operation}: {result}"

        def format_service_status(self, service: str, status: dict) -> str:
            return f"Service {service}: {status}"

    @pytest.fixture
    def base_formatter(self, mock_console):
        """BaseFormatter instance for testing."""
        return self.ConcreteBaseFormatter(mock_console)

    def test_initialization(self, base_formatter, mock_console):
        """Test BaseFormatter initialization."""
        assert base_formatter.console == mock_console

    def test_show_success(self, base_formatter, mock_console):
        """Test success message display."""
        base_formatter.show_success("Operation successful")
        mock_console.print.assert_called_with("[green]✅ Operation successful[/green]")

    def test_show_error(self, base_formatter, mock_console):
        """Test error message display."""
        base_formatter.show_error("Operation failed")
        mock_console.print.assert_called_with("[red]❌ Operation failed[/red]")

    def test_show_warning(self, base_formatter, mock_console):
        """Test warning message display."""
        base_formatter.show_warning("Warning message")
        mock_console.print.assert_called_with("[yellow]⚠️ Warning message[/yellow]")

    def test_show_info(self, base_formatter, mock_console):
        """Test info message display."""
        base_formatter.show_info("Information message")
        mock_console.print.assert_called_with("[blue]ℹ️ Information message[/blue]")

    def test_show_panel(self, base_formatter, mock_console):
        """Test panel display."""
        with patch('rich.panel.Panel') as mock_panel:
            with patch('rich.console.Console.print') as mock_print:
                base_formatter.show_panel("Test content")
                mock_panel.assert_called_once_with("Test content", title="[bold]Information[/bold]")
                mock_print.assert_called_once()

    def test_show_table_simple(self, base_formatter, mock_console):
        """Test simple table display."""
        data = [["Row1"], ["Row2"]]
        headers = ["Column"]

        with patch('rich.table.Table') as mock_table:
            with patch('rich.console.Console.print') as mock_print:
                base_formatter.show_table("Test Table", headers, data)

                # Verify table creation and population
                mock_table.assert_called_once()
                table_instance = mock_table.return_value
                table_instance.add_column.assert_called_once_with("Column")
                assert table_instance.add_row.call_count == 2
                mock_print.assert_called_once_with(table_instance)

    def test_show_dict(self, base_formatter, mock_console):
        """Test dictionary display."""
        test_dict = {"key1": "value1", "key2": "value2"}

        with patch('rich.table.Table') as mock_table:
            with patch('rich.console.Console.print') as mock_print:
                base_formatter.show_dict(test_dict, "Test Dict")

                mock_table.assert_called_once()
                table_instance = mock_table.return_value
                assert table_instance.add_column.call_count == 2
                assert table_instance.add_row.call_count == 2
                mock_print.assert_called_once_with(table_instance)


class TestBaseHandler:
    """Test BaseHandler functionality."""

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing."""
        return Mock(spec=Console)

    class ConcreteBaseHandler(BaseHandler):
        """Concrete implementation of BaseHandler for testing."""
        async def handle_command(self, command: str, **kwargs):
            return f"Handled command: {command}"

    @pytest.fixture
    def base_handler(self, mock_console):
        """BaseHandler instance for testing."""
        return self.ConcreteBaseHandler(mock_console)

    def test_initialization(self, base_handler, mock_console):
        """Test BaseHandler initialization."""
        assert base_handler.console == mock_console

    def test_validate_input_success(self, base_handler):
        """Test successful input validation."""
        result = base_handler.validate_input("test", str, "Test field")
        assert result is True

    def test_validate_input_failure(self, base_handler, mock_console):
        """Test input validation failure."""
        result = base_handler.validate_input(123, str, "Test field")
        assert result is False
        mock_console.print.assert_called_with("[red]❌ Test field must be of type <class 'str'>[/red]")

    def test_validate_input_with_validator(self, base_handler):
        """Test input validation with custom validator."""
        validator = lambda x: len(x) > 3
        result = base_handler.validate_input("test", str, "Test field", validator)
        assert result is True

    def test_validate_input_validator_failure(self, base_handler, mock_console):
        """Test input validation with failing custom validator."""
        validator = lambda x: len(x) > 10
        result = base_handler.validate_input("test", str, "Test field", validator)
        assert result is False
        mock_console.print.assert_called_with("[red]❌ Test field failed validation[/red]")

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, base_handler):
        """Test successful execution with retry."""
        async def operation():
            return "success"

        result = await base_handler.execute_with_retry(operation)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_failure_then_success(self, base_handler):
        """Test execution that fails then succeeds."""
        call_count = 0

        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"

        result = await base_handler.execute_with_retry(operation, max_retries=2)
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self, base_handler, mock_console):
        """Test execution that exceeds max retries."""
        async def operation():
            raise Exception("Persistent failure")

        with pytest.raises(Exception, match="Persistent failure"):
            await base_handler.execute_with_retry(operation, max_retries=2)

    @pytest.mark.asyncio
    async def test_execute_with_retry_custom_error_handler(self, base_handler, mock_console):
        """Test execution with custom error handler."""
        error_handled = False

        def custom_error_handler(error, attempt):
            nonlocal error_handled
            error_handled = True

        async def operation():
            raise Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            await base_handler.execute_with_retry(
                operation,
                max_retries=1,
                error_handler=custom_error_handler
            )

        assert error_handled
