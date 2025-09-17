"""Response DTOs for application layer."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class DocumentResponse:
    """Response DTO for document data."""
    id: str
    title: str
    content_format: str
    author: Optional[str]
    tags: List[str]
    repository_id: Optional[str]
    version: str
    word_count: int
    created_at: datetime
    updated_at: datetime
    is_recently_updated: bool

    @classmethod
    def from_domain(cls, document) -> 'DocumentResponse':
        """Create response from domain document entity."""
        return cls(
            id=document.id.value,
            title=document.title,
            content_format=document.content.format,
            author=document.metadata.author,
            tags=document.metadata.tags,
            repository_id=document.repository_id,
            version=document.version,
            word_count=document.word_count,
            created_at=document.metadata.created_at,
            updated_at=document.metadata.updated_at,
            is_recently_updated=document.is_recently_updated
        )


@dataclass
class AnalysisResponse:
    """Response DTO for analysis data."""
    id: str
    document_id: str
    analysis_type: str
    status: str
    configuration: Dict[str, Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[float]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]

    @classmethod
    def from_domain(cls, analysis) -> 'AnalysisResponse':
        """Create response from domain analysis entity."""
        return cls(
            id=analysis.id.value,
            document_id=analysis.document_id.value,
            analysis_type=analysis.analysis_type,
            status=analysis.status.value,
            configuration=analysis.configuration,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            duration=analysis.duration,
            result=analysis.result,
            error_message=analysis.error_message
        )


@dataclass
class FindingResponse:
    """Response DTO for finding data."""
    id: str
    document_id: str
    analysis_id: str
    title: str
    description: str
    severity: str
    category: str
    confidence: float
    location: Optional[Dict[str, Any]]
    suggestion: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    age_days: int
    is_resolved: bool

    @classmethod
    def from_domain(cls, finding) -> 'FindingResponse':
        """Create response from domain finding entity."""
        return cls(
            id=finding.id.value,
            document_id=finding.document_id.value,
            analysis_id=finding.analysis_id,
            title=finding.title,
            description=finding.description,
            severity=finding.severity.value,
            category=finding.category,
            confidence=finding.confidence,
            location=finding.location,
            suggestion=finding.suggestion,
            created_at=finding.created_at,
            resolved_at=finding.resolved_at,
            resolved_by=finding.resolved_by,
            age_days=finding.age_days,
            is_resolved=finding.is_resolved()
        )


@dataclass
class ErrorResponse:
    """Response DTO for error cases."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_exception(cls, exception: Exception, error_code: str = "INTERNAL_ERROR") -> 'ErrorResponse':
        """Create error response from exception."""
        return cls(
            error_code=error_code,
            message=str(exception),
            details={"exception_type": type(exception).__name__}
        )

    @classmethod
    def from_validation_errors(cls, errors: List[str]) -> 'ErrorResponse':
        """Create error response from validation errors."""
        return cls(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            details={"validation_errors": errors}
        )


@dataclass
class SuccessResponse:
    """Response DTO for successful operations."""
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def with_data(cls, message: str, data: Dict[str, Any]) -> 'SuccessResponse':
        """Create success response with data."""
        return cls(message=message, data=data)

    @classmethod
    def simple(cls, message: str) -> 'SuccessResponse':
        """Create simple success response."""
        return cls(message=message)


@dataclass
class PaginatedResponse:
    """Response DTO for paginated results."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(cls, items: List[Any], total: int, page: int, page_size: int) -> 'PaginatedResponse':
        """Create paginated response."""
        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )


@dataclass
class DocumentListResponse:
    """Response DTO for document list with pagination."""
    documents: List[DocumentResponse]
    pagination: PaginatedResponse
    filters: Dict[str, Any]

    @classmethod
    def create(cls, documents: List[DocumentResponse], total: int,
              page: int, page_size: int, filters: Dict[str, Any]) -> 'DocumentListResponse':
        """Create document list response."""
        pagination = PaginatedResponse.create(documents, total, page, page_size)

        return cls(
            documents=documents,
            pagination=pagination,
            filters=filters
        )


@dataclass
class FindingListResponse:
    """Response DTO for finding list with pagination."""
    findings: List[FindingResponse]
    pagination: PaginatedResponse
    filters: Dict[str, Any]
    summary: Dict[str, Any]

    @classmethod
    def create(cls, findings: List[FindingResponse], total: int,
              page: int, page_size: int, filters: Dict[str, Any]) -> 'FindingListResponse':
        """Create finding list response."""
        pagination = PaginatedResponse.create(findings, total, page, page_size)

        # Calculate summary
        summary = {
            'total_findings': total,
            'severity_breakdown': cls._calculate_severity_breakdown(findings),
            'category_breakdown': cls._calculate_category_breakdown(findings),
            'resolved_count': sum(1 for f in findings if f.is_resolved),
            'unresolved_count': sum(1 for f in findings if not f.is_resolved)
        }

        return cls(
            findings=findings,
            pagination=pagination,
            filters=filters,
            summary=summary
        )

    @staticmethod
    def _calculate_severity_breakdown(findings: List[FindingResponse]) -> Dict[str, int]:
        """Calculate severity breakdown."""
        breakdown = {}
        for finding in findings:
            severity = finding.severity
            breakdown[severity] = breakdown.get(severity, 0) + 1
        return breakdown

    @staticmethod
    def _calculate_category_breakdown(findings: List[FindingResponse]) -> Dict[str, int]:
        """Calculate category breakdown."""
        breakdown = {}
        for finding in findings:
            category = finding.category
            breakdown[category] = breakdown.get(category, 0) + 1
        return breakdown


@dataclass
class AnalysisResultResponse:
    """Response DTO for analysis results."""
    analysis_id: str
    document_id: str
    analysis_type: str
    status: str
    results: Dict[str, Any]
    findings: List[FindingResponse]
    execution_time_seconds: Optional[float]
    completed_at: datetime

    @classmethod
    def create(cls, analysis, findings: List[FindingResponse]) -> 'AnalysisResultResponse':
        """Create analysis result response."""
        return cls(
            analysis_id=analysis.id.value,
            document_id=analysis.document_id.value,
            analysis_type=analysis.analysis_type,
            status=analysis.status.value,
            results=analysis.result or {},
            findings=findings,
            execution_time_seconds=analysis.duration,
            completed_at=analysis.completed_at or datetime.now()
        )


@dataclass
class HealthCheckResponse:
    """Response DTO for health check."""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    metrics: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def healthy(cls, services: Dict[str, str], metrics: Dict[str, Any] = None) -> 'HealthCheckResponse':
        """Create healthy response."""
        return cls(
            status="healthy",
            timestamp=datetime.now(),
            services=services,
            metrics=metrics or {}
        )

    @classmethod
    def unhealthy(cls, services: Dict[str, str], issue: str) -> 'HealthCheckResponse':
        """Create unhealthy response."""
        return cls(
            status="unhealthy",
            timestamp=datetime.now(),
            services=services,
            metrics={"issue": issue}
        )
