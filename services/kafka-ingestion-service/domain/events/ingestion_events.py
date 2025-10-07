"""Ingestion Domain Events."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class EventIngested:
    """
    Event ingested domain event.
    
    Published when a document event is successfully ingested into Kafka.
    """
    
    event_id: str
    document_id: str
    event_type: str
    ingested_at: datetime
    correlation_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        event_id: str,
        document_id: str,
        event_type: str,
        correlation_id: Optional[str] = None
    ) -> "EventIngested":
        """Create event."""
        return cls(
            event_id=event_id,
            document_id=document_id,
            event_type=event_type,
            ingested_at=datetime.now(timezone.utc),
            correlation_id=correlation_id,
        )


@dataclass(frozen=True)
class EventProcessed:
    """
    Event processed domain event.
    
    Published when a document event is successfully processed.
    """
    
    event_id: str
    document_id: str
    processed_at: datetime
    processing_time_seconds: float
    correlation_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        event_id: str,
        document_id: str,
        processing_time_seconds: float,
        correlation_id: Optional[str] = None
    ) -> "EventProcessed":
        """Create event."""
        return cls(
            event_id=event_id,
            document_id=document_id,
            processed_at=datetime.now(timezone.utc),
            processing_time_seconds=processing_time_seconds,
            correlation_id=correlation_id,
        )


@dataclass(frozen=True)
class EventFailed:
    """
    Event failed domain event.
    
    Published when a document event processing fails.
    """
    
    event_id: str
    document_id: str
    error_message: str
    retry_count: int
    can_retry: bool
    failed_at: datetime
    correlation_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        event_id: str,
        document_id: str,
        error_message: str,
        retry_count: int,
        can_retry: bool,
        correlation_id: Optional[str] = None
    ) -> "EventFailed":
        """Create event."""
        return cls(
            event_id=event_id,
            document_id=document_id,
            error_message=error_message,
            retry_count=retry_count,
            can_retry=can_retry,
            failed_at=datetime.now(timezone.utc),
            correlation_id=correlation_id,
        )


@dataclass(frozen=True)
class JobCompleted:
    """
    Job completed domain event.
    
    Published when an ingestion job completes.
    """
    
    job_id: str
    status: str
    total_events: int
    events_succeeded: int
    events_failed: int
    duration_seconds: float
    completed_at: datetime
    
    @classmethod
    def create(
        cls,
        job_id: str,
        status: str,
        total_events: int,
        events_succeeded: int,
        events_failed: int,
        duration_seconds: float
    ) -> "JobCompleted":
        """Create event."""
        return cls(
            job_id=job_id,
            status=status,
            total_events=total_events,
            events_succeeded=events_succeeded,
            events_failed=events_failed,
            duration_seconds=duration_seconds,
            completed_at=datetime.now(timezone.utc),
        )

