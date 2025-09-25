"""Tests for application layer components.

Comprehensive test coverage for:
- Application services
- Use cases
- Commands and queries
- Application layer base classes
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Any, Dict

from services.shared.application import (
    UseCase,
    Command,
    Query,
    CommandHandler,
    QueryHandler,
    ApplicationService
)


class TestUseCase:
    """Test use case base class."""

    def test_use_case_is_abstract(self):
        """Test that UseCase is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            UseCase()

    @pytest.mark.asyncio
    async def test_use_case_subclass(self):
        """Test creating a concrete use case."""

        class CreateUserUseCase(UseCase):
            async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
                return {"id": 1, "name": request["name"]}

        use_case = CreateUserUseCase()
        result = await use_case.execute({"name": "John"})
        assert result == {"id": 1, "name": "John"}


class TestCommandAndQuery:
    """Test command and query base classes."""

    def test_command_creation(self):
        """Test command creation."""
        cmd = Command()
        assert isinstance(cmd, Command)

    def test_query_creation(self):
        """Test query creation."""
        query = Query()
        assert isinstance(query, Query)

    def test_command_with_data(self):
        """Test command with custom data."""

        class CreateUserCommand(Command):
            def __init__(self, name: str, email: str):
                self.name = name
                self.email = email

        cmd = CreateUserCommand("John", "john@example.com")
        assert cmd.name == "John"
        assert cmd.email == "john@example.com"

    def test_query_with_data(self):
        """Test query with custom data."""

        class GetUserQuery(Query):
            def __init__(self, user_id: int):
                self.user_id = user_id

        query = GetUserQuery(123)
        assert query.user_id == 123


class TestCommandHandler:
    """Test command handler protocol."""

    def test_command_handler_protocol(self):
        """Test that CommandHandler is a protocol."""

        # Cannot instantiate protocol directly
        with pytest.raises(TypeError):
            CommandHandler()

    @pytest.mark.asyncio
    async def test_command_handler_implementation(self):
        """Test implementing a command handler."""

        class CreateUserHandler:
            def __init__(self):
                self.repository = MagicMock()

            async def handle(self, command: Command) -> Dict[str, Any]:
                # Simulate handling
                return {"id": 1, "created": True}

        handler = CreateUserHandler()
        command = Command()

        result = await handler.handle(command)
        assert result == {"id": 1, "created": True}


class TestQueryHandler:
    """Test query handler protocol."""

    def test_query_handler_protocol(self):
        """Test that QueryHandler is a protocol."""

        # Cannot instantiate protocol directly
        with pytest.raises(TypeError):
            QueryHandler()

    @pytest.mark.asyncio
    async def test_query_handler_implementation(self):
        """Test implementing a query handler."""

        class GetUserHandler:
            def __init__(self):
                self.repository = MagicMock()

            async def handle(self, query: Query) -> Dict[str, Any]:
                # Simulate handling
                return {"id": 1, "name": "John"}

        handler = GetUserHandler()
        query = Query()

        result = await handler.handle(query)
        assert result == {"id": 1, "name": "John"}


class TestApplicationService:
    """Test application service base class."""

    def test_application_service_initialization(self):
        """Test application service initialization."""
        service = ApplicationService()
        assert service.logger is not None
        assert service.logger.name == "ApplicationService"

    @pytest.mark.asyncio
    async def test_validate_request(self):
        """Test request validation."""
        service = ApplicationService()

        # Should not raise by default
        await service._validate_request({"data": "test"})

    @pytest.mark.asyncio
    async def test_authorize_request(self):
        """Test request authorization."""
        service = ApplicationService()

        # Should not raise by default
        await service._authorize_request({"user": "test"})

    @pytest.mark.asyncio
    async def test_custom_application_service(self):
        """Test creating a custom application service."""

        class UserService(ApplicationService):
            def __init__(self):
                super().__init__()
                self.user_repository = MagicMock()

            async def _validate_request(self, request: Dict[str, Any]) -> None:
                if "name" not in request:
                    raise ValueError("Name is required")

            async def create_user(self, request: Dict[str, Any]) -> Dict[str, Any]:
                await self._validate_request(request)
                await self._authorize_request(request)

                # Simulate user creation
                return {"id": 1, "name": request["name"]}

        service = UserService()

        # Test valid request
        result = await service.create_user({"name": "John"})
        assert result == {"id": 1, "name": "John"}

        # Test invalid request
        with pytest.raises(ValueError, match="Name is required"):
            await service.create_user({})


class TestApplicationLayerIntegration:
    """Test application layer integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete application workflow."""

        # Define command
        class CreateUserCommand(Command):
            def __init__(self, name: str, email: str):
                self.name = name
                self.email = email

        # Define handler
        class CreateUserHandler:
            def __init__(self):
                self.repository = MagicMock()

            async def handle(self, command: CreateUserCommand) -> Dict[str, Any]:
                # Simulate saving to repository
                user = {
                    "id": 1,
                    "name": command.name,
                    "email": command.email
                }
                self.repository.save.return_value = user
                self.repository.save(user)  # Actually call the method
                return user

        # Test the workflow
        command = CreateUserCommand("John Doe", "john@example.com")
        handler = CreateUserHandler()

        result = await handler.handle(command)

        assert result["id"] == 1
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"

        # Verify repository was called
        handler.repository.save.assert_called_once()
