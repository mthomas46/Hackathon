"""
ServiceInfo Domain Entity

Represents a service in the ecosystem with its metadata and business rules.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class ServiceInfo:
    """Domain entity representing a service in the ecosystem.

    This entity encapsulates all information about a service including
    its location, type, status, and metadata with business rules.
    """

    name: str
    path: Path
    type: str = "python"  # python, docker, kubernetes
    status: str = "unknown"  # active, inactive, deprecated
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: Optional[datetime] = None
    last_audited_at: Optional[datetime] = None

    def __post_init__(self):
        """Apply business rules and validations."""
        self._validate_name()
        self._validate_type()
        self._validate_status()
        self._set_discovery_timestamp()

    def _validate_name(self) -> None:
        """Validate service name according to business rules."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Service name must be a non-empty string")

        if len(self.name) > 50:
            raise ValueError("Service name cannot exceed 50 characters")

        # Service names should follow kebab-case convention
        import re
        if not re.match(r'^[a-z][a-z0-9-]*$', self.name):
            raise ValueError("Service name must be in kebab-case format")

    def _validate_type(self) -> None:
        """Validate service type."""
        valid_types = {"python", "docker", "kubernetes", "node", "go", "rust"}
        if self.type not in valid_types:
            raise ValueError(f"Service type must be one of: {', '.join(sorted(valid_types))}")

    def _validate_status(self) -> None:
        """Validate service status."""
        valid_statuses = {"active", "inactive", "deprecated", "maintenance", "unknown"}
        if self.status not in valid_statuses:
            raise ValueError(f"Service status must be one of: {', '.join(sorted(valid_statuses))}")

    def _set_discovery_timestamp(self) -> None:
        """Set discovery timestamp if not provided."""
        if self.discovered_at is None:
            self.discovered_at = datetime.now()

    def mark_as_audited(self) -> None:
        """Mark the service as recently audited."""
        self.last_audited_at = datetime.now()

    def is_active(self) -> bool:
        """Check if the service is currently active."""
        return self.status == "active"

    def is_audit_due(self, audit_interval_days: int = 7) -> bool:
        """Check if the service is due for auditing."""
        if self.last_audited_at is None:
            return True

        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=audit_interval_days)
        return self.last_audited_at < cutoff

    def update_metadata(self, key: str, value: Any) -> None:
        """Update service metadata."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "path": str(self.path),
            "type": self.type,
            "status": self.status,
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "last_audited_at": self.last_audited_at.isoformat() if self.last_audited_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInfo':
        """Create ServiceInfo from dictionary."""
        # Handle path conversion
        path = Path(data["path"]) if isinstance(data.get("path"), str) else data["path"]

        # Handle timestamp conversion
        discovered_at = None
        if data.get("discovered_at"):
            from datetime import datetime
            discovered_at = datetime.fromisoformat(data["discovered_at"])

        last_audited_at = None
        if data.get("last_audited_at"):
            from datetime import datetime
            last_audited_at = datetime.fromisoformat(data["last_audited_at"])

        return cls(
            name=data["name"],
            path=path,
            type=data.get("type", "python"),
            status=data.get("status", "unknown"),
            metadata=data.get("metadata", {}),
            discovered_at=discovered_at,
            last_audited_at=last_audited_at,
        )
