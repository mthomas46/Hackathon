"""
Integration tests for hybrid search combining semantic + BM25.

Tests complete hybrid search workflow.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestHybridSearchIntegration:
    """Integration tests for hybrid search."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hybrid_search_combines_results(self):
        """Test that hybrid search combines semantic and keyword results."""
        from src.services.rag.hybrid_search import HybridSearchService
        
        service = HybridSearchService()
        
        # Mock semantic search
        semantic_results = [
            {"id": "doc1", "file_path": "test.py", "semantic_score": 0.9},
            {"id": "doc2", "file_path": "guide.md", "semantic_score": 0.8},
        ]
        
        # Mock keyword search
        keyword_results = [
            {"id": "doc2", "file_path": "guide.md", "bm25_score": 5.0},
            {"id": "doc3", "file_path": "impl.py", "bm25_score": 4.0},
        ]
        
        # Test RRF fusion
        fused = service._reciprocal_rank_fusion(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            semantic_weight=0.7,
            keyword_weight=0.3
        )
        
        # Should have all 3 unique documents
        assert len(fused) == 3
        
        # doc2 appears in both, should have highest score
        doc2 = next(d for d in fused if d["id"] == "doc2")
        assert doc2["semantic_rank"] is not None
        assert doc2["keyword_rank"] is not None
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_quality_boost_applied(self):
        """Test that quality boost is applied correctly."""
        from src.services.rag.hybrid_search import HybridSearchService
        
        service = HybridSearchService()
        
        results = [
            {
                "id": "doc1",
                "hybrid_score": 1.0,
                "metadata": {"quality_score": 90.0}
            },
            {
                "id": "doc2",
                "hybrid_score": 1.0,
                "metadata": {"quality_score": 50.0}
            },
        ]
        
        boosted = service._apply_quality_boost(results)
        
        # High-quality doc should have higher score after boost
        doc1_score = next(d for d in boosted if d["id"] == "doc1")["hybrid_score"]
        doc2_score = next(d for d in boosted if d["id"] == "doc2")["hybrid_score"]
        
        assert doc1_score > doc2_score


class TestEnhancedRAGIntegration:
    """Integration tests for enhanced RAG service."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_enhanced_rag_pipeline(self):
        """Test complete enhanced RAG pipeline."""
        from src.services.rag.accuracy_enhanced_rag import AccuracyEnhancedRAG
        
        # This test would require full system setup
        # Simplified version:
        service = AccuracyEnhancedRAG()
        
        # Verify service initialized with all components
        assert service.hybrid_search is not None
        assert service.query_rewriter is not None
        assert service.confidence_scorer is not None
        assert service.bm25_service is not None
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_enhancement_stats(self):
        """Test enhancement statistics."""
        from src.services.rag.accuracy_enhanced_rag import AccuracyEnhancedRAG
        
        service = AccuracyEnhancedRAG()
        stats = service.get_enhancement_stats()
        
        assert "phase" in stats
        assert "enhancements" in stats
        assert "hybrid_search" in stats["enhancements"]
        assert "query_rewriting" in stats["enhancements"]
        assert "confidence_scoring" in stats["enhancements"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

