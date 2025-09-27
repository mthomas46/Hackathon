"""CLI Session domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from .cli_command import CLICommand


class SessionStatus(Enum):
    """Status of CLI session."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"


@dataclass
class CLISession:
    """Domain entity representing a CLI session."""

    id: str
    user_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE

    # Session timing
    started_at: datetime = field(default_factory=datetime.now)
    last_activity_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None

    # Session data
    environment: Dict[str, str] = field(default_factory=dict)
    working_directory: str = field(default_factory=lambda: "/")
    command_history: List[CLICommand] = field(default_factory=list)

    # Session configuration
    interactive_mode: bool = False
    auto_save_history: bool = True
    max_history_size: int = 1000

    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization validation."""
        self._validate()

    def _validate(self) -> None:
        """Validate session data."""
        self.validation_errors = []

        if not self.id or not self.id.strip():
            self.validation_errors.append("Session ID cannot be empty")
            self.is_valid = False

        if self.status not in SessionStatus:
            self.validation_errors.append(f"Invalid session status: {self.status}")
            self.is_valid = False

        if self.max_history_size < 0:
            self.validation_errors.append("Max history size cannot be negative")
            self.is_valid = False

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = datetime.now()

    def add_command(self, command: CLICommand) -> None:
        """Add a command to the session history."""
        self.command_history.append(command)

        # Maintain history size limit
        if len(self.command_history) > self.max_history_size:
            self.command_history = self.command_history[-self.max_history_size:]

        self.update_activity()

    def terminate(self) -> None:
        """Terminate the session."""
        self.status = SessionStatus.TERMINATED
        self.ended_at = datetime.now()

    def get_recent_commands(self, limit: int = 10) -> List[CLICommand]:
        """Get recent commands from history."""
        return self.command_history[-limit:] if self.command_history else []

    def get_command_by_id(self, command_id: str) -> Optional[CLICommand]:
        """Get a specific command by ID."""
        for command in self.command_history:
            if command.id == command_id:
                return command
        return None

    def get_session_duration(self) -> Optional[float]:
        """Get session duration in seconds."""
        end_time = self.ended_at or datetime.now()
        if self.started_at:
            return (end_time - self.started_at).total_seconds()
        return None

    def get_active_commands(self) -> List[CLICommand]:
        """Get commands that are currently running."""
        return [cmd for cmd in self.command_history if cmd.is_running]

    def clear_history(self) -> None:
        """Clear command history."""
        self.command_history = []

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == SessionStatus.ACTIVE

    @property
    def command_count(self) -> int:
        """Get total number of commands executed."""
        return len(self.command_history)

    @property
    def successful_command_count(self) -> int:
        """Get number of successful commands."""
        return len([cmd for cmd in self.command_history if cmd.is_successful])

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'environment': self.environment,
            'working_directory': self.working_directory,
            'command_count': self.command_count,
            'interactive_mode': self.interactive_mode,
            'auto_save_history': self.auto_save_history,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors
        }

