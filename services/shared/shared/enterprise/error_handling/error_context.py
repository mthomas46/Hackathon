"""Error context and recovery action classes."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .error_types import ErrorSeverity, ErrorCategory, RecoveryStrategy


@dataclass
class ErrorContext:
    """Context information for an error occurrence."""

    error_id: str = field(default_factory=lambda: str(uuid4()))
    service_name: str = ""
    operation: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN
    error_message: str = ""
    stack_trace: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "error_id": self.error_id,
            "service_name": self.service_name,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace[:500] if self.stack_trace else "",  # Truncate long traces
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass
class RecoveryAction:
    """Action to take for error recovery."""

    strategy: RecoveryStrategy
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    priority: int = 1  # Higher number = higher priority

    def should_retry(self) -> bool:
        """Check if retry should be attempted."""
        return self.strategy == RecoveryStrategy.RETRY

    def get_retry_delay(self) -> float:
        """Get retry delay in seconds."""
        return self.parameters.get("delay", 1.0)

    def get_max_retries(self) -> int:
        """Get maximum retry attempts."""
        return self.parameters.get("max_retries", 3)
