"""Application Events - Domain event representations for the application layer."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from enum import Enum


class EventType(Enum):
    """Application event types."""
    ANALYSIS_REQUESTED = "analysis_requested"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    FINDING_CREATED = "finding_created"
    DOCUMENT_PROCESSED = "document_processed"
    WORKFLOW_TRIGGERED = "workflow_triggered"
    REPORT_GENERATED = "report_generated"
    SYSTEM_HEALTH_CHECK = "system_health_check"


@dataclass(frozen=True)
class ApplicationEvent(ABC):
    """Base class for all application events."""

    event_id: str
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'metadata': self.metadata
        }

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationEvent':
        """Create event from dictionary representation."""
        pass


@dataclass(frozen=True)
class AnalysisRequestedEvent(ApplicationEvent):
    """Event fired when an analysis is requested."""

    event_type: EventType = EventType.ANALYSIS_REQUESTED
    document_id: str = ""
    analysis_type: str = ""
    requested_by: Optional[str] = None
    priority: str = "normal"
    configuration: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'document_id': self.document_id,
            'analysis_type': self.analysis_type,
            'requested_by': self.requested_by,
            'priority': self.priority,
            'configuration': self.configuration
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisRequestedEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {}),
            document_id=data['document_id'],
            analysis_type=data['analysis_type'],
            requested_by=data.get('requested_by'),
            priority=data.get('priority', 'normal'),
            configuration=data.get('configuration', {})
        )


@dataclass(frozen=True)
class AnalysisCompletedEvent(ApplicationEvent):
    """Event fired when an analysis is completed successfully."""

    event_type: EventType = EventType.ANALYSIS_COMPLETED
    analysis_id: str = ""
    document_id: str = ""
    analysis_type: str = ""
    result: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    findings_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'analysis_id': self.analysis_id,
            'document_id': self.document_id,
            'analysis_type': self.analysis_type,
            'result': self.result,
            'execution_time_seconds': self.execution_time_seconds,
            'findings_count': self.findings_count
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisCompletedEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {}),
            analysis_id=data['analysis_id'],
            document_id=data['document_id'],
            analysis_type=data['analysis_type'],
            result=data.get('result', {}),
            execution_time_seconds=data.get('execution_time_seconds', 0.0),
            findings_count=data.get('findings_count', 0)
        )


@dataclass(frozen=True)
class AnalysisFailedEvent(ApplicationEvent):
    """Event fired when an analysis fails."""

    event_type: EventType = EventType.ANALYSIS_FAILED
    analysis_id: str = ""
    document_id: str = ""
    analysis_type: str = ""
    error_message: str = ""
    error_code: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'analysis_id': self.analysis_id,
            'document_id': self.document_id,
            'analysis_type': self.analysis_type,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'retry_count': self.retry_count
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisFailedEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {}),
            analysis_id=data['analysis_id'],
            document_id=data['document_id'],
            analysis_type=data['analysis_type'],
            error_message=data['error_message'],
            error_code=data.get('error_code'),
            retry_count=data.get('retry_count', 0)
        )


@dataclass(frozen=True)
class FindingCreatedEvent(ApplicationEvent):
    """Event fired when a finding is created."""

    event_type: EventType = EventType.FINDING_CREATED
    finding_id: str = ""
    document_id: str = ""
    analysis_id: str = ""
    severity: str = ""
    category: str = ""
    description: str = ""
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'finding_id': self.finding_id,
            'document_id': self.document_id,
            'analysis_id': self.analysis_id,
            'severity': self.severity,
            'category': self.category,
            'description': self.description,
            'confidence': self.confidence
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FindingCreatedEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {}),
            finding_id=data['finding_id'],
            document_id=data['document_id'],
            analysis_id=data['analysis_id'],
            severity=data['severity'],
            category=data['category'],
            description=data['description'],
            confidence=data.get('confidence', 0.0)
        )


@dataclass(frozen=True)
class DocumentProcessedEvent(ApplicationEvent):
    """Event fired when a document is processed."""

    event_type: EventType = EventType.DOCUMENT_PROCESSED
    document_id: str = ""
    processing_type: str = ""
    word_count: int = 0
    processing_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'document_id': self.document_id,
            'processing_type': self.processing_type,
            'word_count': self.word_count,
            'processing_time_seconds': self.processing_time_seconds,
            'metadata': self.metadata
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentProcessedEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {}),
            document_id=data['document_id'],
            processing_type=data['processing_type'],
            word_count=data.get('word_count', 0),
            processing_time_seconds=data.get('processing_time_seconds', 0.0)
        )


@dataclass(frozen=True)
class WorkflowTriggeredEvent(ApplicationEvent):
    """Event fired when a workflow is triggered."""

    event_type: EventType = EventType.WORKFLOW_TRIGGERED
    workflow_id: str = ""
    trigger_type: str = ""
    document_ids: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'workflow_id': self.workflow_id,
            'trigger_type': self.trigger_type,
            'document_ids': self.document_ids,
            'configuration': self.configuration
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowTriggeredEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {}),
            workflow_id=data['workflow_id'],
            trigger_type=data['trigger_type'],
            document_ids=data.get('document_ids', []),
            configuration=data.get('configuration', {})
        )


@dataclass(frozen=True)
class ReportGeneratedEvent(ApplicationEvent):
    """Event fired when a report is generated."""

    event_type: EventType = EventType.REPORT_GENERATED
    report_id: str = ""
    report_type: str = ""
    document_ids: List[str] = field(default_factory=list)
    findings_count: int = 0
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'report_id': self.report_id,
            'report_type': self.report_type,
            'document_ids': self.document_ids,
            'findings_count': self.findings_count,
            'file_size_bytes': self.file_size_bytes,
            'download_url': self.download_url
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportGeneratedEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {}),
            report_id=data['report_id'],
            report_type=data['report_type'],
            document_ids=data.get('document_ids', []),
            findings_count=data.get('findings_count', 0),
            file_size_bytes=data.get('file_size_bytes'),
            download_url=data.get('download_url')
        )


@dataclass(frozen=True)
class SystemHealthCheckEvent(ApplicationEvent):
    """Event fired during system health checks."""

    event_type: EventType = EventType.SYSTEM_HEALTH_CHECK
    service_name: str = ""
    service_version: str = ""
    health_status: str = ""
    response_time_ms: float = 0.0
    system_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'service_name': self.service_name,
            'service_version': self.service_version,
            'health_status': self.health_status,
            'response_time_ms': self.response_time_ms,
            'system_metrics': self.system_metrics
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemHealthCheckEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {}),
            service_name=data['service_name'],
            service_version=data['service_version'],
            health_status=data['health_status'],
            response_time_ms=data.get('response_time_ms', 0.0),
            system_metrics=data.get('system_metrics', {})
        )
