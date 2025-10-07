"""Local embedding generation using sentence-transformers."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np


# Try importing sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None


@dataclass
class EmbeddingModel:
    """Metadata about an embedding model."""
    name: str
    dimensions: int
    max_sequence_length: int
    model_size_mb: float
    language: str = "en"


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    text: str
    embedding: List[float]
    model_name: str
    generation_time_ms: float
    timestamp: datetime


class LocalEmbeddingGenerator:
    """
    Local embedding generator using sentence-transformers.
    
    Provides:
    - Fast local embedding generation
    - No external API calls
    - GPU/CPU support
    - Batch processing
    - Model caching
    """
    
    # Class-level model cache
    _model_cache: Dict[str, Any] = {}
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        cache_folder: Optional[str] = None
    ):
        """
        Initialize local embedding generator.
        
        Args:
            model_name: HuggingFace model name
            device: Device to use ("cuda", "cpu", "mps", or None for auto)
            cache_folder: Optional cache folder for models
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.device = device
        self.cache_folder = cache_folder
        
        # Load model (with caching)
        self.model = self._load_model()
        
        # Get model info
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        self.max_seq_length = self.model.max_seq_length
    
    def _load_model(self) -> SentenceTransformer:
        """
        Load model with caching.
        
        Returns:
            SentenceTransformer model
        """
        # Check cache
        if self.model_name in self._model_cache:
            return self._model_cache[self.model_name]
        
        # Load model
        model = SentenceTransformer(
            self.model_name,
            device=self.device,
            cache_folder=self.cache_folder
        )
        
        # Cache it
        self._model_cache[self.model_name] = model
        
        return model
    
    def generate_embedding(
        self,
        text: str,
        normalize: bool = True
    ) -> EmbeddingResult:
        """
        Generate embedding for single text.
        
        Args:
            text: Input text
            normalize: Whether to L2-normalize the embedding
        
        Returns:
            EmbeddingResult with embedding vector
        """
        start_time = datetime.now()
        
        # Generate embedding
        embedding = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        
        # Convert to list
        embedding_list = embedding.tolist()
        
        # Calculate time
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return EmbeddingResult(
            text=text,
            embedding=embedding_list,
            model_name=self.model_name,
            generation_time_ms=duration_ms,
            timestamp=datetime.now()
        )
    
    def batch_generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            normalize: Whether to L2-normalize embeddings
            show_progress: Show progress bar
        
        Returns:
            List of EmbeddingResults
        """
        start_time = datetime.now()
        
        # Generate embeddings in batches
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress
        )
        
        # Calculate average time per text
        total_duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        avg_duration_ms = total_duration_ms / len(texts) if texts else 0
        
        # Create results
        results = []
        for text, embedding in zip(texts, embeddings):
            results.append(EmbeddingResult(
                text=text,
                embedding=embedding.tolist(),
                model_name=self.model_name,
                generation_time_ms=avg_duration_ms,
                timestamp=datetime.now()
            ))
        
        return results
    
    @staticmethod
    def cosine_similarity(
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Cosine similarity (0-1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Normalize
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)
        
        # Dot product
        similarity = np.dot(vec1_norm, vec2_norm)
        
        return float(similarity)
    
    @staticmethod
    def euclidean_distance(
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate Euclidean distance between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Euclidean distance
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        return float(np.linalg.norm(vec1 - vec2))
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[tuple[int, float]]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
        
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        similarities = []
        
        for idx, candidate in enumerate(candidate_embeddings):
            similarity = self.cosine_similarity(query_embedding, candidate)
            similarities.append((idx, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def semantic_search(
        self,
        query: str,
        corpus: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on a corpus.
        
        Args:
            query: Search query
            corpus: List of documents to search
            top_k: Number of top results
        
        Returns:
            List of search results with scores
        """
        # Generate embeddings
        query_result = self.generate_embedding(query)
        corpus_results = self.batch_generate_embeddings(corpus)
        
        # Extract embeddings
        corpus_embeddings = [r.embedding for r in corpus_results]
        
        # Find most similar
        top_indices = self.find_most_similar(
            query_result.embedding,
            corpus_embeddings,
            top_k
        )
        
        # Build results
        results = []
        for idx, score in top_indices:
            results.append({
                "text": corpus[idx],
                "score": score,
                "index": idx
            })
        
        return results
    
    def cluster_embeddings(
        self,
        embeddings: List[List[float]],
        num_clusters: int = 5,
        method: str = "kmeans"
    ) -> List[int]:
        """
        Cluster embeddings into groups.
        
        Args:
            embeddings: List of embeddings
            num_clusters: Number of clusters
            method: Clustering method ("kmeans")
        
        Returns:
            List of cluster labels
        """
        from sklearn.cluster import KMeans
        
        X = np.array(embeddings)
        
        if method == "kmeans":
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            labels = kmeans.fit_predict(X)
            return labels.tolist()
        else:
            raise ValueError(f"Unsupported clustering method: {method}")
    
    def get_model_info(self) -> EmbeddingModel:
        """
        Get information about the loaded model.
        
        Returns:
            EmbeddingModel with metadata
        """
        # Estimate model size (rough approximation)
        param_count = sum(
            p.numel() for p in self.model.parameters()
        )
        model_size_mb = (param_count * 4) / (1024 * 1024)  # Assuming float32
        
        return EmbeddingModel(
            name=self.model_name,
            dimensions=self.embedding_dimension,
            max_sequence_length=self.max_seq_length,
            model_size_mb=model_size_mb,
            language="en"  # Default, could be detected
        )
    
    @classmethod
    def list_available_models(cls) -> List[str]:
        """
        List commonly available models.
        
        Returns:
            List of model names
        """
        return [
            "sentence-transformers/all-MiniLM-L6-v2",  # Fast, 384 dims
            "sentence-transformers/all-mpnet-base-v2",  # Better quality, 768 dims
            "sentence-transformers/multi-qa-mpnet-base-dot-v1",  # For Q&A
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # Multilingual
            "BAAI/bge-small-en-v1.5",  # High quality, small
            "BAAI/bge-base-en-v1.5",  # High quality, base
            "BAAI/bge-large-en-v1.5",  # High quality, large
        ]
    
    @classmethod
    def clear_cache(cls):
        """Clear the model cache."""
        cls._model_cache.clear()


# Convenience function
def generate_embeddings_fast(
    texts: List[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> List[List[float]]:
    """
    Quick function to generate embeddings.
    
    Args:
        texts: List of texts
        model_name: Model to use
    
    Returns:
        List of embedding vectors
    """
    generator = LocalEmbeddingGenerator(model_name=model_name)
    results = generator.batch_generate_embeddings(texts)
    return [r.embedding for r in results]

