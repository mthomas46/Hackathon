"""Documentation Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.documentation import Documentation


class DocumentationRepository(ABC):
    """Abstract repository for Documentation entities."""
    
    @abstractmethod
    async def add(self, doc: Documentation) -> None:
        """Add documentation."""
        pass
    
    @abstractmethod
    async def get_by_id(self, doc_id: str) -> Optional[Documentation]:
        """Get documentation by ID."""
        pass
    
    @abstractmethod
    async def update(self, doc: Documentation) -> None:
        """Update documentation."""
        pass
    
    @abstractmethod
    async def delete(self, doc_id: str) -> None:
        """Delete documentation."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Documentation]:
        """List all documentation."""
        pass
    
    @abstractmethod
    async def find_by_path(self, file_path: str) -> Optional[Documentation]:
        """Find documentation by file path."""
        pass
    
    @abstractmethod
    async def find_by_source(self, source_type: str, source_repo: str) -> List[Documentation]:
        """Find documentation by source."""
        pass
    
    @abstractmethod
    async def find_outdated(self) -> List[Documentation]:
        """Find outdated documentation."""
        pass
    
    @abstractmethod
    async def find_by_tags(self, tags: List[str]) -> List[Documentation]:
        """Find documentation by tags."""
        pass

