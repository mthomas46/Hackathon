"""AI Request domain entity."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from ..value_objects.request_id import RequestId
from ..value_objects.model_name import ModelName


@dataclass
class AIRequest:
    """Domain entity representing an AI request."""

    id: RequestId
    model: ModelName
    prompt: str
    template: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None

    def __post_init__(self):
        """Initialize timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.parameters is None:
            self.parameters = {}
        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> None:
        """Validate the AI request according to domain rules."""
        if not self.prompt or not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if len(self.prompt) > 10000:  # Domain constraint
            raise ValueError("Prompt too long (max 10000 characters)")

        # Model-specific validation could be added here
        if self.model and not self.model.value:
            raise ValueError("Model name cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': str(self.id),
            'model': str(self.model),
            'prompt': self.prompt,
            'template': self.template,
            'parameters': self.parameters,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIRequest':
        """Create from dictionary representation."""
        return cls(
            id=RequestId(data['id']),
            model=ModelName(data['model']),
            prompt=data['prompt'],
            template=data.get('template'),
            parameters=data.get('parameters', {}),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )
