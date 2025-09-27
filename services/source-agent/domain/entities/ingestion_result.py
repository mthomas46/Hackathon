"""Ingestion result domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class IngestionResult:
    """Domain entity representing the result of a document ingestion operation.

    Tracks the outcome of fetching and processing documents from source systems,
    including success/failure status, metrics, and any errors encountered.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    source_type: str = ""
    operation_type: str = ""  # fetch, ingest, update, delete
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, partial_success

    # Metrics
    documents_processed: int = 0
    documents_succeeded: int = 0
    documents_failed: int = 0
    bytes_processed: int = 0

    # Results
    successful_documents: List[str] = field(default_factory=list)  # Document IDs
    failed_documents: Dict[str, str] = field(default_factory=dict)  # ID -> error message

    # Metadata
    parameters: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate ingestion result after initialization."""
        if not self.source_id.strip():
            raise ValueError("Source ID cannot be empty")
        if not self.operation_type.strip():
            raise ValueError("Operation type cannot be empty")

        valid_operations = ["fetch", "ingest", "update", "delete", "sync"]
        if self.operation_type.lower() not in valid_operations:
            raise ValueError(f"Invalid operation type: {self.operation_type}")

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get the duration of the ingestion operation."""
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.documents_processed == 0:
            return 0.0
        return (self.documents_succeeded / self.documents_processed) * 100.0

    @property
    def has_failures(self) -> bool:
        """Check if any documents failed to process."""
        return self.documents_failed > 0

    @property
    def is_complete(self) -> bool:
        """Check if the operation has completed."""
        return self.status in ["completed", "failed", "partial_success"]

    @property
    def is_successful(self) -> bool:
        """Check if the operation was successful."""
        return self.status in ["completed", "partial_success"]

    def record_success(self, document_id: str, bytes_processed: int = 0) -> None:
        """Record a successful document processing."""
        self.documents_processed += 1
        self.documents_succeeded += 1
        self.bytes_processed += bytes_processed

        if document_id not in self.successful_documents:
            self.successful_documents.append(document_id)

    def record_failure(self, document_id: str, error_message: str, bytes_processed: int = 0) -> None:
        """Record a failed document processing."""
        self.documents_processed += 1
        self.documents_failed += 1
        self.bytes_processed += bytes_processed
        self.failed_documents[document_id] = error_message

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def complete_successfully(self) -> None:
        """Mark the operation as completed successfully."""
        self.completed_at = datetime.now(timezone.utc)
        if self.has_failures:
            self.status = "partial_success"
        else:
            self.status = "completed"

    def complete_with_failure(self, error_message: str) -> None:
        """Mark the operation as failed."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = "failed"
        self.error_message = error_message

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the ingestion result."""
        return {
            "operation_id": self.id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "operation_type": self.operation_type,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "documents_processed": self.documents_processed,
            "documents_succeeded": self.documents_succeeded,
            "documents_failed": self.documents_failed,
            "success_rate": self.success_rate,
            "bytes_processed": self.bytes_processed,
            "warnings_count": len(self.warnings),
            "has_failures": self.has_failures,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "operation_type": self.operation_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "documents_processed": self.documents_processed,
            "documents_succeeded": self.documents_succeeded,
            "documents_failed": self.documents_failed,
            "bytes_processed": self.bytes_processed,
            "successful_documents": self.successful_documents,
            "failed_documents": self.failed_documents,
            "parameters": self.parameters,
            "error_message": self.error_message,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IngestionResult':
        """Create IngestionResult from dictionary."""
        # Handle datetime conversion
        for date_field in ['started_at', 'completed_at']:
            if isinstance(data.get(date_field), str):
                data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))

        return cls(**data)
