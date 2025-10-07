"""Inference Request entity - represents an LLM inference request."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


class InferenceStatus(str, Enum):
    """Inference request status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InferenceRequest:
    """
    Domain entity representing an inference request.
    
    Attributes:
        id: Unique request identifier
        model_name: Name of model to use
        prompt: Input prompt text
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens to generate
        temperature: Generation temperature (0.0-2.0)
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        repeat_penalty: Repetition penalty
        stop_sequences: Stop generation sequences
        stream: Whether to stream response
        context_id: Optional context session ID
        status: Current request status
        created_at: Request creation timestamp
        started_at: Processing start timestamp
        completed_at: Processing completion timestamp
        response_text: Generated response text
        tokens_generated: Number of tokens generated
        generation_time_ms: Total generation time in milliseconds
        error_message: Error description if failed
        metadata: Additional request metadata
    """
    
    id: UUID = field(default_factory=uuid4)
    model_name: str = ""
    prompt: str = ""
    system_prompt: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop_sequences: List[str] = field(default_factory=list)
    stream: bool = False
    context_id: Optional[UUID] = None
    status: InferenceStatus = InferenceStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    response_text: str = ""
    tokens_generated: int = 0
    generation_time_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate inference request after initialization."""
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
        
        if not self.prompt:
            raise ValueError("Prompt cannot be empty")
        
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if not (0.0 <= self.top_p <= 1.0):
            raise ValueError("Top-p must be between 0.0 and 1.0")
        
        if self.top_k <= 0:
            raise ValueError("Top-k must be positive")
    
    def start_processing(self) -> None:
        """Mark request as processing."""
        if self.status != InferenceStatus.PENDING:
            raise ValueError(f"Cannot start processing from status: {self.status.value}")
        
        self.status = InferenceStatus.PROCESSING
        self.started_at = datetime.utcnow()
    
    def complete(self, response_text: str, tokens_generated: int) -> None:
        """
        Mark request as completed.
        
        Args:
            response_text: Generated response
            tokens_generated: Number of tokens generated
        """
        if self.status != InferenceStatus.PROCESSING:
            raise ValueError(f"Cannot complete from status: {self.status.value}")
        
        self.status = InferenceStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.response_text = response_text
        self.tokens_generated = tokens_generated
        
        if self.started_at:
            elapsed = (self.completed_at - self.started_at).total_seconds()
            self.generation_time_ms = elapsed * 1000
    
    def fail(self, error_message: str) -> None:
        """
        Mark request as failed.
        
        Args:
            error_message: Error description
        """
        self.status = InferenceStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def cancel(self) -> None:
        """Cancel the request."""
        if self.status == InferenceStatus.COMPLETED:
            raise ValueError("Cannot cancel completed request")
        
        self.status = InferenceStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status in (InferenceStatus.COMPLETED, InferenceStatus.FAILED, InferenceStatus.CANCELLED)
    
    def get_tokens_per_second(self) -> float:
        """
        Calculate tokens per second generation rate.
        
        Returns:
            Tokens per second, or 0 if not completed
        """
        if self.generation_time_ms > 0 and self.tokens_generated > 0:
            return (self.tokens_generated / self.generation_time_ms) * 1000
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary representation."""
        return {
            "id": str(self.id),
            "model_name": self.model_name,
            "prompt": self.prompt,
            "system_prompt": self.system_prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
            "stop_sequences": self.stop_sequences,
            "stream": self.stream,
            "context_id": str(self.context_id) if self.context_id else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "response_text": self.response_text,
            "tokens_generated": self.tokens_generated,
            "generation_time_ms": self.generation_time_ms,
            "tokens_per_second": self.get_tokens_per_second(),
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

