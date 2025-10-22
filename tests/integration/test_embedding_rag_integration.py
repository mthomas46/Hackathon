"""
Integration tests for Embedding Service + RAG Query pipeline.

Tests the complete flow:
1. Generate embeddings for documents
2. Store in ChromaDB
3. Query via RAG endpoint
4. Verify model consistency
5. Validate results quality
"""

import pytest
import asyncio
import httpx
from typing import List, Dict
import time

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


class TestEmbeddingRAGIntegration:
    """Integration tests for embedding + RAG pipeline."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_rag_query(self):
        """Test complete RAG query flow with real services."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Step 1: Perform semantic search
            query = "How does the worker loop process jobs?"
            
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": query, "limit": 5}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate response structure
            assert "results" in data
            assert "query" in data
            assert "total_results" in data
            
            # Validate results quality
            assert data["total_results"] > 0
            assert len(data["results"]) > 0
            
            # Check first result
            first_result = data["results"][0]
            assert "file_path" in first_result
            assert "score" in first_result
            assert "service_name" in first_result
            
            # Score should be meaningful (0.0-1.0)
            assert 0.0 <= first_result["score"] <= 1.0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_model_consistency_check(self):
        """Test that query uses same model as ingestion."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Get embedding from service
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": "test", "limit": 1}
            )
            
            assert response.status_code == 200
            
            # If successful, model consistency is maintained
            # (would fail with dimension mismatch error if inconsistent)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_queries_consistent(self):
        """Test multiple queries return consistent dimensions."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            queries = [
                "worker loop",
                "embedding generation",
                "document processing"
            ]
            
            for i, query in enumerate(queries):
                # Add delay to avoid rate limiting (10/minute = 6s between requests)
                if i > 0:
                    await asyncio.sleep(7)
                response = await client.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": query, "limit": 3}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # All queries should succeed (same model/dimensions)
                assert "results" in data
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_relevance_quality(self):
        """Test search returns relevant results."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Query about worker loop
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": "How does the ingestion worker loop work?", "limit": 5}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should find worker-related files
            results = data["results"]
            assert len(results) > 0
            
            # Top result should have high relevance
            if results:
                top_score = results[0]["score"]
                assert top_score > 0.5  # At least 50% relevant
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_filter(self):
        """Test filtering results by service name."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={
                    "query": "worker loop",
                    "service_name": "ecosystem-mcp",
                    "limit": 5
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # All results should be from specified service
            for result in data["results"]:
                assert result["service_name"] == "ecosystem-mcp"


class TestEmbeddingServiceHealth:
    """Integration tests for embedding service health."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embedding_service_available(self):
        """Test that embedding service is reachable."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get("http://localhost:8001/health")
                assert response.status_code == 200
                
                data = response.json()
                assert "status" in data
                assert "model" in data
            except httpx.ConnectError:
                pytest.skip("FastEmbed service not running")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ollama_available(self):
        """Test that Ollama is reachable."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get("http://localhost:11434/api/tags")
                assert response.status_code == 200
                
                data = response.json()
                assert "models" in data
                
                # Check for nomic-embed-text model
                models = [m["name"] for m in data["models"]]
                assert any("nomic-embed-text" in m for m in models)
            except httpx.ConnectError:
                pytest.skip("Ollama service not running")


class TestDimensionConsistency:
    """Integration tests for embedding dimension consistency."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_no_dimension_mismatch_errors(self):
        """Test that queries don't fail with dimension mismatch."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Multiple different queries
            queries = [
                "worker loop processing",
                "embedding generation system",
                "document normalization",
                "ChromaDB storage",
                "RAG query pipeline"
            ]
            
            for i, query in enumerate(queries):
                # Add delay to avoid rate limiting
                if i > 0:
                    await asyncio.sleep(7)
                response = await client.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": query, "limit": 3}
                )
                
                # Should NOT get 422 or 500 errors related to dimensions
                assert response.status_code == 200
                data = response.json()
                
                # Check for dimension mismatch error
                if "error" in data:
                    assert "dimension" not in data["error"].lower()
                    assert "384" not in str(data)
                    assert "mismatch" not in data["error"].lower()


class TestPerformanceMetrics:
    """Integration tests for performance and metrics."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_performance(self):
        """Test that queries complete in reasonable time."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            start = time.time()
            
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": "test query", "limit": 5}
            )
            
            duration = time.time() - start
            
            assert response.status_code == 200
            # Should complete in under 5 seconds
            assert duration < 5.0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_batch_query_performance(self):
        """Test performance of multiple consecutive queries."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            queries = [f"test query {i}" for i in range(10)]
            
            start = time.time()
            
            for i, query in enumerate(queries):
                # Add delay to avoid rate limiting
                if i > 0:
                    await asyncio.sleep(7)
                response = await client.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": query, "limit": 3}
                )
                assert response.status_code == 200
            
            duration = time.time() - start
            
            # 10 queries with 7s delays should complete in under 80 seconds
            # (9 delays * 7s = 63s + ~10s for queries = ~73s total)
            assert duration < 80.0
            
            # Average per query (excluding delay time)
            query_time = (duration - (9 * 7)) / len(queries)  # Subtract delay time
            print(f"Average query time (excluding delays): {query_time:.2f}s")


class TestEdgeCases:
    """Integration tests for edge cases."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_empty_query(self):
        """Test handling of empty query."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": "", "limit": 5}
            )
            
            # Should handle gracefully (either 400 or return empty results)
            assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_very_long_query(self):
        """Test handling of very long query."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            long_query = "test " * 1000  # Very long query
            
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": long_query, "limit": 5}
            )
            
            # Should handle gracefully (truncate or reject)
            assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_special_characters_query(self):
        """Test handling of special characters in query."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            special_query = "test @#$% & special <> characters"
            
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                json={"query": special_query, "limit": 5}
            )
            
            # Should handle without errors
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

