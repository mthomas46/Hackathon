"""Log Entry domain entity for DDD compliance."""

from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Domain entity representing a log entry."""

    id: str
    service: str
    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    @property
    def is_error(self) -> bool:
        """Check if this is an error log."""
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]

    @property
    def formatted_message(self) -> str:
        """Get formatted log message."""
        return f"[{self.timestamp.isoformat()}] {self.service} {self.level.value}: {self.message}"
