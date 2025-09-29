"""In-Memory Summary Repository."""

from typing import Dict, List, Optional
from ..domain.repositories.summary_repository import ISummaryRepository
from ..domain.entities.summary import Summary, SummaryId

class InMemorySummaryRepository(ISummaryRepository):
    def __init__(self):
        self._summaries: Dict[str, Summary] = {}

    async def save(self, summary: Summary) -> None:
        self._summaries[summary.id.value] = summary

    async def get_by_id(self, summary_id: SummaryId) -> Optional[Summary]:
        return self._summaries.get(summary_id.value)

    async def list_by_document(self, document_id: str) -> List[Summary]:
        return [s for s in self._summaries.values() if s.document_id == document_id]
