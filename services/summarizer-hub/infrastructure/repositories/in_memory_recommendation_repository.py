"""In-Memory Recommendation Repository."""

from typing import Dict, List, Optional
from ..domain.repositories.recommendation_repository import IRecommendationRepository
from ..domain.entities.recommendation import Recommendation, RecommendationId

class InMemoryRecommendationRepository(IRecommendationRepository):
    def __init__(self):
        self._recommendations: Dict[str, Recommendation] = {}

    async def save(self, recommendation: Recommendation) -> None:
        self._recommendations[recommendation.id.value] = recommendation

    async def get_by_id(self, recommendation_id: RecommendationId) -> Optional[Recommendation]:
        return self._recommendations.get(recommendation_id.value)

    async def list_by_document(self, document_id: str) -> List[Recommendation]:
        return [r for r in self._recommendations.values() if r.document_id == document_id]
