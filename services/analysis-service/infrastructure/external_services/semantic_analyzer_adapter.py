"""Semantic analyzer adapter for external semantic analysis services."""

import asyncio
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import time

from ...domain.exceptions import SemanticAnalysisException
from ..config import ExternalServiceConfig


class SemanticAnalysisResult:
    """Result of semantic analysis."""

    def __init__(self,
                 document_id: str,
                 embeddings: Optional[List[float]] = None,
                 similar_documents: Optional[List[Dict[str, Any]]] = None,
                 clusters: Optional[List[Dict[str, Any]]] = None,
                 keywords: Optional[List[str]] = None,
                 confidence: float = 0.0,
                 processing_time: float = 0.0):
        """Initialize semantic analysis result."""
        self.document_id = document_id
        self.embeddings = embeddings
        self.similar_documents = similar_documents or []
        self.clusters = clusters or []
        self.keywords = keywords or []
        self.confidence = confidence
        self.processing_time = processing_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'document_id': self.document_id,
            'embeddings': self.embeddings,
            'similar_documents': self.similar_documents,
            'clusters': self.clusters,
            'keywords': self.keywords,
            'confidence': self.confidence,
            'processing_time': self.processing_time
        }


class SemanticAnalyzerAdapter(ABC):
    """Abstract adapter for semantic analysis services."""

    def __init__(self, config: ExternalServiceConfig):
        """Initialize adapter with configuration."""
        self.config = config
        self._retry_config = config.get_retry_config()

    @abstractmethod
    async def analyze_semantic_similarity(self,
                                        document_text: str,
                                        document_id: str,
                                        compare_texts: Optional[List[str]] = None) -> SemanticAnalysisResult:
        """Analyze semantic similarity of document."""
        pass

    @abstractmethod
    async def extract_keywords(self, document_text: str, document_id: str) -> List[str]:
        """Extract keywords from document."""
        pass

    @abstractmethod
    async def cluster_documents(self,
                               documents: List[Dict[str, Any]],
                               num_clusters: int = 5) -> List[Dict[str, Any]]:
        """Cluster documents by semantic similarity."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available."""
        pass


class LocalSemanticAnalyzerAdapter(SemanticAnalyzerAdapter):
    """Local implementation using basic text processing."""

    def __init__(self, config: ExternalServiceConfig):
        """Initialize local semantic analyzer."""
        super().__init__(config)
        self.similarity_threshold = config.get_semantic_config().get('similarity_threshold', 0.8)

    async def analyze_semantic_similarity(self,
                                        document_text: str,
                                        document_id: str,
                                        compare_texts: Optional[List[str]] = None) -> SemanticAnalysisResult:
        """Analyze semantic similarity using basic text processing."""
        start_time = time.time()

        try:
            # Simple keyword-based similarity (placeholder for real implementation)
            keywords = self._extract_basic_keywords(document_text)
            embeddings = self._generate_basic_embeddings(document_text)

            similar_documents = []
            if compare_texts:
                for i, compare_text in enumerate(compare_texts):
                    similarity = self._calculate_basic_similarity(document_text, compare_text)
                    if similarity >= self.similarity_threshold:
                        similar_documents.append({
                            'document_id': f'compare_{i}',
                            'similarity_score': similarity,
                            'shared_keywords': self._find_shared_keywords(keywords, compare_text)
                        })

            processing_time = time.time() - start_time

            return SemanticAnalysisResult(
                document_id=document_id,
                embeddings=embeddings,
                similar_documents=similar_documents,
                keywords=keywords,
                confidence=0.7,  # Basic confidence for local implementation
                processing_time=processing_time
            )

        except Exception as e:
            raise SemanticAnalysisException("LocalSemanticAnalyzer", str(e))

    async def extract_keywords(self, document_text: str, document_id: str) -> List[str]:
        """Extract keywords using basic text processing."""
        return self._extract_basic_keywords(document_text)

    async def cluster_documents(self,
                               documents: List[Dict[str, Any]],
                               num_clusters: int = 5) -> List[Dict[str, Any]]:
        """Cluster documents using basic text processing."""
        # Simple clustering based on keyword overlap
        clusters = []
        processed_docs = []

        for doc in documents:
            doc_text = doc.get('content', '')
            doc_keywords = self._extract_basic_keywords(doc_text)
            processed_docs.append({
                'id': doc.get('id'),
                'keywords': doc_keywords,
                'text': doc_text
            })

        # Group by dominant keywords (simplified)
        keyword_groups = {}
        for doc in processed_docs:
            # Use first keyword as cluster key (simplified)
            if doc['keywords']:
                key = doc['keywords'][0]
                if key not in keyword_groups:
                    keyword_groups[key] = []
                keyword_groups[key].append(doc)

        # Convert to cluster format
        for keyword, docs in keyword_groups.items():
            clusters.append({
                'cluster_id': f'cluster_{keyword}',
                'keyword': keyword,
                'documents': [doc['id'] for doc in docs],
                'size': len(docs)
            })

        return clusters[:num_clusters]

    def is_available(self) -> bool:
        """Check if local analyzer is available."""
        return True

    def _extract_basic_keywords(self, text: str) -> List[str]:
        """Extract basic keywords from text."""
        # Simple keyword extraction (placeholder for real implementation)
        words = text.lower().split()
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        # Return unique keywords, limited to top 10
        return list(set(keywords))[:10]

    def _generate_basic_embeddings(self, text: str) -> List[float]:
        """Generate basic embeddings from text."""
        # Simple embedding generation (placeholder for real implementation)
        # This creates a basic vector based on word frequencies
        words = text.lower().split()
        embedding = []
        for i in range(10):  # 10-dimensional embedding
            # Simple hash-based embedding
            embedding.append(sum(ord(c) for c in words[i % len(words)] if i < len(words)) / 100.0)
        return embedding

    def _calculate_basic_similarity(self, text1: str, text2: str) -> float:
        """Calculate basic text similarity."""
        # Simple Jaccard similarity based on word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _find_shared_keywords(self, keywords: List[str], compare_text: str) -> List[str]:
        """Find shared keywords between document and comparison text."""
        compare_words = set(compare_text.lower().split())
        return [kw for kw in keywords if kw in compare_words]


