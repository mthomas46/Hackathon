"""Command Result domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class ResultType(Enum):
    """Type of command result."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class CommandResult:
    """Domain entity representing the result of a CLI command execution."""

    command_id: str
    result_type: ResultType = ResultType.SUCCESS

    # Result data
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""

    # Timing
    executed_at: datetime = field(default_factory=datetime.now)
    execution_duration_seconds: Optional[float] = None

    # Metadata
    exit_code: int = 0
    has_output: bool = False
    output_format: str = "text"  # text, json, table, etc.

    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization validation."""
        self._validate()

    def _validate(self) -> None:
        """Validate result data."""
        self.validation_errors = []

        if not self.command_id or not self.command_id.strip():
            self.validation_errors.append("Command ID cannot be empty")
            self.is_valid = False

        if self.result_type not in ResultType:
            self.validation_errors.append(f"Invalid result type: {self.result_type}")
            self.is_valid = False

        if self.exit_code < 0:
            self.validation_errors.append("Exit code cannot be negative")
            self.is_valid = False

        if self.execution_duration_seconds is not None and self.execution_duration_seconds < 0:
            self.validation_errors.append("Execution duration cannot be negative")

    def set_success(self, data: Optional[Dict[str, Any]] = None, message: str = "") -> None:
        """Set result as successful."""
        self.result_type = ResultType.SUCCESS
        self.exit_code = 0
        if data:
            self.data = data
        if message:
            self.message = message
        self.has_output = bool(data or message)

    def set_error(self, message: str, exit_code: int = 1, data: Optional[Dict[str, Any]] = None) -> None:
        """Set result as error."""
        self.result_type = ResultType.ERROR
        self.exit_code = exit_code
        self.message = message
        if data:
            self.data = data
        self.has_output = True

    def set_warning(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Set result as warning."""
        self.result_type = ResultType.WARNING
        self.exit_code = 0
        self.message = message
        if data:
            self.data = data
        self.has_output = True

    def set_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Set result as info."""
        self.result_type = ResultType.INFO
        self.exit_code = 0
        self.message = message
        if data:
            self.data = data
        self.has_output = True

    def add_data(self, key: str, value: Any) -> None:
        """Add data to the result."""
        self.data[key] = value
        self.has_output = True

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the result."""
        return self.data.get(key, default)

    @property
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self.result_type == ResultType.SUCCESS and self.exit_code == 0

    @property
    def is_error(self) -> bool:
        """Check if result is an error."""
        return self.result_type == ResultType.ERROR or self.exit_code != 0

    @property
    def has_data(self) -> bool:
        """Check if result contains data."""
        return bool(self.data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            'command_id': self.command_id,
            'result_type': self.result_type.value,
            'data': self.data,
            'message': self.message,
            'executed_at': self.executed_at.isoformat(),
            'execution_duration_seconds': self.execution_duration_seconds,
            'exit_code': self.exit_code,
            'has_output': self.has_output,
            'output_format': self.output_format,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors
        }

