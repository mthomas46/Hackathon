"""LLM Request repository interface for DDD compliance."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.llm_request import LLMRequest, RequestStatus


class LLMRequestRepository(ABC):
    """Abstract repository for LLM request operations."""

    @abstractmethod
    async def save(self, request: LLMRequest) -> None:
        """Save an LLM request."""
        pass

    @abstractmethod
    async def find_by_id(self, request_id: str) -> Optional[LLMRequest]:
        """Find request by ID."""
        pass

    @abstractmethod
    async def find_by_status(self, status: RequestStatus, limit: int = 50) -> List[LLMRequest]:
        """Find requests by status."""
        pass

    @abstractmethod
    async def find_recent(self, limit: int = 50) -> List[LLMRequest]:
        """Find recent requests."""
        pass

    @abstractmethod
    async def update_status(self, request_id: str, status: RequestStatus) -> bool:
        """Update request status."""
        pass

    @abstractmethod
    async def delete_old_requests(self, days_old: int) -> int:
        """Delete requests older than specified days."""
        pass
