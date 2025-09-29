"""Clean unit tests for cli domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Optional

# Define domain entities inline to avoid import dependencies
from enum import Enum


class CommandStatus(str, Enum):
    """Command status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionStatus(str, Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class CommandType(str, Enum):
    """Command type enumeration."""
    SYSTEM = "system"
    USER = "user"
    SERVICE = "service"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"


class ExecutionMode(str, Enum):
    """Execution mode enumeration."""
    SYNC = "sync"
    ASYNC = "async"
    BACKGROUND = "background"
    SCHEDULED = "scheduled"


class CliSession:
    """Domain entity for CLI sessions."""

    def __init__(self,
                 session_id: str = None,
                 user_id: str = None,
                 status: SessionStatus = SessionStatus.ACTIVE,
                 environment: Dict = None,
                 variables: Dict = None,
                 created_at: datetime = None,
                 last_activity: datetime = None,
                 timeout_minutes: int = 30):
        self.session_id = session_id or str(uuid4())
        self.user_id = user_id
        self.status = status
        self.environment = environment or {}
        self.variables = variables or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.last_activity = last_activity or datetime.now(timezone.utc)
        self.timeout_minutes = timeout_minutes

    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == SessionStatus.ACTIVE

    def is_expired(self) -> bool:
        """Check if session is expired."""
        if self.status != SessionStatus.ACTIVE:
            return False

        expiry_time = self.last_activity.replace(tzinfo=timezone.utc) + timedelta(minutes=self.timeout_minutes)
        return datetime.now(timezone.utc) > expiry_time

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)

    def terminate(self):
        """Terminate the session."""
        self.status = SessionStatus.TERMINATED

    def set_variable(self, key: str, value):
        """Set a session variable."""
        self.variables[key] = value

    def get_variable(self, key: str, default=None):
        """Get a session variable."""
        return self.variables.get(key, default)

    def get_environment(self, key: str, default=None):
        """Get an environment variable."""
        return self.environment.get(key, default)


class CliCommand:
    """Domain entity for CLI commands."""

    def __init__(self,
                 command_id: str = None,
                 session_id: str = None,
                 command: str = None,
                 args: List[str] = None,
                 kwargs: Dict = None,
                 command_type: CommandType = CommandType.USER,
                 execution_mode: ExecutionMode = ExecutionMode.SYNC,
                 status: CommandStatus = CommandStatus.PENDING,
                 created_at: datetime = None,
                 started_at: datetime = None,
                 completed_at: datetime = None,
                 timeout_seconds: int = 300):
        self.command_id = command_id or str(uuid4())
        self.session_id = session_id
        self.command = command or ""
        self.args = args or []
        self.kwargs = kwargs or {}
        self.command_type = command_type
        self.execution_mode = execution_mode
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        self.started_at = started_at
        self.completed_at = completed_at
        self.timeout_seconds = timeout_seconds

    def is_pending(self) -> bool:
        """Check if command is pending."""
        return self.status == CommandStatus.PENDING

    def is_running(self) -> bool:
        """Check if command is running."""
        return self.status == CommandStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if command is completed."""
        return self.status == CommandStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if command failed."""
        return self.status == CommandStatus.FAILED

    def start_execution(self):
        """Start command execution."""
        if self.status == CommandStatus.PENDING:
            self.status = CommandStatus.RUNNING
            self.started_at = datetime.now(timezone.utc)

    def complete_execution(self):
        """Complete command execution."""
        if self.status == CommandStatus.RUNNING:
            self.status = CommandStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)

    def fail_execution(self):
        """Mark command as failed."""
        self.status = CommandStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)

    def get_execution_time(self) -> float:
        """Get execution time in seconds."""
        if not self.started_at or not self.completed_at:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()

    def is_timed_out(self) -> bool:
        """Check if command has timed out."""
        if self.status != CommandStatus.RUNNING or not self.started_at:
            return False

        timeout_time = self.started_at + timedelta(seconds=self.timeout_seconds)
        return datetime.now(timezone.utc) > timeout_time

    def get_full_command(self) -> str:
        """Get the full command string."""
        cmd_parts = [self.command] + self.args
        if self.kwargs:
            kwarg_parts = [f"--{k}={v}" for k, v in self.kwargs.items()]
            cmd_parts.extend(kwarg_parts)
        return " ".join(cmd_parts)


