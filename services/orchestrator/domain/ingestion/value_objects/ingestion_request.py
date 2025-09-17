"""Ingestion Request Value Object"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4

from .ingestion_source_type import IngestionSourceType


class IngestionRequest:
    """Value object representing an ingestion request."""

    def __init__(
        self,
        source_url: str,
        source_type: IngestionSourceType,
        correlation_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        requested_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        request_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self._request_id = request_id or str(uuid4())
        self._source_url = source_url.strip()
        self._source_type = source_type
        self._correlation_id = correlation_id.strip() if correlation_id else None
        self._parameters = parameters or {}
        self._scope = scope or {}
        self._priority = max(1, min(10, priority))  # Priority 1-10
        self._requested_by = requested_by.strip() if requested_by else None
        self._tags = tags or []
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate ingestion request data."""
        if not self._source_url:
            raise ValueError("Source URL cannot be empty")

        if not isinstance(self._source_type, IngestionSourceType):
            raise ValueError("Source type must be a valid IngestionSourceType")

        if len(self._source_url) > 2000:
            raise ValueError("Source URL too long (max 2000 characters)")

        if self._correlation_id and len(self._correlation_id) > 255:
            raise ValueError("Correlation ID too long (max 255 characters)")

    @property
    def request_id(self) -> str:
        """Get the unique request ID."""
        return self._request_id

    @property
    def source_url(self) -> str:
        """Get the source URL."""
        return self._source_url

    @property
    def source_type(self) -> IngestionSourceType:
        """Get the source type."""
        return self._source_type

    @property
    def correlation_id(self) -> Optional[str]:
        """Get the correlation ID."""
        return self._correlation_id

    @property
    def parameters(self) -> Dict[str, Any]:
        """Get the ingestion parameters."""
        return self._parameters.copy()

    @property
    def scope(self) -> Dict[str, Any]:
        """Get the ingestion scope."""
        return self._scope.copy()

    @property
    def priority(self) -> int:
        """Get the priority level (1-10, higher = more urgent)."""
        return self._priority

    @property
    def requested_by(self) -> Optional[str]:
        """Get the user who requested the ingestion."""
        return self._requested_by

    @property
    def tags(self) -> List[str]:
        """Get the tags associated with this request."""
        return self._tags.copy()

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self._created_at

    @property
    def has_scope_limits(self) -> bool:
        """Check if request has scope limitations."""
        return len(self._scope) > 0

    @property
    def requires_authentication(self) -> bool:
        """Check if this request requires authentication."""
        return self._source_type.requires_authentication

    @property
    def supports_incremental_sync(self) -> bool:
        """Check if this source supports incremental synchronization."""
        return self._source_type.supports_incremental_sync

    def add_parameter(self, key: str, value: Any):
        """Add a parameter to the request."""
        self._parameters[key] = value

    def add_scope_limit(self, key: str, value: Any):
        """Add a scope limitation."""
        self._scope[key] = value

    def add_tag(self, tag: str):
        """Add a tag to the request."""
        if tag not in self._tags:
            self._tags.append(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "request_id": self._request_id,
            "source_url": self._source_url,
            "source_type": self._source_type.value,
            "parameters": self._parameters,
            "scope": self._scope,
            "priority": self._priority,
            "tags": self._tags,
            "created_at": self._created_at.isoformat(),
            "has_scope_limits": self.has_scope_limits,
            "requires_authentication": self.requires_authentication,
            "supports_incremental_sync": self.supports_incremental_sync
        }

        if self._correlation_id:
            result["correlation_id"] = self._correlation_id

        if self._requested_by:
            result["requested_by"] = self._requested_by

        return result

    def __repr__(self) -> str:
        return f"IngestionRequest(request_id='{self._request_id}', source='{self._source_url[:50]}...', type={self._source_type})"
