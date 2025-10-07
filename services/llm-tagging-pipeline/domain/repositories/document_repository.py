"""Document Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.document import Document


class DocumentRepository(ABC):
    """
    Abstract repository for documents.
    
    Defines contract for document persistence operations.
    """
    
    @abstractmethod
    async def save(self, document: Document) -> None:
        """
        Save document.
        
        Args:
            document: Document to save
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_untagged(self, limit: int = 100) -> List[Document]:
        """
        Get untagged documents.
        
        Args:
            limit: Maximum number of documents
            
        Returns:
            List of untagged documents
        """
        pass
    
    @abstractmethod
    async def get_by_source(
        self,
        source_type: str,
        limit: int = 100
    ) -> List[Document]:
        """
        Get documents by source type.
        
        Args:
            source_type: Source type
            limit: Maximum number of documents
            
        Returns:
            List of documents
        """
        pass
    
    @abstractmethod
    async def update(self, document: Document) -> None:
        """
        Update document.
        
        Args:
            document: Document to update
        """
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """
        Delete document.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        pass

