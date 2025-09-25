"""Perform Analysis Use Case with event publishing."""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ...domain.entities import Analysis, Finding
from ...domain.entities.value_objects import AnalysisConfiguration, AnalysisType
from ...domain.exceptions import DocumentNotFoundException
from ...domain.services import AnalysisService, FindingService
from ...infrastructure.repositories import (
    AnalysisRepository,
    DocumentRepository,
    FindingRepository,
)
from ..dto import AnalysisResultResponse, FindingResponse
from ..events import (
    AnalysisCompletedEvent,
    AnalysisFailedEvent,
    AnalysisRequestedEvent,
    EventBus,
    FindingCreatedEvent,
)

logger = logging.getLogger(__name__)


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
    events: List[Any]  # Application events generated during execution


class PerformAnalysisUseCase:
    """Use case for performing document analysis with event publishing."""

    def __init__(
        self,
        analysis_service: AnalysisService,
        finding_service: FindingService,
        document_repository: DocumentRepository,
        analysis_repository: AnalysisRepository,
        finding_repository: FindingRepository,
        event_bus: Optional[EventBus] = None,
    ):
        """Initialize use case with dependencies."""
        self.analysis_service = analysis_service
        self.finding_service = finding_service
        self.document_repository = document_repository
        self.analysis_repository = analysis_repository
        self.finding_repository = finding_repository
        self.event_bus = event_bus

    async def execute(self, command: PerformAnalysisCommand) -> PerformAnalysisResult:
        """Execute the perform analysis use case with event publishing."""
        start_time = time.time()
        events = []

        try:
            # Publish analysis requested event
            requested_event = await self._publish_analysis_requested_event(command)
            if requested_event:
                events.append(requested_event)

            # Get document
            document = await self.document_repository.get_by_id(command.document_id)
            if not document:
                raise DocumentNotFoundException(command.document_id)

            # Create analysis configuration
            config_dict = command.configuration or {}
            if command.timeout_seconds:
                config_dict["timeout_seconds"] = command.timeout_seconds

            config_dict["priority"] = command.priority

            analysis_config = AnalysisConfiguration(**config_dict)

            # Create analysis entity
            analysis = self.analysis_service.create_analysis(
                document=document,
                analysis_type=AnalysisType(command.analysis_type),
                configuration=analysis_config,
            )

            # Save analysis
            await self.analysis_repository.save(analysis)

            # Execute analysis and process results
            result, execution_time, findings = await self._execute_analysis_and_process_results(
                analysis, start_time
            )

            # Publish completion events
            completion_events = await self._publish_analysis_completion_events(
                command, analysis, result, execution_time, findings
            )
            events.extend(completion_events)

            return PerformAnalysisResult(
                analysis=analysis,
                findings=findings,
                execution_time_seconds=execution_time,
                success=True,
                error_message=None,
                events=events,
            )

        except DocumentNotFoundException:
            # Publish document not found event
            if self.event_bus:
                not_found_event = AnalysisFailedEvent(
                    event_id=str(uuid4()),
                    correlation_id=getattr(command, "command_id", str(uuid4())),
                    document_id=command.document_id,
                    analysis_type=command.analysis_type,
                    error_message="Document not found",
                    error_code="DOCUMENT_NOT_FOUND",
                    retry_count=0,
                    metadata={
                        "user_id": getattr(command, "user_id", None),
                        "session_id": getattr(command, "session_id", None),
                    },
                )
                await self.event_bus.publish(not_found_event)
                events.append(not_found_event)
            raise

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            # Create failed analysis result
            if "analysis" in locals():
                analysis.fail(error_message)
                await self.analysis_repository.save(analysis)

                # Publish analysis failed event
                if self.event_bus:
                    failed_event = AnalysisFailedEvent(
                        event_id=str(uuid4()),
                        correlation_id=getattr(command, "command_id", str(uuid4())),
                        document_id=command.document_id,
                        analysis_type=command.analysis_type,
                        error_message=error_message,
                        error_code=e.__class__.__name__,
                        retry_count=getattr(command, "retry_count", 0),
                        metadata={
                            "user_id": getattr(command, "user_id", None),
                            "session_id": getattr(command, "session_id", None),
                            "execution_time_seconds": execution_time,
                        },
                    )
                    await self.event_bus.publish(failed_event)
                    events.append(failed_event)

            return PerformAnalysisResult(
                analysis=analysis if "analysis" in locals() else None,
                findings=[],
                execution_time_seconds=execution_time,
                success=False,
                error_message=error_message,
                events=events,
            )

    async def _process_findings(self, analysis: Analysis, findings_data: List[Dict[str, Any]]) -> List[Finding]:
        """Process findings from analysis result."""
        findings = []

        for finding_data in findings_data:
            finding = self.finding_service.create_finding(
                document_id=analysis.document_id,
                analysis_id=analysis.id.value,
                title=finding_data.get("title", "Analysis Finding"),
                description=finding_data.get("description", ""),
                severity=finding_data.get("severity", "medium"),
                category=finding_data.get("category", "general"),
                confidence=finding_data.get("confidence", 0.5),
                location=finding_data.get("location"),
                suggestion=finding_data.get("suggestion"),
            )

            await self.finding_repository.save(finding)
            findings.append(finding)

        return findings

    async def _publish_analysis_requested_event(self, command: PerformAnalysisCommand) -> Optional[AnalysisRequestedEvent]:
        """Publish analysis requested event.

        Args:
            command: The analysis command

        Returns:
            The published event if event bus is available, None otherwise
        """
        if not self.event_bus:
            return None

        requested_event = AnalysisRequestedEvent(
            event_id=str(uuid4()),
            correlation_id=getattr(command, "command_id", str(uuid4())),
            document_id=command.document_id,
            analysis_type=command.analysis_type,
            requested_by=getattr(command, "user_id", None),
            priority=command.priority,
            configuration=command.configuration or {},
            metadata={
                "user_id": getattr(command, "user_id", None),
                "session_id": getattr(command, "session_id", None),
                "source": getattr(command, "source", "api"),
            },
        )
        await self.event_bus.publish(requested_event)
        return requested_event

    async def _execute_analysis_and_process_results(
        self, analysis: Analysis, start_time: float
    ) -> tuple:
        """Execute analysis and process results.

        Args:
            analysis: The analysis entity
            start_time: Start time of the operation

        Returns:
            Tuple of (result, execution_time, findings)
        """
        # Execute analysis
        analysis.start()
        result = self.analysis_service.execute_analysis(analysis)
        execution_time = time.time() - start_time

        # Mark as completed and save
        analysis.complete(result)
        await self.analysis_repository.save(analysis)

        # Process findings if any
        findings = []
        if "findings" in result:
            findings = await self._process_findings(analysis, result["findings"])

        return result, execution_time, findings

    async def _publish_analysis_completion_events(
        self,
        command: PerformAnalysisCommand,
        analysis: Analysis,
        result: Dict[str, Any],
        execution_time: float,
        findings: List
    ) -> List:
        """Publish analysis completion and finding events.

        Args:
            command: The original command
            analysis: The completed analysis
            result: Analysis results
            execution_time: Time taken for execution
            findings: Generated findings

        Returns:
            List of published events
        """
        events = []
        correlation_id = getattr(command, "command_id", str(uuid4()))

        # Publish analysis completed event
        if self.event_bus:
            completed_event = AnalysisCompletedEvent(
                event_id=str(uuid4()),
                correlation_id=correlation_id,
                analysis_id=analysis.id.value,
                document_id=command.document_id,
                analysis_type=command.analysis_type,
                result=result,
                execution_time_seconds=execution_time,
                findings_count=len(findings),
                metadata={
                    "user_id": getattr(command, "user_id", None),
                    "session_id": getattr(command, "session_id", None),
                },
            )
            await self.event_bus.publish(completed_event)
            events.append(completed_event)

        # Publish finding events
        for finding in findings:
            if self.event_bus:
                finding_event = FindingCreatedEvent(
                    event_id=str(uuid4()),
                    correlation_id=correlation_id,
                    finding_id=finding.id.value,
                    document_id=command.document_id,
                    analysis_id=analysis.id.value,
                    severity=finding.severity,
                    category=finding.category,
                    description=finding.description,
                    confidence=finding.confidence.value,
                    metadata={
                        "user_id": getattr(command, "user_id", None),
                        "session_id": getattr(command, "session_id", None),
                    },
                )
                await self.event_bus.publish(finding_event)
                events.append(finding_event)

        return events

    def to_response(self, result: PerformAnalysisResult) -> AnalysisResultResponse:
        """Convert result to response DTO."""
        findings_responses = [FindingResponse.from_domain(finding) for finding in result.findings]

        return AnalysisResultResponse.create(result.analysis, findings_responses)
