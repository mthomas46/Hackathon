"""Domain events related to model lifecycle."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from uuid import UUID


@dataclass
class DomainEvent:
    """Base class for domain events."""
    occurred_at: datetime
    event_id: UUID
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        raise NotImplementedError


@dataclass
class ModelLoaded(DomainEvent):
    """
    Event fired when a model is successfully loaded.
    
    Attributes:
        model_id: ID of the loaded model
        model_name: Name of the model
        memory_usage_mb: Memory consumed by the model
        gpu_layers: Number of GPU layers loaded
        load_time_ms: Time taken to load in milliseconds
    """
    
    model_id: UUID
    model_name: str
    memory_usage_mb: float
    gpu_layers: int
    load_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "event_type": "model.loaded",
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "model_id": str(self.model_id),
            "model_name": self.model_name,
            "memory_usage_mb": self.memory_usage_mb,
            "gpu_layers": self.gpu_layers,
            "load_time_ms": self.load_time_ms,
        }


@dataclass
class ModelUnloaded(DomainEvent):
    """
    Event fired when a model is unloaded.
    
    Attributes:
        model_id: ID of the unloaded model
        model_name: Name of the model
        uptime_seconds: How long the model was loaded
        total_inferences: Number of inferences performed
    """
    
    model_id: UUID
    model_name: str
    uptime_seconds: float
    total_inferences: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "event_type": "model.unloaded",
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "model_id": str(self.model_id),
            "model_name": self.model_name,
            "uptime_seconds": self.uptime_seconds,
            "total_inferences": self.total_inferences,
        }


@dataclass
class ModelError(DomainEvent):
    """
    Event fired when a model encounters an error.
    
    Attributes:
        model_id: ID of the model
        model_name: Name of the model
        error_type: Type of error
        error_message: Error description
        recoverable: Whether the error is recoverable
    """
    
    model_id: UUID
    model_name: str
    error_type: str
    error_message: str
    recoverable: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "event_type": "model.error",
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "model_id": str(self.model_id),
            "model_name": self.model_name,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "recoverable": self.recoverable,
        }

