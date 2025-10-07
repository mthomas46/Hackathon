"""LogEntry Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class LogEntry:
    """
    Log entry entity.
    
    Represents a single log message with metadata, context,
    and correlation information.
    """
    
    # Identity
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    
    # Content
    message: str = ""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Source
    service: str = ""
    source: str = ""  # Module, function, file
    host: str = ""
    environment: str = "production"
    
    # Timing
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Technical details
    stack_trace: Optional[str] = None
    exception: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    fields: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing
    indexed: bool = False
    indexed_at: Optional[datetime] = None
    processed: bool = False
    
    def __post_init__(self):
        """Validate log entry."""
        if not self.entry_id:
            self.entry_id = str(uuid4())
        if not self.message:
            raise ValueError("Log message is required")
        if not self.service:
            raise ValueError("Service name is required")
        
        # Validate log level
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}")
        self.level = self.level.upper()
    
    def add_tag(self, tag: str) -> None:
        """Add tag to log entry."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def add_field(self, key: str, value: Any) -> None:
        """Add custom field."""
        self.fields[key] = value
    
    def mark_indexed(self) -> None:
        """Mark as indexed in Elasticsearch."""
        self.indexed = True
        self.indexed_at = datetime.now(timezone.utc)
    
    def mark_processed(self) -> None:
        """Mark as processed."""
        self.processed = True
    
    def is_error(self) -> bool:
        """Check if log entry is an error."""
        return self.level in ("ERROR", "CRITICAL")
    
    def is_warning(self) -> bool:
        """Check if log entry is a warning."""
        return self.level == "WARNING"
    
    def has_exception(self) -> bool:
        """Check if log entry has exception."""
        return self.exception is not None or self.stack_trace is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "message": self.message,
            "level": self.level,
            "service": self.service,
            "source": self.source,
            "host": self.host,
            "environment": self.environment,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "stack_trace": self.stack_trace,
            "exception": self.exception,
            "tags": self.tags,
            "fields": self.fields,
            "metadata": self.metadata,
            "indexed": self.indexed,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "processed": self.processed,
        }

