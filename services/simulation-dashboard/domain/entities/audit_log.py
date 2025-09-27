"""Audit Log domain entity."""

from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from services.shared.domain import BaseEntity


class AuditAction(Enum):
    """Audit action enumeration."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    VIEW = "view"
    EXPORT = "export"


@dataclass
class AuditLog(BaseEntity):
    """Domain entity representing an audit log entry."""

    id: str
    user_id: str
    action: AuditAction
    resource_type: str
    resource_id: str
    details: Dict[str, Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        """Post initialization validation."""
        if not self.id:
            raise ValueError("Audit Log ID cannot be empty")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
