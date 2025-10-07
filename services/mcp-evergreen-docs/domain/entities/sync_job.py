"""SyncJob Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class SyncJob:
    """
    Synchronization job entity.
    
    Represents a job that synchronizes documentation from external sources.
    """
    
    # Identity
    job_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    
    # Configuration
    source_type: str = ""  # git, github_api, confluence, jira, etc.
    source_config: Dict[str, Any] = field(default_factory=dict)
    
    # Target
    target_path: str = ""
    file_patterns: List[str] = field(default_factory=list)
    
    # Status
    status: str = "pending"  # pending, running, completed, failed
    progress: int = 0  # 0-100
    
    # Results
    docs_synced: int = 0
    docs_created: int = 0
    docs_updated: int = 0
    docs_skipped: int = 0
    docs_failed: int = 0
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    triggered_by: str = "manual"  # manual, scheduled, webhook
    schedule: Optional[str] = None  # cron expression
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate sync job."""
        if not self.job_id:
            self.job_id = str(uuid4())
        if not self.name:
            raise ValueError("Sync job name is required")
        if not self.source_type:
            raise ValueError("Source type is required")
        if not self.target_path:
            raise ValueError("Target path is required")
    
    def start(self) -> None:
        """Start sync job."""
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)
        self.progress = 0
    
    def complete(self) -> None:
        """Complete sync job successfully."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        self.progress = 100
        
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = duration
    
    def fail(self, error: str) -> None:
        """
        Mark sync job as failed.
        
        Args:
            error: Error message
        """
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        self.errors.append(error)
        
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = duration
    
    def update_progress(self, progress: int) -> None:
        """
        Update progress.
        
        Args:
            progress: Progress percentage (0-100)
        """
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        self.progress = progress
    
    def increment_synced(self) -> None:
        """Increment synced count."""
        self.docs_synced += 1
    
    def increment_created(self) -> None:
        """Increment created count."""
        self.docs_created += 1
        self.docs_synced += 1
    
    def increment_updated(self) -> None:
        """Increment updated count."""
        self.docs_updated += 1
        self.docs_synced += 1
    
    def increment_skipped(self) -> None:
        """Increment skipped count."""
        self.docs_skipped += 1
    
    def increment_failed(self) -> None:
        """Increment failed count."""
        self.docs_failed += 1
    
    def add_error(self, error: str) -> None:
        """
        Add error message.
        
        Args:
            error: Error message
        """
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """
        Add warning message.
        
        Args:
            warning: Warning message
        """
        self.warnings.append(warning)
    
    def is_running(self) -> bool:
        """Check if job is running."""
        return self.status == "running"
    
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status in ("completed", "failed")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "source_type": self.source_type,
            "source_config": self.source_config,
            "target_path": self.target_path,
            "file_patterns": self.file_patterns,
            "status": self.status,
            "progress": self.progress,
            "docs_synced": self.docs_synced,
            "docs_created": self.docs_created,
            "docs_updated": self.docs_updated,
            "docs_skipped": self.docs_skipped,
            "docs_failed": self.docs_failed,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors,
            "warnings": self.warnings,
            "triggered_by": self.triggered_by,
            "schedule": self.schedule,
            "metadata": self.metadata,
        }

