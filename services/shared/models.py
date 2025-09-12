from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

"""Shared Pydantic models used across services.

These normalized types ensure consistent data exchange between agents,
the orchestrator, the consistency engine, and reporting.
"""


class Document(BaseModel):
    """Normalized unit of ingested content from any source.

    - `source_type` indicates origin (e.g., "github", "jira", "confluence").
    - `content` carries the text payload; `metadata` stores source-specific fields.
    """
    id: str
    source_type: str  # github|jira|confluence
    source_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    content_hash: Optional[str] = None
    correlation_id: Optional[str] = None
    version_tag: Optional[str] = None
    last_modified: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    project: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApiEndpoint(BaseModel):
    """Endpoint from a normalized API schema."""
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    responses: Optional[Dict[str, Any]] = None


class ApiSchema(BaseModel):
    """Normalized OpenAPI/Swagger schema subset with enumerated endpoints."""
    id: str
    service_name: Optional[str] = None
    version: Optional[str] = None
    openapi_raw: Dict[str, Any] = Field(default_factory=dict)
    endpoints: List[ApiEndpoint] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_hash: Optional[str] = None
    correlation_id: Optional[str] = None


class Finding(BaseModel):
    """Detected inconsistency or observation produced by the consistency engine."""
    id: str
    type: str  # missing_doc|contradiction|drift|stale|broken_link|schema_mismatch|acceptance_mismatch|security_gap
    title: Optional[str] = None  # Human-readable title for the finding
    severity: str  # low|med|high|crit
    description: str
    source_refs: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    suggestion: Optional[str] = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    score: Optional[int] = None
    rationale: Optional[str] = None


class MemoryItem(BaseModel):
    """Short-term memory item stored by the memory-agent for operational context."""
    id: str
    type: str  # operation|llm_summary|doc_summary|api_summary|finding
    key: Optional[str] = None  # correlation_id, doc id, etc.
    summary: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

