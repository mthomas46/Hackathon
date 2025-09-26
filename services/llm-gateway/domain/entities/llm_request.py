"""LLM Request domain entity for DDD compliance."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class RequestStatus(Enum):
    """Status of LLM request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LLMRequest:
    """Domain entity representing an LLM request."""

    id: str
    prompt: str
    model: str
    provider: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    response: Optional[str] = None
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start_processing(self) -> None:
        """Mark request as started processing."""
        self.status = RequestStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def complete_successfully(self, response: str, token_usage: Optional[Dict[str, int]] = None) -> None:
        """Mark request as completed successfully."""
        self.status = RequestStatus.COMPLETED
        self.response = response
        self.token_usage = token_usage
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """Mark request as failed."""
        self.status = RequestStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def cancel(self) -> None:
        """Mark request as cancelled."""
        self.status = RequestStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    @property
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status in [RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED]

    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Get processing time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
