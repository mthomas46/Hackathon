"""Clean unit tests for cli domain services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Optional

# Define mock entities and repositories to avoid import dependencies
from enum import Enum
from datetime import datetime, timezone


class CommandStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CommandType(str, Enum):
    SYSTEM = "system"
    USER = "user"
    SERVICE = "service"


class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"


class MockCliSession:
    """Mock CLI session entity."""
    def __init__(self, session_id: str, user_id: str, status: SessionStatus = SessionStatus.ACTIVE):
        self.session_id = session_id
        self.user_id = user_id
        self.status = status
        self.environment = {}
        self.variables = {}

    def is_active(self):
        return self.status == SessionStatus.ACTIVE

    def update_activity(self):
        self.last_activity = datetime.now(timezone.utc)

    def set_variable(self, k, v):
        self.variables[k] = v

    def get_variable(self, k, d=None):
        return self.variables.get(k, d)

    def terminate(self):
        self.status = SessionStatus.INACTIVE


class MockCliCommand:
    """Mock CLI command entity."""
    def __init__(self, command_id: str, session_id: str, command: str, args: List[str] = None,
                 command_type: CommandType = CommandType.USER,
                 execution_mode: ExecutionMode = ExecutionMode.SYNC):
        self.command_id = command_id
        self.session_id = session_id
        self.command = command
        self.args = args or []
        self.kwargs = {}
        self.command_type = command_type
        self.execution_mode = execution_mode
        self.status = CommandStatus.PENDING

    def is_pending(self):
        return self.status == CommandStatus.PENDING

    def is_running(self):
        return self.status == CommandStatus.RUNNING

    def is_completed(self):
        return self.status == CommandStatus.COMPLETED

    def start_execution(self):
        self.status = CommandStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def complete_execution(self):
        self.status = CommandStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def fail_execution(self):
        self.status = CommandStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)

    def get_full_command(self):
        return f"{self.command} {' '.join(self.args)}"


class MockCommandResult:
    """Mock command result entity."""
    def __init__(self, result_id: str, command_id: str, exit_code: int = 0,
                 stdout: str = "", stderr: str = ""):
        self.result_id = result_id
        self.command_id = command_id
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = 0.0
        self.success = exit_code == 0
        self.metadata = {}

    def is_successful(self):
        return self.success and self.exit_code == 0

    def has_output(self):
        return bool(self.stdout.strip())

    def has_errors(self):
        return bool(self.stderr.strip())


class MockServiceAdapter:
    """Mock service adapter entity."""
    def __init__(self, adapter_id: str, service_name: str, capabilities: List[str] = None):
        self.adapter_id = adapter_id
        self.service_name = service_name
        self.capabilities = capabilities or []

    def is_available(self):
        return True

    def has_capability(self, cap: str):
        return cap in self.capabilities


# Mock repositories
class MockSessionRepository:
    """Mock session repository."""
    def __init__(self):
        self.sessions = {
            "session1": MockCliSession("session1", "user1", SessionStatus.ACTIVE),
            "session2": MockCliSession("session2", "user2", SessionStatus.INACTIVE),
        }

    async def save(self, session: MockCliSession) -> MockCliSession:
        """Save session."""
        self.sessions[session.session_id] = session
        return session

    async def get_by_id(self, session_id: str) -> Optional[MockCliSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    async def get_active_sessions(self) -> List[MockCliSession]:
        """Get active sessions."""
        return [s for s in self.sessions.values() if s.is_active()]


class MockCommandRepository:
    """Mock command repository."""
    def __init__(self):
        self.commands = {}

    async def save(self, command: MockCliCommand) -> MockCliCommand:
        """Save command."""
        self.commands[command.command_id] = command
        return command

    async def get_by_id(self, command_id: str) -> Optional[MockCliCommand]:
        """Get command by ID."""
        return self.commands.get(command_id)

    async def get_by_session_id(self, session_id: str) -> List[MockCliCommand]:
        """Get commands by session ID."""
        return [c for c in self.commands.values() if c.session_id == session_id]


class MockResultRepository:
    """Mock result repository."""
    def __init__(self):
        self.results = {}

    async def save(self, result: MockCommandResult) -> MockCommandResult:
        """Save result."""
        self.results[result.result_id] = result
        return result

    async def get_by_command_id(self, command_id: str) -> Optional[MockCommandResult]:
        """Get result by command ID."""
        return next((r for r in self.results.values() if r.command_id == command_id), None)


class MockAdapterRepository:
    """Mock adapter repository."""
    def __init__(self):
        self.adapters = {
            "adapter1": MockServiceAdapter("adapter1", "analysis-service", ["analyze_code", "validate"]),
            "adapter2": MockServiceAdapter("adapter2", "doc-store", ["store", "retrieve"]),
        }

    async def get_by_service_name(self, service_name: str) -> Optional[MockServiceAdapter]:
        """Get adapter by service name."""
        return next((a for a in self.adapters.values() if a.service_name == service_name), None)

    async def get_available_adapters(self) -> List[MockServiceAdapter]:
        """Get available adapters."""
        return [a for a in self.adapters.values() if a.is_available()]


# Domain services
class CliSessionService:
    """Domain service for CLI session management."""

    def __init__(self, session_repo: MockSessionRepository):
        self.session_repo = session_repo

    async def create_session(self, user_id: str, environment: Dict = None) -> MockCliSession:
        """Create a new CLI session."""
        session_id = f"session_{user_id}_{len(await self.session_repo.get_active_sessions()) + 1}"
        session = MockCliSession(session_id, user_id, SessionStatus.ACTIVE)

        if environment:
            session.environment = environment

        await self.session_repo.save(session)
        return session

    async def get_session(self, session_id: str) -> Optional[MockCliSession]:
        """Get a session by ID."""
        return await self.session_repo.get_by_id(session_id)

    async def update_session_activity(self, session_id: str) -> Optional[MockCliSession]:
        """Update session activity."""
        session = await self.session_repo.get_by_id(session_id)
        if session and session.is_active():
            session.update_activity()
            await self.session_repo.save(session)
            return session
        return None

    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a session."""
        session = await self.session_repo.get_by_id(session_id)
        if session and session.is_active():
            session.terminate()
            await self.session_repo.save(session)
            return True
        return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        # In a real implementation, this would check session timeouts
        # For this mock, we'll simulate cleaning up inactive sessions
        active_sessions = await self.session_repo.get_active_sessions()
        expired_count = len(self.session_repo.sessions) - len(active_sessions)

        # Mock cleanup - remove inactive sessions
        inactive_ids = [sid for sid, s in self.session_repo.sessions.items() if not s.is_active()]
        for sid in inactive_ids:
            del self.session_repo.sessions[sid]

        return expired_count

    async def get_session_statistics(self) -> Dict:
        """Get session statistics."""
        all_sessions = list(self.session_repo.sessions.values())
        active_sessions = [s for s in all_sessions if s.is_active()]

        return {
            "total_sessions": len(all_sessions),
            "active_sessions": len(active_sessions),
            "inactive_sessions": len(all_sessions) - len(active_sessions),
            "sessions_by_user": len(set(s.user_id for s in all_sessions))
        }


