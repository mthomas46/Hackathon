"""Operation Result DTO."""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from enum import Enum


class OperationStatus(str, Enum):
    """Status of an operation."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class OperationResult:
    """
    Standardized operation result DTO.
    
    Provides consistent response format across all operations.
    """
    
    status: OperationStatus
    message: str
    data: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success(cls, message: str, data: Any = None, **metadata) -> "OperationResult":
        """Create a success result."""
        return cls(
            status=OperationStatus.SUCCESS,
            message=message,
            data=data,
            metadata=metadata,
        )
    
    @classmethod
    def failure(cls, message: str, errors: List[str] = None, **metadata) -> "OperationResult":
        """Create a failure result."""
        return cls(
            status=OperationStatus.FAILURE,
            message=message,
            errors=errors or [],
            metadata=metadata,
        )
    
    @classmethod
    def partial(cls, message: str, data: Any = None, errors: List[str] = None, **metadata) -> "OperationResult":
        """Create a partial success result."""
        return cls(
            status=OperationStatus.PARTIAL,
            message=message,
            data=data,
            errors=errors or [],
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

