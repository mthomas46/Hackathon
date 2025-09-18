"""Semantic Analyzer - Advanced semantic similarity and embedding analysis."""

import asyncio
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json

from services.shared.core.di.services import ILoggerService, ICacheService
from services.shared.core.di.registry import get_service
from services.shared.core.logging.logger import get_logger
from services.shared.core.performance.cache_manager import get_cache_manager
from services.shared.core.performance.profiler import get_async_profiler, profile_async_operation


@dataclass
class EmbeddingResult:
    """Result of embedding calculation."""

    text: str
    embedding: np.ndarray
    model_name: str
    dimensions: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    text_hash: str = ""

    def __post_init__(self):
        """Calculate text hash for caching."""
        self.text_hash = hashlib.md5(self.text.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "embedding": self.embedding.tolist() if isinstance(self.embedding, np.ndarray) else self.embedding,
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "created_at": self.created_at.isoformat(),
            "text_hash": self.text_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbeddingResult':
        """Create from dictionary."""
        return cls(
            text=data["text"],
            embedding=np.array(data["embedding"]),
            model_name=data["model_name"],
            dimensions=data["dimensions"],
            created_at=datetime.fromisoformat(data["created_at"]),
            text_hash=data.get("text_hash", "")
        )


@dataclass
class SimilarityResult:
    """Result of similarity calculation."""

    source_text: str
    target_text: str
    similarity_score: float
    distance_metric: str
    model_name: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_text": self.source_text,
            "target_text": self.target_text,
            "similarity_score": self.similarity_score,
            "distance_metric": self.distance_metric,
            "model_name": self.model_name,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


class EmbeddingCalculator:
    """Calculates text embeddings using various models."""

    def __init__(self,
                 logger: Optional[ILoggerService] = None,
                 cache: Optional[Any] = None,
                 model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding calculator.

        Args:
            logger: Logger service for logging operations
            cache: Cache service for caching embeddings
            model_name: Name of the sentence transformer model to use
        """
        self._logger = logger or get_logger()
        self._cache = cache or get_cache_manager()
        self._model_name = model_name
        self._model = None
        self._dimensions = 0

    async def _load_model(self) -> None:
        """Load the sentence transformer model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._dimensions = self._model.get_sentence_embedding_dimension()

            await self._logger.info(
                f"Loaded semantic model: {self._model_name}",
                model_name=self._model_name,
                dimensions=self._dimensions
            )

        except ImportError:
            await self._logger.warning(
                "SentenceTransformers not available, using fallback",
                model_name=self._model_name
            )
            # Fallback implementation
            self._model = "fallback"
            self._dimensions = 384  # Standard embedding dimension

    async def calculate_embedding(self, text: str) -> EmbeddingResult:
        """Calculate embedding for text.

        Args:
            text: Text to calculate embedding for

        Returns:
            EmbeddingResult with the calculated embedding
        """
        # Check cache first
        cache_key = f"embedding:{self._model_name}:{hashlib.md5(text.encode()).hexdigest()}"
        cached_result = await self._cache.get(cache_key)

        if cached_result:
            await self._logger.debug(
                "Using cached embedding",
                text_length=len(text),
                model_name=self._model_name
            )
            return EmbeddingResult.from_dict(cached_result)

        # Load model if needed
        await self._load_model()

        async with profile_async_operation("calculate_embedding", model=self._model_name):
            if self._model == "fallback":
                # Simple fallback embedding
                embedding = self._calculate_fallback_embedding(text)
            else:
                # Real embedding calculation
                embedding = self._model.encode(text, convert_to_numpy=True)

            result = EmbeddingResult(
                text=text,
                embedding=embedding,
                model_name=self._model_name,
                dimensions=self._dimensions
            )

            # Cache the result
            await self._cache.set(cache_key, result.to_dict(), ttl=3600)  # 1 hour TTL

            await self._logger.debug(
                "Calculated embedding",
                text_length=len(text),
                model_name=self._model_name,
                dimensions=self._dimensions
            )

            return result

    def _calculate_fallback_embedding(self, text: str) -> np.ndarray:
        """Calculate fallback embedding using simple text features."""
        # Simple character-based embedding for fallback
        chars = list(text.lower())
        embedding = np.zeros(self._dimensions)

        for i, char in enumerate(chars[:self._dimensions]):
            embedding[i] = ord(char) / 255.0  # Normalize to 0-1

        # Add some text statistics
        embedding[self._dimensions - 3] = len(text) / 1000.0  # Text length
        embedding[self._dimensions - 2] = len(set(chars)) / 100.0  # Unique chars
        embedding[self._dimensions - 1] = sum(ord(c) for c in chars) / (255 * len(chars))  # Average char value

        return embedding.astype(np.float32)

    async def calculate_batch_embeddings(self, texts: List[str]) -> List[EmbeddingResult]:
        """Calculate embeddings for multiple texts.

        Args:
            texts: List of texts to calculate embeddings for

        Returns:
            List of EmbeddingResult objects
        """
        tasks = [self.calculate_embedding(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                await self._logger.error(
                    f"Failed to calculate embedding for text {i}",
                    error=str(result),
                    text_preview=texts[i][:100]
                )
            else:
                valid_results.append(result)

        return valid_results


class SimilarityCalculator:
    """Calculates similarity between embeddings."""

    def __init__(self,
                 logger: Optional[ILoggerService] = None,
                 cache: Optional[Any] = None):
        """Initialize similarity calculator.

        Args:
            logger: Logger service for logging operations
            cache: Cache service for caching similarity results
        """
        self._logger = logger or get_logger()
        self._cache = cache or get_cache_manager()

    async def calculate_similarity(self,
                                  embedding1: np.ndarray,
                                  embedding2: np.ndarray,
                                  metric: str = "cosine") -> float:
        """Calculate similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            metric: Similarity metric ('cosine', 'euclidean', 'dot_product')

        Returns:
            Similarity score between 0 and 1
        """
        if embedding1.shape != embedding2.shape:
            raise ValueError(f"Embedding shapes don't match: {embedding1.shape} vs {embedding2.shape}")

        async with profile_async_operation("calculate_similarity", metric=metric):
            if metric == "cosine":
                similarity = self._cosine_similarity(embedding1, embedding2)
            elif metric == "euclidean":
                similarity = self._euclidean_similarity(embedding1, embedding2)
            elif metric == "dot_product":
                similarity = self._dot_product_similarity(embedding1, embedding2)
            else:
                raise ValueError(f"Unknown similarity metric: {metric}")

            # Normalize to 0-1 range
            if metric == "euclidean":
                # Convert distance to similarity (closer = more similar)
                similarity = max(0.0, 1.0 - similarity)
            elif metric == "dot_product":
                # Normalize dot product to 0-1 range
                similarity = (similarity + 1.0) / 2.0

            return float(similarity)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _euclidean_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate Euclidean distance (returns distance, not similarity)."""
        return np.linalg.norm(vec1 - vec2)

    def _dot_product_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate dot product similarity."""
        return np.dot(vec1, vec2)

    async def calculate_pairwise_similarities(self,
                                             embeddings: List[np.ndarray],
                                             metric: str = "cosine") -> np.ndarray:
        """Calculate pairwise similarities between all embeddings.

        Args:
            embeddings: List of embedding vectors
            metric: Similarity metric to use

        Returns:
            Symmetric matrix of similarity scores
        """
        n = len(embeddings)
        similarity_matrix = np.zeros((n, n))

        async with profile_async_operation("calculate_pairwise_similarities",
                                         num_embeddings=n, metric=metric):
            # Calculate similarities for upper triangle
            for i in range(n):
                for j in range(i + 1, n):
                    similarity = await self.calculate_similarity(
                        embeddings[i], embeddings[j], metric
                    )
                    similarity_matrix[i, j] = similarity
                    similarity_matrix[j, i] = similarity  # Symmetric

                # Self-similarity is always 1.0
                similarity_matrix[i, i] = 1.0

        return similarity_matrix

    async def find_similar_pairs(self,
                                embeddings: List[np.ndarray],
                                texts: List[str],
                                threshold: float = 0.8,
                                metric: str = "cosine",
                                top_k: Optional[int] = None) -> List[SimilarityResult]:
        """Find similar pairs of texts based on embeddings.

        Args:
            embeddings: List of embedding vectors
            texts: Corresponding list of text strings
            threshold: Similarity threshold for considering pairs similar
            metric: Similarity metric to use
            top_k: Return only top K most similar pairs per text

        Returns:
            List of SimilarityResult objects for similar pairs
        """
        if len(embeddings) != len(texts):
            raise ValueError("Embeddings and texts lists must have the same length")

        async with profile_async_operation("find_similar_pairs",
                                         num_texts=len(texts), threshold=threshold):
            similarity_matrix = await self.calculate_pairwise_similarities(embeddings, metric)

            similar_pairs = []
            n = len(texts)

            for i in range(n):
                similarities = []
                for j in range(n):
                    if i != j:
                        similarity_score = similarity_matrix[i, j]
                        if similarity_score >= threshold:
                            similarities.append((j, similarity_score))

                # Sort by similarity score (descending)
                similarities.sort(key=lambda x: x[1], reverse=True)

                # Take top K if specified
                if top_k:
                    similarities = similarities[:top_k]

                # Create SimilarityResult objects
                for j, similarity_score in similarities:
                    result = SimilarityResult(
                        source_text=texts[i],
                        target_text=texts[j],
                        similarity_score=similarity_score,
                        distance_metric=metric,
                        model_name="unknown",  # Will be set by caller
                        confidence=min(1.0, similarity_score + 0.1),  # Simple confidence calculation
                        metadata={
                            "source_index": i,
                            "target_index": j,
                            "rank": len(similar_pairs) + 1
                        }
                    )
                    similar_pairs.append(result)

            await self._logger.info(
                f"Found {len(similar_pairs)} similar pairs",
                num_texts=n,
                threshold=threshold,
                metric=metric,
                top_k=top_k
            )

            return similar_pairs


class SemanticAnalyzer:
    """Main semantic analysis service combining embedding and similarity calculations."""

    def __init__(self,
                 embedding_calculator: Optional[EmbeddingCalculator] = None,
                 similarity_calculator: Optional[SimilarityCalculator] = None,
                 logger: Optional[ILoggerService] = None):
        """Initialize semantic analyzer.

        Args:
            embedding_calculator: Embedding calculator instance
            similarity_calculator: Similarity calculator instance
            logger: Logger service for logging operations
        """
        self._embedding_calculator = embedding_calculator or EmbeddingCalculator()
        self._similarity_calculator = similarity_calculator or SimilarityCalculator()
        self._logger = logger or get_logger()

    async def analyze_semantic_similarity(self,
                                        texts: List[str],
                                        threshold: float = 0.8,
                                        metric: str = "cosine",
                                        top_k: Optional[int] = None) -> Dict[str, Any]:
        """Perform complete semantic similarity analysis.

        Args:
            texts: List of texts to analyze
            threshold: Similarity threshold for finding similar pairs
            metric: Similarity metric to use
            top_k: Return only top K most similar pairs per text

        Returns:
            Dictionary containing analysis results
        """
        async with profile_async_operation("analyze_semantic_similarity",
                                         num_texts=len(texts), threshold=threshold):
            start_time = datetime.now(timezone.utc)

            try:
                # Calculate embeddings
                await self._logger.info("Starting semantic similarity analysis", num_texts=len(texts))
                embedding_results = await self._embedding_calculator.calculate_batch_embeddings(texts)

                if not embedding_results:
                    return {
                        "error": "Failed to calculate embeddings for any texts",
                        "analysis_id": f"error-{start_time.timestamp()}",
                        "execution_time_seconds": 0.0
                    }

                # Extract embeddings and model info
                embeddings = [result.embedding for result in embedding_results]
                model_name = embedding_results[0].model_name if embedding_results else "unknown"

                # Find similar pairs
                similar_pairs = await self._similarity_calculator.find_similar_pairs(
                    embeddings, texts, threshold, metric, top_k
                )

                # Update model name in results
                for pair in similar_pairs:
                    pair.model_name = model_name

                # Calculate pairwise similarities for matrix
                similarity_matrix = await self._similarity_calculator.calculate_pairwise_similarities(
                    embeddings, metric
                )

                # Prepare summary statistics
                execution_time = datetime.now(timezone.utc) - start_time
                summary = {
                    "total_texts": len(texts),
                    "total_pairs_analyzed": len(texts) * (len(texts) - 1) // 2,
                    "similar_pairs_found": len(similar_pairs),
                    "similarity_threshold": threshold,
                    "metric_used": metric,
                    "model_used": model_name,
                    "average_similarity": float(np.mean(similarity_matrix)) if len(similarity_matrix) > 0 else 0.0,
                    "max_similarity": float(np.max(similarity_matrix)) if len(similarity_matrix) > 0 else 0.0,
                    "min_similarity": float(np.min(similarity_matrix)) if len(similarity_matrix) > 0 else 0.0
                }

                result = {
                    "analysis_id": f"semantic-{start_time.timestamp()}",
                    "status": "completed",
                    "texts": texts,
                    "embeddings": [result.to_dict() for result in embedding_results],
                    "similarity_matrix": similarity_matrix.tolist(),
                    "similar_pairs": [pair.to_dict() for pair in similar_pairs],
                    "summary": summary,
                    "execution_time_seconds": execution_time.total_seconds(),
                    "created_at": start_time.isoformat()
                }

                await self._logger.info(
                    "Completed semantic similarity analysis",
                    analysis_id=result["analysis_id"],
                    execution_time_seconds=result["execution_time_seconds"],
                    similar_pairs_found=len(similar_pairs)
                )

                return result

            except Exception as e:
                execution_time = datetime.now(timezone.utc) - start_time
                error_msg = f"Semantic similarity analysis failed: {str(e)}"

                await self._logger.error(
                    error_msg,
                    error=str(e),
                    num_texts=len(texts),
                    execution_time_seconds=execution_time.total_seconds()
                )

                return {
                    "error": error_msg,
                    "analysis_id": f"error-{start_time.timestamp()}",
                    "execution_time_seconds": execution_time.total_seconds(),
                    "status": "failed"
                }

    async def find_most_similar(self,
                               target_text: str,
                               candidate_texts: List[str],
                               top_k: int = 5,
                               metric: str = "cosine") -> Dict[str, Any]:
        """Find most similar texts to a target text.

        Args:
            target_text: The target text to find similarities for
            candidate_texts: List of candidate texts to compare against
            top_k: Number of most similar texts to return
            metric: Similarity metric to use

        Returns:
            Dictionary containing similarity results
        """
        async with profile_async_operation("find_most_similar",
                                         target_length=len(target_text),
                                         num_candidates=len(candidate_texts)):
            all_texts = [target_text] + candidate_texts
            analysis_result = await self.analyze_semantic_similarity(
                all_texts, threshold=0.0, metric=metric, top_k=top_k
            )

            if "error" in analysis_result:
                return analysis_result

            # Extract similarities for the target text (first in the list)
            target_similarities = []
            similar_pairs = analysis_result.get("similar_pairs", [])

            for pair in similar_pairs:
                if pair["source_text"] == target_text:
                    target_similarities.append({
                        "candidate_text": pair["target_text"],
                        "similarity_score": pair["similarity_score"],
                        "confidence": pair["confidence"],
                        "metric": pair["distance_metric"]
                    })

            # Sort by similarity score and take top K
            target_similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
            target_similarities = target_similarities[:top_k]

            result = {
                "target_text": target_text,
                "most_similar": target_similarities,
                "analysis_id": analysis_result["analysis_id"],
                "execution_time_seconds": analysis_result["execution_time_seconds"],
                "model_used": analysis_result["summary"]["model_used"]
            }

            await self._logger.info(
                f"Found {len(target_similarities)} most similar texts",
                target_length=len(target_text),
                num_candidates=len(candidate_texts),
                top_k=top_k
            )

            return result


# Global semantic analyzer instance
_semantic_analyzer: Optional[SemanticAnalyzer] = None


def get_semantic_analyzer() -> SemanticAnalyzer:
    """Get global semantic analyzer instance."""
    global _semantic_analyzer
    if _semantic_analyzer is None:
        _semantic_analyzer = SemanticAnalyzer()
    return _semantic_analyzer


# Convenience functions
async def analyze_semantic_similarity(texts: List[str], **kwargs) -> Dict[str, Any]:
    """Convenience function for semantic similarity analysis."""
    return await get_semantic_analyzer().analyze_semantic_similarity(texts, **kwargs)


async def find_most_similar(target_text: str, candidate_texts: List[str], **kwargs) -> Dict[str, Any]:
    """Convenience function to find most similar texts."""
    return await get_semantic_analyzer().find_most_similar(target_text, candidate_texts, **kwargs)