"""Domain events related to inference operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from .model_events import DomainEvent


@dataclass
class InferenceStarted(DomainEvent):
    """
    Event fired when inference request starts processing.
    
    Attributes:
        request_id: ID of the inference request
        model_name: Name of model being used
        prompt_length: Length of input prompt
        context_id: Optional context session ID
    """
    
    request_id: UUID
    model_name: str
    prompt_length: int
    context_id: Optional[UUID] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "event_type": "inference.started",
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "request_id": str(self.request_id),
            "model_name": self.model_name,
            "prompt_length": self.prompt_length,
            "context_id": str(self.context_id) if self.context_id else None,
        }


@dataclass
class InferenceCompleted(DomainEvent):
    """
    Event fired when inference completes successfully.
    
    Attributes:
        request_id: ID of the inference request
        model_name: Name of model used
        tokens_generated: Number of tokens generated
        generation_time_ms: Time taken in milliseconds
        tokens_per_second: Generation rate
        cached: Whether response was served from cache
    """
    
    request_id: UUID
    model_name: str
    tokens_generated: int
    generation_time_ms: float
    tokens_per_second: float
    cached: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "event_type": "inference.completed",
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "request_id": str(self.request_id),
            "model_name": self.model_name,
            "tokens_generated": self.tokens_generated,
            "generation_time_ms": self.generation_time_ms,
            "tokens_per_second": self.tokens_per_second,
            "cached": self.cached,
        }


@dataclass
class InferenceFailed(DomainEvent):
    """
    Event fired when inference fails.
    
    Attributes:
        request_id: ID of the inference request
        model_name: Name of model attempted
        error_type: Type of error encountered
        error_message: Error description
        retry_count: Number of retries attempted
    """
    
    request_id: UUID
    model_name: str
    error_type: str
    error_message: str
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "event_type": "inference.failed",
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "request_id": str(self.request_id),
            "model_name": self.model_name,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }

