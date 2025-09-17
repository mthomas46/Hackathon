"""Automated document categorization module for Summarizer Hub.

Provides ML-based document classification and automated tagging capabilities
using transformer models and traditional ML approaches.
"""
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import Counter

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    import numpy as np
    CATEGORIZATION_AVAILABLE = True
except ImportError:
    CATEGORIZATION_AVAILABLE = False
    pipeline = None
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    TfidfVectorizer = None
    MultinomialNB = None
    Pipeline = None
    np = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class DocumentCategorizer:
    """Automated document categorization using ML models."""

    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        """Initialize the document categorizer.

        Args:
            model_name: Name of the transformer model to use for zero-shot classification
        """
        self.model_name = model_name
        self.zero_shot_classifier = None
        self.traditional_model = None
        self.categories = []
        self.initialized = False

    def _initialize_models(self) -> bool:
        """Initialize the categorization models."""
        if not CATEGORIZATION_AVAILABLE:
            logger.warning("Categorization dependencies not available")
            return False

        try:
            # Initialize zero-shot classification pipeline
            if self.zero_shot_classifier is None:
                logger.info(f"Loading zero-shot classification model: {self.model_name}")
                self.zero_shot_classifier = pipeline(
                    "zero-shot-classification",
                    model=self.model_name,
                    device=-1  # Use CPU
                )

            # Initialize traditional ML model for backup
            if self.traditional_model is None:
                self.traditional_model = self._create_traditional_model()

            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize categorization models: {e}")
            return False

    def _create_traditional_model(self):
        """Create a traditional ML model for categorization."""
        # Create a simple pipeline with TF-IDF and Naive Bayes
        return Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
            ('clf', MultinomialNB())
        ])

    def _get_document_text(self, document: Dict[str, Any]) -> str:
        """Extract text content from document for categorization."""
        text_parts = []

        # Extract title
        if 'title' in document and document['title']:
            text_parts.append(document['title'])

        # Extract content
        if 'content' in document and document['content']:
            text_parts.append(document['content'])

        # Extract metadata descriptions
        if 'metadata' in document and document['metadata']:
            metadata = document['metadata']
            if 'description' in metadata and metadata['description']:
                text_parts.append(metadata['description'])
            if 'summary' in metadata and metadata['summary']:
                text_parts.append(metadata['summary'])

        return ' '.join(text_parts).strip()

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text using simple frequency analysis."""
        # Simple keyword extraction using word frequency
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]

        # Get most common words
        word_counts = Counter(filtered_words)
        keywords = [word for word, _ in word_counts.most_common(max_keywords)]

        return keywords

    def _categorize_with_zero_shot(self, text: str, candidate_categories: List[str]) -> Dict[str, Any]:
        """Categorize document using zero-shot classification."""
        try:
            result = self.zero_shot_classifier(
                text,
                candidate_labels=candidate_categories,
                multi_label=True
            )

            # Get the top category and confidence
            if result['labels'] and result['scores']:
                top_category = result['labels'][0]
                confidence = float(result['scores'][0])

                return {
                    'category': top_category,
                    'confidence': confidence,
                    'all_scores': dict(zip(result['labels'], result['scores']))
                }
            else:
                return {
                    'category': 'uncategorized',
                    'confidence': 0.0,
                    'all_scores': {}
                }

        except Exception as e:
            logger.warning(f"Zero-shot classification failed: {e}")
            return {
                'category': 'uncategorized',
                'confidence': 0.0,
                'all_scores': {},
                'error': str(e)
            }

    def _categorize_with_traditional(self, text: str) -> Dict[str, Any]:
        """Categorize document using traditional ML approach."""
        try:
            # This is a simplified approach - in practice, you'd need trained models
            # For now, we'll use rule-based categorization
            return self._rule_based_categorization(text)
        except Exception as e:
            logger.warning(f"Traditional categorization failed: {e}")
            return {
                'category': 'uncategorized',
                'confidence': 0.0,
                'method': 'rule_based_fallback'
            }

    def _rule_based_categorization(self, text: str) -> Dict[str, Any]:
        """Simple rule-based categorization as fallback."""
        text_lower = text.lower()

        # Define category patterns
        patterns = {
            'api_documentation': ['api', 'endpoint', 'request', 'response', 'rest', 'graphql', 'swagger'],
            'user_guide': ['guide', 'tutorial', 'getting started', 'how to', 'walkthrough'],
            'technical_specification': ['specification', 'spec', 'requirements', 'architecture', 'design'],
            'troubleshooting': ['troubleshoot', 'error', 'issue', 'problem', 'fix', 'debug'],
            'configuration': ['config', 'setup', 'installation', 'deploy', 'environment'],
            'security': ['security', 'authentication', 'authorization', 'encryption', 'privacy'],
            'performance': ['performance', 'optimization', 'benchmark', 'speed', 'efficiency'],
            'integration': ['integration', 'webhook', 'callback', 'third-party', 'external']
        }

        category_scores = {}

        for category, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = min(category_scores[best_category] / len(patterns[best_category]), 1.0)
            return {
                'category': best_category,
                'confidence': confidence,
                'method': 'rule_based'
            }
        else:
            return {
                'category': 'general',
                'confidence': 0.1,
                'method': 'rule_based'
            }

    def _generate_tags(self, text: str, category: str, max_tags: int = 5) -> List[str]:
        """Generate relevant tags for the document."""
        keywords = self._extract_keywords(text, max_tags * 2)

        # Filter keywords based on category
        category_keywords = {
            'api_documentation': ['api', 'endpoint', 'request', 'response', 'integration'],
            'user_guide': ['guide', 'tutorial', 'getting-started', 'how-to'],
            'technical_specification': ['spec', 'requirements', 'architecture'],
            'troubleshooting': ['error', 'fix', 'debug', 'issue'],
            'configuration': ['config', 'setup', 'install'],
            'security': ['security', 'auth', 'encryption'],
            'performance': ['performance', 'optimization', 'speed'],
            'integration': ['integration', 'webhook', 'callback']
        }

        relevant_keywords = category_keywords.get(category, [])
        tags = []

        # Add category-relevant keywords first
        for keyword in relevant_keywords:
            if keyword in keywords and keyword not in tags:
                tags.append(keyword)
                if len(tags) >= max_tags:
                    break

        # Fill remaining slots with other keywords
        for keyword in keywords:
            if keyword not in tags and keyword not in relevant_keywords:
                tags.append(keyword)
                if len(tags) >= max_tags:
                    break

        return tags[:max_tags]

    async def categorize_document(
        self,
        document: Dict[str, Any],
        candidate_categories: Optional[List[str]] = None,
        use_zero_shot: bool = True
    ) -> Dict[str, Any]:
        """Categorize a single document.

        Args:
            document: Document to categorize
            candidate_categories: List of candidate categories (for zero-shot)
            use_zero_shot: Whether to use zero-shot classification

        Returns:
            Categorization result
        """
        if not self._initialize_models():
            return {
                'error': 'Categorization models not available',
                'message': 'Required dependencies not installed or model initialization failed'
            }

        try:
            text = self._get_document_text(document)

            if not text:
                return {
                    'category': 'empty',
                    'confidence': 0.0,
                    'tags': [],
                    'message': 'No text content found in document'
                }

            # Default categories if none provided
            if not candidate_categories:
                candidate_categories = [
                    'api_documentation', 'user_guide', 'technical_specification',
                    'troubleshooting', 'configuration', 'security', 'performance',
                    'integration', 'general'
                ]

            # Perform categorization
            if use_zero_shot and self.zero_shot_classifier:
                result = self._categorize_with_zero_shot(text, candidate_categories)
            else:
                result = self._categorize_with_traditional(text)

            # Generate tags
            tags = self._generate_tags(text, result['category'])

            return {
                'document_id': document.get('id', 'unknown'),
                'category': result['category'],
                'confidence': result['confidence'],
                'tags': tags,
                'method': result.get('method', 'zero_shot'),
                'all_scores': result.get('all_scores', {})
            }

        except Exception as e:
            logger.error(f"Document categorization failed: {e}")
            return {
                'error': 'Categorization failed',
                'message': str(e),
                'document_id': document.get('id', 'unknown')
            }

    async def categorize_documents_batch(
        self,
        documents: List[Dict[str, Any]],
        candidate_categories: Optional[List[str]] = None,
        use_zero_shot: bool = True
    ) -> Dict[str, Any]:
        """Categorize multiple documents in batch.

        Args:
            documents: List of documents to categorize
            candidate_categories: List of candidate categories
            use_zero_shot: Whether to use zero-shot classification

        Returns:
            Batch categorization results
        """
        start_time = time.time()

        if not documents:
            return {
                'total_documents': 0,
                'results': [],
                'processing_time': 0.0,
                'message': 'No documents provided'
            }

        results = []
        for doc in documents:
            result = await self.categorize_document(doc, candidate_categories, use_zero_shot)
            results.append(result)

        processing_time = time.time() - start_time

        # Calculate summary statistics
        successful_results = [r for r in results if 'error' not in r]
        category_counts = Counter(r['category'] for r in successful_results)
        avg_confidence = sum(r['confidence'] for r in successful_results) / len(successful_results) if successful_results else 0.0

        return {
            'total_documents': len(documents),
            'successful_categorizations': len(successful_results),
            'results': results,
            'summary': {
                'category_distribution': dict(category_counts),
                'average_confidence': avg_confidence,
                'most_common_category': category_counts.most_common(1)[0][0] if category_counts else None
            },
            'processing_time': processing_time
        }


# Global instance for reuse
document_categorizer = DocumentCategorizer()


async def categorize_document(
    document: Dict[str, Any],
    candidate_categories: Optional[List[str]] = None,
    use_zero_shot: bool = True
) -> Dict[str, Any]:
    """Convenience function for single document categorization.

    Args:
        document: Document to categorize
        candidate_categories: List of candidate categories
        use_zero_shot: Whether to use zero-shot classification

    Returns:
        Categorization result
    """
    return await document_categorizer.categorize_document(
        document=document,
        candidate_categories=candidate_categories,
        use_zero_shot=use_zero_shot
    )


async def categorize_documents_batch(
    documents: List[Dict[str, Any]],
    candidate_categories: Optional[List[str]] = None,
    use_zero_shot: bool = True
) -> Dict[str, Any]:
    """Convenience function for batch document categorization.

    Args:
        documents: List of documents to categorize
        candidate_categories: List of candidate categories
        use_zero_shot: Whether to use zero-shot classification

    Returns:
        Batch categorization results
    """
    return await document_categorizer.categorize_documents_batch(
        documents=documents,
        candidate_categories=candidate_categories,
        use_zero_shot=use_zero_shot
    )
