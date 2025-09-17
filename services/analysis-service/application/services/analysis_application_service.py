"""Analysis Application Service."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ...domain.entities import Document, Analysis, Finding
from ...domain.services import AnalysisService, DocumentService, FindingService
from ...domain.entities.value_objects import AnalysisType, AnalysisConfiguration
from ...infrastructure.repositories import DocumentRepository, AnalysisRepository, FindingRepository


class AnalysisApplicationService:
    """Application service for analysis operations."""

    def __init__(self,
                 analysis_service: AnalysisService,
                 document_service: DocumentService,
                 finding_service: FindingService,
                 document_repository: DocumentRepository,
                 analysis_repository: AnalysisRepository,
                 finding_repository: FindingRepository):
        """Initialize application service with dependencies."""
        self.analysis_service = analysis_service
        self.document_service = document_service
        self.finding_service = finding_service
        self.document_repository = document_repository
        self.analysis_repository = analysis_repository
        self.finding_repository = finding_repository

    async def perform_analysis(self, document_id: str, analysis_type: str,
                              configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on a document."""
        try:
            # Get document
            document = await self.document_repository.get_by_id(document_id)
            if not document:
                raise ValueError(f"Document not found: {document_id}")

            # Create analysis entity
            analysis_type_enum = AnalysisType(analysis_type)
            analysis_config = AnalysisConfiguration(
                detectors=configuration.get('detectors', []),
                options=configuration.get('options', {}),
                priority=configuration.get('priority', 'normal'),
                timeout_seconds=configuration.get('timeout_seconds', 300)
            )

            analysis = self.analysis_service.create_analysis(
                document, analysis_type_enum, analysis_config
            )

            # Save analysis
            await self.analysis_repository.save(analysis)

            # Execute analysis
            analysis.start()
            result = self.analysis_service.execute_analysis(analysis)
            analysis.complete(result)

            # Save updated analysis
            await self.analysis_repository.save(analysis)

            # Process findings if any
            if 'findings' in result:
                await self._process_findings(analysis, result['findings'])

            return {
                'analysis_id': analysis.id.value,
                'status': 'completed',
                'result': result
            }

        except Exception as e:
            # Handle analysis failure
            if 'analysis' in locals():
                analysis.fail(str(e))
                await self.analysis_repository.save(analysis)

            return {
                'error': str(e),
                'status': 'failed'
            }

    async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result."""
        analysis = await self.analysis_repository.get_by_id(analysis_id)
        if not analysis:
            return None

        return {
            'analysis_id': analysis.id.value,
            'document_id': analysis.document_id.value,
            'status': analysis.status.value,
            'result': analysis.result,
            'error_message': analysis.error_message,
            'started_at': analysis.started_at.isoformat() if analysis.started_at else None,
            'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
            'duration': analysis.duration
        }

    async def get_document_analyses(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all analyses for a document."""
        analyses = await self.analysis_repository.get_by_document_id(document_id)

        return [
            {
                'analysis_id': analysis.id.value,
                'analysis_type': analysis.analysis_type,
                'status': analysis.status.value,
                'created_at': analysis.created_at.isoformat(),
                'duration': analysis.duration
            }
            for analysis in analyses
        ]

    async def get_findings(self, document_id: Optional[str] = None,
                          category: Optional[str] = None,
                          severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get findings with optional filtering."""
        findings = await self.finding_repository.get_all()

        # Apply filters
        if document_id:
            findings = [f for f in findings if f.document_id.value == document_id]

        if category:
            findings = [f for f in findings if f.category == category]

        if severity:
            findings = [f for f in findings if f.severity.value == severity]

        return [finding.to_dict() for finding in findings]

    async def create_document(self, title: str, content: str,
                             content_format: str = "markdown",
                             author: Optional[str] = None,
                             tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new document."""
        document = self.document_service.create_document(
            title=title,
            content_text=content,
            content_format=content_format,
            author=author,
            tags=tags
        )

        # Validate document
        issues = self.document_service.validate_document(document)
        if issues:
            return {
                'error': 'Document validation failed',
                'issues': issues
            }

        # Save document
        await self.document_repository.save(document)

        return {
            'document_id': document.id.value,
            'status': 'created'
        }

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            return None

        return document.to_dict()

    async def _process_findings(self, analysis: Analysis, findings_data: List[Dict[str, Any]]) -> None:
        """Process findings from analysis result."""
        for finding_data in findings_data:
            finding = self.finding_service.create_finding(
                document_id=analysis.document_id,
                analysis_id=analysis.id.value,
                title=finding_data.get('title', 'Unknown Issue'),
                description=finding_data.get('description', ''),
                severity=finding_data.get('severity', 'medium'),
                category=finding_data.get('category', 'general'),
                confidence=finding_data.get('confidence', 0.5),
                location=finding_data.get('location'),
                suggestion=finding_data.get('suggestion')
            )

            await self.finding_repository.save(finding)

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'analysis_service': 'operational',
                'document_service': 'operational',
                'finding_service': 'operational'
            }
        }