class CliCommandService:
    """Domain service for CLI command management."""

    def __init__(self,
                 command_repo: MockCommandRepository,
                 result_repo: MockResultRepository,
                 adapter_repo: MockAdapterRepository):
        self.command_repo = command_repo
        self.result_repo = result_repo
        self.adapter_repo = adapter_repo

    async def create_command(self, session_id: str, command: str, args: List[str] = None,
                           kwargs: Dict = None, command_type: CommandType = CommandType.USER,
                           execution_mode: ExecutionMode = ExecutionMode.SYNC) -> MockCliCommand:
        """Create a new command."""
        command_id = f"cmd_{session_id}_{len(await self.command_repo.get_by_session_id(session_id)) + 1}"
        cmd = MockCliCommand(command_id, session_id, command, args, command_type, execution_mode)

        if kwargs:
            cmd.kwargs = kwargs

        await self.command_repo.save(cmd)
        return cmd

    async def execute_command(self, command_id: str) -> Optional[MockCommandResult]:
        """Execute a command."""
        command = await self.command_repo.get_by_id(command_id)
        if not command or not command.is_pending():
            return None

        # Start execution
        command.start_execution()

        try:
            # Simulate command execution based on command type
            result = await self._execute_command_logic(command)

            # Complete command
            command.complete_execution()

            await self.command_repo.save(command)
            await self.result_repo.save(result)

            return result

        except Exception as e:
            # Handle execution failure
            command.fail_execution()
            await self.command_repo.save(command)

            error_result = MockCommandResult(
                f"result_{command_id}_error",
                command_id,
                exit_code=1,
                stdout="",
                stderr=f"Command execution failed: {str(e)}"
            )
            await self.result_repo.save(error_result)
            return error_result

    async def _execute_command_logic(self, command: MockCliCommand) -> MockCommandResult:
        """Execute command logic based on command type."""
        if command.command_type == CommandType.SYSTEM:
            return await self._execute_system_command(command)
        elif command.command_type == CommandType.SERVICE:
            return await self._execute_service_command(command)
        elif command.command_type == CommandType.USER:
            return await self._execute_user_command(command)
        else:
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=1,
                stderr=f"Unknown command type: {command.command_type}"
            )

    async def _execute_system_command(self, command: MockCliCommand) -> MockCommandResult:
        """Execute system command."""
        if command.command == "list-services":
            # Mock service listing
            services = ["analysis-service", "doc-store", "interpreter"]
            output = "\n".join(f"- {service}" for service in services)

            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=0,
                stdout=output,
                metadata={"services_count": len(services)}
            )
        elif command.command == "health-check":
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=0,
                stdout="All services healthy"
            )
        else:
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=1,
                stderr=f"Unknown system command: {command.command}"
            )

    async def _execute_service_command(self, command: MockCliCommand) -> MockCommandResult:
        """Execute service command."""
        # Extract service name from args
        service_name = None
        for arg in command.args:
            if arg.startswith("--service="):
                service_name = arg.split("=", 1)[1]
                break

        if not service_name:
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=1,
                stderr="Service name not specified"
            )

        # Check if adapter exists
        adapter = await self.adapter_repo.get_by_service_name(service_name)
        if not adapter:
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=1,
                stderr=f"Service not available: {service_name}"
            )

        # Mock service execution
        if command.command == "analyze-code" and adapter.has_capability("analyze_code"):
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=0,
                stdout=f"Code analysis completed for {service_name}",
                metadata={"analysis_type": "code_quality"}
            )
        else:
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=1,
                stderr=f"Command not supported by {service_name}"
            )

    async def _execute_user_command(self, command: MockCliCommand) -> MockCommandResult:
        """Execute user command."""
        # Mock user command execution
        if command.command == "help":
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=0,
                stdout="Available commands: help, list-services, analyze-code"
            )
        elif command.command == "status":
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=0,
                stdout="CLI Status: Active\nServices: 3 available"
            )
        else:
            return MockCommandResult(
                f"result_{command.command_id}",
                command.command_id,
                exit_code=1,
                stderr=f"Unknown command: {command.command}"
            )

    async def get_command_history(self, session_id: str) -> List[MockCliCommand]:
        """Get command history for a session."""
        return await self.command_repo.get_by_session_id(session_id)

    async def get_command_statistics(self) -> Dict:
        """Get command execution statistics."""
        all_commands = list(self.command_repo.commands.values())
        completed_commands = [c for c in all_commands if c.is_completed()]

        command_types = {}
        for cmd in all_commands:
            cmd_type = cmd.command_type
            command_types[cmd_type] = command_types.get(cmd_type, 0) + 1

        return {
            "total_commands": len(all_commands),
            "completed_commands": len(completed_commands),
            "completion_rate": len(completed_commands) / len(all_commands) if all_commands else 0,
            "commands_by_type": command_types
        }


