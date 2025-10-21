"""
Context-Aware RAG System (Week 3, Day 2)

Enables RAG queries filtered by repository context with:
- Repository-specific filtering
- Hierarchical context filtering (ROOT/SERVICE/MODULE/COMPONENT)
- Technology stack awareness
- Service-level isolation
- Time range filtering
- Language filtering

Builds on top of existing RAG and hierarchical context systems.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..analysis.hierarchical_context_manager import (
    get_hierarchical_context_manager,
    HierarchicalContext,
    ContextLevel
)
from ...storage.chromadb_client import get_chroma_client
from ..embeddings.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class ContextAwareRAG:
    """
    Context-aware RAG with hierarchical filtering.
    
    Enables filtering RAG queries by:
    - Repository ID
    - Hierarchical context (ROOT/SERVICE/MODULE/COMPONENT)
    - Technology stack
    - Programming language
    - Service name
    - Time range
    - File patterns
    
    Features:
    - Smart context resolution
    - Multi-level filtering
    - Metadata enrichment
    - Performance optimization
    """
    
    def __init__(self):
        self.context_manager = get_hierarchical_context_manager()
        self.chromadb = get_chroma_client()
        self.embedding_service = get_embedding_service()
        logger.info("ContextAwareRAG initialized")
    
    async def query_with_context(
        self,
        query: str,
        repo_id: Optional[str] = None,
        context_id: Optional[str] = None,
        context_level: Optional[ContextLevel] = None,
        service_filter: Optional[str] = None,
        tech_filter: Optional[List[str]] = None,
        language_filter: Optional[str] = None,
        time_range: Optional[timedelta] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Query with context filtering.
        
        Args:
            query: Query text
            repo_id: Optional repository filter
            context_id: Optional hierarchical context ID
            context_level: Optional context level filter
            service_filter: Optional service name filter
            tech_filter: Optional technology stack filter
            language_filter: Optional programming language filter
            time_range: Optional time range for documents
            limit: Max results
        
        Returns:
            Query results with context metadata
        """
        logger.info(f"🔍 Context-aware RAG query: {query[:100]}")
        
        # Get context if specified
        context = None
        if context_id:
            context = await self.context_manager.get_context(context_id)
            logger.info(f"   📍 Using context: {context.name if context else 'NOT FOUND'}")
        
        # Build ChromaDB where clause
        where = self._build_where_clause(
            repo_id=repo_id,
            context=context,
            context_level=context_level,
            service_filter=service_filter,
            tech_filter=tech_filter,
            language_filter=language_filter,
            time_range=time_range
        )
        
        if where:
            logger.info(f"   🎯 Filters: {list(where.keys())}")
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Query ChromaDB with context
        try:
            results = await self.chromadb.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where if where else None
            )
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB query with filters failed, retrying without filters: {e}")
            # Fallback: query without filters
            results = await self.chromadb.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
        
        # Enhance results with context info
        enhanced_results = await self._enhance_with_context(results, context)
        
        # Calculate relevance scores
        scored_results = self._calculate_relevance_scores(enhanced_results, query)
        
        return {
            "query": query,
            "filters": {
                "repo_id": repo_id,
                "context_id": context_id,
                "context_level": context_level.name if context_level else None,
                "service": service_filter,
                "tech_stack": tech_filter,
                "language": language_filter,
                "time_range_hours": time_range.total_seconds() / 3600 if time_range else None
            },
            "context_info": {
                "name": context.name if context else None,
                "level": context.level.name if context else None,
                "full_path": context.full_path if context else None,
                "file_count": context.level_files if context else None
            } if context else None,
            "results": scored_results,
            "total": len(scored_results),
            "metadata": {
                "filters_applied": where is not None,
                "context_used": context is not None
            }
        }
    
    def _build_where_clause(
        self,
        repo_id: Optional[str],
        context: Optional[HierarchicalContext],
        context_level: Optional[ContextLevel],
        service_filter: Optional[str],
        tech_filter: Optional[List[str]],
        language_filter: Optional[str],
        time_range: Optional[timedelta]
    ) -> Optional[Dict]:
        """
        Build ChromaDB where clause for filtering.
        
        Returns:
            Where clause dictionary or None if no filters
        """
        where = {}
        
        # Repository filter
        if repo_id:
            where["repo_id"] = repo_id
        
        # Context-based filtering
        if context:
            # Filter by context's file patterns
            if context.file_patterns:
                # Use pattern matching (if ChromaDB supports it)
                where["file_path"] = {"$in": context.file_paths}
            elif context.file_paths:
                where["file_path"] = {"$in": context.file_paths}
        
        # Context level filter
        if context_level:
            where["context_level"] = context_level.name
        
        # Service filter
        if service_filter:
            where["service"] = service_filter
        
        # Technology stack filter
        if tech_filter and len(tech_filter) > 0:
            # Tech filter with OR logic
            where["$or"] = [
                {"technology": tech}
                for tech in tech_filter
            ]
        
        # Language filter
        if language_filter:
            where["language"] = language_filter
        
        # Time range filter
        if time_range:
            cutoff = datetime.utcnow() - time_range
            where["created_at"] = {"$gte": cutoff.isoformat()}
        
        return where if where else None
    
    async def _enhance_with_context(
        self,
        results: Dict,
        context: Optional[HierarchicalContext]
    ) -> List[Dict]:
        """
        Enhance results with context information.
        
        Args:
            results: Raw ChromaDB results
            context: Optional context to enhance with
        
        Returns:
            Enhanced results list
        """
        enhanced = []
        
        # Handle both list and dict formats from ChromaDB
        documents = results.get("documents", [[]])[0] if isinstance(results.get("documents"), list) else []
        metadatas = results.get("metadatas", [[]])[0] if isinstance(results.get("metadatas"), list) else []
        distances = results.get("distances", [[]])[0] if isinstance(results.get("distances"), list) else []
        
        for idx, (doc, metadata) in enumerate(zip(documents, metadatas)):
            enhanced_doc = {
                "content": doc,
                "metadata": metadata or {},
                "distance": distances[idx] if idx < len(distances) else None,
                "context": None
            }
            
            # Add context info if available
            if context:
                enhanced_doc["context"] = {
                    "name": context.name,
                    "level": context.level.name,
                    "full_path": context.full_path,
                    "technologies": context.technologies
                }
            
            enhanced.append(enhanced_doc)
        
        return enhanced
    
    def _calculate_relevance_scores(
        self,
        results: List[Dict],
        query: str
    ) -> List[Dict]:
        """
        Calculate relevance scores for results.
        
        Combines:
        - Vector distance (from ChromaDB)
        - Keyword matching
        - Context relevance
        
        Args:
            results: Enhanced results
            query: Original query
        
        Returns:
            Results with relevance scores
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for result in results:
            # Base score from vector distance (0-1, lower is better)
            distance = result.get("distance", 1.0)
            vector_score = 1.0 - min(distance, 1.0)  # Convert to 0-1, higher is better
            
            # Keyword matching score
            content = result.get("content", "").lower()
            matches = sum(1 for word in query_words if word in content)
            keyword_score = min(matches / len(query_words), 1.0) if query_words else 0.0
            
            # Combined relevance score (weighted average)
            relevance_score = (vector_score * 0.7) + (keyword_score * 0.3)
            
            result["relevance_score"] = round(relevance_score, 3)
            result["vector_score"] = round(vector_score, 3)
            result["keyword_score"] = round(keyword_score, 3)
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results
    
    async def get_repository_contexts(
        self,
        repo_id: str
    ) -> List[HierarchicalContext]:
        """
        Get all available contexts for a repository.
        
        Args:
            repo_id: Repository ID
        
        Returns:
            List of available contexts
        """
        logger.info(f"📚 Fetching contexts for repo: {repo_id}")
        
        # Query all contexts for this repo
        contexts = await self.context_manager.search_contexts(
            query=repo_id,
            level=None  # Get all levels
        )
        
        logger.info(f"   ✅ Found {len(contexts)} contexts")
        
        return contexts
    
    async def get_context_summary(
        self,
        context_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get summary of a specific context.
        
        Args:
            context_id: Context ID
        
        Returns:
            Context summary with stats
        """
        context = await self.context_manager.get_context(context_id)
        
        if not context:
            return None
        
        # Get children
        children = await self.context_manager.get_children(context_id)
        
        return {
            "id": context.id,
            "name": context.name,
            "level": context.level.name,
            "full_path": context.full_path,
            "parent_id": context.parent_id,
            "children_count": len(children),
            "file_count": context.level_files,
            "lines_of_code": context.level_lines,
            "technologies": context.technologies,
            "primary_language": context.primary_language,
            "services": context.services,
            "description": context.description
        }


# Singleton
_context_aware_rag_instance: Optional[ContextAwareRAG] = None


def get_context_aware_rag() -> ContextAwareRAG:
    """Get singleton context-aware RAG instance."""
    global _context_aware_rag_instance
    if _context_aware_rag_instance is None:
        _context_aware_rag_instance = ContextAwareRAG()
    return _context_aware_rag_instance