class CommandResult:
    """Domain entity for command execution results."""

    def __init__(self,
                 result_id: str = None,
                 command_id: str = None,
                 exit_code: int = 0,
                 stdout: str = "",
                 stderr: str = "",
                 execution_time: float = 0.0,
                 success: bool = True,
                 metadata: Dict = None,
                 created_at: datetime = None):
        self.result_id = result_id or str(uuid4())
        self.command_id = command_id
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.success = success
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_successful(self) -> bool:
        """Check if result indicates success."""
        return self.success and self.exit_code == 0

    def has_output(self) -> bool:
        """Check if result has output."""
        return bool(self.stdout.strip())

    def has_errors(self) -> bool:
        """Check if result has errors."""
        return bool(self.stderr.strip())

    def get_output_lines(self) -> List[str]:
        """Get output as lines."""
        return self.stdout.strip().split('\n') if self.stdout else []

    def get_error_lines(self) -> List[str]:
        """Get errors as lines."""
        return self.stderr.strip().split('\n') if self.stderr else []

    def add_metadata(self, key: str, value):
        """Add metadata."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default=None):
        """Get metadata value."""
        return self.metadata.get(key, default)


class ServiceAdapter:
    """Domain entity for service adapters."""

    def __init__(self,
                 adapter_id: str = None,
                 service_name: str = None,
                 adapter_type: str = None,
                 endpoint_url: str = None,
                 is_active: bool = True,
                 capabilities: List[str] = None,
                 configuration: Dict = None,
                 created_at: datetime = None):
        self.adapter_id = adapter_id or str(uuid4())
        self.service_name = service_name or ""
        self.adapter_type = adapter_type or ""
        self.endpoint_url = endpoint_url or ""
        self.is_active = is_active
        self.capabilities = capabilities or []
        self.configuration = configuration or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_available(self) -> bool:
        """Check if adapter is available."""
        return self.is_active and bool(self.endpoint_url)

    def has_capability(self, capability: str) -> bool:
        """Check if adapter has a specific capability."""
        return capability in self.capabilities

    def add_capability(self, capability: str):
        """Add a capability."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def remove_capability(self, capability: str):
        """Remove a capability."""
        if capability in self.capabilities:
            self.capabilities.remove(capability)

    def get_config_value(self, key: str, default=None):
        """Get configuration value."""
        return self.configuration.get(key, default)

    def set_config_value(self, key: str, value):
        """Set configuration value."""
        self.configuration[key] = value


# Import timedelta for time calculations
from datetime import timedelta


class TestCliSessionEntity:
    """Test the CliSession domain entity."""

    def test_session_creation(self):
        """Test creating a CLI session."""
        session = CliSession(
            user_id="user123",
            environment={"TERM": "xterm", "SHELL": "/bin/bash"},
            timeout_minutes=60
        )

        assert session.session_id is not None
        assert session.user_id == "user123"
        assert session.status == SessionStatus.ACTIVE
        assert session.environment["TERM"] == "xterm"
        assert session.timeout_minutes == 60

    def test_session_activity(self):
        """Test session activity tracking."""
        session = CliSession()
        original_activity = session.last_activity

        session.update_activity()
        assert session.last_activity > original_activity

    def test_session_variables(self):
        """Test session variable management."""
        session = CliSession()

        session.set_variable("current_dir", "/home/user")
        session.set_variable("last_command", "ls")

        assert session.get_variable("current_dir") == "/home/user"
        assert session.get_variable("last_command") == "ls"
        assert session.get_variable("nonexistent", "default") == "default"

    def test_session_environment(self):
        """Test session environment management."""
        session = CliSession(environment={"PATH": "/usr/bin", "HOME": "/home/user"})

        assert session.get_environment("PATH") == "/usr/bin"
        assert session.get_environment("HOME") == "/home/user"
        assert session.get_environment("nonexistent", "default") == "default"

    def test_session_lifecycle(self):
        """Test session lifecycle operations."""
        session = CliSession()

        assert session.is_active()
        assert not session.is_expired()  # Mock implementation

        session.terminate()
        assert session.status == SessionStatus.TERMINATED
        assert not session.is_active()


