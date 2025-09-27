"""Type definitions and basic classes for intelligent ingestion."""

import hashlib
import json
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class IngestionPriority(Enum):
    """Data ingestion priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataSource(Enum):
    """Supported data sources."""

    GITHUB = "github"
    JIRA = "jira"
    CONFLUENCE = "confluence"
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    API = "api"


class ConflictResolutionStrategy(Enum):
    """Conflict resolution strategies."""

    LATEST_WINS = "latest_wins"
    OLDEST_WINS = "oldest_wins"
    MERGE = "merge"
    MANUAL = "manual"
    SOURCE_PRIORITY = "source_priority"


@dataclass
class DataIngestionJob:
    """Represents a data ingestion job with metadata and status tracking."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: DataSource = DataSource.FILESYSTEM
    priority: IngestionPriority = IngestionPriority.MEDIUM
    data_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    progress: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def start_job(self) -> None:
        """Mark job as started."""
        self.started_at = datetime.utcnow()
        self.status = "running"

    def complete_job(self) -> None:
        """Mark job as completed."""
        self.completed_at = datetime.utcnow()
        self.status = "completed"
        self.progress = 100.0

    def fail_job(self, error: str) -> None:
        """Mark job as failed with error message."""
        self.error_message = error
        self.status = "failed"

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1

    def get_duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "source": self.source.value,
            "priority": self.priority.value,
            "data_path": self.data_path,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "progress": self.progress,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "dependencies": self.dependencies,
            "tags": self.tags
        }


@dataclass
class DataQualityMetrics:
    """Metrics for assessing data quality during ingestion."""

    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    missing_required_fields: int = 0
    data_type_errors: int = 0
    constraint_violations: int = 0
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    consistency_score: float = 0.0
    timeliness_score: float = 0.0
    overall_quality_score: float = 0.0
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)

    def calculate_scores(self) -> None:
        """Calculate quality scores based on metrics."""
        if self.total_records > 0:
            self.completeness_score = self.valid_records / self.total_records
            self.accuracy_score = 1.0 - (self.data_type_errors / self.total_records)
            self.consistency_score = 1.0 - (self.constraint_violations / self.total_records)

            # Overall quality score (weighted average)
            self.overall_quality_score = (
                self.completeness_score * 0.4 +
                self.accuracy_score * 0.3 +
                self.consistency_score * 0.2 +
                self.timeliness_score * 0.1
            )

    def add_record_validation(self, is_valid: bool, has_duplicates: bool = False) -> None:
        """Add record validation results."""
        self.total_records += 1
        if is_valid and not has_duplicates:
            self.valid_records += 1
        elif has_duplicates:
            self.duplicate_records += 1
        else:
            self.invalid_records += 1

    def add_field_validation(self, missing_required: bool = False, data_type_error: bool = False) -> None:
        """Add field-level validation results."""
        if missing_required:
            self.missing_required_fields += 1
        if data_type_error:
            self.data_type_errors += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "duplicate_records": self.duplicate_records,
            "missing_required_fields": self.missing_required_fields,
            "data_type_errors": self.data_type_errors,
            "constraint_violations": self.constraint_violations,
            "completeness_score": self.completeness_score,
            "accuracy_score": self.accuracy_score,
            "consistency_score": self.consistency_score,
            "timeliness_score": self.timeliness_score,
            "overall_quality_score": self.overall_quality_score,
            "assessment_timestamp": self.assessment_timestamp.isoformat()
        }
