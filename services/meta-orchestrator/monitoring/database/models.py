"""Database models for configuration monitoring and drift detection"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import json


@dataclass
class ConfigurationSnapshot:
    """Snapshot of service configuration at a point in time"""
    id: Optional[int] = None
    service_name: str = ""
    config_hash: str = ""
    config_data: Dict[str, Any] = None
    timestamp: datetime = None
    source: str = "compose"  # compose, runtime, manual

    def __post_init__(self):
        if self.config_data is None:
            self.config_data = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigurationSnapshot':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data_copy)


@dataclass
class ConfigurationDrift:
    """Record of configuration drift detection"""
    id: Optional[int] = None
    service_name: str = ""
    drift_type: str = ""  # added, removed, modified, environment, ports, volumes
    severity: str = "low"  # low, medium, high, critical
    description: str = ""
    expected_value: Any = None
    actual_value: Any = None
    timestamp: datetime = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_action: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigurationDrift':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'resolved_at' in data and data['resolved_at']:
            data_copy['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        return cls(**data_copy)


@dataclass
class ServiceHealth:
    """Service health check record"""
    id: Optional[int] = None
    service_name: str = ""
    health_status: str = "unknown"  # healthy, unhealthy, degraded, unknown
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceHealth':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data_copy)


@dataclass
class Alert:
    """Alert record for configuration drift or health issues"""
    id: Optional[int] = None
    alert_type: str = ""  # drift, health, performance
    severity: str = "info"  # info, warning, error, critical
    service_name: str = ""
    title: str = ""
    message: str = ""
    timestamp: datetime = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.acknowledged_at:
            data['acknowledged_at'] = self.acknowledged_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'acknowledged_at' in data and data['acknowledged_at']:
            data_copy['acknowledged_at'] = datetime.fromisoformat(data['acknowledged_at'])
        if 'resolved_at' in data and data['resolved_at']:
            data_copy['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        return cls(**data_copy)


@dataclass
class DriftPattern:
    """Analysis of configuration drift patterns"""
    id: Optional[int] = None
    service_name: str = ""
    pattern_type: str = ""  # frequent_changes, seasonal, environmental, manual
    frequency: str = ""  # daily, weekly, monthly, irregular
    impact: str = "low"  # low, medium, high
    description: str = ""
    first_seen: datetime = None
    last_seen: datetime = None
    occurrence_count: int = 0
    affected_configs: List[str] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = datetime.utcnow()
        if self.last_seen is None:
            self.last_seen = datetime.utcnow()
        if self.affected_configs is None:
            self.affected_configs = []
        if self.recommendations is None:
            self.recommendations = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['first_seen'] = self.first_seen.isoformat()
        data['last_seen'] = self.last_seen.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriftPattern':
        """Create from dictionary"""
        data_copy = data.copy()
        data_copy['first_seen'] = datetime.fromisoformat(data['first_seen'])
        data_copy['last_seen'] = datetime.fromisoformat(data['last_seen'])
        return cls(**data_copy)
