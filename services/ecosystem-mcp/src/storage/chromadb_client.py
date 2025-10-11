"""
ChromaDB client for Ecosystem MCP Service.

Provides vector storage and similarity search with single-writer pattern
to prevent index corruption.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..config import settings

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """
    ChromaDB client with single-writer pattern.
    
    ⚠️ CRITICAL: ChromaDB does NOT support concurrent writes!
    All writes MUST go through the write lock to prevent corruption.
    """
    
    def __init__(self, path: str | None = None, collection_name: str | None = None):
        """
        Initialize ChromaDB client.
        
        Args:
            path: Path to persistent storage (uses settings if None)
            collection_name: Collection name (uses settings if None)
        """
        self.path = path or str(settings.chroma_path)
        self.collection_name = collection_name or settings.chroma_collection_name
        
        # Single writer lock - CRITICAL for data integrity
        self._write_lock = asyncio.Lock()
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Get or create collection with optimal settings
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",           # Cosine similarity
                "hnsw:construction_ef": 200,      # Build quality (higher = better)
                "hnsw:search_ef": 100,            # Search quality (higher = better)
                "hnsw:M": 16,                     # Max connections per node
            }
        )
        
        logger.info(
            f"ChromaDB initialized: path={self.path}, "
            f"collection={self.collection_name}, "
            f"count={self.collection.count()}"
        )
    
    async def add_embeddings(
        self,
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        documents: Optional[List[str]] = None
    ) -> None:
        """
        Add embeddings to collection.
        
        ⚠️ Uses write lock to prevent concurrent writes.
        
        Args:
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts
            ids: List of unique IDs
            documents: Optional list of original documents
        """
        async with self._write_lock:
            # Run in thread pool to avoid blocking
            await asyncio.to_thread(
                self.collection.add,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
                documents=documents
            )
        
        logger.info(f"Added {len(embeddings)} embeddings to ChromaDB")
    
    async def update_embeddings(
        self,
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        documents: Optional[List[str]] = None
    ) -> None:
        """
        Update existing embeddings.
        
        ⚠️ Uses write lock to prevent concurrent writes.
        """
        async with self._write_lock:
            await asyncio.to_thread(
                self.collection.update,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
                documents=documents
            )
        
        logger.info(f"Updated {len(embeddings)} embeddings in ChromaDB")
    
    async def delete_embeddings(self, ids: List[str]) -> None:
        """
        Delete embeddings by ID.
        
        ⚠️ Uses write lock to prevent concurrent writes.
        """
        async with self._write_lock:
            await asyncio.to_thread(
                self.collection.delete,
                ids=ids
            )
        
        logger.info(f"Deleted {len(ids)} embeddings from ChromaDB")
    
    async def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query similar embeddings.
        
        Queries are read-only and safe to run concurrently.
        
        Args:
            query_embeddings: Query vectors
            n_results: Number of results per query
            where: Metadata filters
            where_document: Document content filters
            include: Fields to include in results
        
        Returns:
            Query results with IDs, distances, metadatas, documents
        """
        if include is None:
            include = ["metadatas", "documents", "distances"]
        
        # Queries don't need the write lock
        results = await asyncio.to_thread(
            self.collection.query,
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include
        )
        
        return results
    
    async def get_by_ids(
        self,
        ids: List[str],
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get embeddings by ID.
        
        Args:
            ids: List of IDs to retrieve
            include: Fields to include
        
        Returns:
            Results with requested fields
        """
        if include is None:
            include = ["metadatas", "documents", "embeddings"]
        
        results = await asyncio.to_thread(
            self.collection.get,
            ids=ids,
            include=include
        )
        
        return results
    
    async def count(self) -> int:
        """Get total number of embeddings in collection."""
        return await asyncio.to_thread(self.collection.count)
    
    async def reset(self) -> None:
        """
        Reset collection (delete all embeddings).
        
        ⚠️ DANGER: This will delete all data!
        """
        async with self._write_lock:
            await asyncio.to_thread(self.client.delete_collection, self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:search_ef": 100,
                    "hnsw:M": 16,
                }
            )
        
        logger.warning("ChromaDB collection reset")
    
    async def health_check(self) -> bool:
        """
        Check if ChromaDB is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            await self.count()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False


# Global ChromaDB instance
_chroma_client: ChromaDBClient | None = None


def get_chroma_client() -> ChromaDBClient:
    """
    Get global ChromaDB instance.
    
    Creates instance on first call.
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaDBClient()
    return _chroma_client


async def init_chroma():
    """Initialize ChromaDB on application startup."""
    chroma = get_chroma_client()
    healthy = await chroma.health_check()
    if not healthy:
        from ..utils.exceptions import StorageError
        raise StorageError("ChromaDB is not accessible")
    count = await chroma.count()
    logger.info(f"ChromaDB initialized successfully ({count} embeddings)")


async def close_chroma():
    """Close ChromaDB on application shutdown."""
    global _chroma_client
    if _chroma_client is not None:
        # ChromaDB cleanup (if needed)
        _chroma_client = None
    logger.info("ChromaDB closed")

