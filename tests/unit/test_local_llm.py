"""Unit tests for Local LLM Platform (TDD Red Phase)."""

import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

import pytest
from datetime import datetime
from typing import List, Dict, Any

# Test imports (will fail until implemented)
from mcp_local_llm.src.ollama_client import (
    OllamaClient,
    ModelInfo,
    GenerationRequest,
    GenerationResponse,
    EmbeddingRequest,
    EmbeddingResponse
)
from mcp_local_llm.src.local_embeddings import (
    LocalEmbeddingGenerator,
    EmbeddingModel,
    EmbeddingResult
)
from mcp_local_llm.src.m4_optimizer import (
    M4Optimizer,
    OptimizationConfig,
    PerformanceMetrics
)


class TestOllamaClient:
    """Test Ollama integration client."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = OllamaClient(base_url="http://localhost:11434")
    
    @pytest.mark.asyncio
    async def test_list_models(self):
        """Test listing available models."""
        models = await self.client.list_models()
        
        assert isinstance(models, list)
        for model in models:
            assert isinstance(model, ModelInfo)
            assert model.name
            assert model.size > 0
    
    @pytest.mark.asyncio
    async def test_pull_model(self):
        """Test pulling a model from Ollama."""
        result = await self.client.pull_model("llama2:7b")
        
        assert result["status"] == "success"
        assert "model" in result
    
    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test text generation."""
        request = GenerationRequest(
            model="llama2:7b",
            prompt="What is the capital of France?",
            temperature=0.7,
            max_tokens=100
        )
        
        response = await self.client.generate(request)
        
        assert isinstance(response, GenerationResponse)
        assert response.text
        assert response.model == "llama2:7b"
        assert response.tokens_generated > 0
        assert response.generation_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming text generation."""
        request = GenerationRequest(
            model="llama2:7b",
            prompt="Count from 1 to 5",
            stream=True
        )
        
        chunks = []
        async for chunk in self.client.generate_stream(request):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert len(full_text) > 0
    
    @pytest.mark.asyncio
    async def test_generate_embeddings(self):
        """Test embedding generation."""
        request = EmbeddingRequest(
            model="llama2:7b",
            text="This is a test sentence for embedding generation."
        )
        
        response = await self.client.generate_embeddings(request)
        
        assert isinstance(response, EmbeddingResponse)
        assert len(response.embedding) > 0
        assert response.model == "llama2:7b"
        assert response.embedding_dimensions > 0
    
    @pytest.mark.asyncio
    async def test_batch_embeddings(self):
        """Test batch embedding generation."""
        texts = [
            "First sentence",
            "Second sentence",
            "Third sentence"
        ]
        
        embeddings = await self.client.batch_embeddings("llama2:7b", texts)
        
        assert len(embeddings) == len(texts)
        for embedding in embeddings:
            assert len(embedding) > 0
    
    @pytest.mark.asyncio
    async def test_model_info(self):
        """Test getting model information."""
        info = await self.client.get_model_info("llama2:7b")
        
        assert isinstance(info, ModelInfo)
        assert info.name == "llama2:7b"
        assert info.size > 0
        assert info.parameter_count > 0
        assert info.quantization
    
    @pytest.mark.asyncio
    async def test_delete_model(self):
        """Test deleting a model."""
        result = await self.client.delete_model("test-model")
        
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test Ollama health check."""
        is_healthy = await self.client.health_check()
        
        assert isinstance(is_healthy, bool)


