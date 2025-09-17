"""Query handlers for CQRS pattern."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from .queries import (
    GetDocumentQuery,
    GetDocumentsQuery,
    GetAnalysisQuery,
    GetAnalysesQuery,
    GetFindingQuery,
    GetFindingsQuery,
    GetRepositoryQuery,
    GetRepositoriesQuery,
    GetStatisticsQuery
)
from ...domain.entities import Document, Analysis, Finding
from ...infrastructure.repositories import (
    DocumentRepository,
    AnalysisRepository,
    FindingRepository
)


class QueryHandler(ABC):
    """Base class for query handlers."""

    @abstractmethod
    async def handle(self, query):
        """Handle the query."""
        pass


class GetDocumentQueryHandler(QueryHandler):
    """Handler for getting documents."""

    def __init__(self, document_repository: DocumentRepository):
        """Initialize handler with dependencies."""
        self.document_repository = document_repository

    async def handle(self, query: GetDocumentQuery) -> Optional[Document]:
        """Handle get document query."""
        return await self.document_repository.get_by_id(query.document_id)


class GetDocumentsQueryHandler(QueryHandler):
    """Handler for getting multiple documents."""

    def __init__(self, document_repository: DocumentRepository):
        """Initialize handler with dependencies."""
        self.document_repository = document_repository

    async def handle(self, query: GetDocumentsQuery) -> List[Document]:
        """Handle get documents query."""
        # Get all documents (in a real implementation, this would be filtered in the repository)
        all_documents = await self.document_repository.get_all()

        # Apply filters
        filtered_documents = self._apply_filters(all_documents, query)

        # Apply pagination
        start_idx = query.offset
        end_idx = start_idx + query.limit
        return filtered_documents[start_idx:end_idx]

    def _apply_filters(self, documents: List[Document], query: GetDocumentsQuery) -> List[Document]:
        """Apply filters to document list."""
        filtered = documents

        if query.author:
            filtered = [d for d in filtered if d.metadata.author and
                       query.author.lower() in d.metadata.author.lower()]

        if query.tags:
            filtered = [d for d in filtered if any(tag in d.metadata.tags for tag in query.tags)]

        if query.repository_id:
            filtered = [d for d in filtered if d.repository_id == query.repository_id]

        return filtered


class GetAnalysisQueryHandler(QueryHandler):
    """Handler for getting analyses."""

    def __init__(self, analysis_repository: AnalysisRepository):
        """Initialize handler with dependencies."""
        self.analysis_repository = analysis_repository

    async def handle(self, query: GetAnalysisQuery) -> Optional[Analysis]:
        """Handle get analysis query."""
        return await self.analysis_repository.get_by_id(query.analysis_id)


class GetAnalysesQueryHandler(QueryHandler):
    """Handler for getting multiple analyses."""

    def __init__(self, analysis_repository: AnalysisRepository):
        """Initialize handler with dependencies."""
        self.analysis_repository = analysis_repository

    async def handle(self, query: GetAnalysesQuery) -> List[Analysis]:
        """Handle get analyses query."""
        if query.document_id:
            # Get analyses for specific document
            return await self.analysis_repository.get_by_document_id(query.document_id)
        elif query.status:
            # Get analyses by status
            return await self.analysis_repository.get_by_status(query.status)
        else:
            # Get all analyses with pagination
            all_analyses = await self.analysis_repository.get_all()

            # Apply filters
            filtered_analyses = self._apply_filters(all_analyses, query)

            # Apply pagination
            start_idx = query.offset
            end_idx = start_idx + query.limit
            return filtered_analyses[start_idx:end_idx]

    def _apply_filters(self, analyses: List[Analysis], query: GetAnalysesQuery) -> List[Analysis]:
        """Apply filters to analysis list."""
        filtered = analyses

        if query.analysis_type:
            filtered = [a for a in filtered if a.analysis_type == query.analysis_type]

        if query.status:
            filtered = [a for a in filtered if a.status.value == query.status]

        return filtered


class GetFindingQueryHandler(QueryHandler):
    """Handler for getting findings."""

    def __init__(self, finding_repository: FindingRepository):
        """Initialize handler with dependencies."""
        self.finding_repository = finding_repository

    async def handle(self, query: GetFindingQuery) -> Optional[Finding]:
        """Handle get finding query."""
        return await self.finding_repository.get_by_id(query.finding_id)


class GetFindingsQueryHandler(QueryHandler):
    """Handler for getting multiple findings."""

    def __init__(self, finding_repository: FindingRepository):
        """Initialize handler with dependencies."""
        self.finding_repository = finding_repository

    async def handle(self, query: GetFindingsQuery) -> List[Finding]:
        """Handle get findings query."""
        if query.document_id:
            # Get findings for specific document
            return await self.finding_repository.get_by_document_id(query.document_id)
        elif query.category:
            # Get findings by category
            return await self.finding_repository.get_by_category(query.category)
        else:
            # Get all findings
            all_findings = await self.finding_repository.get_all()

            # Apply filters
            filtered_findings = self._apply_filters(all_findings, query)

            # Apply sorting (prioritize by severity and confidence)
            filtered_findings = self._sort_findings(filtered_findings)

            # Apply pagination
            start_idx = query.offset
            end_idx = start_idx + query.limit
            return filtered_findings[start_idx:end_idx]

    def _apply_filters(self, findings: List[Finding], query: GetFindingsQuery) -> List[Finding]:
        """Apply filters to findings list."""
        filtered = findings

        if query.severity:
            filtered = [f for f in filtered if f.severity.value == query.severity]

        if query.resolved is not None:
            filtered = [f for f in filtered if f.is_resolved() == query.resolved]

        return filtered

    def _sort_findings(self, findings: List[Finding]) -> List[Finding]:
        """Sort findings by priority (severity and confidence)."""
        def priority_key(finding: Finding) -> tuple:
            # Sort by: severity (desc), confidence (desc), age (desc)
            severity_score = finding.severity_score
            confidence = finding.confidence
            age_days = finding.age_days
            return (-severity_score, -confidence, -age_days)

        return sorted(findings, key=priority_key)


class GetStatisticsQueryHandler(QueryHandler):
    """Handler for getting system statistics."""

    def __init__(self,
                 document_repository: DocumentRepository,
                 analysis_repository: AnalysisRepository,
                 finding_repository: FindingRepository):
        """Initialize handler with dependencies."""
        self.document_repository = document_repository
        self.analysis_repository = analysis_repository
        self.finding_repository = finding_repository

    async def handle(self, query: GetStatisticsQuery) -> Dict[str, Any]:
        """Handle get statistics query."""
        stats = {}

        if query.include_documents:
            documents = await self.document_repository.get_all()
            stats['documents'] = {
                'total': len(documents),
                'by_format': self._count_by_attribute(documents, lambda d: d.content.format),
                'by_author': self._count_by_attribute(documents, lambda d: d.metadata.author or 'Unknown'),
                'recent': len([d for d in documents if d.is_recently_updated])
            }

        if query.include_analyses:
            analyses = await self.analysis_repository.get_all()
            stats['analyses'] = {
                'total': len(analyses),
                'by_type': self._count_by_attribute(analyses, lambda a: a.analysis_type),
                'by_status': self._count_by_attribute(analyses, lambda a: a.status.value),
                'completed': len([a for a in analyses if a.is_completed])
            }

        if query.include_findings:
            findings = await self.finding_repository.get_all()
            unresolved = await self.finding_repository.get_unresolved()
            stats['findings'] = {
                'total': len(findings),
                'by_category': self._count_by_attribute(findings, lambda f: f.category),
                'by_severity': self._count_by_attribute(findings, lambda f: f.severity.value),
                'unresolved': len(unresolved),
                'resolved': len(findings) - len(unresolved)
            }

        return stats

    def _count_by_attribute(self, items: List, attribute_func) -> Dict[str, int]:
        """Count items by attribute value."""
        counts = {}
        for item in items:
            key = attribute_func(item)
            counts[key] = counts.get(key, 0) + 1
        return counts
