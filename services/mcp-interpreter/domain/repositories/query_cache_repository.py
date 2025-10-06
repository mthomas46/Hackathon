"""Query Cache Repository Interface - Domain Layer."""

from abc import ABC, abstractmethod
from typing import Optional

from services.mcp_interpreter.domain.entities.parsed_query import ParsedQuery


class QueryCacheRepository(ABC):
    """
    Abstract repository interface for caching parsed queries.
    
    Enables fast lookup of previously parsed queries to avoid
    redundant NLP processing.
    """
    
    @abstractmethod
    async def save(self, query: ParsedQuery, ttl_seconds: int = 3600) -> None:
        """
        Save a parsed query to cache.
        
        Args:
            query: Parsed query to cache
            ttl_seconds: Time-to-live in seconds (default 1 hour)
        
        Raises:
            RepositoryError: If save fails
        """
        pass
    
    @abstractmethod
    async def find_by_query_text(self, query_text: str) -> Optional[ParsedQuery]:
        """
        Find a cached parsed query by original query text.
        
        Args:
            query_text: Original query text to search for
        
        Returns:
            Cached ParsedQuery if found, None otherwise
        
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, query_id: str) -> Optional[ParsedQuery]:
        """
        Find a cached parsed query by ID.
        
        Args:
            query_id: Query ID to search for
        
        Returns:
            Cached ParsedQuery if found, None otherwise
        
        Raises:
            RepositoryError: If search fails
        """
        pass
    
    @abstractmethod
    async def delete(self, query_id: str) -> bool:
        """
        Delete a cached query by ID.
        
        Args:
            query_id: Query ID to delete
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            RepositoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def clear_cache(self) -> int:
        """
        Clear all cached queries.
        
        Returns:
            Number of queries deleted
        
        Raises:
            RepositoryError: If clearing fails
        """
        pass

