"""Integration tests for Local LLM Platform."""

import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

import pytest
from datetime import datetime

from mcp_local_llm.src.ollama_client import (
    OllamaClient,
    GenerationRequest,
    EmbeddingRequest
)
from mcp_local_llm.src.local_embeddings import (
    LocalEmbeddingGenerator,
    generate_embeddings_fast
)
from mcp_local_llm.src.m4_optimizer import (
    M4Optimizer,
    OptimizationConfig,
    optimize_for_m4_max
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestLocalLLMIntegration:
    """Integration tests for Local LLM Platform."""
    
    async def test_complete_llm_workflow(self):
        """Test complete workflow: optimize -> generate -> embed."""
        # Step 1: Optimize configuration
        optimizer = M4Optimizer()
        config = optimizer.get_recommended_config(model_size_gb=7.0)
        
        assert config.use_metal or config.use_neural_engine
        assert config.batch_size > 0
        
        # Step 2: Initialize Ollama client (mock in tests)
        ollama = OllamaClient()
        
        # Check health (will work if Ollama is running locally)
        is_healthy = await ollama.health_check()
        
        if is_healthy:
            # Step 3: Generate text
            request = GenerationRequest(
                model="llama2:7b",
                prompt="What is machine learning in one sentence?",
                max_tokens=50
            )
            
            response = await ollama.generate(request)
            
            assert response.text
            assert response.generation_time_ms > 0
            assert response.tokens_generated > 0
            
            # Step 4: Generate embedding for response
            embedding_gen = LocalEmbeddingGenerator()
            embedding_result = embedding_gen.generate_embedding(response.text)
            
            assert len(embedding_result.embedding) > 0
            assert embedding_result.generation_time_ms > 0
        
        await ollama.close()
    
    async def test_local_embeddings_with_semantic_search(self):
        """Test local embeddings with semantic search."""
        # Create embedding generator
        generator = LocalEmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Test corpus
        corpus = [
            "Machine learning is a subset of artificial intelligence",
            "Python is a popular programming language",
            "Neural networks are inspired by biological neurons",
            "Cloud computing provides on-demand resources",
            "Deep learning uses multiple layers of neural networks"
        ]
        
        # Search query
        query = "What is AI and neural networks?"
        
        # Perform semantic search
        results = generator.semantic_search(query, corpus, top_k=3)
        
        assert len(results) == 3
        
        # First result should be about ML/AI
        assert "machine learning" in results[0]["text"].lower() or \
               "neural networks" in results[0]["text"].lower()
        
        # Scores should be between 0 and 1
        for result in results:
            assert 0 <= result["score"] <= 1
    
    async def test_batch_embedding_performance(self):
        """Test batch embedding generation performance."""
        generator = LocalEmbeddingGenerator()
        
        # Generate test texts
        texts = [f"This is test sentence number {i}" for i in range(100)]
        
        # Generate embeddings in batches
        start_time = datetime.now()
        results = generator.batch_generate_embeddings(
            texts,
            batch_size=32,
            show_progress=False
        )
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        assert len(results) == len(texts)
        
        # Should be reasonably fast (< 10 seconds for 100 embeddings)
        assert duration_ms < 10000
        
        # All embeddings should have same dimension
        dims = set(len(r.embedding) for r in results)
        assert len(dims) == 1
    
    async def test_m4_optimization_report(self):
        """Test M4 optimization report generation."""
        optimizer = M4Optimizer()
        
        # Generate report
        report = optimizer.generate_optimization_report()
        
        assert "hardware" in report
        assert "configuration" in report
        assert "optimizations" in report
        assert "recommendations" in report
        
        # Check hardware detection
        hw = report["hardware"]
        assert "cpu_cores" in hw
        assert "memory_gb" in hw
        assert hw["memory_gb"] > 0
    
    async def test_ollama_streaming(self):
        """Test Ollama streaming generation."""
        ollama = OllamaClient()
        
        # Check if Ollama is running
        is_healthy = await ollama.health_check()
        
        if is_healthy:
            request = GenerationRequest(
                model="llama2:7b",
                prompt="Count from 1 to 5",
                stream=True,
                max_tokens=50
            )
            
            chunks = []
            async for chunk in ollama.generate_stream(request):
                chunks.append(chunk)
            
            # Should receive multiple chunks
            assert len(chunks) > 0
            
            # Combined should form coherent text
            full_text = "".join(chunks)
            assert len(full_text) > 0
        
        await ollama.close()
    
    async def test_embedding_similarity_search(self):
        """Test embedding-based similarity search."""
        generator = LocalEmbeddingGenerator()
        
        # Documents
        documents = [
            "The cat sits on the mat",
            "A dog plays in the park",
            "The kitten sleeps on the carpet",
            "Birds fly in the sky",
            "Fish swim in the ocean"
        ]
        
        # Generate embeddings
        doc_results = generator.batch_generate_embeddings(documents)
        doc_embeddings = [r.embedding for r in doc_results]
        
        # Query
        query = "Where is the cat?"
        query_result = generator.generate_embedding(query)
        
        # Find most similar
        top_matches = generator.find_most_similar(
            query_result.embedding,
            doc_embeddings,
            top_k=2
        )
        
        # Should find cat-related documents
        assert len(top_matches) == 2
        
        # First match should be about cat
        first_idx = top_matches[0][0]
        assert "cat" in documents[first_idx].lower() or \
               "kitten" in documents[first_idx].lower()
    
    async def test_m4_batch_size_optimization(self):
        """Test batch size optimization for different models."""
        optimizer = M4Optimizer()
        
        # Small model (3B)
        batch_3b = optimizer.optimize_batch_size(3.0)
        
        # Medium model (7B)
        batch_7b = optimizer.optimize_batch_size(7.0)
        
        # Large model (13B)
        batch_13b = optimizer.optimize_batch_size(13.0)
        
        # Batch size should decrease with model size
        assert batch_3b >= batch_7b >= batch_13b
        
        # All should be positive
        assert batch_3b > 0
        assert batch_7b > 0
        assert batch_13b > 0
    
    async def test_embedding_clustering(self):
        """Test embedding clustering."""
        generator = LocalEmbeddingGenerator()
        
        # Create distinct groups of documents
        group1 = ["ML is great", "AI is powerful", "Neural nets work"]
        group2 = ["Pizza is delicious", "Pasta is tasty", "Italian food"]
        group3 = ["Python code", "JavaScript program", "C++ software"]
        
        all_docs = group1 + group2 + group3
        
        # Generate embeddings
        results = generator.batch_generate_embeddings(all_docs)
        embeddings = [r.embedding for r in results]
        
        # Cluster into 3 groups
        labels = generator.cluster_embeddings(embeddings, num_clusters=3)
        
        assert len(labels) == len(all_docs)
        
        # Should have 3 distinct clusters
        unique_labels = set(labels)
        assert len(unique_labels) == 3
    
    async def test_recommended_config_generation(self):
        """Test recommended configuration generation."""
        optimizer = M4Optimizer()
        
        # Get config for different model sizes
        config_small = optimizer.get_recommended_config(3.0)
        config_large = optimizer.get_recommended_config(13.0)
        
        # Large model should use more aggressive optimization
        assert config_large.batch_size <= config_small.batch_size
        
        # Both should enable available optimizations
        if optimizer.hardware_info["has_metal"]:
            assert config_small.use_metal
            assert config_large.use_metal
    
    async def test_model_info_caching(self):
        """Test model caching in embedding generator."""
        # First load
        gen1 = LocalEmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Second load (should use cache)
        gen2 = LocalEmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Should use cached model
        assert gen1.model is gen2.model
        
        # Clear cache
        LocalEmbeddingGenerator.clear_cache()
        
        # Third load (should reload)
        gen3 = LocalEmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Should be different instance after cache clear
        assert gen1.model is not gen3.model
    
    async def test_convenience_function(self):
        """Test convenience function for quick embedding generation."""
        texts = ["Quick test", "Another test", "Final test"]
        
        embeddings = generate_embeddings_fast(texts)
        
        assert len(embeddings) == len(texts)
        for embedding in embeddings:
            assert len(embedding) > 0
    
    async def test_performance_comparison(self):
        """Test performance comparison between configurations."""
        optimizer = M4Optimizer()
        
        # Create different configurations
        config1 = OptimizationConfig(
            use_metal=True,
            precision="float16",
            batch_size=8
        )
        
        config2 = OptimizationConfig(
            use_metal=False,
            precision="float32",
            batch_size=4
        )
        
        # Compare (simulated)
        results = optimizer.compare_configurations(
            model="llama2:7b",
            prompt="Test prompt",
            configurations=[config1, config2]
        )
        
        assert len(results) == 2
        
        for result in results:
            assert "config" in result
            assert "metrics" in result
            assert result["metrics"]["inference_time_ms"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "integration"])

