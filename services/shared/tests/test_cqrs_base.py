"""Tests for CQRS base classes.

Comprehensive test coverage for:
- CommandHandler functionality and error handling
- QueryHandler functionality and error handling
- CommandBus dispatch and registration
- QueryBus dispatch and registration
- CommandResult and QueryResult data structures
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Any, Dict, Optional

from services.shared.domain.cqrs_base import (
    CommandHandler,
    QueryHandler,
    CommandBus,
    QueryBus,
    CommandResult,
    QueryResult,
    LoggerProtocol,
)


# Test Commands and Queries
class TestCommand:
    """Test command for CQRS testing."""

    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return f"TestCommand(value={self.value})"


class TestQuery:
    """Test query for CQRS testing."""

    def __init__(self, param: str):
        self.param = param

    def __str__(self):
        return f"TestQuery(param={self.param})"


class TestCommandHandler(CommandHandler[TestCommand]):
    """Test command handler implementation."""

    def __init__(self, logger: Optional[LoggerProtocol] = None):
        super().__init__(logger)
        self.executed_commands = []

    async def _execute(self, command: TestCommand) -> Any:
        """Execute the command."""
        self.executed_commands.append(command)
        if command.value == "fail":
            raise ValueError("Command failed")
        return {"result": f"processed_{command.value}"}


class TestQueryHandler(QueryHandler[TestQuery, Dict[str, Any]]):
    """Test query handler implementation."""

    def __init__(self, logger: Optional[LoggerProtocol] = None):
        super().__init__(logger)
        self.executed_queries = []

    async def _execute(self, query: TestQuery) -> tuple:
        """Execute the query."""
        self.executed_queries.append(query)
        if query.param == "fail":
            raise ValueError("Query failed")
        results = [{"id": "1", "name": f"item_{query.param}"}]
        return results, len(results)


class MockLogger:
    """Mock logger for testing."""

    def __init__(self):
        self.info_calls = []
        self.error_calls = []

    def info(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        self.info_calls.append((message, extra, exc_info))

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        self.error_calls.append((message, extra, exc_info))


class TestCommandResult:
    """Test CommandResult data structure."""

    def test_command_result_success(self):
        """Test successful command result."""
        result = CommandResult(
            success=True,
            message="Command executed successfully",
            data={"key": "value"},
            correlation_id="test-id",
        )

        assert result.success is True
        assert result.message == "Command executed successfully"
        assert result.data == {"key": "value"}
        assert result.errors is None
        assert result.correlation_id == "test-id"

    def test_command_result_failure(self):
        """Test failed command result."""
        result = CommandResult(
            success=False,
            message="Command failed",
            errors=["Error 1", "Error 2"],
            correlation_id="test-id",
        )

        assert result.success is False
        assert result.message == "Command failed"
        assert result.errors == ["Error 1", "Error 2"]
        assert result.data is None
        assert result.correlation_id == "test-id"


class TestQueryResult:
    """Test QueryResult data structure."""

    def test_query_result_success(self):
        """Test successful query result."""
        result = QueryResult(
            success=True,
            message="Query executed successfully",
            data=[{"id": "1", "name": "test"}],
            total_count=1,
            correlation_id="test-id",
        )

        assert result.success is True
        assert result.message == "Query executed successfully"
        assert result.data == [{"id": "1", "name": "test"}]
        assert result.total_count == 1
        assert result.errors is None
        assert result.correlation_id == "test-id"

    def test_query_result_failure(self):
        """Test failed query result."""
        result = QueryResult(
            success=False,
            message="Query failed",
            errors=["Database error"],
            correlation_id="test-id",
        )

        assert result.success is False
        assert result.message == "Query failed"
        assert result.errors == ["Database error"]
        assert result.data is None
        assert result.total_count is None
        assert result.correlation_id == "test-id"


class TestCommandHandler:
    """Test CommandHandler base class."""

    def test_initialization(self):
        """Test CommandHandler initialization."""
        logger = MockLogger()
        handler = TestCommandHandler(logger)

        assert handler._logger == logger
        assert handler._correlation_id is None

    def test_set_correlation_id(self):
        """Test setting correlation ID."""
        handler = TestCommandHandler()
        handler.set_correlation_id("test-correlation-id")

        assert handler._correlation_id == "test-correlation-id"

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful command handling."""
        logger = MockLogger()
        handler = TestCommandHandler(logger)
        command = TestCommand("test_value")

        result = await handler.handle(command)

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert result.message == "Command executed successfully"
        assert result.data == {"result": "processed_test_value"}
        assert result.correlation_id is None

        # Verify logging
        assert len(logger.info_calls) == 2  # Pre and post execution
        assert "Handling command" in logger.info_calls[0][0]
        assert "Command handled successfully" in logger.info_calls[1][0]

        # Verify command execution
        assert len(handler.executed_commands) == 1
        assert handler.executed_commands[0] == command

    @pytest.mark.asyncio
    async def test_handle_with_correlation_id(self):
        """Test command handling with correlation ID."""
        handler = TestCommandHandler()
        handler.set_correlation_id("test-id")
        command = TestCommand("test_value")

        result = await handler.handle(command)

        assert result.correlation_id == "test-id"

    @pytest.mark.asyncio
    async def test_handle_failure(self):
        """Test command handling failure."""
        logger = MockLogger()
        handler = TestCommandHandler(logger)
        command = TestCommand("fail")  # This will cause _execute to raise

        result = await handler.handle(command)

        assert isinstance(result, CommandResult)
        assert result.success is False
        assert "Failed to execute command" in result.message
        assert result.errors == ["Command failed"]

        # Verify error logging
        assert len(logger.error_calls) == 1
        assert "Error handling command" in logger.error_calls[0][0]

    @pytest.mark.asyncio
    async def test_pre_validate_called(self):
        """Test that pre-validation is called."""
        handler = TestCommandHandler()
        command = TestCommand("test")

        # Override pre_validate to track calls
        pre_validate_calls = []
        original_pre_validate = handler._pre_validate

        async def mock_pre_validate(cmd):
            pre_validate_calls.append(cmd)

        handler._pre_validate = mock_pre_validate

        await handler.handle(command)

        assert len(pre_validate_calls) == 1
        assert pre_validate_calls[0] == command

        # Restore original
        handler._pre_validate = original_pre_validate

    @pytest.mark.asyncio
    async def test_post_validate_called(self):
        """Test that post-validation is called."""
        handler = TestCommandHandler()
        command = TestCommand("test")

        # Override post_validate to track calls
        post_validate_calls = []
        original_post_validate = handler._post_validate

        async def mock_post_validate(cmd, result):
            post_validate_calls.append((cmd, result))

        handler._post_validate = mock_post_validate

        await handler.handle(command)

        assert len(post_validate_calls) == 1
        assert post_validate_calls[0][0] == command
        assert post_validate_calls[0][1] == {"result": "processed_test"}

        # Restore original
        handler._post_validate = original_post_validate


