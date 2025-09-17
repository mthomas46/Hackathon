"""Sentiment analysis module for Analysis Service.

Provides comprehensive sentiment analysis and clarity assessment for documentation,
including tone analysis, readability scoring, and clarity metrics.
"""
import time
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
import statistics

try:
    from textblob import TextBlob
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from transformers import pipeline
    import torch
    SENTIMENT_ANALYSIS_AVAILABLE = True
except ImportError:
    SENTIMENT_ANALYSIS_AVAILABLE = False
    TextBlob = None
    sent_tokenize = None
    word_tokenize = None
    stopwords = None
    pipeline = None
    torch = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment, tone, and clarity of documentation."""

    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """Initialize the sentiment analyzer.

        Args:
            model_name: Name of the transformer model for advanced sentiment analysis
        """
        self.model_name = model_name
        self.sentiment_pipeline = None
        self.initialized = False

        # Download NLTK data if available
        if SENTIMENT_ANALYSIS_AVAILABLE:
            try:
                import nltk
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
            except Exception as e:
                logger.warning(f"Failed to download NLTK data: {e}")

    def _initialize_models(self) -> bool:
        """Initialize the sentiment analysis models."""
        if not SENTIMENT_ANALYSIS_AVAILABLE:
            logger.warning("Sentiment analysis dependencies not available")
            return False

        try:
            # Initialize transformer-based sentiment analysis
            if self.sentiment_pipeline is None:
                logger.info(f"Loading sentiment analysis model: {self.model_name}")
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.model_name,
                    tokenizer=self.model_name,
                    device=-1,  # Use CPU
                    return_all_scores=True
                )

            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize sentiment models: {e}")
            return False

    def _analyze_sentiment_textblob(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob (rule-based approach)."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Convert polarity to sentiment categories
            if polarity > 0.1:
                sentiment = "positive"
            elif polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            # Calculate confidence based on polarity strength
            confidence = min(abs(polarity) * 2, 1.0)

            return {
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': subjectivity,
                'confidence': confidence,
                'method': 'textblob'
            }

        except Exception as e:
            logger.warning(f"TextBlob sentiment analysis failed: {e}")
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.5,
                'confidence': 0.0,
                'method': 'textblob_error',
                'error': str(e)
            }

    def _analyze_sentiment_transformer(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using transformer model."""
        try:
            if not self.sentiment_pipeline:
                return self._analyze_sentiment_textblob(text)

            # Truncate text if too long (model limit)
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]

            results = self.sentiment_pipeline(text)

            if not results or len(results) == 0:
                return self._analyze_sentiment_textblob(text)

            # Process results - expect list of dicts with scores
            if isinstance(results[0], list):
                results = results[0]

            # Find the highest scoring sentiment
            best_result = max(results, key=lambda x: x['score'])

            # Map model labels to standard categories
            label = best_result['label'].lower()
            if 'positive' in label or 'pos' in label:
                sentiment = 'positive'
            elif 'negative' in label or 'neg' in label:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            return {
                'sentiment': sentiment,
                'polarity': best_result['score'] if sentiment == 'positive' else -best_result['score'] if sentiment == 'negative' else 0.0,
                'confidence': best_result['score'],
                'method': 'transformer',
                'model': self.model_name,
                'all_scores': {r['label']: r['score'] for r in results}
            }

        except Exception as e:
            logger.warning(f"Transformer sentiment analysis failed: {e}")
            return self._analyze_sentiment_textblob(text)

    def _calculate_readability_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate readability and clarity metrics."""
        try:
            sentences = sent_tokenize(text) if sent_tokenize else text.split('.')
            words = word_tokenize(text) if word_tokenize else text.split()

            # Remove stop words for better analysis
            if stopwords:
                stop_words = set(stopwords.words('english'))
                content_words = [word.lower() for word in words if word.isalpha() and word.lower() not in stop_words]
            else:
                content_words = [word.lower() for word in words if word.isalpha()]

            # Basic readability metrics
            num_sentences = len([s for s in sentences if s.strip()])
            num_words = len(words)
            num_content_words = len(content_words)
            num_chars = len(text)

            # Average sentence length
            avg_sentence_length = num_words / max(num_sentences, 1)

            # Average word length
            avg_word_length = num_chars / max(num_words, 1)

            # Lexical diversity (unique words / total words)
            unique_words = len(set(word.lower() for word in words if word.isalpha()))
            lexical_diversity = unique_words / max(num_words, 1)

            # Simple readability score (lower is easier to read)
            readability_score = avg_sentence_length * 0.4 + avg_word_length * 0.6

            # Flesch-Kincaid Grade Level approximation
            if num_sentences > 0 and num_words > 0:
                fk_grade = 0.39 * avg_sentence_length + 11.8 * (num_chars / num_words) - 15.59
            else:
                fk_grade = 0.0

            # Clarity assessment
            clarity_score = self._assess_clarity(text, sentences, content_words)

            return {
                'sentence_count': num_sentences,
                'word_count': num_words,
                'content_word_count': num_content_words,
                'character_count': num_chars,
                'avg_sentence_length': avg_sentence_length,
                'avg_word_length': avg_word_length,
                'lexical_diversity': lexical_diversity,
                'readability_score': readability_score,
                'flesch_kincaid_grade': fk_grade,
                'clarity_score': clarity_score,
                'readability_level': self._interpret_readability(fk_grade)
            }

        except Exception as e:
            logger.warning(f"Readability calculation failed: {e}")
            return {
                'sentence_count': 0,
                'word_count': len(text.split()),
                'character_count': len(text),
                'readability_score': 0.5,
                'clarity_score': 0.5,
                'error': str(e)
            }

    def _assess_clarity(self, text: str, sentences: List[str], content_words: List[str]) -> float:
        """Assess the clarity of the text content."""
        clarity_score = 0.5  # Base score

        try:
            # Factor 1: Sentence length variety (good writing has varied sentence lengths)
            if sentences:
                sentence_lengths = [len(sent.split()) for sent in sentences if sent.strip()]
                if len(sentence_lengths) > 1:
                    length_std = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
                    # Reward moderate variation (not too uniform, not too varied)
                    optimal_variation = 5.0
                    clarity_score += 0.1 * (1 - abs(length_std - optimal_variation) / optimal_variation)

            # Factor 2: Use of common words vs complex jargon
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
            common_word_ratio = sum(1 for word in content_words if word in common_words) / max(len(content_words), 1)
            clarity_score += 0.2 * common_word_ratio  # Reward use of common words

            # Factor 3: Avoid very long sentences
            long_sentences = sum(1 for sent in sentences if len(sent.split()) > 30)
            long_sentence_penalty = long_sentences / max(len(sentences), 1)
            clarity_score -= 0.2 * long_sentence_penalty

            # Factor 4: Check for passive voice (generally harder to read)
            passive_indicators = ['is', 'are', 'was', 'were', 'be', 'been', 'being', 'has', 'have', 'had']
            passive_verbs = ['done', 'made', 'taken', 'given', 'shown', 'told', 'seen', 'found', 'used', 'called']
            passive_score = 0
            for sent in sentences:
                words = sent.lower().split()
                if any(indicator in words for indicator in passive_indicators):
                    if any(verb in words for verb in passive_verbs):
                        passive_score += 1
            passive_ratio = passive_score / max(len(sentences), 1)
            clarity_score -= 0.1 * passive_ratio  # Slight penalty for passive voice

            # Ensure score stays within bounds
            clarity_score = max(0.0, min(1.0, clarity_score))

        except Exception as e:
            logger.warning(f"Clarity assessment failed: {e}")
            clarity_score = 0.5

        return clarity_score

    def _interpret_readability(self, fk_grade: float) -> str:
        """Interpret Flesch-Kincaid grade level into readability category."""
        if fk_grade < 6:
            return "very_easy"
        elif fk_grade < 8:
            return "easy"
        elif fk_grade < 10:
            return "fairly_easy"
        elif fk_grade < 12:
            return "standard"
        elif fk_grade < 14:
            return "fairly_difficult"
        elif fk_grade < 16:
            return "difficult"
        else:
            return "very_difficult"

    def _analyze_tone_patterns(self, text: str) -> Dict[str, Any]:
        """Analyze tone patterns and writing style."""
        try:
            text_lower = text.lower()

            # Define tone indicators
            positive_indicators = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'helpful', 'useful', 'easy', 'simple', 'clear', 'best', 'recommend', 'love', 'enjoy']
            negative_indicators = ['bad', 'terrible', 'awful', 'horrible', 'difficult', 'hard', 'complex', 'confusing', 'worst', 'hate', 'problem', 'issue', 'error', 'fail']
            professional_indicators = ['accordingly', 'therefore', 'however', 'furthermore', 'consequently', 'specifically', 'additionally', 'importantly', 'note', 'please', 'ensure']
            technical_indicators = ['implementation', 'configuration', 'deployment', 'architecture', 'framework', 'protocol', 'algorithm', 'database', 'interface', 'integration']

            # Count occurrences
            positive_count = sum(1 for word in positive_indicators if word in text_lower)
            negative_count = sum(1 for word in negative_indicators if word in text_lower)
            professional_count = sum(1 for word in professional_indicators if word in text_lower)
            technical_count = sum(1 for word in technical_indicators if word in text_lower)

            # Calculate tone scores
            total_indicators = len(text.split()) / 100  # Normalize per 100 words
            positive_score = positive_count / max(total_indicators, 1)
            negative_score = negative_count / max(total_indicators, 1)
            professional_score = professional_count / max(total_indicators, 1)
            technical_score = technical_count / max(total_indicators, 1)

            # Determine primary tone
            if positive_score > negative_score and positive_score > 0.5:
                primary_tone = "encouraging"
            elif negative_score > positive_score and negative_score > 0.5:
                primary_tone = "critical"
            elif professional_score > 1.0:
                primary_tone = "formal"
            elif technical_score > 1.0:
                primary_tone = "technical"
            else:
                primary_tone = "neutral"

            return {
                'primary_tone': primary_tone,
                'tone_scores': {
                    'positive': positive_score,
                    'negative': negative_score,
                    'professional': professional_score,
                    'technical': technical_score
                },
                'tone_indicators': {
                    'positive_words': positive_count,
                    'negative_words': negative_count,
                    'professional_phrases': professional_count,
                    'technical_terms': technical_count
                }
            }

        except Exception as e:
            logger.warning(f"Tone analysis failed: {e}")
            return {
                'primary_tone': 'neutral',
                'tone_scores': {'positive': 0, 'negative': 0, 'professional': 0, 'technical': 0},
                'error': str(e)
            }

    async def analyze_sentiment_and_clarity(
        self,
        document: Dict[str, Any],
        use_transformer: bool = True,
        include_tone_analysis: bool = True
    ) -> Dict[str, Any]:
        """Analyze sentiment, tone, and clarity of a document.

        Args:
            document: Document to analyze
            use_transformer: Whether to use transformer model for sentiment
            include_tone_analysis: Whether to include detailed tone analysis

        Returns:
            Comprehensive sentiment and clarity analysis
        """
        start_time = time.time()

        if not self._initialize_models():
            return {
                'error': 'Sentiment analysis not available',
                'message': 'Required dependencies not installed or model initialization failed'
            }

        try:
            # Extract text content
            content = document.get('content', '')
            title = document.get('title', '')

            # Combine title and content for analysis
            full_text = f"{title}. {content}" if title else content

            if not full_text.strip():
                return {
                    'document_id': document.get('id', 'unknown'),
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'readability_score': 0.5,
                    'clarity_score': 0.5,
                    'message': 'No text content found for analysis'
                }

            # Perform sentiment analysis
            if use_transformer and self.sentiment_pipeline:
                sentiment_result = self._analyze_sentiment_transformer(full_text)
            else:
                sentiment_result = self._analyze_sentiment_textblob(full_text)

            # Calculate readability metrics
            readability_metrics = self._calculate_readability_metrics(full_text)

            # Analyze tone patterns
            tone_analysis = {}
            if include_tone_analysis:
                tone_analysis = self._analyze_tone_patterns(full_text)

            # Calculate overall quality score
            quality_score = self._calculate_overall_quality_score(
                sentiment_result, readability_metrics
            )

            processing_time = time.time() - start_time

            return {
                'document_id': document.get('id', 'unknown'),
                'sentiment_analysis': sentiment_result,
                'readability_metrics': readability_metrics,
                'tone_analysis': tone_analysis,
                'quality_score': quality_score,
                'processing_time': processing_time,
                'recommendations': self._generate_recommendations(
                    sentiment_result, readability_metrics, tone_analysis
                )
            }

        except Exception as e:
            logger.error(f"Sentiment and clarity analysis failed: {e}")
            return {
                'error': 'Analysis failed',
                'message': str(e),
                'document_id': document.get('id', 'unknown'),
                'processing_time': time.time() - start_time
            }

    def _calculate_overall_quality_score(
        self,
        sentiment: Dict[str, Any],
        readability: Dict[str, Any]
    ) -> float:
        """Calculate an overall quality score based on sentiment and readability."""
        try:
            # Base score from sentiment (neutral is good, extremes might indicate issues)
            if sentiment['sentiment'] == 'neutral':
                sentiment_score = 0.8
            elif sentiment['sentiment'] == 'positive':
                sentiment_score = 0.9
            else:  # negative
                sentiment_score = 0.6

            # Readability score (invert so higher readability = higher score)
            readability_score = max(0, 1 - (readability.get('readability_score', 0.5) - 10) / 20)

            # Clarity score
            clarity_score = readability.get('clarity_score', 0.5)

            # Weighted average
            overall_score = (
                sentiment_score * 0.3 +
                readability_score * 0.4 +
                clarity_score * 0.3
            )

            return round(overall_score, 3)

        except Exception as e:
            logger.warning(f"Quality score calculation failed: {e}")
            return 0.5

    def _generate_recommendations(
        self,
        sentiment: Dict[str, Any],
        readability: Dict[str, Any],
        tone: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on the analysis."""
        recommendations = []

        try:
            # Sentiment-based recommendations
            if sentiment.get('sentiment') == 'negative':
                recommendations.append("Consider revising negative language to be more encouraging")
            elif sentiment.get('sentiment') == 'positive':
                recommendations.append("Good use of positive language - maintain this tone")

            # Readability recommendations
            fk_grade = readability.get('flesch_kincaid_grade', 12)
            if fk_grade > 14:
                recommendations.append("Consider simplifying complex sentences for better readability")
            elif fk_grade < 8:
                recommendations.append("Consider adding more technical depth for advanced readers")

            # Clarity recommendations
            clarity_score = readability.get('clarity_score', 0.5)
            if clarity_score < 0.4:
                recommendations.append("Improve clarity by using shorter sentences and simpler language")
            elif clarity_score > 0.8:
                recommendations.append("Excellent clarity - maintain this clear writing style")

            # Tone recommendations
            primary_tone = tone.get('primary_tone', 'neutral')
            if primary_tone == 'technical' and readability.get('readability_level') == 'very_difficult':
                recommendations.append("Balance technical content with clearer explanations")
            elif primary_tone == 'formal':
                recommendations.append("Consider adding more conversational elements to engage readers")

        except Exception as e:
            logger.warning(f"Recommendation generation failed: {e}")
            recommendations.append("Unable to generate specific recommendations due to analysis error")

        return recommendations if recommendations else ["Analysis complete - no specific recommendations needed"]


# Global instance for reuse
sentiment_analyzer = SentimentAnalyzer()


async def analyze_document_sentiment(
    document: Dict[str, Any],
    use_transformer: bool = True,
    include_tone_analysis: bool = True
) -> Dict[str, Any]:
    """Convenience function for document sentiment analysis.

    Args:
        document: Document to analyze
        use_transformer: Whether to use transformer model
        include_tone_analysis: Whether to include tone analysis

    Returns:
        Sentiment and clarity analysis results
    """
    return await sentiment_analyzer.analyze_sentiment_and_clarity(
        document=document,
        use_transformer=use_transformer,
        include_tone_analysis=include_tone_analysis
    )
