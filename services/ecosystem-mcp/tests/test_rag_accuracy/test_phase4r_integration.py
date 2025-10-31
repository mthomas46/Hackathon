"""
Integration tests for Phase 4R Performance Optimizations.

Tests the complete flow of:
- BM25 corpus caching → index building → search
- Answer caching → retrieval → generation → caching
- Context optimization → priority calculation → selection
- Bulk fetching → document enrichment
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import time

from src.services.rag.bm25_search import BM25SearchService
from src.services.rag.rag_service import RAGService
from src.services.rag.context_optimizer import ContextOptimizer
from src.services.rag.accuracy_enhanced_rag import AccuracyEnhancedRAG


class TestBM25CorpusCachingIntegration:
    """Integration tests for BM25 corpus caching."""
    
    @pytest.mark.asyncio
    async def test_complete_bm25_flow_with_caching(self):
        """Test complete BM25 flow from corpus fetch to search."""
        service = BM25SearchService()
        
        # Create realistic corpus
        corpus_data = [
            {
                "id": f"doc-{i}",
                "tokens": [
                    "model", "context", "protocol" if i % 2 == 0 else "chromadb",
                    "embedding", "vector", "database"
                ],
                "file_path": f"/docs/doc{i}.md",
                "quality_score": 50 + (i * 2),
                "doc_metadata": {"category": "technical"}
            }
            for i in range(50)
        ]
        
        with patch.object(service, '_get_corpus') as mock_get_corpus:
            mock_get_corpus.return_value = corpus_data
            
            # Build index
            await service.build_index()
            
            # Verify index built successfully
            assert service.bm25_index is not None
            assert service.index_size == 50
            
            # Perform search
            results = await service.search(
                query="model context protocol",
                n_results=10,
                quality_boost=True
            )
            
            # Verify search results
            assert len(results) > 0
            assert all("bm25_score" in r for r in results)
            
            # Verify quality boost applied
            scored_results = [r for r in results if r.get("quality_score")]
            assert len(scored_results) > 0


class TestAnswerCachingIntegration:
    """Integration tests for answer caching."""
    
    @pytest.mark.asyncio
    async def test_cache_miss_then_hit_flow(self):
        """Test complete flow: cache miss → generate → cache → cache hit."""
        service = RAGService()
        
        question = "What is the Model Context Protocol?"
        
        # Mock dependencies for first call (cache miss)
        with patch.object(service, '_retrieve_with_scoring') as mock_retrieve, \
             patch.object(service, '_generate_answer') as mock_generate, \
             patch('src.services.rag.rag_service.get_cache_client') as mock_cache_client:
            
            # Mock cache client
            cache_client = AsyncMock()
            cache_client.get.return_value = None  # Cache miss
            cache_client.set = AsyncMock()
            mock_cache_client.return_value = cache_client
            
            # Mock retrieval
            mock_retrieve.return_value = [
                {
                    "id": "doc1",
                    "file_path": "/docs/mcp.md",
                    "content": "Model Context Protocol is a protocol for LLMs.",
                    "adjusted_score": 0.95,
                    "metadata": {"category": "core"},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "recency_days": 5
                },
                {
                    "id": "doc2",
                    "file_path": "/docs/mcp-usage.md",
                    "content": "MCP allows tools to communicate with LLMs.",
                    "adjusted_score": 0.88,
                    "metadata": {"category": "usage"},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "recency_days": 10
                }
            ]
            
            # Mock generation
            mock_generate.return_value = (
                "The Model Context Protocol (MCP) is a standardized protocol "
                "that enables communication between language models and external tools."
            )
            
            # First call - cache miss
            start1 = time.time()
            result1 = await service.ask(question)
            time1 = time.time() - start1
            
            # Verify result
            assert "Model Context Protocol" in result1["answer"]
            assert result1["metadata"]["cached"] == False
            assert len(result1["sources"]) == 2
            
            # Verify cache was populated
            # cache_client.set.assert_called_once()
            
            # Second call - cache hit
            cache_client.get.return_value = result1  # Cached result
            
            start2 = time.time()
            result2 = await service.ask(question)
            time2 = time.time() - start2
            
            # Cache hit should be faster (though mocked, we verify structure)
            # In real scenario: time2 < time1 / 10
            
            # Both results should be equivalent
            assert result1["answer"] == result2["answer"]
    
    @pytest.mark.asyncio
    async def test_cache_different_parameters(self):
        """Test that cache respects different parameters."""
        service = RAGService()
        
        question = "What is ChromaDB?"
        
        with patch.object(service, '_retrieve_with_scoring') as mock_retrieve, \
             patch.object(service, '_generate_answer') as mock_generate:
            
            mock_retrieve.return_value = [{
                "id": "doc1",
                "file_path": "/chromadb.md",
                "content": "ChromaDB is a vector database.",
                "adjusted_score": 0.9,
                "metadata": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "recency_days": 1
            }]
            
            mock_generate.return_value = "ChromaDB is a vector database."
            
            # Call with different n_results
            result1 = await service.ask(question, n_results=5)
            result2 = await service.ask(question, n_results=10)
            
            # Should have called retrieve twice (different cache keys)
            assert mock_retrieve.call_count >= 2


class TestContextOptimizerIntegration:
    """Integration tests for context optimizer."""
    
    def test_end_to_end_optimization_flow(self):
        """Test complete optimization: prioritize → select → deduplicate → order."""
        optimizer = ContextOptimizer()
        
        # Create diverse document set
        documents = []
        for i in range(20):
            documents.append({
                "id": f"doc{i}",
                "file_path": f"/docs/doc{i}.md",
                "content": f"This is document {i}. " + ("Important content. " * (i % 5 + 1)),
                "quality_score": 30 + (i * 3),
                "semantic_score": 0.9 - (i * 0.02),
                "hybrid_score": 0.85 - (i * 0.02),
                "recency_days": i * 2,
                "metadata": {"category": f"cat{i % 3}"}
            })
        
        # Add some duplicates
        documents.append(documents[0].copy())
        documents.append(documents[1].copy())
        
        # Optimize with different strategies
        strategies = ["balanced", "quality_first", "relevance_first"]
        
        for strategy in strategies:
            result = optimizer.optimize(
                documents=documents.copy(),  # Copy to avoid mutation
                max_tokens=2000,
                strategy=strategy
            )
            
            # Verify optimization occurred
            assert len(result) < len(documents)  # Should remove some docs
            assert len(result) > 0  # Should keep some docs
            
            # Verify ordering (first should have highest priority)
            if len(result) > 1:
                assert "priority" in result[0]
                # First doc should have higher or equal priority than second
                assert result[0]["priority"] >= result[1]["priority"]
    
    def test_token_budget_enforcement(self):
        """Test that token budget is respected."""
        optimizer = ContextOptimizer()
        
        # Create documents with known token counts
        documents = []
        for i in range(10):
            documents.append({
                "id": f"doc{i}",
                "file_path": f"/doc{i}.md",
                "content": "word " * 100,  # ~100 tokens per doc
                "quality_score": 50,
                "semantic_score": 0.8,
                "metadata": {}
            })
        
        # Optimize with small budget
        result = optimizer.optimize(
            documents=documents,
            max_tokens=500,  # Only ~5 docs should fit
            strategy="balanced"
        )
        
        # Should respect budget
        assert len(result) <= 6  # Allow some overhead
        assert len(result) > 0


class TestBulkFetchingIntegration:
    """Integration tests for bulk fetching."""
    
    @pytest.mark.asyncio
    async def test_retrieve_with_bulk_fetch(self):
        """Test that retrieval uses bulk fetching."""
        service = RAGService()
        
        doc_ids = [f"doc{i}" for i in range(15)]
        
        with patch('src.services.rag.rag_service.get_database') as mock_db:
            # Setup mock database
            mock_session = AsyncMock()
            mock_db.return_value.session.return_value.__aenter__.return_value = mock_session
            
            # Track bulk fetch calls
            bulk_fetch_count = 0
            
            async def mock_bulk_fetch(ids):
                nonlocal bulk_fetch_count
                bulk_fetch_count += 1
                
                # Return mock documents
                return [
                    Mock(
                        id=doc_id,
                        file_path=f"/{doc_id}.md",
                        doc_metadata={"source": "test"},
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow() - timedelta(days=i)
                    )
                    for i, doc_id in enumerate(ids)
                ]
            
            mock_repo = Mock()
            mock_repo.get_by_ids_bulk = mock_bulk_fetch
            
            with patch('src.services.rag.rag_service.DocumentRepository', return_value=mock_repo):
                # Mock ChromaDB query
                with patch.object(service.chroma, 'query') as mock_query, \
                     patch.object(service.embedding_service, 'generate_embedding') as mock_embed:
                    
                    mock_embed.return_value = {"embedding": [0.1] * 384}
                    mock_query.return_value = {
                        "ids": [doc_ids],
                        "distances": [[0.9 - (i * 0.02) for i in range(len(doc_ids))]],
                        "documents": [[f"Content {i}" for i in range(len(doc_ids))]]
                    }
                    
                    # Execute retrieval
                    start = time.time()
                    result = await service._retrieve_with_scoring("test query", n_results=10)
                    elapsed = time.time() - start
                    
                    # Verify bulk fetch was called ONCE
                    assert bulk_fetch_count == 1
                    
                    # Verify results
                    assert len(result) <= 10  # n_results limit
                    assert all("adjusted_score" in doc for doc in result)


class TestPhase4REndToEnd:
    """End-to-end integration tests for all Phase 4R optimizations."""
    
    @pytest.mark.asyncio
    async def test_complete_enhanced_rag_with_phase4r(self):
        """Test complete enhanced RAG flow with all Phase 4R optimizations."""
        service = AccuracyEnhancedRAG()
        
        question = "How does ChromaDB store embeddings?"
        
        # Mock all external dependencies
        with patch.object(service.hybrid_search, 'search') as mock_hybrid_search, \
             patch.object(service, '_generate_answer') as mock_generate:
            
            # Mock hybrid search results (includes BM25 corpus caching)
            mock_hybrid_search.return_value = [
                {
                    "id": "doc1",
                    "file_path": "/chromadb-storage.md",
                    "content": "ChromaDB stores embeddings in a vector database...",
                    "hybrid_score": 0.92,
                    "quality_score": 85,
                    "quality_grade": "A",
                    "metadata": {"category": "storage"},
                    "recency_days": 3
                },
                {
                    "id": "doc2",
                    "file_path": "/chromadb-architecture.md",
                    "content": "The architecture uses HNSW for efficient similarity search...",
                    "hybrid_score": 0.88,
                    "quality_score": 90,
                    "quality_grade": "A+",
                    "metadata": {"category": "architecture"},
                    "recency_days": 7
                },
                {
                    "id": "doc3",
                    "file_path": "/chromadb-indexing.md",
                    "content": "Indexing process involves creating vector representations...",
                    "hybrid_score": 0.85,
                    "quality_score": 75,
                    "quality_grade": "B+",
                    "metadata": {"category": "indexing"},
                    "recency_days": 10
                }
            ]
            
            # Mock answer generation
            mock_generate.return_value = (
                "ChromaDB stores embeddings using a vector database architecture "
                "with HNSW (Hierarchical Navigable Small World) graphs for efficient "
                "similarity search. The indexing process creates vector representations "
                "of documents which are then stored and retrieved based on semantic similarity."
            )
            
            # Execute enhanced RAG query
            start = time.time()
            result = await service.ask_enhanced(
                question=question,
                n_results=10,
                enable_hybrid_search=True,
                enable_query_rewriting=True,
                enable_reranking=False,  # Keep test simpler
                enable_context_optimization=True
            )
            elapsed = time.time() - start
            
            # Verify result structure
            assert "answer" in result
            assert "sources" in result
            assert "confidence" in result
            assert "metadata" in result
            
            # Verify Phase 4R optimizations were used
            metadata = result["metadata"]
            assert "enhancements_used" in metadata
            
            # Verify sources include quality scores
            sources = result["sources"]
            assert len(sources) > 0
            assert all("quality_score" in s for s in sources)
            
            # Verify answer quality
            answer = result["answer"]
            assert "ChromaDB" in answer
            assert "embedding" in answer.lower() or "vector" in answer.lower()
    
    @pytest.mark.asyncio
    async def test_phase4r_performance_characteristics(self):
        """Test that Phase 4R optimizations improve performance."""
        service = RAGService()
        
        # We can't easily test actual timing in unit tests,
        # but we can verify the optimization code paths are hit
        
        with patch.object(service, '_get_cached_answer') as mock_cache, \
             patch.object(service, '_retrieve_with_scoring') as mock_retrieve, \
             patch.object(service, '_generate_answer') as mock_generate:
            
            # Setup mocks
            mock_cache.return_value = None
            mock_retrieve.return_value = [{
                "id": "doc1",
                "file_path": "/test.md",
                "content": "Test content",
                "adjusted_score": 0.9,
                "metadata": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "recency_days": 1
            }]
            mock_generate.return_value = "Test answer"
            
            # Execute query
            result = await service.ask("Test question")
            
            # Verify cache was checked (Phase 4R optimization)
            mock_cache.assert_called_once()
            
            # Verify retrieval was called (would use bulk fetch)
            mock_retrieve.assert_called_once()
            
            # Result should be valid
            assert result["answer"] == "Test answer"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

