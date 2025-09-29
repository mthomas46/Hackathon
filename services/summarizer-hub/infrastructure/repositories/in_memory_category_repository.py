"""In-Memory Category Repository."""

from typing import Dict, List, Optional
from ..domain.repositories.category_repository import ICategoryRepository
from ..domain.entities.category import Category, CategoryId

class InMemoryCategoryRepository(ICategoryRepository):
    def __init__(self):
        self._categories: Dict[str, Category] = {}

    async def save(self, category: Category) -> None:
        self._categories[category.id.value] = category

    async def get_by_id(self, category_id: CategoryId) -> Optional[Category]:
        return self._categories.get(category_id.value)

    async def list_by_document(self, document_id: str) -> List[Category]:
        return [c for c in self._categories.values() if c.document_id == document_id]
