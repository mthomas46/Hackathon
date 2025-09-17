"""Command classes for CQRS pattern."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class CreateDocumentCommand:
    """Command to create a new document."""
    title: str
    content: str
    format: str = "markdown"
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    repository_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateDocumentCommand:
    """Command to update an existing document."""
    document_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    format: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DeleteDocumentCommand:
    """Command to delete a document."""
    document_id: str


@dataclass
class PerformAnalysisCommand:
    """Command to perform analysis on a document."""
    document_id: str
    analysis_type: str
    configuration: Optional[Dict[str, Any]] = None
    priority: str = "normal"
    timeout_seconds: Optional[int] = None


@dataclass
class CreateFindingCommand:
    """Command to create a new finding."""
    document_id: str
    analysis_id: str
    title: str
    description: str
    severity: str
    category: str
    location: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    confidence: float = 0.8
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateFindingCommand:
    """Command to update an existing finding."""
    finding_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    confidence: Optional[float] = None
    resolved: Optional[bool] = None
    resolved_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DeleteFindingCommand:
    """Command to delete a finding."""
    finding_id: str


@dataclass
class CancelAnalysisCommand:
    """Command to cancel a running analysis."""
    analysis_id: str


@dataclass
class RetryAnalysisCommand:
    """Command to retry a failed analysis."""
    analysis_id: str
    configuration: Optional[Dict[str, Any]] = None
