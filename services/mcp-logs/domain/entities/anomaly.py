"""Anomaly Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class Anomaly:
    """
    Anomaly entity.
    
    Represents a detected anomaly in log patterns or metrics.
    """
    
    # Identity
    anomaly_id: str = field(default_factory=lambda: str(uuid4()))
    
    # Classification
    type: str = "pattern"  # pattern, rate, error_spike, metric
    severity: str = "medium"  # low, medium, high, critical
    
    # Detection
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detection_method: str = "statistical"  # statistical, ml, threshold
    confidence: float = 0.0  # 0.0 - 1.0
    
    # Context
    service: str = ""
    stream_id: Optional[str] = None
    description: str = ""
    
    # Metrics
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    deviation: Optional[float] = None
    
    # Related logs
    related_entry_ids: List[str] = field(default_factory=list)
    sample_messages: List[str] = field(default_factory=list)
    
    # Status
    status: str = "active"  # active, investigating, resolved, false_positive
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    # Resolution
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate anomaly."""
        if not self.anomaly_id:
            self.anomaly_id = str(uuid4())
        if not self.service:
            raise ValueError("Service name is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    def acknowledge(self, user: str) -> None:
        """Acknowledge anomaly."""
        self.acknowledged = True
        self.acknowledged_at = datetime.now(timezone.utc)
        self.acknowledged_by = user
        self.status = "investigating"
    
    def resolve(self, notes: str) -> None:
        """Resolve anomaly."""
        self.status = "resolved"
        self.resolved_at = datetime.now(timezone.utc)
        self.resolution_notes = notes
    
    def mark_false_positive(self) -> None:
        """Mark as false positive."""
        self.status = "false_positive"
        self.resolved_at = datetime.now(timezone.utc)
    
    def is_high_severity(self) -> bool:
        """Check if anomaly is high severity."""
        return self.severity in ("high", "critical")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anomaly_id": self.anomaly_id,
            "type": self.type,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "detection_method": self.detection_method,
            "confidence": self.confidence,
            "service": self.service,
            "stream_id": self.stream_id,
            "description": self.description,
            "baseline_value": self.baseline_value,
            "observed_value": self.observed_value,
            "deviation": self.deviation,
            "related_entry_ids": self.related_entry_ids,
            "sample_messages": self.sample_messages,
            "status": self.status,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "metadata": self.metadata,
        }

