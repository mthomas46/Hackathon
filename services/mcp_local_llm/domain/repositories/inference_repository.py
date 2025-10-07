"""Inference request repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from ..entities import InferenceRequest


class InferenceRepository(ABC):
    """Repository interface for InferenceRequest entity persistence."""
    
    @abstractmethod
    async def get(self, request_id: UUID) -> Optional[InferenceRequest]:
        """Get inference request by ID."""
        pass
    
    @abstractmethod
    async def save(self, request: InferenceRequest) -> InferenceRequest:
        """Save or update inference request."""
        pass
    
    @abstractmethod
    async def list_pending(self) -> List[InferenceRequest]:
        """List all pending inference requests."""
        pass
    
    @abstractmethod
    async def list_by_model(self, model_name: str, limit: int = 100) -> List[InferenceRequest]:
        """List recent inference requests for a model."""
        pass
    
    @abstractmethod
    async def list_by_context(self, context_id: UUID) -> List[InferenceRequest]:
        """List all inference requests for a context session."""
        pass
    
    @abstractmethod
    async def get_statistics(
        self,
        model_name: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> dict:
        """
        Get inference statistics.
        
        Returns dict with:
        - total_requests
        - completed_requests
        - failed_requests
        - average_generation_time_ms
        - average_tokens_per_second
        """
        pass

