"""Business domain entities for Doc Store service.

Defines core business objects and their relationships.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod


class BaseEntity(ABC):
    """Base entity with common fields and methods."""

    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        pass

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()


@dataclass
class Document(BaseEntity):
    """Core document entity."""
    id: str
    content: str
    content_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class Analysis(BaseEntity):
    """Analysis result entity."""
    id: str
    document_id: str
    analyzer: str
    model: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "analyzer": self.analyzer,
            "model": self.model,
            "result": self.result,
            "score": self.score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DocumentRelationship(BaseEntity):
    """Document relationship entity."""
    id: str
    source_document_id: str
    target_document_id: str
    relationship_type: str
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "source_document_id": self.source_document_id,
            "target_document_id": self.target_document_id,
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class GraphNode:
    """Graph node with document information."""
    document_id: str
    title: str = ""
    content_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    degree: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_id": self.document_id,
            "title": self.title,
            "content_type": self.content_type,
            "metadata": self.metadata,
            "degree": self.degree,
        }


@dataclass
class GraphEdge:
    """Graph edge with relationship information."""
    source_id: str
    target_id: str
    relationship_type: str
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "metadata": self.metadata,
        }


@dataclass
class DocumentTag(BaseEntity):
    """Document tag entity."""
    id: str
    document_id: str
    tag: str
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "tag": self.tag,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class LifecyclePolicy(BaseEntity):
    """Lifecycle policy entity."""
    id: str
    name: str
    description: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def matches_document(self, document: Dict[str, Any], lifecycle: Dict[str, Any]) -> bool:
        """Check if policy matches document."""
        try:
            conditions = self.conditions

            # Check content type
            if "content_types" in conditions:
                doc_type = document.get("metadata", {}).get("type", "")
                if doc_type not in conditions["content_types"]:
                    return False

            # Check age
            if "max_age_days" in conditions:
                from datetime import datetime
                created_at = datetime.fromisoformat(document["created_at"])
                age_days = (datetime.utcnow() - created_at).days
                if age_days < conditions["max_age_days"]:
                    return False

            # Check tags
            if "required_tags" in conditions:
                doc_tags = lifecycle.get("tags", [])
                required_tags = conditions["required_tags"]
                if not all(tag in doc_tags for tag in required_tags):
                    return False

            return True

        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "actions": self.actions,
            "priority": self.priority,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class BulkOperation:
    """Bulk operation entity."""
    operation_id: str
    operation_type: str
    status: str = "pending"
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "status": self.status,
            "progress": {
                "total": self.total_items,
                "processed": self.processed_items,
                "successful": self.successful_items,
                "failed": self.failed_items,
                "percentage": (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0
            },
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class NotificationEvent(BaseEntity):
    """Notification event entity."""
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class Webhook(BaseEntity):
    """Webhook configuration entity."""
    id: str
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    retry_count: int = 3
    timeout_seconds: int = 30
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "secret": "***" if self.secret else None,  # Don't expose secrets
            "events": self.events,
            "headers": self.headers,
            "is_active": self.is_active,
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class WebhookDelivery(BaseEntity):
    """Webhook delivery record entity."""
    id: str
    webhook_id: str
    event_id: str
    status: str
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int = 1
    delivered_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "event_id": self.event_id,
            "status": self.status,
            "response_code": self.response_code,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "attempt_count": self.attempt_count,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
