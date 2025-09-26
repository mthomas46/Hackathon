"""AI Request repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.ai_request import AIRequest
from ..value_objects.request_id import RequestId


class AIRequestRepository(ABC):
    """Abstract repository for AI request persistence."""

    @abstractmethod
    async def save(self, request: AIRequest) -> None:
        """Save an AI request."""
        pass

    @abstractmethod
    async def find_by_id(self, request_id: RequestId) -> Optional[AIRequest]:
        """Find an AI request by ID."""
        pass

    @abstractmethod
    async def find_by_model(self, model_name: str, limit: int = 100) -> List[AIRequest]:
        """Find AI requests by model name."""
        pass

    @abstractmethod
    async def find_recent(self, limit: int = 50) -> List[AIRequest]:
        """Find recent AI requests."""
        pass

    @abstractmethod
    async def delete(self, request_id: RequestId) -> bool:
        """Delete an AI request by ID."""
        pass

    @abstractmethod
    async def count_by_model(self, model_name: str) -> int:
        """Count requests by model name."""
        pass
