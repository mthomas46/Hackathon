"""Analysis domain events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

from ..entities import AnalysisId, DocumentId


@dataclass(frozen=True)
class AnalysisStarted:
    """Event fired when analysis starts."""
    analysis_id: AnalysisId
    document_id: DocumentId
    analysis_type: str
    started_at: datetime
    configuration: Dict[str, Any]

    @property
    def event_type(self) -> str:
        return "analysis.started"


@dataclass(frozen=True)
class AnalysisCompleted:
    """Event fired when analysis completes successfully."""
    analysis_id: AnalysisId
    document_id: DocumentId
    analysis_type: str
    completed_at: datetime
    result: Dict[str, Any]
    execution_time_seconds: float

    @property
    def event_type(self) -> str:
        return "analysis.completed"


@dataclass(frozen=True)
class AnalysisFailed:
    """Event fired when analysis fails."""
    analysis_id: AnalysisId
    document_id: DocumentId
    analysis_type: str
    failed_at: datetime
    error_message: str
    execution_time_seconds: Optional[float] = None

    @property
    def event_type(self) -> str:
        return "analysis.failed"
