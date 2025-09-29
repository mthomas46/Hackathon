"""Query Execution Result Value Object"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    """Enumeration of query execution statuses."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self in (ExecutionStatus.SUCCESS, ExecutionStatus.PARTIAL_SUCCESS)

    @property
    def is_final(self) -> bool:
        """Check if execution status is final."""
        return self != ExecutionStatus.PARTIAL_SUCCESS  # Could still be running

    def __str__(self) -> str:
        return self.value


class QueryExecutionResult:
    """Value object representing the result of executing a query."""

    def __init__(
        self,
        query_id: str,
        execution_id: str,
        status: ExecutionStatus,
        results: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_time_seconds: Optional[float] = None,
        services_used: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_timestamp: Optional[datetime] = None
    ):
        self._query_id = query_id
        self._execution_id = execution_id
        self._status = status
        self._results = results or {}
        self._error_message = error_message
        self._execution_time_seconds = execution_time_seconds
        self._services_used = services_used or []
        self._metadata = metadata or {}
        self._execution_timestamp = execution_timestamp or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate query execution result data."""
        if not self._query_id:
            raise ValueError("Query ID cannot be empty")

        if not self._execution_id:
            raise ValueError("Execution ID cannot be empty")

        if self._status == ExecutionStatus.FAILED and not self._error_message:
            raise ValueError("Error message required for failed executions")

    @property
    def query_id(self) -> str:
        """Get the query ID."""
        return self._query_id

    @property
    def execution_id(self) -> str:
        """Get the execution ID."""
        return self._execution_id

    @property
    def status(self) -> ExecutionStatus:
        """Get the execution status."""
        return self._status

    @property
    def results(self) -> Dict[str, Any]:
        """Get the execution results."""
        return self._results.copy()

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message."""
        return self._error_message

    @property
    def execution_time_seconds(self) -> Optional[float]:
        """Get the execution time in seconds."""
        return self._execution_time_seconds

    @property
    def services_used(self) -> list[str]:
        """Get the list of services used."""
        return self._services_used.copy()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the execution metadata."""
        return self._metadata.copy()

    @property
    def execution_timestamp(self) -> datetime:
        """Get the execution timestamp."""
        return self._execution_timestamp

    @property
    def has_results(self) -> bool:
        """Check if execution produced results."""
        return len(self._results) > 0

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self._status.is_successful

    @property
    def has_errors(self) -> bool:
        """Check if execution had errors."""
        return self._status == ExecutionStatus.FAILED

    def add_result(self, key: str, value: Any):
        """Add a result to the execution results."""
        self._results[key] = value

    def add_service_used(self, service_name: str):
        """Add a service to the list of services used."""
        if service_name not in self._services_used:
            self._services_used.append(service_name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "query_id": self._query_id,
            "execution_id": self._execution_id,
            "status": self._status.value,
            "results": self._results,
            "services_used": self._services_used,
            "metadata": self._metadata,
            "execution_timestamp": self._execution_timestamp.isoformat(),
            "has_results": self.has_results,
            "is_successful": self.is_successful,
            "has_errors": self.has_errors
        }

        if self._error_message:
            result["error_message"] = self._error_message

        if self._execution_time_seconds is not None:
            result["execution_time_seconds"] = self._execution_time_seconds

        return result

    def __repr__(self) -> str:
        return f"QueryExecutionResult(query_id='{self._query_id}', execution_id='{self._execution_id}', status={self._status}, successful={self.is_successful})"