class TestLocalEmbeddingGenerator:
    """Test local embedding generation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.generator = LocalEmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"  # Use CPU for testing
        )
    
    def test_load_model(self):
        """Test model loading."""
        assert self.generator.model is not None
        assert self.generator.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert self.generator.embedding_dimension > 0
    
    def test_generate_embedding(self):
        """Test single embedding generation."""
        text = "This is a test sentence."
        
        result = self.generator.generate_embedding(text)
        
        assert isinstance(result, EmbeddingResult)
        assert len(result.embedding) == self.generator.embedding_dimension
        assert result.text == text
        assert result.generation_time_ms > 0
    
    def test_batch_generate_embeddings(self):
        """Test batch embedding generation."""
        texts = [
            "First sentence",
            "Second sentence",
            "Third sentence",
            "Fourth sentence",
            "Fifth sentence"
        ]
        
        results = self.generator.batch_generate_embeddings(texts, batch_size=2)
        
        assert len(results) == len(texts)
        for i, result in enumerate(results):
            assert result.text == texts[i]
            assert len(result.embedding) == self.generator.embedding_dimension
    
    def test_similarity_score(self):
        """Test similarity calculation between embeddings."""
        text1 = "The cat sits on the mat"
        text2 = "A feline rests on a rug"
        text3 = "Python is a programming language"
        
        emb1 = self.generator.generate_embedding(text1)
        emb2 = self.generator.generate_embedding(text2)
        emb3 = self.generator.generate_embedding(text3)
        
        # Similar sentences should have higher similarity
        sim_12 = self.generator.cosine_similarity(emb1.embedding, emb2.embedding)
        sim_13 = self.generator.cosine_similarity(emb1.embedding, emb3.embedding)
        
        assert 0 <= sim_12 <= 1
        assert 0 <= sim_13 <= 1
        assert sim_12 > sim_13  # cat/mat more similar than cat/python
    
    def test_normalize_embeddings(self):
        """Test embedding normalization."""
        text = "Test normalization"
        
        result = self.generator.generate_embedding(text, normalize=True)
        
        # Normalized embedding should have magnitude ~1.0
        import numpy as np
        magnitude = np.linalg.norm(result.embedding)
        assert abs(magnitude - 1.0) < 0.01
    
    def test_model_cache(self):
        """Test model caching."""
        # First load
        gen1 = LocalEmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Second load (should use cache)
        gen2 = LocalEmbeddingGenerator(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Should return same model instance
        assert gen1.model is gen2.model


class TestM4Optimizer:
    """Test M4 Max optimizations."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = OptimizationConfig(
            use_metal=True,
            use_neural_engine=True,
            max_memory_gb=32,
            batch_size=8,
            num_threads=10
        )
        self.optimizer = M4Optimizer(self.config)
    
    def test_detect_hardware(self):
        """Test M4 Max hardware detection."""
        hw_info = self.optimizer.detect_hardware()
        
        assert "cpu_cores" in hw_info
        assert "memory_gb" in hw_info
        assert "has_metal" in hw_info
        assert "has_neural_engine" in hw_info
    
    def test_optimize_model_loading(self):
        """Test optimized model loading."""
        model_path = "llama2:7b"
        
        optimized_model = self.optimizer.optimize_model_loading(model_path)
        
        assert optimized_model is not None
        assert "optimization_applied" in optimized_model
    
    def test_metal_acceleration(self):
        """Test Metal GPU acceleration."""
        if not self.optimizer.config.use_metal:
            pytest.skip("Metal not available")
        
        result = self.optimizer.enable_metal_acceleration()
        
        assert result["enabled"] is True
        assert "device" in result
    
    def test_neural_engine_optimization(self):
        """Test Neural Engine optimization."""
        if not self.optimizer.config.use_neural_engine:
            pytest.skip("Neural Engine not available")
        
        result = self.optimizer.enable_neural_engine()
        
        assert result["enabled"] is True
    
    def test_batch_size_optimization(self):
        """Test automatic batch size optimization."""
        optimal_batch_size = self.optimizer.optimize_batch_size(
            model_size_gb=7.0,
            available_memory_gb=32.0
        )
        
        assert optimal_batch_size > 0
        assert optimal_batch_size <= 32  # Reasonable max
    
    def test_memory_optimization(self):
        """Test memory optimization strategies."""
        result = self.optimizer.optimize_memory_usage()
        
        assert "strategy" in result
        assert "memory_saved_gb" in result
        assert result["memory_saved_gb"] >= 0
    
    def test_performance_metrics(self):
        """Test performance metric tracking."""
        metrics = PerformanceMetrics(
            inference_time_ms=150.0,
            tokens_per_second=45.0,
            memory_usage_gb=12.5,
            gpu_utilization=0.85,
            cpu_utilization=0.45
        )
        
        assert metrics.inference_time_ms > 0
        assert metrics.tokens_per_second > 0
        assert 0 <= metrics.gpu_utilization <= 1
        assert 0 <= metrics.cpu_utilization <= 1
    
    def test_benchmark_inference(self):
        """Test inference benchmarking."""
        prompt = "What is machine learning?"
        
        metrics = self.optimizer.benchmark_inference(
            model="llama2:7b",
            prompt=prompt,
            num_runs=5
        )
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.inference_time_ms > 0
        assert metrics.tokens_per_second > 0
    
    def test_optimization_report(self):
        """Test optimization report generation."""
        report = self.optimizer.generate_optimization_report()
        
        assert "hardware" in report
        assert "optimizations" in report
        assert "performance" in report
        assert "recommendations" in report


class TestIntegration:
    """Integration tests for Local LLM Platform."""
    
    @pytest.mark.asyncio
    async def test_ollama_to_local_embeddings(self):
        """Test using Ollama with local embeddings."""
        ollama = OllamaClient()
        embedding_gen = LocalEmbeddingGenerator()
        
        # Generate text with Ollama
        gen_request = GenerationRequest(
            model="llama2:7b",
            prompt="Describe artificial intelligence",
            max_tokens=50
        )
        
        response = await ollama.generate(gen_request)
        
        # Generate embedding from response
        embedding_result = embedding_gen.generate_embedding(response.text)
        
        assert len(embedding_result.embedding) > 0
    
    @pytest.mark.asyncio
    async def test_optimized_ollama_inference(self):
        """Test Ollama inference with M4 optimizations."""
        optimizer = M4Optimizer(OptimizationConfig(use_metal=True))
        ollama = OllamaClient()
        
        # Optimize
        optimizer.enable_metal_acceleration()
        
        # Run inference
        request = GenerationRequest(
            model="llama2:7b",
            prompt="Test optimized inference"
        )
        
        response = await ollama.generate(request)
        
        assert response.generation_time_ms > 0
        # Optimized should be faster (in real scenario)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

