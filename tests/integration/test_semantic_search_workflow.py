"""
Integration Tests for Complete Semantic Search Workflow

Tests the full end-to-end workflow:
1. Document ingestion
2. Embedding generation
3. Vector storage
4. Semantic search
5. Result retrieval

These tests require:
- Database connection
- Embedding model (sentence-transformers)
- doc-store service
"""

import pytest
import asyncio
from typing import List, Dict, Any
import time


@pytest.mark.integration
class TestCompleteSemanticSearchWorkflow:
    """Test complete semantic search workflow end-to-end."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_single_document(self):
        """
        Test complete workflow for single document:
        1. Create document
        2. Generate embedding
        3. Search semantically
        4. Verify results
        """
        from services.doc_store.db.queries import (
            insert_document,
            insert_document_vector,
            semantic_search_documents
        )
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        # Step 1: Create document
        doc_id = "test-doc-001"
        content = "Machine learning algorithms are used for data analysis and prediction."
        
        insert_document(
            doc_id=doc_id,
            content=content,
            content_hash="hash123",
            metadata={"source": "test"},
            tags=["machine-learning", "algorithms"]
        )
        
        # Step 2: Generate embedding
        service = get_embedding_service()
        embedding = await service.generate_embedding(content)
        
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        
        # Step 3: Store embedding
        vector_id = insert_document_vector(
            document_id=doc_id,
            embedding=embedding,
            vector_model="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        assert vector_id is not None
        
        # Step 4: Search with similar query
        query = "algorithms for machine learning"
        query_embedding = await service.generate_embedding(query)
        
        results = semantic_search_documents(
            query_embedding=query_embedding,
            limit=10,
            min_similarity=0.5
        )
        
        # Step 5: Verify results
        assert len(results) > 0
        assert results[0]["id"] == doc_id
        assert results[0]["semantic_similarity"] > 0.5
    
    @pytest.mark.asyncio
    async def test_workflow_with_multiple_documents(self):
        """Test workflow with multiple related and unrelated documents."""
        from services.doc_store.db.queries import insert_document, insert_document_vector
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        
        # Create documents on different topics
        documents = [
            {
                "id": "doc-ml-1",
                "content": "Deep learning neural networks for image classification",
                "topic": "machine-learning"
            },
            {
                "id": "doc-ml-2",
                "content": "Supervised learning algorithms and training techniques",
                "topic": "machine-learning"
            },
            {
                "id": "doc-cooking-1",
                "content": "How to bake chocolate chip cookies at home",
                "topic": "cooking"
            },
            {
                "id": "doc-cooking-2",
                "content": "Best pasta recipes for Italian cuisine",
                "topic": "cooking"
            },
        ]
        
        # Insert and embed all documents
        for doc in documents:
            insert_document(
                doc_id=doc["id"],
                content=doc["content"],
                content_hash=f"hash-{doc['id']}",
                metadata={"topic": doc["topic"]}
            )
            
            embedding = await service.generate_embedding(doc["content"])
            insert_document_vector(
                document_id=doc["id"],
                embedding=embedding
            )
        
        # Search for machine learning
        ml_results = await service.semantic_search(
            query="neural networks and deep learning",
            limit=4,
            min_similarity=0.3
        )
        
        # Verify ML documents ranked higher
        ml_doc_ids = {r["id"] for r in ml_results[:2]}
        assert "doc-ml-1" in ml_doc_ids or "doc-ml-2" in ml_doc_ids
        
        # Search for cooking
        cooking_results = await service.semantic_search(
            query="recipes and cooking techniques",
            limit=4,
            min_similarity=0.3
        )
        
        # Verify cooking documents ranked higher
        cooking_doc_ids = {r["id"] for r in cooking_results[:2]}
        assert "doc-cooking-1" in cooking_doc_ids or "doc-cooking-2" in cooking_doc_ids
    
    @pytest.mark.asyncio
    async def test_batch_embedding_workflow(self):
        """Test batch embedding generation workflow."""
        from services.doc_store.db.queries import (
            insert_document,
            get_documents_without_vectors
        )
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        # Create multiple documents
        doc_ids = []
        for i in range(10):
            doc_id = f"batch-doc-{i}"
            doc_ids.append(doc_id)
            insert_document(
                doc_id=doc_id,
                content=f"Test document {i} with unique content",
                content_hash=f"hash-{i}",
                metadata={"index": i}
            )
        
        # Get documents without vectors
        docs_to_embed = get_documents_without_vectors(limit=20)
        assert len(docs_to_embed) >= 10
        
        # Batch embed
        service = get_embedding_service()
        results = await service.embed_documents_batch(docs_to_embed[:10])
        
        # Verify all succeeded
        successful = [r for r in results if r.get("success")]
        assert len(successful) == 10
        
        # Verify no more documents without vectors
        remaining = get_documents_without_vectors(limit=20)
        assert len(remaining) == 0 or all(d["id"] not in doc_ids for d in remaining)
    
    @pytest.mark.asyncio
    async def test_search_performance_with_many_documents(self):
        """Test search performance with larger document set."""
        from services.doc_store.db.queries import insert_document, insert_document_vector
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        
        # Create 100 documents
        contents = []
        for i in range(100):
            content = f"Document number {i} about various topics and subjects"
            contents.append(content)
            insert_document(
                doc_id=f"perf-doc-{i}",
                content=content,
                content_hash=f"hash-perf-{i}",
                metadata={"index": i}
            )
        
        # Batch generate embeddings
        embeddings = await service.generate_embeddings_batch(contents)
        
        # Store embeddings
        for i, embedding in enumerate(embeddings):
            insert_document_vector(
                document_id=f"perf-doc-{i}",
                embedding=embedding
            )
        
        # Measure search performance
        start = time.time()
        results = await service.semantic_search(
            query="topics and subjects",
            limit=20,
            min_similarity=0.3
        )
        search_duration = time.time() - start
        
        # Verify search completed quickly
        assert search_duration < 5.0  # Should complete within 5 seconds
        assert len(results) > 0


@pytest.mark.integration
class TestSemanticSearchAccuracy:
    """Test accuracy and relevance of semantic search."""
    
    @pytest.mark.asyncio
    async def test_exact_match_highest_similarity(self):
        """Test that exact matches have highest similarity."""
        from services.doc_store.db.queries import insert_document, insert_document_vector
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        
        content = "Python programming language for web development"
        doc_id = "exact-match-doc"
        
        # Insert document
        insert_document(
            doc_id=doc_id,
            content=content,
            content_hash="hash-exact",
            metadata={}
        )
        
        # Generate and store embedding
        embedding = await service.generate_embedding(content)
        insert_document_vector(document_id=doc_id, embedding=embedding)
        
        # Search with exact same text
        results = await service.semantic_search(
            query=content,
            limit=1,
            min_similarity=0.0
        )
        
        # Should have very high similarity (close to 1.0)
        assert len(results) > 0
        assert results[0]["id"] == doc_id
        assert results[0]["semantic_similarity"] > 0.95
    
    @pytest.mark.asyncio
    async def test_paraphrase_detection(self):
        """Test that paraphrased content is detected as similar."""
        from services.doc_store.db.queries import insert_document, insert_document_vector
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        
        # Original content
        original = "Artificial intelligence enables computers to learn from data"
        doc_id = "paraphrase-doc"
        
        insert_document(
            doc_id=doc_id,
            content=original,
            content_hash="hash-para",
            metadata={}
        )
        
        embedding = await service.generate_embedding(original)
        insert_document_vector(document_id=doc_id, embedding=embedding)
        
        # Paraphrased query
        paraphrase = "AI allows machines to acquire knowledge from information"
        results = await service.semantic_search(query=paraphrase, limit=1)
        
        # Should find original despite different wording
        assert len(results) > 0
        assert results[0]["id"] == doc_id
        assert results[0]["semantic_similarity"] > 0.6  # Reasonably high
    
    @pytest.mark.asyncio
    async def test_topic_filtering(self):
        """Test that searches filter by topic effectively."""
        from services.doc_store.db.queries import insert_document, insert_document_vector
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        
        # Create documents on specific topics
        tech_doc = "Cloud computing and distributed systems architecture"
        food_doc = "Organic farming and sustainable agriculture practices"
        
        for doc_id, content in [("tech-1", tech_doc), ("food-1", food_doc)]:
            insert_document(
                doc_id=doc_id,
                content=content,
                content_hash=f"hash-{doc_id}",
                metadata={}
            )
            embedding = await service.generate_embedding(content)
            insert_document_vector(document_id=doc_id, embedding=embedding)
        
        # Search for tech topic
        tech_results = await service.semantic_search(
            query="software systems and cloud infrastructure",
            limit=2,
            min_similarity=0.3
        )
        
        # Tech doc should rank higher
        assert len(tech_results) > 0
        assert tech_results[0]["id"] == "tech-1"


@pytest.mark.integration
class TestSemanticSearchEdgeCases:
    """Test edge cases in semantic search workflow."""
    
    @pytest.mark.asyncio
    async def test_search_with_no_embeddings(self):
        """Test search when no documents have embeddings."""
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        # Clear all vectors (in test environment)
        # ...
        
        service = get_embedding_service()
        results = await service.semantic_search(query="test", limit=10)
        
        # Should return empty gracefully
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_with_very_short_query(self):
        """Test search with single-word query."""
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        results = await service.semantic_search(query="AI", limit=10)
        
        # Should not crash
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_search_with_very_long_query(self):
        """Test search with extremely long query."""
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        long_query = " ".join(["word"] * 1000)  # 1000 words
        results = await service.semantic_search(query=long_query, limit=10)
        
        # Should handle truncation gracefully
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_concurrent_embedding_generation(self):
        """Test concurrent embedding generation doesn't cause conflicts."""
        from services.doc_store.db.queries import insert_document
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        
        # Create documents
        for i in range(10):
            insert_document(
                doc_id=f"concurrent-{i}",
                content=f"Content {i}",
                content_hash=f"hash-{i}",
                metadata={}
            )
        
        # Generate embeddings concurrently
        tasks = []
        for i in range(10):
            task = service.embed_document(
                document_id=f"concurrent-{i}",
                content=f"Content {i}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0


@pytest.mark.integration
class TestSemanticSearchWithRealData:
    """Test semantic search with realistic data scenarios."""
    
    @pytest.mark.asyncio
    async def test_technical_documentation_search(self):
        """Test search over technical documentation."""
        from services.doc_store.db.queries import insert_document, insert_document_vector
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service = get_embedding_service()
        
        # Simulate technical docs
        docs = [
            ("api-auth", "API Authentication using OAuth 2.0 and JWT tokens"),
            ("api-rate", "Rate limiting and API quota management strategies"),
            ("db-optimization", "Database query optimization and indexing techniques"),
            ("cache-strategy", "Caching strategies for improved application performance"),
        ]
        
        for doc_id, content in docs:
            insert_document(
                doc_id=doc_id,
                content=content,
                content_hash=f"hash-{doc_id}",
                metadata={"type": "technical"}
            )
            embedding = await service.generate_embedding(content)
            insert_document_vector(document_id=doc_id, embedding=embedding)
        
        # Search for authentication
        auth_results = await service.semantic_search(
            query="How do I authenticate API requests?",
            limit=2
        )
        
        assert len(auth_results) > 0
        assert auth_results[0]["id"] == "api-auth"
        
        # Search for performance
        perf_results = await service.semantic_search(
            query="Improving application speed and performance",
            limit=2
        )
        
        # Should find cache and db docs
        perf_ids = {r["id"] for r in perf_results}
        assert "cache-strategy" in perf_ids or "db-optimization" in perf_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

