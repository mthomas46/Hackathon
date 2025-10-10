"""
Document repository for interacting with doc-store service.
"""

from typing import List, Dict, Any
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository):
    """
    Repository for doc-store service operations.
    
    Provides methods to fetch document data from the doc-store service.
    
    Inherits HTTP client and retry logic from BaseRepository,
    eliminating duplication.
    """
    
    async def get_documents_by_author(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents authored by a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of document dictionaries
        """
        documents = await self._get(f"documents/by-author/{user_id}", default=[])
        
        if documents:
            logger.info(f"Found {len(documents)} documents for user {user_id}")
        
        return documents
    
    async def get_document_count_by_author(self, user_id: str) -> int:
        """
        Get count of documents authored by a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of documents
        """
        documents = await self.get_documents_by_author(user_id)
        return len(documents)
    
    async def get_documents_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        Get documents related to a specific topic.
        
        Args:
            topic: Topic to filter by
            
        Returns:
            List of document dictionaries
        """
        documents = await self._get(
            "documents/by-topic",
            params={"topic": topic},
            default=[]
        )
        
        return documents
    
    async def get_recent_documents(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent documents by a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of documents to return
            
        Returns:
            List of recent document dictionaries
        """
        documents = await self.get_documents_by_author(user_id)
        
        # Sort by created_at (most recent first)
        documents.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        
        return documents[:limit]

