"""Recommendation Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.recommendation import Recommendation, RecommendationId

class IRecommendationRepository(ABC):
    @abstractmethod
    async def save(self, recommendation: Recommendation) -> None: pass

    @abstractmethod
    async def get_by_id(self, recommendation_id: RecommendationId) -> Optional[Recommendation]: pass

    @abstractmethod
    async def list_by_document(self, document_id: str) -> List[Recommendation]: pass