class TestQueryHandler:
    """Test QueryHandler base class."""

    def test_initialization(self):
        """Test QueryHandler initialization."""
        logger = MockLogger()
        handler = TestQueryHandler(logger)

        assert handler._logger == logger
        assert handler._correlation_id is None

    def test_set_correlation_id(self):
        """Test setting correlation ID."""
        handler = TestQueryHandler()
        handler.set_correlation_id("test-correlation-id")

        assert handler._correlation_id == "test-correlation-id"

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful query handling."""
        logger = MockLogger()
        handler = TestQueryHandler(logger)
        query = TestQuery("test_param")

        result = await handler.handle(query)

        assert isinstance(result, QueryResult)
        assert result.success is True
        assert result.message == "Query executed successfully"
        assert result.data == [{"id": "1", "name": "item_test_param"}]
        assert result.total_count == 1
        assert result.correlation_id is None

        # Verify logging
        assert len(logger.info_calls) == 2  # Pre and post execution
        assert "Handling query" in logger.info_calls[0][0]
        assert "Query handled successfully" in logger.info_calls[1][0]

        # Verify query execution
        assert len(handler.executed_queries) == 1
        assert handler.executed_queries[0] == query

    @pytest.mark.asyncio
    async def test_handle_failure(self):
        """Test query handling failure."""
        logger = MockLogger()
        handler = TestQueryHandler(logger)
        query = TestQuery("fail")  # This will cause _execute to raise

        result = await handler.handle(query)

        assert isinstance(result, QueryResult)
        assert result.success is False
        assert "Failed to execute query" in result.message
        assert result.errors == ["Query failed"]

        # Verify error logging
        assert len(logger.error_calls) == 1
        assert "Error handling query" in logger.error_calls[0][0]


class TestCommandBus:
    """Test CommandBus functionality."""

    def test_initialization(self):
        """Test CommandBus initialization."""
        logger = MockLogger()
        bus = CommandBus(logger)

        assert bus._handlers == {}
        assert bus._logger == logger

    def test_register_handler(self):
        """Test registering a command handler."""
        bus = CommandBus()
        handler = TestCommandHandler()

        bus.register_handler("TestCommand", handler)

        assert "TestCommand" in bus._handlers
        assert bus._handlers["TestCommand"] == handler

    def test_register_handler_logging(self):
        """Test that handler registration is logged."""
        logger = MockLogger()
        bus = CommandBus(logger)
        handler = TestCommandHandler()

        bus.register_handler("TestCommand", handler)

        assert len(logger.info_calls) == 1
        assert "Registered command handler: TestCommand" in logger.info_calls[0][0]

    @pytest.mark.asyncio
    async def test_dispatch_success(self):
        """Test successful command dispatch."""
        bus = CommandBus()
        handler = TestCommandHandler()
        bus.register_handler("TestCommand", handler)

        command = TestCommand("test_value")
        result = await bus.dispatch(command)

        assert isinstance(result, CommandResult)
        assert result.success is True
        assert len(handler.executed_commands) == 1

    @pytest.mark.asyncio
    async def test_dispatch_with_correlation_id(self):
        """Test command dispatch with correlation ID."""
        bus = CommandBus()
        handler = TestCommandHandler()
        bus.register_handler("TestCommand", handler)

        command = TestCommand("test_value")
        result = await bus.dispatch(command, correlation_id="test-id")

        assert result.correlation_id == "test-id"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_command(self):
        """Test dispatching unknown command."""
        logger = MockLogger()
        bus = CommandBus(logger)

        command = TestCommand("test_value")
        result = await bus.dispatch(command)

        assert isinstance(result, CommandResult)
        assert result.success is False
        assert "No handler for command" in result.message

        # Verify error logging
        assert len(logger.error_calls) == 1
        assert "No handler registered" in logger.error_calls[0][0]

    @pytest.mark.asyncio
    async def test_dispatch_handler_error(self):
        """Test dispatch when handler raises error."""
        bus = CommandBus()
        handler = TestCommandHandler()
        bus.register_handler("TestCommand", handler)

        command = TestCommand("fail")  # Handler will raise error
        result = await bus.dispatch(command)

        assert isinstance(result, CommandResult)
        assert result.success is False
        assert result.errors == ["Command failed"]


class TestQueryBus:
    """Test QueryBus functionality."""

    def test_initialization(self):
        """Test QueryBus initialization."""
        logger = MockLogger()
        bus = QueryBus(logger)

        assert bus._handlers == {}
        assert bus._logger == logger

    def test_register_handler(self):
        """Test registering a query handler."""
        bus = QueryBus()
        handler = TestQueryHandler()

        bus.register_handler("TestQuery", handler)

        assert "TestQuery" in bus._handlers
        assert bus._handlers["TestQuery"] == handler

    @pytest.mark.asyncio
    async def test_dispatch_success(self):
        """Test successful query dispatch."""
        bus = QueryBus()
        handler = TestQueryHandler()
        bus.register_handler("TestQuery", handler)

        query = TestQuery("test_param")
        result = await bus.dispatch(query)

        assert isinstance(result, QueryResult)
        assert result.success is True
        assert len(handler.executed_queries) == 1

    @pytest.mark.asyncio
    async def test_dispatch_unknown_query(self):
        """Test dispatching unknown query."""
        logger = MockLogger()
        bus = QueryBus(logger)

        query = TestQuery("test_param")
        result = await bus.dispatch(query)

        assert isinstance(result, QueryResult)
        assert result.success is False
        assert "No handler for query" in result.message


class TestIntegration:
    """Integration tests for CQRS components."""

    @pytest.mark.asyncio
    async def test_full_command_flow(self):
        """Test complete command flow from bus to handler."""
        # Setup
        bus = CommandBus()
        handler = TestCommandHandler()
        bus.register_handler("TestCommand", handler)

        # Execute command
        command = TestCommand("integration_test")
        result = await bus.dispatch(command, correlation_id="integration-test-id")

        # Verify results
        assert result.success is True
        assert result.correlation_id == "integration-test-id"
        assert result.data == {"result": "processed_integration_test"}
        assert len(handler.executed_commands) == 1

    @pytest.mark.asyncio
    async def test_full_query_flow(self):
        """Test complete query flow from bus to handler."""
        # Setup
        bus = QueryBus()
        handler = TestQueryHandler()
        bus.register_handler("TestQuery", handler)

        # Execute query
        query = TestQuery("integration_param")
        result = await bus.dispatch(query, correlation_id="integration-test-id")

        # Verify results
        assert result.success is True
        assert result.correlation_id == "integration-test-id"
        assert result.data == [{"id": "1", "name": "item_integration_param"}]
        assert result.total_count == 1
        assert len(handler.executed_queries) == 1

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test error propagation through CQRS layers."""
        # Setup failing handlers
        command_bus = CommandBus()
        query_bus = QueryBus()

        command_handler = TestCommandHandler()
        query_handler = TestQueryHandler()

        command_bus.register_handler("TestCommand", command_handler)
        query_bus.register_handler("TestQuery", query_handler)

        # Execute failing operations
        command_result = await command_bus.dispatch(TestCommand("fail"))
        query_result = await query_bus.dispatch(TestQuery("fail"))

        # Verify errors are properly handled
        assert command_result.success is False
        assert "Command failed" in str(command_result.errors)

        assert query_result.success is False
        assert "Query failed" in str(query_result.errors)


if __name__ == "__main__":
    pytest.main([__file__])