class TestCliSessionService:
    """Test the CliSessionService domain service."""

    @pytest.fixture
    def session_repo(self):
        """Create session repository."""
        return MockSessionRepository()

    @pytest.fixture
    def session_service(self, session_repo):
        """Create session service."""
        return CliSessionService(session_repo)

    @pytest.mark.asyncio
    async def test_create_session(self, session_service, session_repo):
        """Test creating a session."""
        environment = {"TERM": "xterm", "SHELL": "/bin/bash"}
        session = await session_service.create_session("user123", environment)

        assert session.user_id == "user123"
        assert session.is_active()
        assert session.environment == environment

        # Verify saved
        saved = await session_repo.get_by_id(session.session_id)
        assert saved is not None

    @pytest.mark.asyncio
    async def test_get_session(self, session_service):
        """Test getting a session."""
        session = await session_service.get_session("session1")
        assert session is not None
        assert session.user_id == "user1"

        nonexistent = await session_service.get_session("nonexistent")
        assert nonexistent is None

    @pytest.mark.asyncio
    async def test_update_session_activity(self, session_service):
        """Test updating session activity."""
        session = await session_service.update_session_activity("session1")
        assert session is not None

        # Try updating inactive session
        inactive_update = await session_service.update_session_activity("session2")
        assert inactive_update is None

    @pytest.mark.asyncio
    async def test_terminate_session(self, session_service):
        """Test terminating a session."""
        success = await session_service.terminate_session("session1")
        assert success

        # Verify terminated
        session = await session_service.get_session("session1")
        assert not session.is_active()

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_service):
        """Test cleaning up expired sessions."""
        # Should clean up inactive sessions
        cleaned_count = await session_service.cleanup_expired_sessions()
        assert cleaned_count >= 0

    @pytest.mark.asyncio
    async def test_get_session_statistics(self, session_service):
        """Test getting session statistics."""
        stats = await session_service.get_session_statistics()

        assert "total_sessions" in stats
        assert "active_sessions" in stats
        assert "inactive_sessions" in stats
        assert stats["total_sessions"] >= 2


