"""AI Response domain entity."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from ..value_objects.request_id import RequestId
from .base_entity import BaseEntity


@dataclass
class AIResponse:
    """Domain entity representing an AI response."""

    request_id: RequestId
    content: str
    model_used: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    processing_time_ms: Optional[int] = None
    cost_estimate: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    def validate(self) -> None:
        """Validate the AI response."""
        if not self.content:
            raise ValueError("Response content cannot be empty")

        if self.tokens_used is not None and self.tokens_used < 0:
            raise ValueError("tokens_used cannot be negative")

        if self.processing_time_ms is not None and self.processing_time_ms < 0:
            raise ValueError("processing_time_ms cannot be negative")

        if self.cost_estimate is not None and self.cost_estimate < 0:
            raise ValueError("cost_estimate cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'request_id': str(self.request_id),
            'content': self.content,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'finish_reason': self.finish_reason,
            'processing_time_ms': self.processing_time_ms,
            'cost_estimate': self.cost_estimate,
            **self.to_dict_common()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIResponse':
        """Create from dictionary representation."""
        return cls(
            request_id=RequestId(data['request_id']),
            content=data['content'],
            model_used=data['model_used'],
            tokens_used=data.get('tokens_used'),
            finish_reason=data.get('finish_reason'),
            processing_time_ms=data.get('processing_time_ms'),
            cost_estimate=data.get('cost_estimate'),
            **cls.from_dict_common(data)
        )

    def is_successful(self) -> bool:
        """Check if the response represents a successful AI generation."""
        return self.finish_reason in ['stop', 'completed', None]

    def is_truncated(self) -> bool:
        """Check if the response was truncated."""
        return self.finish_reason == 'length'
