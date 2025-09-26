"""AI Model repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.ai_model import AIModel
from ..value_objects.model_name import ModelName


class AIModelRepository(ABC):
    """Abstract repository for AI model persistence."""

    @abstractmethod
    async def save(self, model: AIModel) -> None:
        """Save an AI model."""
        pass

    @abstractmethod
    async def find_by_name(self, model_name: ModelName) -> Optional[AIModel]:
        """Find an AI model by name."""
        pass

    @abstractmethod
    async def find_by_provider(self, provider: str) -> List[AIModel]:
        """Find AI models by provider."""
        pass

    @abstractmethod
    async def find_active_models(self) -> List[AIModel]:
        """Find all active AI models."""
        pass

    @abstractmethod
    async def update(self, model: AIModel) -> None:
        """Update an AI model."""
        pass

    @abstractmethod
    async def delete(self, model_name: ModelName) -> bool:
        """Delete an AI model by name."""
        pass

    @abstractmethod
    async def exists(self, model_name: ModelName) -> bool:
        """Check if a model exists."""
        pass
