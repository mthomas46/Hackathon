"""Operation Result DTO - Application Layer.

This DTO provides standardized responses for operations.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from enum import Enum


class OperationStatus(str, Enum):
    """Status of an operation."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class OperationResultDTO:
    """
    Data Transfer Object for operation results.
    
    Provides a standardized way to communicate operation
    outcomes across layers.
    """
    
    status: OperationStatus
    message: str
    data: Optional[Any] = None
    errors: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success(cls, message: str, data: Any = None, **metadata) -> "OperationResultDTO":
        """Create a success result."""
        return cls(
            status=OperationStatus.SUCCESS,
            message=message,
            data=data,
            metadata=metadata,
        )
    
    @classmethod
    def failure(cls, message: str, errors: list[str] = None, **metadata) -> "OperationResultDTO":
        """Create a failure result."""
        return cls(
            status=OperationStatus.FAILURE,
            message=message,
            errors=errors or [],
            metadata=metadata,
        )
    
    @classmethod
    def partial(cls, message: str, data: Any = None, errors: list[str] = None, **metadata) -> "OperationResultDTO":
        """Create a partial success result."""
        return cls(
            status=OperationStatus.PARTIAL,
            message=message,
            data=data,
            errors=errors or [],
            metadata=metadata,
        )
    
    @classmethod
    def pending(cls, message: str, data: Any = None, **metadata) -> "OperationResultDTO":
        """Create a pending result."""
        return cls(
            status=OperationStatus.PENDING,
            message=message,
            data=data,
            metadata=metadata,
        )
    
    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.status == OperationStatus.SUCCESS
    
    def is_failure(self) -> bool:
        """Check if operation failed."""
        return self.status == OperationStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "metadata": self.metadata,
        }

