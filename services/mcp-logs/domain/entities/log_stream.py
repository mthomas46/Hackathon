"""LogStream Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from uuid import uuid4


@dataclass
class LogStream:
    """
    Log stream entity.
    
    Represents a continuous stream of logs from a specific source.
    """
    
    # Identity
    stream_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    
    # Source
    service: str = ""
    environment: str = "production"
    source_type: str = "application"  # application, system, infrastructure
    
    # Status
    status: str = "active"  # active, paused, stopped
    health: str = "healthy"  # healthy, degraded, unhealthy
    
    # Metrics
    total_entries: int = 0
    error_count: int = 0
    warning_count: int = 0
    last_entry_at: Optional[datetime] = None
    
    # Rate limiting
    rate_limit: int = 10000  # entries per second
    current_rate: float = 0.0
    
    # Lifecycle
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate log stream."""
        if not self.stream_id:
            self.stream_id = str(uuid4())
        if not self.name:
            raise ValueError("Stream name is required")
        if not self.service:
            raise ValueError("Service name is required")
    
    def start(self) -> None:
        """Start log stream."""
        self.status = "active"
        self.started_at = datetime.now(timezone.utc)
    
    def pause(self) -> None:
        """Pause log stream."""
        self.status = "paused"
    
    def stop(self) -> None:
        """Stop log stream."""
        self.status = "stopped"
        self.stopped_at = datetime.now(timezone.utc)
    
    def record_entry(self, is_error: bool = False, is_warning: bool = False) -> None:
        """Record log entry in stream."""
        self.total_entries += 1
        if is_error:
            self.error_count += 1
        if is_warning:
            self.warning_count += 1
        self.last_entry_at = datetime.now(timezone.utc)
    
    def update_health(self) -> None:
        """Update stream health based on error rate."""
        if self.total_entries == 0:
            self.health = "healthy"
            return
        
        error_rate = self.error_count / self.total_entries
        
        if error_rate > 0.1:  # > 10%
            self.health = "unhealthy"
        elif error_rate > 0.05:  # > 5%
            self.health = "degraded"
        else:
            self.health = "healthy"
    
    def get_error_rate(self) -> float:
        """Get error rate."""
        if self.total_entries == 0:
            return 0.0
        return self.error_count / self.total_entries
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stream_id": self.stream_id,
            "name": self.name,
            "service": self.service,
            "environment": self.environment,
            "source_type": self.source_type,
            "status": self.status,
            "health": self.health,
            "total_entries": self.total_entries,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "last_entry_at": self.last_entry_at.isoformat() if self.last_entry_at else None,
            "rate_limit": self.rate_limit,
            "current_rate": self.current_rate,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "config": self.config,
        }