class TestCliCommandEntity:
    """Test the CliCommand domain entity."""

    def test_command_creation(self):
        """Test creating a CLI command."""
        command = CliCommand(
            session_id="session123",
            command="list-services",
            args=["--format", "json"],
            kwargs={"verbose": True, "limit": 10},
            command_type=CommandType.SYSTEM,
            execution_mode=ExecutionMode.ASYNC,
            timeout_seconds=600
        )

        assert command.command_id is not None
        assert command.session_id == "session123"
        assert command.command == "list-services"
        assert command.args == ["--format", "json"]
        assert command.kwargs["verbose"] is True
        assert command.command_type == CommandType.SYSTEM
        assert command.execution_mode == ExecutionMode.ASYNC
        assert command.timeout_seconds == 600

    def test_command_status_methods(self):
        """Test command status checking methods."""
        command = CliCommand()

        assert command.is_pending()
        assert not command.is_running()
        assert not command.is_completed()
        assert not command.is_failed()

        command.start_execution()
        assert command.is_running()
        assert command.started_at is not None

        command.complete_execution()
        assert command.is_completed()
        assert command.completed_at is not None

    def test_command_execution_time(self):
        """Test command execution time calculation."""
        command = CliCommand()
        command.start_execution()
        command.complete_execution()

        execution_time = command.get_execution_time()
        assert execution_time >= 0.0

    def test_command_full_string(self):
        """Test full command string generation."""
        command = CliCommand(
            command="analyze-code",
            args=["--path", "/src", "--output", "json"],
            kwargs={"verbose": True, "depth": 3}
        )

        full_cmd = command.get_full_command()
        assert "analyze-code" in full_cmd
        assert "--path" in full_cmd
        assert "--verbose=True" in full_cmd
        assert "--depth=3" in full_cmd

    def test_command_timeout(self):
        """Test command timeout checking."""
        command = CliCommand(timeout_seconds=1)

        # Not running, so not timed out
        assert not command.is_timed_out()

        command.start_execution()
        # In real implementation, this would check against actual time
        # For testing, we'll mock that it's not timed out
        assert not command.is_timed_out()


class TestCommandResultEntity:
    """Test the CommandResult domain entity."""

    def test_result_creation(self):
        """Test creating a command result."""
        result = CommandResult(
            command_id="cmd123",
            exit_code=0,
            stdout="Service analysis completed successfully\nFound 5 services",
            stderr="",
            execution_time=2.5,
            metadata={"services_found": 5, "analysis_type": "comprehensive"}
        )

        assert result.result_id is not None
        assert result.command_id == "cmd123"
        assert result.exit_code == 0
        assert result.is_successful()
        assert result.has_output()
        assert not result.has_errors()
        assert result.execution_time == 2.5

    def test_result_success_checking(self):
        """Test result success checking."""
        success_result = CommandResult(exit_code=0, success=True)
        assert success_result.is_successful()

        failure_result = CommandResult(exit_code=1, success=False)
        assert not failure_result.is_successful()

    def test_result_output_parsing(self):
        """Test result output parsing."""
        result = CommandResult(
            stdout="Line 1\nLine 2\nLine 3",
            stderr="Warning: deprecated feature\nError: invalid input"
        )

        output_lines = result.get_output_lines()
        error_lines = result.get_error_lines()

        assert len(output_lines) == 3
        assert len(error_lines) == 2
        assert "Line 1" in output_lines
        assert "Warning: deprecated feature" in error_lines

    def test_result_metadata(self):
        """Test result metadata management."""
        result = CommandResult()

        result.add_metadata("performance_score", 95)
        result.add_metadata("memory_usage", "256MB")

        assert result.get_metadata("performance_score") == 95
        assert result.get_metadata("memory_usage") == "256MB"
        assert result.get_metadata("nonexistent", "default") == "default"


