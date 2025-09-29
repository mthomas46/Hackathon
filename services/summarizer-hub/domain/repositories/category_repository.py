"""Category Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.category import Category, CategoryId

class ICategoryRepository(ABC):
    @abstractmethod
    async def save(self, category: Category) -> None: pass

    @abstractmethod
    async def get_by_id(self, category_id: CategoryId) -> Optional[Category]: pass

    @abstractmethod
    async def list_by_document(self, document_id: str) -> List[Category]: pass
