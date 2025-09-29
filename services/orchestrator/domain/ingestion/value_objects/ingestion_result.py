"""Ingestion Result Value Object"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4

from .ingestion_status import IngestionStatus


class IngestionResult:
    """Value object representing the result of an ingestion operation."""

    def __init__(
        self,
        request_id: str,
        status: IngestionStatus,
        ingestion_id: Optional[str] = None,
        total_items: int = 0,
        successful_items: int = 0,
        failed_items: int = 0,
        skipped_items: int = 0,
        errors: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_seconds: Optional[float] = None
    ):
        self._ingestion_id = ingestion_id or str(uuid4())
        self._request_id = request_id
        self._status = status
        self._total_items = max(0, total_items)
        self._successful_items = max(0, min(successful_items, self._total_items))
        self._failed_items = max(0, min(failed_items, self._total_items))
        self._skipped_items = max(0, min(skipped_items, self._total_items))
        self._errors = errors or []
        self._metadata = metadata or {}
        self._started_at = started_at
        self._completed_at = completed_at

        # Calculate duration if both timestamps are available
        if self._started_at and self._completed_at:
            self._duration_seconds = (self._completed_at - self._started_at).total_seconds()
        else:
            self._duration_seconds = duration_seconds

        self._validate()

    def _validate(self):
        """Validate ingestion result data."""
        if not self._request_id:
            raise ValueError("Request ID cannot be empty")

        if not isinstance(self._status, IngestionStatus):
            raise ValueError("Status must be a valid IngestionStatus")

        # Ensure item counts are consistent
        processed_items = self._successful_items + self._failed_items + self._skipped_items
        if processed_items > self._total_items:
            raise ValueError("Processed items cannot exceed total items")

    @property
    def ingestion_id(self) -> str:
        """Get the unique ingestion ID."""
        return self._ingestion_id

    @property
    def request_id(self) -> str:
        """Get the request ID."""
        return self._request_id

    @property
    def status(self) -> IngestionStatus:
        """Get the ingestion status."""
        return self._status

    @property
    def total_items(self) -> int:
        """Get the total number of items to process."""
        return self._total_items

    @property
    def successful_items(self) -> int:
        """Get the number of successfully processed items."""
        return self._successful_items

    @property
    def failed_items(self) -> int:
        """Get the number of failed items."""
        return self._failed_items

    @property
    def skipped_items(self) -> int:
        """Get the number of skipped items."""
        return self._skipped_items

    @property
    def processed_items(self) -> int:
        """Get the total number of processed items."""
        return self._successful_items + self._failed_items + self._skipped_items

    @property
    def errors(self) -> List[Dict[str, Any]]:
        """Get the list of errors."""
        return self._errors.copy()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the ingestion metadata."""
        return self._metadata.copy()

    @property
    def started_at(self) -> Optional[datetime]:
        """Get the start timestamp."""
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get the completion timestamp."""
        return self._completed_at

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get the duration in seconds."""
        return self._duration_seconds

    @property
    def success_rate(self) -> float:
        """Get the success rate as a percentage (0.0 to 1.0)."""
        if self._total_items == 0:
            return 1.0 if self._status.is_successful else 0.0
        return self._successful_items / self._total_items

    @property
    def progress_percentage(self) -> int:
        """Get the current progress percentage."""
        if self._status.is_final:
            return 100
        return self._status.progress_percentage

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self._errors) > 0

    @property
    def is_complete(self) -> bool:
        """Check if ingestion is complete."""
        return self._status.is_final

    @property
    def is_successful(self) -> bool:
        """Check if ingestion was successful."""
        return self._status.is_successful

    def add_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to the result."""
        error = {
            "type": error_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if details:
            error["details"] = details

        self._errors.append(error)

    def update_counts(self, successful: int = 0, failed: int = 0, skipped: int = 0):
        """Update the item counts."""
        self._successful_items += successful
        self._failed_items += failed
        self._skipped_items += skipped

        # Ensure we don't exceed total
        total_processed = self.processed_items
        if total_processed > self._total_items:
            excess = total_processed - self._total_items
            self._successful_items -= min(excess, self._successful_items)
            excess -= min(excess, self._successful_items)
            if excess > 0:
                self._failed_items -= min(excess, self._failed_items)

    def mark_started(self, timestamp: Optional[datetime] = None):
        """Mark the ingestion as started."""
        self._started_at = timestamp or datetime.utcnow()

    def mark_completed(self, status: IngestionStatus, timestamp: Optional[datetime] = None):
        """Mark the ingestion as completed."""
        self._status = status
        self._completed_at = timestamp or datetime.utcnow()

        if self._started_at and self._completed_at:
            self._duration_seconds = (self._completed_at - self._started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "ingestion_id": self._ingestion_id,
            "request_id": self._request_id,
            "status": self._status.value,
            "total_items": self._total_items,
            "successful_items": self._successful_items,
            "failed_items": self._failed_items,
            "skipped_items": self._skipped_items,
            "processed_items": self.processed_items,
            "errors": self._errors,
            "metadata": self._metadata,
            "success_rate": self.success_rate,
            "progress_percentage": self.progress_percentage,
            "has_errors": self.has_errors,
            "is_complete": self.is_complete,
            "is_successful": self.is_successful
        }

        if self._started_at:
            result["started_at"] = self._started_at.isoformat()

        if self._completed_at:
            result["completed_at"] = self._completed_at.isoformat()

        if self._duration_seconds is not None:
            result["duration_seconds"] = self._duration_seconds

        return result

    def __repr__(self) -> str:
        return f"IngestionResult(ingestion_id='{self._ingestion_id}', status={self._status}, success_rate={self.success_rate:.2f})"
