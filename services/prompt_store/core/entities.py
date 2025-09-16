"""Core entities for Prompt Store service.

Following domain-driven design principles with base entities and specific domain entities.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class BaseEntity(ABC):
    """Base entity with common fields and methods."""

    def __init__(self):
        self.id: Optional[str] = None
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """Create entity from dictionary representation."""
        pass

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class Prompt(BaseEntity):
    """Core prompt entity."""
    name: str
    category: str
    description: str = ""
    content: str = ""
    variables: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    is_template: bool = False
    lifecycle_status: str = "draft"  # draft, published, deprecated, archived
    created_by: str = ""
    version: int = 1
    parent_id: Optional[str] = None  # For forked prompts
    performance_score: float = 0.0
    usage_count: int = 0

    def __post_init__(self):
        """Initialize BaseEntity fields."""
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert prompt to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "content": self.content,
            "variables": self.variables,
            "tags": self.tags,
            "is_active": self.is_active,
            "is_template": self.is_template,
            "lifecycle_status": self.lifecycle_status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "parent_id": self.parent_id,
            "performance_score": self.performance_score,
            "usage_count": self.usage_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prompt':
        """Create prompt from dictionary."""
        prompt = cls(
            name=data["name"],
            category=data["category"],
            description=data.get("description", ""),
            content=data.get("content", ""),
            variables=data.get("variables", []),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True),
            is_template=data.get("is_template", False),
            lifecycle_status=data.get("lifecycle_status", "draft"),
            created_by=data.get("created_by", ""),
            version=data.get("version", 1),
            parent_id=data.get("parent_id"),
            performance_score=data.get("performance_score", 0.0),
            usage_count=data.get("usage_count", 0)
        )
        prompt.id = data.get("id")
        if "created_at" in data:
            prompt.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data:
            prompt.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        return prompt


@dataclass
class PromptVersion(BaseEntity):
    """Prompt version history entity."""
    prompt_id: str
    version: int
    content: str
    variables: List[str]
    change_summary: str = ""
    change_type: str = "update"  # create, update, fork, rollback
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "content": self.content,
            "variables": self.variables,
            "change_summary": self.change_summary,
            "change_type": self.change_type,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptVersion':
        """Create version from dictionary."""
        version = cls(
            prompt_id=data["prompt_id"],
            version=data["version"],
            content=data["content"],
            variables=data.get("variables", []),
            change_summary=data.get("change_summary", ""),
            change_type=data.get("change_type", "update"),
            created_by=data.get("created_by", "")
        )
        version.id = data.get("id")
        if "created_at" in data:
            version.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        return version


@dataclass
class ABTest(BaseEntity):
    """A/B testing configuration entity."""
    name: str
    description: str = ""
    prompt_a_id: str = ""
    prompt_b_id: str = ""
    test_metric: str = "response_quality"
    is_active: bool = True
    traffic_split: float = 0.5
    start_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None
    target_audience: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    winner: Optional[str] = None  # "A", "B", or None

    def to_dict(self) -> Dict[str, Any]:
        """Convert A/B test to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prompt_a_id": self.prompt_a_id,
            "prompt_b_id": self.prompt_b_id,
            "test_metric": self.test_metric,
            "is_active": self.is_active,
            "traffic_split": self.traffic_split,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "target_audience": self.target_audience,
            "created_by": self.created_by,
            "winner": self.winner,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ABTest':
        """Create A/B test from dictionary."""
        test = cls(
            name=data["name"],
            description=data.get("description", ""),
            prompt_a_id=data.get("prompt_a_id", ""),
            prompt_b_id=data.get("prompt_b_id", ""),
            test_metric=data.get("test_metric", "response_quality"),
            is_active=data.get("is_active", True),
            traffic_split=data.get("traffic_split", 0.5),
            target_audience=data.get("target_audience", {}),
            created_by=data.get("created_by", ""),
            winner=data.get("winner")
        )
        test.id = data.get("id")
        if "start_date" in data:
            test.start_date = datetime.fromisoformat(data["start_date"].replace('Z', '+00:00'))
        if "end_date" in data and data["end_date"]:
            test.end_date = datetime.fromisoformat(data["end_date"].replace('Z', '+00:00'))
        if "created_at" in data:
            test.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data:
            test.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        return test