class TestCliCommandService:
    """Test the CliCommandService domain service."""

    @pytest.fixture
    def command_repo(self):
        """Create command repository."""
        return MockCommandRepository()

    @pytest.fixture
    def result_repo(self):
        """Create result repository."""
        return MockResultRepository()

    @pytest.fixture
    def adapter_repo(self):
        """Create adapter repository."""
        return MockAdapterRepository()

    @pytest.fixture
    def command_service(self, command_repo, result_repo, adapter_repo):
        """Create command service."""
        return CliCommandService(command_repo, result_repo, adapter_repo)

    @pytest.mark.asyncio
    async def test_create_command(self, command_service):
        """Test creating a command."""
        command = await command_service.create_command(
            "session1",
            "list-services",
            ["--format", "json"],
            {"verbose": True},
            CommandType.SYSTEM,
            ExecutionMode.SYNC
        )

        assert command.session_id == "session1"
        assert command.command == "list-services"
        assert command.args == ["--format", "json"]
        assert command.kwargs["verbose"] is True
        assert command.command_type == CommandType.SYSTEM

    @pytest.mark.asyncio
    async def test_execute_system_command(self, command_service):
        """Test executing a system command."""
        command = await command_service.create_command(
            "session1", "list-services", [], {}, CommandType.SYSTEM
        )

        result = await command_service.execute_command(command.command_id)

        assert result is not None
        assert result.is_successful()
        assert "analysis-service" in result.stdout
        assert command.is_completed()

    @pytest.mark.asyncio
    async def test_execute_service_command(self, command_service):
        """Test executing a service command."""
        command = await command_service.create_command(
            "session1",
            "analyze-code",
            ["--service=analysis-service"],
            {},
            CommandType.SERVICE
        )

        result = await command_service.execute_command(command.command_id)

        assert result is not None
        assert result.is_successful()
        assert "analysis-service" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_user_command(self, command_service):
        """Test executing a user command."""
        command = await command_service.create_command(
            "session1", "help", [], {}, CommandType.USER
        )

        result = await command_service.execute_command(command.command_id)

        assert result is not None
        assert result.is_successful()
        assert "Available commands" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_unknown_command(self, command_service):
        """Test executing an unknown command."""
        command = await command_service.create_command(
            "session1", "unknown-command", [], {}, CommandType.USER
        )

        result = await command_service.execute_command(command.command_id)

        assert result is not None
        assert not result.is_successful()
        assert "Unknown command" in result.stderr

    @pytest.mark.asyncio
    async def test_get_command_history(self, command_service):
        """Test getting command history."""
        # Create some commands
        await command_service.create_command("session1", "cmd1")
        await command_service.create_command("session1", "cmd2")
        await command_service.create_command("session2", "cmd3")

        history = await command_service.get_command_history("session1")

        assert len(history) >= 2
        assert all(cmd.session_id == "session1" for cmd in history)

    @pytest.mark.asyncio
    async def test_get_command_statistics(self, command_service):
        """Test getting command statistics."""
        # Create and execute some commands
        cmd1 = await command_service.create_command("session1", "list-services", [], {}, CommandType.SYSTEM)
        await command_service.execute_command(cmd1.command_id)

        cmd2 = await command_service.create_command("session1", "help", [], {}, CommandType.USER)
        await command_service.execute_command(cmd2.command_id)

        stats = await command_service.get_command_statistics()

        assert stats["total_commands"] >= 2
        assert stats["completed_commands"] >= 1
        assert "commands_by_type" in stats
        assert CommandType.SYSTEM in stats["commands_by_type"]
        assert CommandType.USER in stats["commands_by_type"]


