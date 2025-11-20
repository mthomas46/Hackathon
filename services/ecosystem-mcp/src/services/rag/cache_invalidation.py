"""
Cache Invalidation Service for RAG

Provides methods to invalidate RAG cache when documents change.
Combines two strategies:
1. Document hash in cache key - automatic invalidation
2. Explicit invalidation on ingestion - immediate clearing
"""

import hashlib
import logging
from typing import Optional, List
from datetime import datetime

from ...storage.database import get_database
from ...storage.models_documents import DocumentModel
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class CacheInvalidationService:
    """
    Manages RAG cache invalidation to prevent stale responses.
    
    Features:
    - Document hash generation for cache key versioning
    - Explicit cache invalidation on ingestion
    - Service-specific and global cache clearing
    """
    
    def __init__(self):
        """Initialize cache invalidation service."""
        self._cache_client = None
        logger.info("CacheInvalidationService initialized")
    
    async def _get_cache_client(self):
        """Get Redis cache client lazily."""
        if self._cache_client is None:
            try:
                from aiocache import Cache
                self._cache_client = Cache(Cache.REDIS)
            except ImportError:
                logger.warning("aiocache not available, cache invalidation disabled")
                return None
        return self._cache_client
    
    async def get_document_hash(
        self,
        service_name: Optional[str] = None,
        repo_path: Optional[str] = None
    ) -> str:
        """
        Get a hash representing the current state of documents.
        
        This hash changes when:
        - Documents are added
        - Documents are updated
        - Documents are deleted
        
        Args:
            service_name: Optional service name to scope hash
            repo_path: Optional repo path to scope hash
        
        Returns:
            Hash string representing document state
        """
        try:
            async with get_database().session() as session:
                # Build query
                query = select(
                    func.count(DocumentModel.id),
                    func.max(DocumentModel.created_at),
                    func.max(DocumentModel.updated_at)
                )
                
                # Add filters if provided
                if service_name:
                    query = query.filter(
                        DocumentModel.doc_metadata['service_name'].astext == service_name
                    )
                
                if repo_path:
                    query = query.filter(DocumentModel.repo_path == repo_path)
                
                result = await session.execute(query)
                count, max_created, max_updated = result.first()
                
                # Create hash from metadata
                hash_input = f"{count}:{max_created}:{max_updated}"
                doc_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
                
                logger.debug(
                    f"Document hash for service={service_name}, repo={repo_path}: "
                    f"{doc_hash} (count={count})"
                )
                
                return doc_hash
                
        except Exception as e:
            logger.error(f"Error generating document hash: {e}", exc_info=True)
            # Return timestamp-based hash as fallback
            return hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:8]
    
    async def invalidate_service_cache(
        self,
        service_name: str,
        cache_patterns: Optional[List[str]] = None
    ) -> int:
        """
        Invalidate all RAG cache entries for a specific service.
        
        Args:
            service_name: Service name to invalidate cache for
            cache_patterns: Optional list of cache key patterns to clear
                          Defaults to all RAG-related patterns
        
        Returns:
            Number of cache keys deleted
        """
        cache_client = await self._get_cache_client()
        if not cache_client:
            logger.warning("Cache client not available, skipping invalidation")
            return 0
        
        if cache_patterns is None:
            cache_patterns = [
                f"rag_answer_v2:*{service_name}*",
                f"rag_answer_enhanced_v1:*{service_name}*",
                f"chroma_search:*{service_name}*",
                f"bm25_search:*{service_name}*",
            ]
        
        deleted_count = 0
        
        try:
            import redis.asyncio as redis
            
            # Get Redis connection from cache client
            redis_client = redis.from_url("redis://redis:6379/0")
            
            for pattern in cache_patterns:
                try:
                    # Find all keys matching pattern
                    cursor = 0
                    while True:
                        cursor, keys = await redis_client.scan(
                            cursor=cursor,
                            match=pattern,
                            count=100
                        )
                        
                        if keys:
                            # Delete keys
                            deleted = await redis_client.delete(*keys)
                            deleted_count += deleted
                            logger.info(
                                f"Deleted {deleted} cache keys matching '{pattern}'"
                            )
                        
                        if cursor == 0:
                            break
                    
                except Exception as e:
                    logger.error(
                        f"Error deleting cache keys for pattern '{pattern}': {e}",
                        exc_info=True
                    )
            
            await redis_client.close()
            
            logger.info(
                f"✅ Invalidated {deleted_count} cache entries for service '{service_name}'"
            )
            
        except Exception as e:
            logger.error(f"Error invalidating service cache: {e}", exc_info=True)
        
        return deleted_count
    
    async def invalidate_all_rag_cache(self) -> int:
        """
        Invalidate ALL RAG cache entries (nuclear option).
        
        Returns:
            Number of cache keys deleted
        """
        cache_client = await self._get_cache_client()
        if not cache_client:
            logger.warning("Cache client not available, skipping invalidation")
            return 0
        
        patterns = [
            "rag_answer_v2:*",
            "rag_answer_enhanced_v1:*",
            "chroma_search:*",
            "bm25_search:*",
            "rerank_scores_v1:*",
        ]
        
        deleted_count = 0
        
        try:
            import redis.asyncio as redis
            
            redis_client = redis.from_url("redis://redis:6379/0")
            
            for pattern in patterns:
                try:
                    cursor = 0
                    while True:
                        cursor, keys = await redis_client.scan(
                            cursor=cursor,
                            match=pattern,
                            count=100
                        )
                        
                        if keys:
                            deleted = await redis_client.delete(*keys)
                            deleted_count += deleted
                        
                        if cursor == 0:
                            break
                    
                except Exception as e:
                    logger.error(
                        f"Error deleting cache keys for pattern '{pattern}': {e}"
                    )
            
            await redis_client.close()
            
            logger.info(f"✅ Invalidated {deleted_count} total RAG cache entries")
            
        except Exception as e:
            logger.error(f"Error invalidating all cache: {e}", exc_info=True)
        
        return deleted_count
    
    async def get_cache_stats(self, service_name: Optional[str] = None) -> dict:
        """
        Get statistics about cached entries.
        
        Args:
            service_name: Optional service to get stats for
        
        Returns:
            Dict with cache statistics
        """
        try:
            import redis.asyncio as redis
            
            redis_client = redis.from_url("redis://redis:6379/0")
            
            if service_name:
                pattern = f"*{service_name}*"
            else:
                pattern = "rag_*"
            
            cursor = 0
            total_keys = 0
            
            while True:
                cursor, keys = await redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                total_keys += len(keys)
                
                if cursor == 0:
                    break
            
            await redis_client.close()
            
            return {
                "service_name": service_name,
                "pattern": pattern,
                "total_cached_keys": total_keys
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}", exc_info=True)
            return {"error": str(e)}


# Singleton instance
_cache_invalidation_service: Optional[CacheInvalidationService] = None


def get_cache_invalidation_service() -> CacheInvalidationService:
    """Get singleton cache invalidation service instance."""
    global _cache_invalidation_service
    
    if _cache_invalidation_service is None:
        _cache_invalidation_service = CacheInvalidationService()
    
    return _cache_invalidation_service