@dataclass
class PromptUsage(BaseEntity):
    """Prompt usage tracking entity."""
    prompt_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    service_name: str = ""
    operation: str = "generate"
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    response_time_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert usage to dictionary."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "service_name": self.service_name,
            "operation": self.operation,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "response_time_ms": self.response_time_ms,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptUsage':
        """Create usage from dictionary."""
        usage = cls(
            prompt_id=data["prompt_id"],
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            service_name=data.get("service_name", ""),
            operation=data.get("operation", "generate"),
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            response_time_ms=data.get("response_time_ms"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {})
        )
        usage.id = data.get("id")
        if "created_at" in data:
            usage.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        return usage


@dataclass
class PromptRelationship(BaseEntity):
    """Prompt relationship entity for semantic connections."""
    source_prompt_id: str
    target_prompt_id: str
    relationship_type: str  # extends, references, alternative, similar
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary."""
        return {
            "id": self.id,
            "source_prompt_id": self.source_prompt_id,
            "target_prompt_id": self.target_prompt_id,
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptRelationship':
        """Create relationship from dictionary."""
        relationship = cls(
            source_prompt_id=data["source_prompt_id"],
            target_prompt_id=data["target_prompt_id"],
            relationship_type=data["relationship_type"],
            strength=data.get("strength", 1.0),
            metadata=data.get("metadata", {}),
            created_by=data.get("created_by", "")
        )
        relationship.id = data.get("id")
        if "created_at" in data:
            relationship.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data:
            relationship.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        return relationship


@dataclass
class ABTestResult(BaseEntity):
    """A/B test results and analytics entity."""
    test_id: str
    prompt_id: str
    metric_value: float
    sample_size: int
    confidence_level: float = 0.0
    statistical_significance: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert A/B test result to dictionary."""
        return {
            "id": self.id,
            "test_id": self.test_id,
            "prompt_id": self.prompt_id,
            "metric_value": self.metric_value,
            "sample_size": self.sample_size,
            "confidence_level": self.confidence_level,
            "statistical_significance": self.statistical_significance,
            "recorded_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ABTestResult':
        """Create A/B test result from dictionary."""
        result = cls(
            test_id=data["test_id"],
            prompt_id=data["prompt_id"],
            metric_value=data["metric_value"],
            sample_size=data["sample_size"],
            confidence_level=data.get("confidence_level", 0.0),
            statistical_significance=data.get("statistical_significance", False)
        )
        result.id = data.get("id")
        if "recorded_at" in data:
            result.created_at = datetime.fromisoformat(data["recorded_at"].replace('Z', '+00:00'))
        return result


@dataclass
class BulkOperation(BaseEntity):
    """Bulk operation tracking entity."""
    operation_type: str  # create_prompts, update_prompts, delete_prompts, tag_prompts
    status: str = "pending"  # pending, processing, completed, failed
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    created_by: str = ""

    def __init__(self, operation_type: str, status: str = "pending", total_items: int = 0,
                 processed_items: int = 0, successful_items: int = 0, failed_items: int = 0,
                 errors: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None,
                 results: Optional[List[Dict[str, Any]]] = None, completed_at: Optional[datetime] = None,
                 created_by: str = "", id: Optional[str] = None):
        """Initialize bulk operation with proper field handling."""
        super().__init__()
        self.id = id
        self.operation_type = operation_type
        self.status = status
        self.total_items = total_items
        self.processed_items = processed_items
        self.successful_items = successful_items
        self.failed_items = failed_items
        self.errors = errors or []
        self.metadata = metadata or {}
        self.results = results or []
        self.completed_at = completed_at
        self.created_by = created_by

    def to_dict(self) -> Dict[str, Any]:
        """Convert bulk operation to dictionary."""
        return {
            "id": self.id,
            "operation_type": self.operation_type,
            "status": self.status,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "errors": self.errors,
            "metadata": self.metadata,
            "results": self.results,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BulkOperation':
        """Create bulk operation from dictionary."""
        operation = cls(
            operation_type=data["operation_type"],
            status=data.get("status", "pending"),
            total_items=data.get("total_items", 0),
            processed_items=data.get("processed_items", 0),
            successful_items=data.get("successful_items", 0),
            failed_items=data.get("failed_items", 0),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {}),
            results=data.get("results", []),
            created_by=data.get("created_by", ""),
            id=data.get("id")
        )
        if "created_at" in data:
            operation.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "completed_at" in data and data["completed_at"]:
            operation.completed_at = datetime.fromisoformat(data["completed_at"].replace('Z', '+00:00'))
        return operation
