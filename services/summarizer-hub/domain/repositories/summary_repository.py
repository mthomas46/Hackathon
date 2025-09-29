"""Summary Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.summary import Summary, SummaryId

class ISummaryRepository(ABC):
    @abstractmethod
    async def save(self, summary: Summary) -> None: pass

    @abstractmethod
    async def get_by_id(self, summary_id: SummaryId) -> Optional[Summary]: pass

    @abstractmethod
    async def list_by_document(self, document_id: str) -> List[Summary]: pass
