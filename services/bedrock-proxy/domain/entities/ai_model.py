"""AI Model domain entity."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from ..value_objects.model_name import ModelName


@dataclass
class AIModel:
    """Domain entity representing an AI model configuration."""

    name: ModelName
    provider: str
    max_tokens: int = 4096
    supports_streaming: bool = False
    context_window: int = 4096
    input_cost_per_token: float = 0.0
    output_cost_per_token: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> None:
        """Validate the AI model configuration."""
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        if self.context_window <= 0:
            raise ValueError("context_window must be positive")

        if self.input_cost_per_token < 0:
            raise ValueError("input_cost_per_token cannot be negative")

        if self.output_cost_per_token < 0:
            raise ValueError("output_cost_per_token cannot be negative")

    def can_handle_request(self, token_count: int) -> bool:
        """Check if this model can handle a request with given token count."""
        return token_count <= self.context_window

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request."""
        return (input_tokens * self.input_cost_per_token) + (output_tokens * self.output_cost_per_token)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': str(self.name),
            'provider': self.provider,
            'max_tokens': self.max_tokens,
            'supports_streaming': self.supports_streaming,
            'context_window': self.context_window,
            'input_cost_per_token': self.input_cost_per_token,
            'output_cost_per_token': self.output_cost_per_token,
            'metadata': self.metadata,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
