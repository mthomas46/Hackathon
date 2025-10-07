"""Alert Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class Alert:
    """
    Alert entity.
    
    Represents an alert triggered by log conditions or anomalies.
    """
    
    # Identity
    alert_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    
    # Classification
    severity: str = "medium"  # low, medium, high, critical
    category: str = "error"  # error, performance, security, anomaly
    
    # Trigger
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trigger_condition: str = ""
    trigger_count: int = 1
    
    # Context
    service: str = ""
    environment: str = "production"
    description: str = ""
    
    # Related entities
    anomaly_id: Optional[str] = None
    stream_id: Optional[str] = None
    log_entry_ids: List[str] = field(default_factory=list)
    
    # Status
    status: str = "active"  # active, acknowledged, resolved, silenced
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    # Resolution
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Notification
    notified: bool = False
    notified_at: Optional[datetime] = None
    notification_channels: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate alert."""
        if not self.alert_id:
            self.alert_id = str(uuid4())
        if not self.name:
            raise ValueError("Alert name is required")
        if not self.service:
            raise ValueError("Service name is required")
    
    def acknowledge(self, user: str) -> None:
        """Acknowledge alert."""
        self.acknowledged = True
        self.acknowledged_at = datetime.now(timezone.utc)
        self.acknowledged_by = user
        self.status = "acknowledged"
    
    def resolve(self, notes: str) -> None:
        """Resolve alert."""
        self.status = "resolved"
        self.resolved_at = datetime.now(timezone.utc)
        self.resolution_notes = notes
    
    def silence(self) -> None:
        """Silence alert."""
        self.status = "silenced"
    
    def mark_notified(self, channels: List[str]) -> None:
        """Mark as notified."""
        self.notified = True
        self.notified_at = datetime.now(timezone.utc)
        self.notification_channels = channels
    
    def increment_trigger_count(self) -> None:
        """Increment trigger count."""
        self.trigger_count += 1
        self.triggered_at = datetime.now(timezone.utc)
    
    def is_critical(self) -> bool:
        """Check if alert is critical."""
        return self.severity == "critical"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "severity": self.severity,
            "category": self.category,
            "triggered_at": self.triggered_at.isoformat(),
            "trigger_condition": self.trigger_condition,
            "trigger_count": self.trigger_count,
            "service": self.service,
            "environment": self.environment,
            "description": self.description,
            "anomaly_id": self.anomaly_id,
            "stream_id": self.stream_id,
            "log_entry_ids": self.log_entry_ids,
            "status": self.status,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "notified": self.notified,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "notification_channels": self.notification_channels,
            "metadata": self.metadata,
        }

