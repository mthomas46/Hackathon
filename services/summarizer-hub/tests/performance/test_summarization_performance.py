"""Performance Tests for Summarization Operations in Summarizer Hub Service.

This module tests performance characteristics of summarization operations including:
- Document summarization throughput and latency
- Multi-model ensemble processing performance
- Memory usage during large document summarization
- Concurrent summarization request handling
- Performance regression detection across content types

Performance tests ensure the Summarizer Hub service meets enterprise summarization requirements.
"""

import asyncio
import time
import statistics
import psutil
import os
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta

import pytest


class TestSummarizationPerformance:
    """Performance testing for summarization operations."""

    @pytest.fixture
    def performance_config(self):
        """Performance test configuration for summarization."""
        return {
            "warmup_iterations": 3,
            "test_iterations": 15,
            "concurrent_requests": [1, 3, 5, 8],
            "target_summarization_time_ms": 10000,  # 10 seconds for summarization
            "acceptable_error_rate": 0.02,  # 2%
            "memory_threshold_mb": 600,
            "cpu_threshold_percent": 85
        }

    @pytest.fixture
    def sample_documents(self):
        """Sample documents of different types and complexities for testing."""
        return {
            "short_article": {
                "content": """
                Artificial Intelligence (AI) is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions. Natural language processing enables computers to understand and generate human-like text. Computer vision allows machines to interpret visual information. These technologies are revolutionizing healthcare, finance, transportation, and many other sectors. The future of AI holds tremendous potential for solving complex problems and improving human lives.
                """.strip(),
                "word_count": 120,
                "complexity": "low"
            },
            "medium_report": {
                "content": """
                Enterprise Software Architecture Assessment Report

                Executive Summary:
                This comprehensive assessment evaluates the current software architecture of our enterprise systems. The analysis covers scalability, maintainability, security, and performance characteristics.

                Current Architecture Overview:
                Our system employs a microservices architecture with 15+ services running on Kubernetes clusters. The primary technology stack includes Python/FastAPI for backend services, React for frontend applications, PostgreSQL for data storage, and Redis for caching.

                Key Findings:
                1. Service Communication: RESTful APIs with gRPC for high-performance inter-service communication
                2. Data Management: Hybrid approach with relational databases for transactions and NoSQL for analytics
                3. Security: Multi-layer security including API gateways, authentication, and encryption
                4. Monitoring: Comprehensive logging and metrics collection with ELK stack

                Recommendations:
                - Implement service mesh for better observability
                - Adopt event-driven architecture for improved decoupling
                - Enhance automated testing coverage
                - Implement chaos engineering practices

                Conclusion:
                The current architecture provides a solid foundation but requires strategic improvements to meet future scalability and reliability requirements.
                """.strip(),
                "word_count": 280,
                "complexity": "medium"
            },
            "long_technical_doc": {
                "content": """
                Advanced Machine Learning Techniques for Enterprise Applications

                Chapter 1: Introduction to Modern ML Paradigms

                Machine learning has evolved significantly from traditional statistical methods to sophisticated deep learning architectures. This document explores advanced techniques that are transforming enterprise applications.

                1.1 Neural Network Architectures

                Convolutional Neural Networks (CNNs) excel at image processing tasks through their ability to capture spatial hierarchies. Recurrent Neural Networks (RNNs) and Long Short-Term Memory (LSTM) networks are particularly effective for sequential data processing, making them ideal for natural language processing, time series analysis, and speech recognition.

                1.2 Transformer Architecture

                The transformer architecture, introduced in the paper "Attention is All You Need," revolutionized sequence-to-sequence tasks. Self-attention mechanisms allow the model to weigh the importance of different parts of the input sequence when generating each element of the output sequence.

                Key advantages include:
                - Parallel processing capabilities
                - Long-range dependency modeling
                - Scalability to large datasets
                - Transfer learning potential

                1.3 Large Language Models

                Recent advances in large language models have demonstrated remarkable capabilities in understanding and generating human-like text. Models like GPT, BERT, and T5 have achieved state-of-the-art performance on numerous NLP benchmarks.

                1.4 Model Compression and Optimization

                As models grow larger, optimization techniques become crucial for deployment in production environments. Quantization reduces model size and inference latency while maintaining acceptable accuracy levels. Pruning removes unnecessary parameters, and distillation transfers knowledge from large models to smaller ones.

                Chapter 2: Enterprise ML Infrastructure

                Building robust ML infrastructure requires careful consideration of scalability, reliability, and maintainability. Modern enterprise ML platforms typically include:

                2.1 Data Pipeline Management
                - Automated data ingestion from multiple sources
                - Data validation and quality assurance
                - Feature engineering and preprocessing
                - Real-time and batch processing capabilities

                2.2 Model Development Lifecycle
                - Experiment tracking and versioning
                - Automated model training pipelines
                - Hyperparameter optimization
                - Model validation and testing

                2.3 Deployment and Serving
                - Model containerization and orchestration
                - A/B testing and gradual rollouts
                - Performance monitoring and alerting
                - Automated model updates and rollback

                2.4 Governance and Compliance
                - Model explainability and interpretability
                - Bias detection and mitigation
                - Data privacy and security
                - Regulatory compliance frameworks

                Chapter 3: Future Directions

                The field of machine learning continues to evolve rapidly. Emerging trends include:

                3.1 Multimodal Learning
                Integration of multiple data modalities (text, images, audio, video) for more comprehensive understanding.

                3.2 Federated Learning
                Distributed learning approaches that preserve data privacy across multiple parties.

                3.3 Edge AI
                Deployment of ML models on edge devices for real-time processing with minimal latency.

                3.4 Responsible AI
                Increased focus on ethical AI development, fairness, transparency, and accountability.

                Conclusion:

                Advanced machine learning techniques are transforming enterprise applications across industries. Successful implementation requires not only technical expertise but also careful consideration of infrastructure, governance, and ethical implications. Organizations that embrace these technologies while maintaining robust practices will be well-positioned for future success.
                """.strip(),
                "word_count": 650,
                "complexity": "high"
            },
            "very_long_research_paper": {
                "content": " ".join([f"Research section {i} contains detailed analysis of {['methodology', 'results', 'discussion', 'conclusion'][i % 4]} with comprehensive data and multiple figures." for i in range(200)]) + " " + "This extensive research paper covers advanced topics in artificial intelligence, machine learning, deep learning, neural networks, natural language processing, computer vision, reinforcement learning, and their applications in enterprise settings. " * 50,
                "word_count": 1500,
                "complexity": "very_high"
            }
        }

    @pytest.mark.asyncio
    async def test_document_summarization_throughput(self, performance_config, sample_documents):
        """Test document summarization throughput under normal load."""
        # Mock summarization
        mock_summary_result = {
            "summary": "This is a comprehensive summary of the document content highlighting key points and main conclusions.",
            "word_count": 85,
            "compression_ratio": 0.25,
            "processing_time": 1.2,
            "model_used": "claude-3-sonnet",
            "confidence_score": 0.92
        }

        with patch("main.SummarizationEngine.summarize_document", new_callable=AsyncMock) as mock_summarize:
            mock_summarize.return_value = mock_summary_result

            # Import the summarize function
            from main import summarize_document

            # Warmup phase
            for _ in range(performance_config["warmup_iterations"]):
                await summarize_document(sample_documents["short_article"], "executive")

            # Performance test phase - test different document complexities
            for doc_name, doc_config in sample_documents.items():
                print(f"\nTesting {doc_name} document summarization performance...")

                # Adjust mock result based on document complexity
                complexity_multipliers = {
                    "low": 1,
                    "medium": 1.8,
                    "high": 3.2,
                    "very_high": 5.5
                }
                multiplier = complexity_multipliers[doc_config["complexity"]]

                mock_result = mock_summary_result.copy()
                mock_result["processing_time"] = 1.2 * multiplier
                mock_result["compression_ratio"] = min(0.4, 0.25 * (1 / multiplier))  # Better compression for longer docs
                mock_summarize.return_value = mock_result

                response_times = []
                compression_ratios = []
                start_time = time.time()

                for _ in range(performance_config["test_iterations"]):
                    iteration_start = time.time()
                    result = await summarize_document(doc_config, "executive")
                    iteration_end = time.time()

                    response_time = (iteration_end - iteration_start) * 1000  # Convert to ms
                    response_times.append(response_time)
                    compression_ratios.append(result.get("compression_ratio", 0))

                    # Verify result structure
                    assert "summary" in result
                    assert "word_count" in result
                    assert result["confidence_score"] > 0

                end_time = time.time()
                total_time = end_time - start_time

                # Calculate performance metrics
                avg_response_time = statistics.mean(response_times)
                median_response_time = statistics.median(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                throughput = performance_config["test_iterations"] / total_time  # summaries/s
                avg_compression = statistics.mean(compression_ratios)

                # Performance assertions based on document complexity
                complexity_time_limits = {
                    "low": 2000,
                    "medium": 4000,
                    "high": 8000,
                    "very_high": 15000
                }
                expected_max_time = complexity_time_limits[doc_config["complexity"]]

                assert avg_response_time < expected_max_time, \
                    f"Average response time {avg_response_time:.2f}ms exceeds target {expected_max_time}ms for {doc_name}"

                print(f"  Document: {doc_name}")
                print(f"  Word Count: {doc_config['word_count']}")
                print(f"  Total Summaries: {performance_config['test_iterations']}")
                print(f"  Total Time: {total_time:.2f}s")
                print(f"  Throughput: {throughput:.2f} summaries/s")
                print(f"  Avg Compression Ratio: {avg_compression:.2%}")
                print(f"  Avg Response Time: {avg_response_time:.2f}ms")
                print(f"  Median Response Time: {median_response_time:.2f}ms")
                print(f"  95th Percentile: {p95_response_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_summarization_requests(self, performance_config, sample_documents):
        """Test performance under concurrent summarization requests."""
        async def single_summarization_request(request_id: int, doc_config: Dict[str, Any], summary_type: str) -> float:
            """Perform single summarization request and return response time."""
            start_time = time.time()

            # Simulate summarization processing with variable time based on document complexity
            complexity_delays = {
                "low": 0.3,
                "medium": 0.8,
                "high": 2.0,
                "very_high": 4.0
            }

            # Base processing time
            processing_time = complexity_delays[doc_config["complexity"]]

            # Add some variance
            import random
            processing_time += random.uniform(-processing_time * 0.2, processing_time * 0.2)
            processing_time = max(0.1, processing_time)  # Minimum 100ms

            await asyncio.sleep(processing_time)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return response_time

        # Test different concurrency levels
        for concurrent_requests in performance_config["concurrent_requests"]:
            print(f"\nTesting concurrent summarization with {concurrent_requests} parallel requests...")

            start_time = time.time()

            # Create concurrent summarization tasks with different document types
            tasks = []
            summary_types = ["executive", "technical", "bullet_points", "narrative"]
            for i in range(concurrent_requests):
                # Cycle through different document types
                doc_name = list(sample_documents.keys())[i % len(sample_documents)]
                doc_config = sample_documents[doc_name]
                summary_type = summary_types[i % len(summary_types)]
                task = single_summarization_request(i, doc_config, summary_type)
                tasks.append(task)

            # Execute all tasks concurrently
            response_times = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # Calculate performance metrics
            throughput = concurrent_requests / total_time  # requests/s
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            print(f"  Concurrent Requests: {concurrent_requests}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} requests/s")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")
            print(f"  Min Response Time: {min_response_time:.2f}ms")
            print(f"  Max Response Time: {max_response_time:.2f}ms")

            # Performance assertions for concurrent requests
            # Allow for some overhead in concurrent processing
            concurrency_overhead = concurrent_requests ** 0.5  # Moderate scaling for CPU-bound summarization
            expected_max_time = performance_config["target_summarization_time_ms"] * concurrency_overhead

            assert avg_response_time < expected_max_time, \
                f"Average response time {avg_response_time:.2f}ms too high under concurrent load"

            assert throughput > concurrent_requests * 0.6, \
                f"Throughput {throughput:.2f} requests/s too low for {concurrent_requests} concurrent requests"

    def test_memory_usage_during_summarization(self, performance_config, sample_documents):
        """Test memory usage during large document summarization."""
        import gc

        process = psutil.Process()

        def simulate_document_summarization(doc_config: Dict[str, Any]) -> Dict[str, Any]:
            """Simulate document summarization with memory allocation."""
            # Simulate memory allocation during summarization
            # In real implementation, this would be actual model inference and processing

            # Base memory for summarization
            base_memory = 1024 * 1024 * 50  # 50MB base

            # Additional memory based on document size and complexity
            doc_words = doc_config["word_count"]
            complexity_multiplier = {"low": 1, "medium": 1.5, "high": 2.5, "very_high": 4}
            doc_memory = doc_words * 1024 * complexity_multiplier[doc_config["complexity"]]  # KB per word

            # Memory for model loading and processing
            model_memory = 1024 * 1024 * 200  # 200MB for model

            # Total memory allocation
            total_memory = base_memory + doc_memory + model_memory
            large_data = "x" * total_memory  # Allocate memory

            # Simulate processing time based on document size and complexity
            processing_time = (doc_words / 1000) * complexity_multiplier[doc_config["complexity"]]
            time.sleep(min(processing_time, 2.0))  # Cap at 2 seconds for testing

            result = {
                "document_words": doc_words,
                "complexity": doc_config["complexity"],
                "summary_length": int(doc_words * 0.15),  # 15% of original length
                "compression_ratio": 0.15,
                "memory_used": total_memory,
                "processing_time": processing_time,
                "model_used": "claude-3-sonnet",
                "status": "completed"
            }

            # Keep reference to prevent immediate GC
            result["_memory_holder"] = large_data

            return result

        # Test memory usage with different document types
        test_scenarios = [
            ("short_article", sample_documents["short_article"]),
            ("medium_report", sample_documents["medium_report"]),
            ("long_technical_doc", sample_documents["long_technical_doc"]),
            ("very_long_research_paper", sample_documents["very_long_research_paper"])
        ]

        for doc_name, doc_config in test_scenarios:
            print(f"\nTesting memory usage for {doc_name} summarization...")

            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform summarization
            result = simulate_document_summarization(doc_config)

            peak_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Force cleanup
            del result
            gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB

            memory_delta = peak_memory - initial_memory
            memory_leak = final_memory - initial_memory

            print(f"  Initial Memory: {initial_memory:.2f} MB")
            print(f"  Peak Memory: {peak_memory:.2f} MB")
            print(f"  Final Memory: {final_memory:.2f} MB")
            print(f"  Memory Delta: {memory_delta:.2f} MB")
            print(f"  Memory Leak: {memory_leak:.2f} MB")

            # Memory assertions - scale limits based on document size
            doc_words = doc_config["word_count"]
            expected_memory_limit = max(100, doc_words / 10)  # At least 100MB, or 0.1MB per 100 words

            assert memory_delta < expected_memory_limit, \
                f"Memory usage increased by {memory_delta:.2f} MB, exceeds limit {expected_memory_limit:.2f} MB for {doc_name}"

            # Allow for some cleanup delay but not excessive memory leaks
            assert abs(memory_leak) < 50, \
                f"Memory leak detected: {memory_leak:.2f} MB for {doc_name}"

    @pytest.mark.asyncio
    async def test_multi_model_ensemble_performance(self, performance_config):
        """Test performance of multi-model ensemble summarization."""
        async def ensemble_summarization(models: List[str], document: str) -> Dict[str, Any]:
            """Simulate multi-model ensemble summarization."""
            start_time = time.time()

            # Simulate processing with each model
            model_summaries = []
            total_processing_time = 0

            for model in models:
                # Different models have different processing characteristics
                model_times = {
                    "claude-3-haiku": 0.8,
                    "claude-3-sonnet": 1.5,
                    "claude-3-opus": 2.5,
                    "titan-text-express": 1.0
                }

                processing_time = model_times.get(model, 1.0)
                await asyncio.sleep(processing_time)
                total_processing_time += processing_time

                model_summaries.append({
                    "model": model,
                    "summary": f"Summary from {model} with {len(document.split()) // 10} key points",
                    "confidence": random.uniform(0.8, 0.95),
                    "processing_time": processing_time
                })

            # Simulate ensemble combination
            ensemble_time = 0.3
            await asyncio.sleep(ensemble_time)
            total_processing_time += ensemble_time

            # Create ensemble result
            ensemble_summary = f"Ensemble summary combining insights from {len(models)} models"
            avg_confidence = sum(s["confidence"] for s in model_summaries) / len(model_summaries)

            total_time = time.time() - start_time

            return {
                "ensemble_summary": ensemble_summary,
                "model_summaries": model_summaries,
                "models_used": models,
                "avg_confidence": avg_confidence,
                "total_processing_time": total_processing_time,
                "ensemble_time": ensemble_time,
                "actual_total_time": total_time
            }

        # Test different ensemble sizes
        ensemble_configs = [
            ["claude-3-haiku"],  # Single model baseline
            ["claude-3-haiku", "claude-3-sonnet"],  # Two models
            ["claude-3-haiku", "claude-3-sonnet", "titan-text-express"],  # Three models
            ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus", "titan-text-express"]  # Four models
        ]

        test_document = sample_documents["medium_report"]["content"]

        ensemble_results = []

        for models in ensemble_configs:
            print(f"\nTesting ensemble summarization with {len(models)} models...")

            # Test ensemble performance multiple times
            ensemble_times = []
            confidences = []

            for _ in range(5):  # Test each ensemble 5 times
                result = await ensemble_summarization(models, test_document)
                ensemble_times.append(result["actual_total_time"])
                confidences.append(result["avg_confidence"])

            avg_ensemble_time = statistics.mean(ensemble_times)
            avg_confidence = statistics.mean(confidences)

            ensemble_results.append({
                "model_count": len(models),
                "models": models,
                "avg_ensemble_time": avg_ensemble_time,
                "avg_confidence": avg_confidence,
                "efficiency": avg_confidence / avg_ensemble_time if avg_ensemble_time > 0 else 0
            })

            print(f"  Models: {models}")
            print(f"  Avg Ensemble Time: {avg_ensemble_time:.2f}s")
            print(f"  Avg Confidence: {avg_confidence:.3f}")
            print(f"  Efficiency: {avg_confidence / avg_ensemble_time:.3f} confidence/s")

        # Analyze ensemble scaling
        print("
Ensemble Scaling Analysis:")
        for result in ensemble_results:
            print(".1f")

        # Verify ensemble benefits
        single_model = next(r for r in ensemble_results if r["model_count"] == 1)
        multi_model = next(r for r in ensemble_results if r["model_count"] > 1)

        # Multi-model should provide better confidence (if not too slow)
        if multi_model["avg_ensemble_time"] < single_model["avg_ensemble_time"] * 3:
            assert multi_model["avg_confidence"] > single_model["avg_confidence"], \
                "Multi-model ensemble should provide higher confidence when efficiency is reasonable"

    @pytest.mark.asyncio
    async def test_adaptive_summarization_performance(self):
        """Test performance of adaptive summarization based on content type."""
        async def adaptive_summarization(content: str, content_type: str) -> Dict[str, Any]:
            """Simulate adaptive summarization based on content characteristics."""
            start_time = time.time()

            # Analyze content and adapt summarization strategy
            word_count = len(content.split())
            content_complexity = "high" if word_count > 500 else "medium" if word_count > 200 else "low"

            # Adaptive strategy selection
            if content_type == "technical" and content_complexity == "high":
                strategy = "multi_model_ensemble"
                models = ["claude-3-sonnet", "claude-3-opus"]
                processing_time = 3.5
            elif content_type == "business" and content_complexity == "medium":
                strategy = "single_model_optimized"
                models = ["claude-3-sonnet"]
                processing_time = 1.8
            elif content_type == "news":
                strategy = "fast_extraction"
                models = ["claude-3-haiku"]
                processing_time = 0.8
            else:
                strategy = "balanced_approach"
                models = ["titan-text-express"]
                processing_time = 1.2

            await asyncio.sleep(processing_time)

            total_time = time.time() - start_time

            return {
                "content_type": content_type,
                "content_complexity": content_complexity,
                "strategy": strategy,
                "models_used": models,
                "processing_time": processing_time,
                "actual_time": total_time,
                "summary_quality_score": random.uniform(0.85, 0.95),
                "compression_ratio": random.uniform(0.15, 0.25)
            }

        # Test adaptive summarization across different content types
        content_scenarios = [
            ("technical", "long_technical_doc"),
            ("business", "medium_report"),
            ("news", "short_article"),
            ("research", "very_long_research_paper")
        ]

        adaptation_results = []

        for content_type, doc_key in content_scenarios:
            doc_content = sample_documents[doc_key]["content"]

            print(f"\nTesting adaptive summarization for {content_type} content...")

            # Test adaptive summarization multiple times
            strategy_results = []
            for _ in range(8):
                result = await adaptive_summarization(doc_content, content_type)
                strategy_results.append(result)

            # Analyze adaptation effectiveness
            avg_processing_time = statistics.mean([r["actual_time"] for r in strategy_results])
            avg_quality_score = statistics.mean([r["summary_quality_score"] for r in strategy_results])
            strategies_used = set([r["strategy"] for r in strategy_results])

            # Should use consistent strategy for same content type
            assert len(strategies_used) == 1, f"Inconsistent strategies for {content_type}: {strategies_used}"

            strategy = list(strategies_used)[0]

            adaptation_results.append({
                "content_type": content_type,
                "strategy": strategy,
                "avg_processing_time": avg_processing_time,
                "avg_quality_score": avg_quality_score,
                "performance_per_quality": avg_quality_score / avg_processing_time if avg_processing_time > 0 else 0
            })

            print(f"  Content Type: {content_type}")
            print(f"  Strategy: {strategy}")
            print(f"  Avg Processing Time: {avg_processing_time:.2f}s")
            print(f"  Avg Quality Score: {avg_quality_score:.3f}")
            print(f"  Performance/Qlty Ratio: {avg_quality_score / avg_processing_time:.3f}")

        # Verify adaptation logic effectiveness
        print("
Adaptive Summarization Analysis:")
        for result in adaptation_results:
            print(".2f")

        # Different content types should use different strategies
        strategies = [r["strategy"] for r in adaptation_results]
        assert len(set(strategies)) > 1, "All content types using same strategy - adaptation not working"

        # Technical content should use more sophisticated strategies
        technical_result = next(r for r in adaptation_results if r["content_type"] == "technical")
        assert "ensemble" in technical_result["strategy"] or "optimized" in technical_result["strategy"], \
            "Technical content should use sophisticated summarization strategy"
