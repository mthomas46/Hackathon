"""Perform Analysis Use Case."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ...domain.entities import Document, Analysis, Finding
from ...domain.services import AnalysisService, FindingService
from ...domain.entities.value_objects import AnalysisType, AnalysisConfiguration
from ...domain.exceptions import (
    DocumentNotFoundException,
    AnalysisExecutionException,
    AnalysisTimeoutException
)
from ...infrastructure.repositories import DocumentRepository, AnalysisRepository, FindingRepository
from ..dto import PerformAnalysisRequest, AnalysisResultResponse, FindingResponse


@dataclass
class PerformAnalysisCommand:
    """Command for performing analysis."""
    document_id: str
    analysis_type: str
    configuration: Optional[Dict[str, Any]] = None
    priority: str = "normal"
    timeout_seconds: Optional[int] = None


@dataclass
class PerformAnalysisResult:
    """Result of analysis execution."""
    analysis: Analysis
    findings: List[Finding]
    execution_time_seconds: Optional[float]
    success: bool
    error_message: Optional[str]


class PerformAnalysisUseCase:
    """Use case for performing document analysis."""

    def __init__(self,
                 analysis_service: AnalysisService,
                 finding_service: FindingService,
                 document_repository: DocumentRepository,
                 analysis_repository: AnalysisRepository,
                 finding_repository: FindingRepository):
        """Initialize use case with dependencies."""
        self.analysis_service = analysis_service
        self.finding_service = finding_service
        self.document_repository = document_repository
        self.analysis_repository = analysis_repository
        self.finding_repository = finding_repository

    async def execute(self, command: PerformAnalysisCommand) -> PerformAnalysisResult:
        """Execute the perform analysis use case."""
        try:
            # Get document
            document = await self.document_repository.get_by_id(command.document_id)
            if not document:
                raise DocumentNotFoundException(command.document_id)

            # Create analysis configuration
            config_dict = command.configuration or {}
            if command.timeout_seconds:
                config_dict['timeout_seconds'] = command.timeout_seconds

            config_dict['priority'] = command.priority

            analysis_config = AnalysisConfiguration(**config_dict)

            # Create analysis entity
            analysis = self.analysis_service.create_analysis(
                document=document,
                analysis_type=AnalysisType(command.analysis_type),
                configuration=analysis_config
            )

            # Save analysis
            await self.analysis_repository.save(analysis)

            # Execute analysis
            analysis.start()
            result = self.analysis_service.execute_analysis(analysis)

            # Mark as completed
            analysis.complete(result)
            await self.analysis_repository.save(analysis)

            # Process findings if any
            findings = []
            if 'findings' in result:
                findings = await self._process_findings(analysis, result['findings'])

            return PerformAnalysisResult(
                analysis=analysis,
                findings=findings,
                execution_time_seconds=analysis.duration,
                success=True,
                error_message=None
            )

        except DocumentNotFoundException:
            raise
        except Exception as e:
            # Create failed analysis result
            error_message = str(e)
            analysis.fail(error_message)
            await self.analysis_repository.save(analysis)

            return PerformAnalysisResult(
                analysis=analysis,
                findings=[],
                execution_time_seconds=analysis.duration,
                success=False,
                error_message=error_message
            )

    async def _process_findings(self, analysis: Analysis, findings_data: List[Dict[str, Any]]) -> List[Finding]:
        """Process findings from analysis result."""
        findings = []

        for finding_data in findings_data:
            finding = self.finding_service.create_finding(
                document_id=analysis.document_id,
                analysis_id=analysis.id.value,
                title=finding_data.get('title', 'Analysis Finding'),
                description=finding_data.get('description', ''),
                severity=finding_data.get('severity', 'medium'),
                category=finding_data.get('category', 'general'),
                confidence=finding_data.get('confidence', 0.5),
                location=finding_data.get('location'),
                suggestion=finding_data.get('suggestion')
            )

            await self.finding_repository.save(finding)
            findings.append(finding)

        return findings

    def to_response(self, result: PerformAnalysisResult) -> AnalysisResultResponse:
        """Convert result to response DTO."""
        findings_responses = [
            FindingResponse.from_domain(finding) for finding in result.findings
        ]

        return AnalysisResultResponse.create(result.analysis, findings_responses)
