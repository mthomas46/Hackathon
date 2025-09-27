"""CLI Command domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class CommandStatus(Enum):
    """Status of CLI command execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandType(Enum):
    """Type of CLI command."""
    INTERACTIVE = "interactive"
    SINGLE_COMMAND = "single_command"
    BATCH = "batch"
    WORKFLOW = "workflow"


@dataclass
class CLICommand:
    """Domain entity representing a CLI command execution."""

    id: str
    name: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    command_type: CommandType = CommandType.SINGLE_COMMAND
    status: CommandStatus = CommandStatus.PENDING

    # Execution details
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None

    # Results
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None

    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    working_directory: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)

    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization validation."""
        self._validate()

    def _validate(self) -> None:
        """Validate command data."""
        self.validation_errors = []

        if not self.name or not self.name.strip():
            self.validation_errors.append("Command name cannot be empty")
            self.is_valid = False

        if self.command_type not in CommandType:
            self.validation_errors.append(f"Invalid command type: {self.command_type}")
            self.is_valid = False

        if self.status not in CommandStatus:
            self.validation_errors.append(f"Invalid command status: {self.status}")
            self.is_valid = False

    def start_execution(self) -> None:
        """Mark command as started."""
        self.status = CommandStatus.RUNNING
        self.started_at = datetime.now()

    def complete_execution(self, exit_code: int = 0, stdout: str = "", stderr: str = "") -> None:
        """Mark command as completed."""
        self.status = CommandStatus.COMPLETED if exit_code == 0 else CommandStatus.FAILED
        self.completed_at = datetime.now()
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def fail_execution(self, error_message: str) -> None:
        """Mark command as failed."""
        self.status = CommandStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message

        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()

    def cancel_execution(self) -> None:
        """Mark command as cancelled."""
        self.status = CommandStatus.CANCELLED
        self.completed_at = datetime.now()

        if self.started_at:
            self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds()

    @property
    def is_running(self) -> bool:
        """Check if command is currently running."""
        return self.status == CommandStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """Check if command has completed (successfully or with failure)."""
        return self.status in [CommandStatus.COMPLETED, CommandStatus.FAILED, CommandStatus.CANCELLED]

    @property
    def is_successful(self) -> bool:
        """Check if command completed successfully."""
        return self.status == CommandStatus.COMPLETED and self.exit_code == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'args': self.args,
            'kwargs': self.kwargs,
            'command_type': self.command_type.value,
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time_seconds': self.execution_time_seconds,
            'exit_code': self.exit_code,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'error_message': self.error_message,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'working_directory': self.working_directory,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors
        }

