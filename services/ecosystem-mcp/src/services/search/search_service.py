"""
Search Service

High-level search service wrapping RAG infrastructure.
Provides a clean interface for semantic search and document retrieval.
"""

import logging
from typing import List, Dict, Any, Optional

from ...services.rag import RAGService, get_rag_service
from ...storage.chromadb_client import get_chroma_client
from ...storage import get_database
from ...storage.repositories import DocumentRepository
from ..embeddings.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class SearchService:
    """
    High-level search service.
    
    Provides:
    - Semantic search via RAG
    - Document retrieval
    - Fallback to database search
    - Error handling
    
    Wraps existing RAG and ChromaDB infrastructure.
    """
    
    def __init__(self):
        """Initialize search service."""
        self.rag_service = get_rag_service()
        self.chroma = get_chroma_client()
        self.embedding_service = get_embedding_service()
        logger.info("SearchService initialized")
    
    async def search(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents.
        
        Args:
            query: Search query
            n_results: Number of results
            filter_metadata: Optional metadata filters
        
        Returns:
            List of matching documents
        """
        logger.info(f"Search query: {query[:100]}...")
        
        try:
            # Try ChromaDB search first
            embedding_result = await self.embedding_service.generate_embedding(query)
            query_embedding = embedding_result["embedding"]
            
            results = await self.chroma.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            if results and results.get("documents"):
                logger.info(f"✅ Found {len(results['documents'][0])} results via ChromaDB")
                return self._format_chroma_results(results)
            
            # Fallback to database search
            logger.info("⚠️ ChromaDB returned no results, falling back to database")
            return await self._database_search(query, n_results)
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            # Fallback to database search
            return await self._database_search(query, n_results)
    
    async def semantic_search(
        self,
        query: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using embeddings.
        
        Args:
            query: Search query
            n_results: Number of results
        
        Returns:
            List of semantically similar documents
        """
        return await self.search(query, n_results=n_results)
    
    async def keyword_search(
        self,
        keywords: List[str],
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Keyword-based search.
        
        Args:
            keywords: List of keywords
            n_results: Number of results
        
        Returns:
            List of matching documents
        """
        query = " ".join(keywords)
        return await self._database_search(query, n_results)
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
        
        Returns:
            Document or None
        """
        db = get_database()
        async with db.session() as session:
            doc_repo = DocumentRepository(session)
            from uuid import UUID
            doc = await doc_repo.get_by_id(UUID(document_id))
            
            if doc:
                return {
                    "id": str(doc.id),
                    "file_path": doc.file_path,
                    "content": doc.normalized_content,
                    "service_name": doc.service_name,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
            return None
    
    async def _database_search(
        self,
        query: str,
        n_results: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback database search.
        
        Args:
            query: Search query
            n_results: Number of results
        
        Returns:
            List of matching documents
        """
        logger.info(f"Database search: {query[:100]}...")
        
        db = get_database()
        async with db.session() as session:
            doc_repo = DocumentRepository(session)
            
            # Simple text search in normalized content
            from sqlalchemy import select, or_
            from ...storage.db_models import DocumentModel
            
            query_lower = query.lower()
            stmt = select(DocumentModel).where(
                or_(
                    DocumentModel.file_path.ilike(f"%{query_lower}%"),
                    DocumentModel.normalized_content.ilike(f"%{query_lower}%")
                )
            ).limit(n_results)
            
            result = await session.execute(stmt)
            docs = result.scalars().all()
            
            logger.info(f"✅ Found {len(docs)} results via database")
            
            return [
                {
                    "id": str(doc.id),
                    "file_path": doc.file_path,
                    "content": doc.normalized_content[:500] if doc.normalized_content else "",
                    "service_name": doc.service_name,
                    "score": 0.5,  # Default score for database search
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
                for doc in docs
            ]
    
    def _format_chroma_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format ChromaDB results.
        
        Args:
            results: ChromaDB query results
        
        Returns:
            Formatted results
        """
        formatted = []
        
        if not results.get("documents"):
            return formatted
        
        documents = results["documents"][0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]
        
        for i, doc in enumerate(documents):
            formatted.append({
                "id": ids[i] if i < len(ids) else None,
                "content": doc[:500] if doc else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "score": 1.0 - (distances[i] if i < len(distances) else 0.0),
                "distance": distances[i] if i < len(distances) else 0.0
            })
        
        return formatted


# Singleton instance
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """Get singleton search service."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

