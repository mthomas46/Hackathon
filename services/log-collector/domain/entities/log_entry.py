"""Log entry domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class LogEntry:
    """Domain entity representing a log entry.

    Encapsulates log data with proper typing and validation.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    service: str = ""
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    source: str = ""  # file, console, network, etc.
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate log entry after initialization."""
        if not self.message.strip():
            raise ValueError("Log message cannot be empty")
        if not self.service.strip():
            raise ValueError("Service name cannot be empty")
        if self.level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {self.level}")

    @property
    def is_error(self) -> bool:
        """Check if this is an error-level log entry."""
        return self.level in ["ERROR", "CRITICAL"]

    @property
    def is_warning(self) -> bool:
        """Check if this is a warning-level log entry."""
        return self.level == "WARNING"

    def add_tag(self, tag: str) -> None:
        """Add a tag to this log entry."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this log entry."""
        if tag in self.tags:
            self.tags.remove(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "service": self.service,
            "message": self.message,
            "metadata": self.metadata,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "source": self.source,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create LogEntry from dictionary."""
        # Handle timestamp conversion
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))

        return cls(**data)
