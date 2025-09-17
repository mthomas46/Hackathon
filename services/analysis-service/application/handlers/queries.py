"""Query classes for CQRS pattern."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class GetDocumentQuery:
    """Query to get a single document."""
    document_id: str


@dataclass
class GetDocumentsQuery:
    """Query to get multiple documents with filtering."""
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    repository_id: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetAnalysisQuery:
    """Query to get a single analysis."""
    analysis_id: str


@dataclass
class GetAnalysesQuery:
    """Query to get multiple analyses with filtering."""
    document_id: Optional[str] = None
    analysis_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetFindingQuery:
    """Query to get a single finding."""
    finding_id: str


@dataclass
class GetFindingsQuery:
    """Query to get multiple findings with filtering."""
    document_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    resolved: Optional[bool] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetRepositoryQuery:
    """Query to get a single repository."""
    repository_id: str


@dataclass
class GetRepositoriesQuery:
    """Query to get multiple repositories with filtering."""
    provider: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetStatisticsQuery:
    """Query to get system statistics."""
    include_documents: bool = True
    include_analyses: bool = True
    include_findings: bool = True
