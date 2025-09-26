"""LLM Provider repository interface for DDD compliance."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.llm_provider import LLMProvider, ProviderStatus


class LLMProviderRepository(ABC):
    """Abstract repository for LLM provider operations."""

    @abstractmethod
    async def save(self, provider: LLMProvider) -> None:
        """Save an LLM provider."""
        pass

    @abstractmethod
    async def find_by_id(self, provider_id: str) -> Optional[LLMProvider]:
        """Find provider by ID."""
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[LLMProvider]:
        """Find provider by name."""
        pass

    @abstractmethod
    async def find_active(self) -> List[LLMProvider]:
        """Find all active providers."""
        pass

    @abstractmethod
    async def find_supporting_model(self, model: str) -> List[LLMProvider]:
        """Find providers that support a specific model."""
        pass

    @abstractmethod
    async def update_status(self, provider_id: str, status: ProviderStatus) -> bool:
        """Update provider status."""
        pass
