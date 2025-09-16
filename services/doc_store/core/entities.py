"""Business domain entities for Doc Store service.

Defines core business objects and their relationships.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class Document:
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
class Analysis:
    """Analysis result entity."""
    id: str
    document_id: str
    analyzer: str
    model: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

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
class DocumentRelationship:
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
class DocumentTag:
    """Document tag entity."""
    id: str
    document_id: str
    tag: str
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)

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
class LifecyclePolicy:
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