class OpenAISemanticAnalyzerAdapter(SemanticAnalyzerAdapter):
    """OpenAI-based semantic analyzer adapter."""

    def __init__(self, config: ExternalServiceConfig):
        """Initialize OpenAI semantic analyzer."""
        super().__init__(config)
        self.api_key = config.openai_api_key
        self.model = config.openai_model
        self.max_tokens = config.openai_max_tokens

    async def analyze_semantic_similarity(self,
                                        document_text: str,
                                        document_id: str,
                                        compare_texts: Optional[List[str]] = None) -> SemanticAnalysisResult:
        """Analyze semantic similarity using OpenAI."""
        if not self.api_key:
            raise SemanticAnalysisException("OpenAI", "API key not configured")

        start_time = time.time()

        try:
            # Placeholder for OpenAI API call
            # In a real implementation, this would call OpenAI's embeddings API
            embeddings = self._generate_mock_embeddings(document_text)
            keywords = self._extract_openai_keywords(document_text)

            similar_documents = []
            if compare_texts:
                # Compare with other texts using embeddings
                for i, compare_text in enumerate(compare_texts):
                    similarity = self._calculate_embedding_similarity(embeddings, compare_text)
                    if similarity >= 0.8:  # High similarity threshold
                        similar_documents.append({
                            'document_id': f'compare_{i}',
                            'similarity_score': similarity,
                            'embedding_distance': 1.0 - similarity
                        })

            processing_time = time.time() - start_time

            return SemanticAnalysisResult(
                document_id=document_id,
                embeddings=embeddings,
                similar_documents=similar_documents,
                keywords=keywords,
                confidence=0.9,  # Higher confidence for OpenAI
                processing_time=processing_time
            )

        except Exception as e:
            raise SemanticAnalysisException("OpenAI", str(e))

    async def extract_keywords(self, document_text: str, document_id: str) -> List[str]:
        """Extract keywords using OpenAI."""
        if not self.api_key:
            raise SemanticAnalysisException("OpenAI", "API key not configured")

        # Placeholder for OpenAI API call
        return self._extract_openai_keywords(document_text)

    async def cluster_documents(self,
                               documents: List[Dict[str, Any]],
                               num_clusters: int = 5) -> List[Dict[str, Any]]:
        """Cluster documents using OpenAI embeddings."""
        if not self.api_key:
            raise SemanticAnalysisException("OpenAI", "API key not configured")

        # Placeholder for OpenAI clustering
        return [{
            'cluster_id': f'openai_cluster_{i}',
            'centroid': f'centroid_{i}',
            'documents': [doc.get('id') for doc in documents[i::num_clusters]],
            'size': len(documents[i::num_clusters])
        } for i in range(min(num_clusters, len(documents)))]

    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.api_key is not None

    def _generate_mock_embeddings(self, text: str) -> List[float]:
        """Generate mock embeddings (placeholder for OpenAI API)."""
        # This would be replaced with actual OpenAI API call
        return [0.1 * i for i in range(1536)]  # OpenAI ada-002 embedding size

    def _extract_openai_keywords(self, text: str) -> List[str]:
        """Extract keywords using OpenAI (placeholder)."""
        # This would be replaced with actual OpenAI API call
        words = text.lower().split()
        return list(set(words))[:15]  # Return more keywords for OpenAI

    def _calculate_embedding_similarity(self, embeddings: List[float], compare_text: str) -> float:
        """Calculate embedding similarity (placeholder)."""
        # This would use cosine similarity on actual embeddings
        return 0.85  # Mock high similarity