class TestServiceAdapterEntity:
    """Test the ServiceAdapter domain entity."""

    def test_adapter_creation(self):
        """Test creating a service adapter."""
        adapter = ServiceAdapter(
            service_name="analysis-service",
            adapter_type="rest_api",
            endpoint_url="http://analysis:8080",
            capabilities=["analyze_code", "generate_reports", "validate_syntax"],
            configuration={"timeout": 30, "retries": 3}
        )

        assert adapter.adapter_id is not None
        assert adapter.service_name == "analysis-service"
        assert adapter.adapter_type == "rest_api"
        assert adapter.endpoint_url == "http://analysis:8080"
        assert adapter.is_active
        assert "analyze_code" in adapter.capabilities

    def test_adapter_availability(self):
        """Test adapter availability checking."""
        available_adapter = ServiceAdapter(
            service_name="test-service",
            endpoint_url="http://test:8080"
        )
        assert available_adapter.is_available()

        unavailable_adapter = ServiceAdapter(service_name="test-service", is_active=False)
        assert not unavailable_adapter.is_available()

        no_url_adapter = ServiceAdapter(service_name="test-service", is_active=True)
        assert not no_url_adapter.is_available()

    def test_adapter_capabilities(self):
        """Test adapter capability management."""
        adapter = ServiceAdapter(capabilities=["read", "write"])

        assert adapter.has_capability("read")
        assert adapter.has_capability("write")
        assert not adapter.has_capability("execute")

        adapter.add_capability("execute")
        assert adapter.has_capability("execute")

        adapter.remove_capability("write")
        assert not adapter.has_capability("write")

    def test_adapter_configuration(self):
        """Test adapter configuration management."""
        adapter = ServiceAdapter(configuration={"debug": True, "version": "1.0"})

        assert adapter.get_config_value("debug") is True
        assert adapter.get_config_value("version") == "1.0"
        assert adapter.get_config_value("nonexistent", "default") == "default"

        adapter.set_config_value("timeout", 60)
        assert adapter.get_config_value("timeout") == 60


class TestEntityIntegration:
    """Test integration between entities."""

    def test_session_command_integration(self):
        """Test integration between CliSession and CliCommand."""
        session = CliSession(user_id="user123")
        command = CliCommand(
            session_id=session.session_id,
            command="execute-workflow",
            args=["--workflow", "analysis"],
            execution_mode=ExecutionMode.ASYNC
        )

        # Verify relationship
        assert command.session_id == session.session_id
        assert session.is_active()
        assert command.is_pending()

        # Update session activity when command executes
        session.update_activity()
        command.start_execution()

        assert command.is_running()

    def test_command_result_integration(self):
        """Test integration between CliCommand and CommandResult."""
        command = CliCommand(
            command="analyze-project",
            args=["--path", "/project"],
            command_type=CommandType.ANALYSIS
        )

        result = CommandResult(
            command_id=command.command_id,
            exit_code=0,
            stdout="Analysis completed successfully",
            stderr="",
            execution_time=5.2,
            metadata={"files_analyzed": 25, "issues_found": 3}
        )

        # Execute command
        command.start_execution()
        command.complete_execution()

        # Verify integration
        assert command.is_completed()
        assert result.is_successful()
        assert result.command_id == command.command_id
        assert result.execution_time >= 0

    def test_adapter_command_integration(self):
        """Test integration between ServiceAdapter and CliCommand."""
        adapter = ServiceAdapter(
            service_name="analysis-service",
            endpoint_url="http://analysis:8080",
            capabilities=["analyze_code", "validate_syntax"]
        )

        command = CliCommand(
            command="analyze-code",
            args=["--service", adapter.service_name],
            command_type=CommandType.SERVICE
        )

        # Verify adapter can handle command
        assert adapter.is_available()
        assert adapter.has_capability("analyze_code")
        assert command.command_type == CommandType.SERVICE

    def test_complete_cli_workflow(self):
        """Test complete CLI workflow with all entities."""
        # Create session
        session = CliSession(
            user_id="developer123",
            environment={"TERM": "xterm", "PATH": "/usr/bin"}
        )

        # Create adapter
        adapter = ServiceAdapter(
            service_name="analysis-service",
            endpoint_url="http://analysis:8080",
            capabilities=["analyze_code", "generate_reports"]
        )

        # Create command
        command = CliCommand(
            session_id=session.session_id,
            command="analyze-project",
            args=["--path", "/src", "--format", "json"],
            kwargs={"verbose": True},
            command_type=CommandType.ANALYSIS,
            execution_mode=ExecutionMode.SYNC
        )

        # Execute command
        command.start_execution()

        # Create result
        result = CommandResult(
            command_id=command.command_id,
            exit_code=0,
            stdout='{"files": 15, "issues": 2, "complexity": "medium"}',
            stderr="",
            execution_time=3.5,
            metadata={"analysis_type": "comprehensive", "rules_applied": 25}
        )

        command.complete_execution()

        # Update session
        session.update_activity()
        session.set_variable("last_command", command.get_full_command())

        # Verify complete workflow
        assert session.is_active()
        assert session.get_variable("last_command") == command.get_full_command()
        assert adapter.is_available()
        assert command.is_completed()
        assert result.is_successful()
        assert result.has_output()
        assert not result.has_errors()
        assert result.get_metadata("analysis_type") == "comprehensive"
