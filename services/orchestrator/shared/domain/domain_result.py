"""Domain Result Class"""

from typing import Generic, TypeVar, Optional, List
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class DomainResult(Generic[T]):
    """Standardized result wrapper for domain operations."""

    success: bool
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    message: Optional[str] = None

    @classmethod
    def success_result(cls, data: T, message: Optional[str] = None) -> 'DomainResult[T]':
        """Create a successful result."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def failure_result(cls, errors: List[str], message: Optional[str] = None) -> 'DomainResult[T]':
        """Create a failure result."""
        return cls(success=False, errors=errors, message=message)

    @classmethod
    def single_error(cls, error: str, message: Optional[str] = None) -> 'DomainResult[T]':
        """Create a failure result with a single error."""
        return cls(success=False, errors=[error], message=message)

    def is_success(self) -> bool:
        """Check if result is successful."""
        return self.success

    def is_failure(self) -> bool:
        """Check if result is a failure."""
        return not self.success

    def get_errors_string(self) -> str:
        """Get errors as a single string."""
        if not self.errors:
            return ""
        return "; ".join(self.errors)
