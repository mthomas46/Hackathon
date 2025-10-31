"""
BM25 Keyword Search Service

Provides keyword-based search using the BM25 algorithm.
Complements semantic search for hybrid retrieval.

BM25 (Best Matching 25):
- Industry-standard keyword search algorithm
- Better than TF-IDF for search ranking
- Excellent for exact matches (function names, error codes, etc.)
"""

import logging
import pickle
import hashlib
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from collections import defaultdict
import re

from ...storage import get_database
from ...storage.repositories import DocumentRepository
from ...utils.cache_decorator import cache

logger = logging.getLogger(__name__)


class BM25SearchService:
    """
    BM25 keyword search service.
    
    Features:
    - Fast keyword-based search
    - Excellent for exact matches
    - Works with existing document corpus
    - Periodic index updates
    """
    
    def __init__(self):
        """Initialize BM25 search service."""
        self.bm25_index = None
        self.document_ids = []
        self.documents_metadata = []
        self.index_size = 0
        self.last_indexed = None
        
        logger.info("BM25SearchService initialized (index not yet built)")
    
    @cache(ttl=7200, key_prefix="bm25_corpus_v1")  # ⚡ PHASE 4R: Cache corpus for 2 hours
    async def _get_corpus(self) -> List[Dict[str, Any]]:
        """
        Get tokenized corpus from database (CACHED).
        
        PHASE 4R: Cache the tokenized corpus instead of the BM25 index.
        - Corpus is serializable (list of lists of strings)
        - Index building from corpus is FAST (< 1 second)
        - Cache hit rate is HIGH (corpus changes rarely)
        
        Returns:
            List of corpus data with id, tokens, file_path, quality_score
        
        Performance:
        - Cache MISS: ~2-5s (fetch from DB + tokenize)
        - Cache HIT: ~50-100ms (from Redis)
        - Speedup: 20-50x on cache hit
        """
        logger.info("📊 Fetching corpus from database (or cache)...")
        start_time = __import__('time').time()
        
        try:
            # Get all documents from database
            db = get_database()
            async with db.session() as session:
                doc_repo = DocumentRepository(session)
                documents = await doc_repo.get_all(limit=100000)
            
            if not documents:
                logger.warning("⚠️  No documents found in database")
                return []
            
            logger.info(f"   Fetched {len(documents)} documents from DB")
            
            # Tokenize and build corpus data
            corpus_data = []
            for doc in documents:
                # Use normalized_content (processed) or fall back to original
                content = doc.normalized_content if doc.normalized_content else doc.original_content
                tokens = self._tokenize(content)
                
                corpus_data.append({
                    "id": str(doc.id),
                    "tokens": tokens,
                    "file_path": doc.file_path,
                    "quality_score": getattr(doc, "quality_score", None),
                    "doc_metadata": doc.doc_metadata
                })
            
            elapsed = __import__('time').time() - start_time
            logger.info(f"✅ Corpus prepared: {len(corpus_data)} documents in {elapsed:.2f}s")
            
            return corpus_data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch corpus: {e}", exc_info=True)
            raise
    
    async def _get_serialized_index(self) -> Optional[bytes]:
        """
        Get serialized BM25 index from Redis cache (PHASE 3B).
        
        Returns:
            Serialized index bytes or None if not cached
        """
        try:
            from ...utils.cache_decorator import get_cache_client
            cache_client = get_cache_client()
            if not cache_client:
                return None
            
            # Generate cache key from corpus hash
            corpus_data = await self._get_corpus()
            if not corpus_data:
                return None
            
            # Hash corpus to detect changes
            corpus_str = str(sorted([d["id"] for d in corpus_data]))
            corpus_hash = hashlib.md5(corpus_str.encode()).hexdigest()
            cache_key = f"bm25_index_serialized:{corpus_hash}"
            
            # Try to get from cache
            cached = await cache_client.get(cache_key)
            if cached:
                logger.info(f"   💾 BM25 index cache HIT (corpus hash: {corpus_hash[:8]})")
                return cached
            
            logger.debug(f"   💾 BM25 index cache MISS (corpus hash: {corpus_hash[:8]})")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to get serialized index from cache: {e}")
            return None
    
    async def _save_serialized_index(self, corpus_data: List[Dict[str, Any]]):
        """
        Save serialized BM25 index to Redis cache (PHASE 3B).
        
        Args:
            corpus_data: Corpus data used to build index
        """
        try:
            from ...utils.cache_decorator import get_cache_client
            cache_client = get_cache_client()
            if not cache_client or not self.bm25_index:
                return
            
            # Generate cache key from corpus hash
            corpus_str = str(sorted([d["id"] for d in corpus_data]))
            corpus_hash = hashlib.md5(corpus_str.encode()).hexdigest()
            cache_key = f"bm25_index_serialized:{corpus_hash}"
            
            # Serialize index components
            index_data = {
                "bm25_index": self.bm25_index,
                "document_ids": self.document_ids,
                "documents_metadata": self.documents_metadata,
                "index_size": self.index_size,
                "last_indexed": self.last_indexed
            }
            
            serialized = pickle.dumps(index_data)
            
            # Store in cache (TTL: 2 hours, same as corpus)
            await cache_client.set(cache_key, serialized, ttl=7200)
            
            logger.info(
                f"   💾 BM25 index cached: {len(serialized)/1024:.1f}KB "
                f"(corpus hash: {corpus_hash[:8]}, TTL: 2h)"
            )
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to cache serialized index: {e}")
    
    async def build_index(self, force_rebuild: bool = False):
        """
        Build BM25 index from cached corpus OR deserialize from cache.
        
        PHASE 3B (AUDIT FIX): Serialize BM25 index to Redis for faster cold starts.
        
        Performance improvements:
        - PHASE 4R: Corpus cached (2-5s → 50-100ms)
        - PHASE 3B: Index cached (0.5-1s → 10-20ms)
        - Combined: 2.5-6s → 60-120ms (20-50x faster!)
        
        Benefits:
        - Shared across all workers (consistency)
        - Faster cold starts (service restarts)
        - Only rebuild when corpus actually changes
        
        Args:
            force_rebuild: Force rebuild even if cached index exists
        """
        if self.bm25_index and not force_rebuild:
            logger.info(f"BM25 index already built ({self.index_size} documents)")
            return
        
        logger.info("🔨 Building BM25 index...")
        start_time = __import__('time').time()
        
        try:
            # === PHASE 3B: Try to load serialized index from cache ===
            if not force_rebuild:
                serialized = await self._get_serialized_index()
                if serialized:
                    try:
                        index_data = pickle.loads(serialized)
                        self.bm25_index = index_data["bm25_index"]
                        self.document_ids = index_data["document_ids"]
                        self.documents_metadata = index_data["documents_metadata"]
                        self.index_size = index_data["index_size"]
                        self.last_indexed = index_data["last_indexed"]
                        
                        elapsed = __import__('time').time() - start_time
                        logger.info(
                            f"✅ BM25 index loaded from cache: {self.index_size} docs "
                            f"in {elapsed:.3f}s (20-50x faster!)"
                        )
                        return
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to deserialize index, rebuilding: {e}")
            
            # === Cache miss or force rebuild: Build from corpus ===
            corpus_fetch_start = __import__('time').time()
            corpus_data = await self._get_corpus()
            corpus_fetch_time = __import__('time').time() - corpus_fetch_start
            
            logger.info(f"   Corpus fetch: {corpus_fetch_time:.2f}s")
            
            if not corpus_data:
                logger.warning("⚠️  No corpus data available, cannot build index")
                return
            
            # Extract components
            self.document_ids = [doc["id"] for doc in corpus_data]
            self.documents_metadata = [
                {
                    "id": doc["id"],
                    "file_path": doc["file_path"],
                    "quality_score": doc["quality_score"],
                    "doc_metadata": doc["doc_metadata"]
                }
                for doc in corpus_data
            ]
            corpus = [doc["tokens"] for doc in corpus_data]
            
            # Build BM25 index (FAST operation: < 1 second)
            index_build_start = __import__('time').time()
            self.bm25_index = BM25Okapi(corpus)
            index_build_time = __import__('time').time() - index_build_start
            
            self.index_size = len(corpus)
            
            from datetime import datetime
            self.last_indexed = datetime.now()
            
            # === PHASE 3B: Save serialized index to cache ===
            await self._save_serialized_index(corpus_data)
            
            total_time = __import__('time').time() - start_time
            
            logger.info(
                f"✅ BM25 index built: {self.index_size} docs in {total_time:.2f}s "
                f"(corpus: {corpus_fetch_time:.2f}s, index: {index_build_time:.2f}s)"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to build BM25 index: {e}", exc_info=True)
            raise
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.
        
        Simple tokenization:
        - Lowercase
        - Split on whitespace and punctuation
        - Keep alphanumeric + underscores (good for code)
        
        Args:
            text: Text to tokenize
        
        Returns:
            List of tokens
        """
        # Lowercase
        text = text.lower()
        
        # Split on whitespace and most punctuation, but keep underscores
        tokens = re.findall(r'\w+', text)
        
        return tokens
    
    @cache(ttl=1800, key_prefix="bm25_search")  # ⚡ Cache for 30 min
    async def search(
        self,
        query: str,
        n_results: int = 10,
        quality_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using BM25 keyword matching (CACHED).
        
        Args:
            query: Search query
            n_results: Number of results to return
            quality_threshold: Optional minimum quality score
        
        Returns:
            List of ranked documents with BM25 scores
        """
        if not self.bm25_index:
            logger.warning("BM25 index not built yet, building now...")
            await self.build_index()
        
        if not self.bm25_index:
            logger.error("BM25 index unavailable")
            return []
        
        try:
            # Tokenize query
            query_tokens = self._tokenize(query)
            
            if not query_tokens:
                logger.warning("Query tokenized to empty list")
                return []
            
            # Get BM25 scores for all documents
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Get top N results
            top_n_indices = scores.argsort()[-n_results * 2:][::-1]  # Get 2x, filter later
            
            results = []
            for idx in top_n_indices:
                score = float(scores[idx])
                
                # Skip if score too low (not relevant)
                if score < 0.01:
                    continue
                
                metadata = self.documents_metadata[idx]
                
                # Apply quality threshold if specified
                if quality_threshold and metadata.get("quality_score"):
                    if metadata["quality_score"] < quality_threshold:
                        continue
                
                results.append({
                    "id": self.document_ids[idx],
                    "file_path": metadata["file_path"],
                    "content": "",  # Will be enriched below
                    "quality_score": metadata.get("quality_score"),
                    "bm25_score": score,
                    "metadata": metadata["doc_metadata"],
                    "recency_days": None  # Will be enriched below
                })
                
                # Stop when we have enough results
                if len(results) >= n_results:
                    break
            
            logger.info(f"🔍 BM25 search: '{query[:50]}...' → {len(results)} results")
            
            # 🔧 FIX: Enrich with content from database
            if results:
                logger.debug(f"Enriching {len(results)} BM25 results with content...")
                results = await self._enrich_with_content(results)
                # Verify enrichment worked
                enriched_count = sum(1 for r in results if r.get("content"))
                logger.info(f"✅ BM25 enrichment: {enriched_count}/{len(results)} documents have content")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ BM25 search failed: {e}", exc_info=True)
            return []
    
    async def _enrich_with_content(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich BM25 results with document content from database."""
        try:
            from ...storage import get_database
            from ...storage.repositories import DocumentRepository
            from datetime import datetime
            
            from uuid import UUID
            
            # Convert IDs to UUIDs for database lookup
            doc_ids = []
            for r in results:
                try:
                    # Handle both string and UUID types
                    id_val = r["id"]
                    if isinstance(id_val, str):
                        doc_ids.append(UUID(id_val))
                    elif isinstance(id_val, UUID):
                        doc_ids.append(id_val)
                    else:
                        doc_ids.append(UUID(str(id_val)))
                except Exception as e:
                    logger.warning(f"Could not convert ID {r['id']} to UUID: {e}")
            
            if not doc_ids:
                logger.warning("No valid UUIDs to enrich")
                return results
            
            logger.debug(f"Enriching {len(doc_ids)} BM25 results with bulk fetch")
            
            db = get_database()
            async with db.session() as session:
                doc_repo = DocumentRepository(session)
                # Use optimized bulk fetch
                documents = await doc_repo.get_by_ids_bulk(doc_ids)
            
            logger.info(f"Fetched {len(documents)} documents from DB for {len(doc_ids)} IDs")
            
            # Build ID -> document map (ensure both are strings for matching)
            doc_map = {str(doc.id): doc for doc in documents}
            
            # Enrich results
            for result in results:
                # Ensure result ID is string for lookup
                doc = doc_map.get(str(result["id"]))
                if doc:
                    # Add content (prefer normalized over original)
                    content = doc.normalized_content if doc.normalized_content else doc.original_content
                    result["content"] = content
                    
                    # Add recency
                    if doc.updated_at:
                        recency_days = (datetime.utcnow() - doc.updated_at).days
                        result["recency_days"] = recency_days
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to enrich BM25 results with content: {e}", exc_info=True)
            return results  # Return unenriched on error
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get BM25 index statistics."""
        return {
            "indexed": self.bm25_index is not None,
            "index_size": self.index_size,
            "last_indexed": self.last_indexed.isoformat() if self.last_indexed else None
        }


# Singleton instance
_bm25_service = None


def get_bm25_service() -> BM25SearchService:
    """Get or create BM25 search service singleton."""
    global _bm25_service
    if _bm25_service is None:
        _bm25_service = BM25SearchService()
    return _bm25_service

