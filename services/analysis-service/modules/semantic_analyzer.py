"""Semantic similarity analysis module for Analysis Service.

Provides semantic similarity detection using sentence transformers and vector embeddings
to identify conceptually similar but differently worded content across documents.
"""
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import cos_sim
    import faiss
    SEMANTIC_ANALYSIS_AVAILABLE = True
except ImportError:
    SEMANTIC_ANALYSIS_AVAILABLE = False
    SentenceTransformer = None
    cos_sim = None
    faiss = None

from services.shared.models import Document
from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class SemanticSimilarityAnalyzer:
    """Analyzes semantic similarity between documents using embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the semantic similarity analyzer.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.embeddings = None
        self.document_ids = []
        self.initialized = False

    def _initialize_model(self) -> bool:
        """Initialize the sentence transformer model and FAISS index."""
        if not SEMANTIC_ANALYSIS_AVAILABLE:
            logger.warning("Semantic analysis dependencies not available")
            return False

        try:
            if self.model is None:
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)

            # Initialize FAISS index for efficient similarity search
            if self.index is None:
                # Use IndexFlatIP for inner product (cosine similarity)
                embedding_dim = self.model.get_sentence_embedding_dimension()
                self.index = faiss.IndexFlatIP(embedding_dim)

            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize semantic analyzer: {e}")
            return False

    def _extract_text_for_analysis(self, document: Document, scope: str) -> str:
        """Extract text content based on analysis scope.

        Args:
            document: Document to extract text from
            scope: Analysis scope ('content', 'titles', 'metadata', 'combined')

        Returns:
            Extracted text for analysis
        """
        text_parts = []

        if scope in ['content', 'combined']:
            if hasattr(document, 'content') and document.content:
                text_parts.append(document.content)

        if scope in ['titles', 'combined']:
            if hasattr(document, 'title') and document.title:
                text_parts.append(document.title)
            if hasattr(document, 'metadata') and document.metadata:
                if 'title' in document.metadata:
                    text_parts.append(document.metadata['title'])

        if scope in ['metadata', 'combined']:
            if hasattr(document, 'metadata') and document.metadata:
                # Extract relevant metadata fields
                metadata_text = []
                for key, value in document.metadata.items():
                    if isinstance(value, str) and len(value.strip()) > 0:
                        metadata_text.append(f"{key}: {value}")
                if metadata_text:
                    text_parts.append(" ".join(metadata_text))

        return " ".join(text_parts).strip()

    def _chunk_text(self, text: str, chunk_size: int = 512) -> List[str]:
        """Split text into manageable chunks for embedding.

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size in characters

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = []

        for word in words:
            if len(" ".join(current_chunk + [word])) <= chunk_size:
                current_chunk.append(word)
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _calculate_similarities(self, embeddings: np.ndarray, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Calculate semantic similarities between all document pairs.

        Args:
            embeddings: Document embeddings matrix
            threshold: Similarity threshold for filtering results

        Returns:
            List of similarity pairs above threshold
        """
        if len(embeddings) < 2:
            return []

        # Calculate cosine similarities
        similarities = cos_sim(embeddings, embeddings)

        similarity_pairs = []
        n_docs = len(self.document_ids)

        for i in range(n_docs):
            for j in range(i + 1, n_docs):
                similarity_score = float(similarities[i][j])

                if similarity_score >= threshold:
                    # Calculate confidence based on similarity score
                    confidence = min(1.0, similarity_score * 1.2)  # Boost confidence for high similarities

                    pair = {
                        'document_id_1': self.document_ids[i],
                        'document_id_2': self.document_ids[j],
                        'similarity_score': similarity_score,
                        'confidence': confidence,
                        'similar_sections': ['content'],  # Could be enhanced to detect specific sections
                        'rationale': f"Semantic similarity score: {similarity_score:.3f}"
                    }
                    similarity_pairs.append(pair)

        # Sort by similarity score (highest first)
        similarity_pairs.sort(key=lambda x: x['similarity_score'], reverse=True)

        return similarity_pairs

    async def analyze_similarity(
        self,
        documents: List[Document],
        similarity_threshold: float = 0.8,
        analysis_scope: str = "content"
    ) -> Dict[str, Any]:
        """Analyze semantic similarity between documents.

        Args:
            documents: List of documents to analyze
            similarity_threshold: Minimum similarity score to include in results
            analysis_scope: What parts of documents to analyze ('content', 'titles', 'metadata', 'combined')

        Returns:
            Analysis results with similarity pairs and summary
        """
        start_time = time.time()

        if not self._initialize_model():
            return {
                'error': 'Semantic analysis not available',
                'message': 'Required dependencies not installed or model initialization failed'
            }

        if len(documents) < 2:
            return {
                'total_documents': len(documents),
                'similarity_pairs': [],
                'analysis_summary': {
                    'high_similarity_pairs': 0,
                    'medium_similarity_pairs': 0,
                    'low_similarity_pairs': 0,
                    'average_similarity': 0.0
                },
                'processing_time': time.time() - start_time,
                'model_used': self.model_name,
                'message': 'At least 2 documents required for similarity analysis'
            }

        try:
            # Extract text for analysis
            texts = []
            self.document_ids = []

            for doc in documents:
                text = self._extract_text_for_analysis(doc, analysis_scope)
                if text.strip():  # Only include documents with content
                    texts.append(text)
                    self.document_ids.append(doc.id if hasattr(doc, 'id') else str(id(doc)))

            if len(texts) < 2:
                return {
                    'total_documents': len(documents),
                    'similarity_pairs': [],
                    'analysis_summary': {
                        'high_similarity_pairs': 0,
                        'medium_similarity_pairs': 0,
                        'low_similarity_pairs': 0,
                        'average_similarity': 0.0
                    },
                    'processing_time': time.time() - start_time,
                    'model_used': self.model_name,
                    'message': 'Insufficient content for similarity analysis'
                }

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} documents")
            embeddings = self.model.encode(texts, convert_to_tensor=True, show_progress_bar=False)
            embeddings = embeddings.cpu().numpy()

            # Calculate similarities
            similarity_pairs = self._calculate_similarities(embeddings, similarity_threshold)

            # Generate analysis summary
            analysis_summary = self._generate_analysis_summary(similarity_pairs)

            processing_time = time.time() - start_time

            return {
                'total_documents': len(documents),
                'similarity_pairs': similarity_pairs,
                'analysis_summary': analysis_summary,
                'processing_time': processing_time,
                'model_used': self.model_name
            }

        except Exception as e:
            logger.error(f"Semantic similarity analysis failed: {e}")
            return {
                'error': 'Analysis failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }

    def _generate_analysis_summary(self, similarity_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for similarity analysis.

        Args:
            similarity_pairs: List of similarity pairs

        Returns:
            Summary statistics
        """
        if not similarity_pairs:
            return {
                'high_similarity_pairs': 0,
                'medium_similarity_pairs': 0,
                'low_similarity_pairs': 0,
                'average_similarity': 0.0,
                'max_similarity': 0.0,
                'total_pairs': 0
            }

        scores = [pair['similarity_score'] for pair in similarity_pairs]

        # Categorize by similarity level
        high_similarity = len([s for s in scores if s >= 0.9])
        medium_similarity = len([s for s in scores if 0.7 <= s < 0.9])
        low_similarity = len([s for s in scores if s < 0.7])

        return {
            'high_similarity_pairs': high_similarity,
            'medium_similarity_pairs': medium_similarity,
            'low_similarity_pairs': low_similarity,
            'average_similarity': float(np.mean(scores)),
            'max_similarity': float(max(scores)),
            'total_pairs': len(similarity_pairs)
        }


# Global instance for reuse
semantic_analyzer = SemanticSimilarityAnalyzer()


async def analyze_semantic_similarity(
    documents: List[Document],
    similarity_threshold: float = 0.8,
    analysis_scope: str = "content"
) -> Dict[str, Any]:
    """Convenience function for semantic similarity analysis.

    Args:
        documents: List of documents to analyze
        similarity_threshold: Minimum similarity score
        analysis_scope: What parts of documents to analyze

    Returns:
        Analysis results
    """
    return await semantic_analyzer.analyze_similarity(
        documents=documents,
        similarity_threshold=similarity_threshold,
        analysis_scope=analysis_scope
    )
