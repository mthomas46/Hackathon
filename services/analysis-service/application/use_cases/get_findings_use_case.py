"""Get Findings Use Case."""

from typing import Optional, List
from dataclasses import dataclass

from ...domain.entities import Finding
from ...domain.services import FindingService
from ...infrastructure.repositories import FindingRepository
from ..dto import GetFindingsRequest, FindingResponse, FindingListResponse


@dataclass
class GetFindingsQuery:
    """Query for getting findings."""
    document_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    resolved: Optional[bool] = None
    confidence_min: Optional[float] = None
    limit: int = 50
    offset: int = 0


@dataclass
class FindingsQueryResult:
    """Result of findings query."""
    findings: List[Finding]
    total_count: int
    has_more: bool


class GetFindingsUseCase:
    """Use case for retrieving findings."""

    def __init__(self,
                 finding_service: FindingService,
                 finding_repository: FindingRepository):
        """Initialize use case with dependencies."""
        self.finding_service = finding_service
        self.finding_repository = finding_repository

    async def get_list(self, query: GetFindingsQuery) -> FindingsQueryResult:
        """Get a list of findings with filtering."""
        # Get all findings (in a real implementation, this would be filtered in the repository)
        all_findings = await self.finding_repository.get_all()

        # Apply filters
        filtered_findings = self._apply_filters(all_findings, query)

        # Apply sorting (prioritize by severity and confidence)
        filtered_findings = self.finding_service.prioritize_findings(filtered_findings)

        # Apply pagination
        total_count = len(filtered_findings)
        start_idx = query.offset
        end_idx = start_idx + query.limit
        paginated_findings = filtered_findings[start_idx:end_idx]

        has_more = end_idx < total_count

        return FindingsQueryResult(
            findings=paginated_findings,
            total_count=total_count,
            has_more=has_more
        )

    async def get_by_document(self, document_id: str) -> List[Finding]:
        """Get all findings for a specific document."""
        return await self.finding_repository.get_by_document_id(document_id)

    async def get_unresolved(self, limit: int = 100) -> List[Finding]:
        """Get unresolved findings."""
        unresolved = await self.finding_repository.get_unresolved()
        return unresolved[:limit]

    async def get_high_priority(self, limit: int = 10) -> List[Finding]:
        """Get high priority findings."""
        all_findings = await self.finding_repository.get_all()
        return self.finding_service.get_high_priority_findings(all_findings, limit)

    def _apply_filters(self, findings: List[Finding], query: GetFindingsQuery) -> List[Finding]:
        """Apply filters to findings list."""
        filtered = findings

        if query.document_id:
            filtered = [f for f in filtered if f.document_id.value == query.document_id]

        if query.category:
            filtered = [f for f in filtered if f.category == query.category]

        if query.severity:
            filtered = [f for f in filtered if f.severity.value == query.severity]

        if query.resolved is not None:
            filtered = [f for f in filtered if f.is_resolved() == query.resolved]

        if query.confidence_min is not None:
            filtered = [f for f in filtered if f.confidence >= query.confidence_min]

        return filtered

    def to_response(self, finding: Finding) -> FindingResponse:
        """Convert finding to response DTO."""
        return FindingResponse.from_domain(finding)

    def to_list_response(self, result: FindingsQueryResult, query: GetFindingsQuery) -> FindingListResponse:
        """Convert query result to list response DTO."""
        finding_responses = [FindingResponse.from_domain(finding) for finding in result.findings]

        filters = {
            'document_id': query.document_id,
            'category': query.category,
            'severity': query.severity,
            'resolved': query.resolved,
            'confidence_min': query.confidence_min
        }

        return FindingListResponse.create(
            findings=finding_responses,
            total=result.total_count,
            page=(query.offset // query.limit) + 1,
            page_size=query.limit,
            filters=filters
        )