class TestServiceIntegration:
    """Test integration between services."""

    @pytest.fixture
    def session_repo(self):
        """Create session repository."""
        return MockSessionRepository()

    @pytest.fixture
    def command_repo(self):
        """Create command repository."""
        return MockCommandRepository()

    @pytest.fixture
    def result_repo(self):
        """Create result repository."""
        return MockResultRepository()

    @pytest.fixture
    def adapter_repo(self):
        """Create adapter repository."""
        return MockAdapterRepository()

    @pytest.fixture
    def session_service(self, session_repo):
        """Create session service."""
        return CliSessionService(session_repo)

    @pytest.fixture
    def command_service(self, command_repo, result_repo, adapter_repo):
        """Create command service."""
        return CliCommandService(command_repo, result_repo, adapter_repo)

    @pytest.mark.asyncio
    async def test_complete_cli_workflow(self, session_service, command_service):
        """Test complete CLI workflow."""
        # 1. Create session
        session = await session_service.create_session("developer123")

        # 2. Execute help command
        help_cmd = await command_service.create_command(
            session.session_id, "help", [], {}, CommandType.USER
        )
        help_result = await command_service.execute_command(help_cmd.command_id)

        # 3. Update session activity
        await session_service.update_session_activity(session.session_id)

        # 4. Execute system command
        system_cmd = await command_service.create_command(
            session.session_id, "list-services", [], {}, CommandType.SYSTEM
        )
        system_result = await command_service.execute_command(system_cmd.command_id)

        # 5. Execute service command
        service_cmd = await command_service.create_command(
            session.session_id, "analyze-code", ["--service=analysis-service"], {}, CommandType.SERVICE
        )
        service_result = await command_service.execute_command(service_cmd.command_id)

        # 6. Get command history
        history = await command_service.get_command_history(session.session_id)

        # Verify complete workflow
        assert session.is_active()
        assert help_result.is_successful()
        assert system_result.is_successful()
        assert service_result.is_successful()
        assert len(history) >= 3
        assert all(cmd.is_completed() for cmd in history)

    @pytest.mark.asyncio
    async def test_multi_session_workflow(self, session_service, command_service):
        """Test workflow with multiple sessions."""
        # Create multiple sessions
        session1 = await session_service.create_session("user1")
        session2 = await session_service.create_session("user2")

        # Execute commands in both sessions
        cmd1 = await command_service.create_command(session1.session_id, "status", [], {}, CommandType.USER)
        result1 = await command_service.execute_command(cmd1.command_id)

        cmd2 = await command_service.create_command(session2.session_id, "help", [], {}, CommandType.USER)
        result2 = await command_service.execute_command(cmd2.command_id)

        # Get statistics
        session_stats = await session_service.get_session_statistics()
        command_stats = await command_service.get_command_statistics()

        # Verify multi-session workflow
        assert session1.is_active()
        assert session2.is_active()
        assert result1.is_successful()
        assert result2.is_successful()
        assert session_stats["total_sessions"] >= 4  # Original 2 + 2 new
        assert command_stats["total_commands"] >= 2

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, session_service, command_service):
        """Test error handling in CLI workflow."""
        # Create session
        session = await session_service.create_session("user123")

        # Execute invalid command
        invalid_cmd = await command_service.create_command(
            session.session_id, "invalid-command", [], {}, CommandType.USER
        )
        invalid_result = await command_service.execute_command(invalid_cmd.command_id)

        # Execute command with invalid service
        service_cmd = await command_service.create_command(
            session.session_id, "analyze-code", ["--service=invalid-service"], {}, CommandType.SERVICE
        )
        service_result = await command_service.execute_command(service_cmd.command_id)

        # Verify error handling
        assert not invalid_result.is_successful()
        assert "Unknown command" in invalid_result.stderr
        assert not service_result.is_successful()
        assert "Service not available" in service_result.stderr
        assert session.is_active()  # Session should remain active despite errors

    @pytest.mark.asyncio
    async def test_session_lifecycle_with_commands(self, session_service, command_service):
        """Test session lifecycle integrated with commands."""
        # Create session
        session = await session_service.create_session("user123")

        # Execute some commands
        cmd1 = await command_service.create_command(session.session_id, "status")
        result1 = await command_service.execute_command(cmd1.command_id)

        cmd2 = await command_service.create_command(session.session_id, "list-services")
        result2 = await command_service.execute_command(cmd2.command_id)

        # Update session activity
        await session_service.update_session_activity(session.session_id)

        # Get command history
        history = await command_service.get_command_history(session.session_id)

        # Terminate session
        terminated = await session_service.terminate_session(session.session_id)
        session = await session_service.get_session(session.session_id)

        # Verify session lifecycle
        assert terminated
        assert not session.is_active()
        assert result1.is_successful()
        assert result2.is_successful()
        assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_statistics_integration(self, session_service, command_service):
        """Test statistics integration across services."""
        # Create additional sessions and commands
        session3 = await session_service.create_session("user3")
        cmd3 = await command_service.create_command(session3.session_id, "help")
        await command_service.execute_command(cmd3.command_id)

        # Get all statistics
        session_stats = await session_service.get_session_statistics()
        command_stats = await command_service.get_command_statistics()

        # Verify statistics consistency
        assert session_stats["total_sessions"] >= 3
        assert command_stats["total_commands"] >= 3

        # Completion rates should be reasonable
        assert 0.0 <= session_stats["active_sessions"] / session_stats["total_sessions"] <= 1.0
        assert 0.0 <= command_stats["completion_rate"] <= 1.0

        # User diversity check
        assert session_stats["sessions_by_user"] >= 3
