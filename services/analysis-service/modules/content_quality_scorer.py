"""Content Quality Scoring module for Analysis Service.

Provides comprehensive automated assessment of documentation quality including
readability, structure, completeness, technical accuracy, and overall quality metrics.
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
    import nltk
    # Try to download NLTK data if not available
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    CONTENT_QUALITY_AVAILABLE = True
except ImportError:
    CONTENT_QUALITY_AVAILABLE = False
    TextBlob = None
    sent_tokenize = None
    word_tokenize = None
    stopwords = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class ContentQualityScorer:
    """Comprehensive content quality assessment system."""

    def __init__(self):
        """Initialize the content quality scorer."""
        self.initialized = False
        self._initialize_scorer()

    def _initialize_scorer(self) -> bool:
        """Initialize the quality scorer components."""
        if not CONTENT_QUALITY_AVAILABLE:
            logger.warning("Content quality analysis dependencies not available")
            return False

        self.initialized = True
        return True

    def _extract_text_content(self, document: Dict[str, Any]) -> str:
        """Extract text content from document for analysis."""
        text_parts = []

        # Extract title
        if 'title' in document and document['title']:
            text_parts.append(document['title'])

        # Extract content
        if 'content' in document and document['content']:
            text_parts.append(document['content'])

        # Extract description/summary from metadata
        if 'metadata' in document and document['metadata']:
            metadata = document['metadata']
            if 'description' in metadata and metadata['description']:
                text_parts.append(metadata['description'])
            if 'summary' in metadata and metadata['summary']:
                text_parts.append(metadata['summary'])

        return ' '.join(text_parts).strip()

    def _tokenize_content(self, text: str) -> Tuple[List[str], List[str]]:
        """Tokenize content into sentences and words."""
        try:
            if sent_tokenize and word_tokenize:
                sentences = sent_tokenize(text)
                words = word_tokenize(text)
            else:
                # Fallback tokenization
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                words = text.split()

            return sentences, words
        except Exception as e:
            logger.warning(f"Tokenization failed: {e}")
            # Very basic fallback
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            words = text.split()
            return sentences, words

    def _calculate_readability_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate comprehensive readability metrics."""
        sentences, words = self._tokenize_content(text)

        if not sentences or not words:
            return {
                'sentence_count': 0,
                'word_count': 0,
                'character_count': len(text),
                'avg_sentence_length': 0,
                'avg_word_length': 0,
                'readability_score': 0.5,
                'flesch_kincaid_grade': 0,
                'readability_level': 'unknown'
            }

        # Basic counts
        sentence_count = len(sentences)
        word_count = len(words)
        character_count = len(text)

        # Average lengths
        avg_sentence_length = word_count / sentence_count
        avg_word_length = character_count / word_count

        # Remove punctuation for better analysis
        words_no_punct = [word.lower() for word in words if word.isalpha()]

        # Lexical diversity
        unique_words = len(set(words_no_punct))
        lexical_diversity = unique_words / len(words_no_punct) if words_no_punct else 0

        # Stop word ratio
        if stopwords:
            stop_words = set(stopwords.words('english'))
            stop_word_count = sum(1 for word in words_no_punct if word in stop_words)
            stop_word_ratio = stop_word_count / len(words_no_punct) if words_no_punct else 0
        else:
            stop_word_ratio = 0.3  # Default estimate

        # Flesch-Kincaid Grade Level
        syllables = self._count_syllables(text)
        if sentence_count > 0 and word_count > 0:
            fk_grade = 0.39 * avg_sentence_length + 11.8 * (syllables / word_count) - 15.59
            fk_grade = max(0, min(20, fk_grade))  # Clamp to reasonable range
        else:
            fk_grade = 10  # Default

        # Overall readability score (0-1, higher is easier)
        readability_score = max(0, min(1, 1 - (fk_grade - 6) / 10))

        # Readability level interpretation
        readability_level = self._interpret_readability_level(fk_grade)

        return {
            'sentence_count': sentence_count,
            'word_count': word_count,
            'character_count': character_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_word_length': round(avg_word_length, 1),
            'lexical_diversity': round(lexical_diversity, 3),
            'stop_word_ratio': round(stop_word_ratio, 3),
            'syllable_count': syllables,
            'readability_score': round(readability_score, 3),
            'flesch_kincaid_grade': round(fk_grade, 1),
            'readability_level': readability_level
        }

    def _count_syllables(self, text: str) -> int:
        """Count syllables in text."""
        text = text.lower()
        syllable_count = 0

        # Simple syllable counting algorithm
        vowels = "aeiouy"
        words = re.findall(r'\b\w+\b', text)

        for word in words:
            word_syllables = 0
            prev_char_was_vowel = False

            for char in word:
                if char in vowels:
                    if not prev_char_was_vowel:
                        word_syllables += 1
                    prev_char_was_vowel = True
                else:
                    prev_char_was_vowel = False

            # Handle silent 'e'
            if word.endswith('e') and word_syllables > 1:
                word_syllables -= 1

            # Every word has at least one syllable
            word_syllables = max(1, word_syllables)
            syllable_count += word_syllables

        return syllable_count

    def _interpret_readability_level(self, fk_grade: float) -> str:
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

    def _assess_content_structure(self, text: str, sentences: List[str]) -> Dict[str, Any]:
        """Assess content structure and organization."""
        structure_score = 0.5  # Base score

        # Check for headings and sections
        heading_patterns = [
            r'^#{1,6}\s',  # Markdown headings
            r'^\d+\.',    # Numbered sections
            r'^[A-Z][^.!?]*:$',  # Title case sections ending with colon
        ]

        heading_count = 0
        for sentence in sentences:
            for pattern in heading_patterns:
                if re.match(pattern, sentence.strip()):
                    heading_count += 1
                    break

        # Heading density score
        heading_density = heading_count / len(sentences) if sentences else 0
        structure_score += min(0.2, heading_density * 2)  # Max 0.2 points

        # Check for lists and bullet points
        list_indicators = ['-', '*', '•', '1.', '2.', '3.']
        list_count = 0
        for sentence in sentences:
            if any(sentence.strip().startswith(indicator) for indicator in list_indicators):
                list_count += 1

        list_density = list_count / len(sentences) if sentences else 0
        structure_score += min(0.15, list_density * 1.5)  # Max 0.15 points

        # Check for transitions and connectors
        transitions = [
            'however', 'therefore', 'consequently', 'furthermore', 'moreover',
            'additionally', 'similarly', 'likewise', 'in contrast', 'on the other hand',
            'first', 'second', 'third', 'finally', 'in conclusion'
        ]

        transition_count = sum(1 for sentence in sentences
                              for transition in transitions
                              if transition in sentence.lower())

        transition_density = transition_count / len(sentences) if sentences else 0
        structure_score += min(0.15, transition_density * 3)  # Max 0.15 points

        # Ensure score stays within bounds
        structure_score = max(0.0, min(1.0, structure_score))

        return {
            'structure_score': round(structure_score, 3),
            'heading_count': heading_count,
            'heading_density': round(heading_density, 3),
            'list_count': list_count,
            'list_density': round(list_density, 3),
            'transition_count': transition_count,
            'transition_density': round(transition_density, 3),
            'structure_level': self._interpret_structure_level(structure_score)
        }

    def _interpret_structure_level(self, structure_score: float) -> str:
        """Interpret structure score into quality level."""
        if structure_score < 0.3:
            return "poor"
        elif structure_score < 0.5:
            return "basic"
        elif structure_score < 0.7:
            return "good"
        elif structure_score < 0.9:
            return "excellent"
        else:
            return "outstanding"

    def _assess_content_completeness(self, text: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Assess content completeness and coverage."""
        completeness_score = 0.5  # Base score

        # Check for common documentation elements
        completeness_indicators = {
            'introduction': ['introduction', 'overview', 'about', 'purpose'],
            'requirements': ['requirements', 'prerequisites', 'dependencies', 'needed'],
            'instructions': ['how to', 'steps', 'procedure', 'guide', 'tutorial'],
            'examples': ['example', 'sample', 'code', 'snippet', 'demonstration'],
            'troubleshooting': ['troubleshoot', 'problem', 'issue', 'error', 'fix'],
            'references': ['reference', 'documentation', 'docs', 'additional', 'further reading']
        }

        text_lower = text.lower()
        found_elements = []

        for category, keywords in completeness_indicators.items():
            if any(keyword in text_lower for keyword in keywords):
                found_elements.append(category)
                completeness_score += 0.1  # 0.1 points per element found

        # Check for code blocks (technical documentation)
        code_indicators = ['```', '`', 'function', 'class', 'import', 'def ', 'const ']
        code_count = sum(1 for indicator in code_indicators if indicator in text)
        if code_count > 0:
            completeness_score += 0.1  # Bonus for technical content

        # Check for links/references
        link_count = len(re.findall(r'http[s]?://', text))
        if link_count > 0:
            completeness_score += min(0.1, link_count * 0.02)  # Up to 0.1 for references

        # Check document length (too short might indicate incomplete)
        word_count = len(text.split())
        if word_count < 50:
            completeness_score -= 0.2  # Penalty for very short content
        elif word_count > 200:
            completeness_score += 0.1  # Bonus for comprehensive content

        # Ensure score stays within bounds
        completeness_score = max(0.0, min(1.0, completeness_score))

        return {
            'completeness_score': round(completeness_score, 3),
            'found_elements': found_elements,
            'element_count': len(found_elements),
            'code_references': code_count > 0,
            'link_count': link_count,
            'word_count': word_count,
            'completeness_level': self._interpret_completeness_level(completeness_score)
        }

    def _interpret_completeness_level(self, completeness_score: float) -> str:
        """Interpret completeness score into quality level."""
        if completeness_score < 0.3:
            return "incomplete"
        elif completeness_score < 0.5:
            return "basic"
        elif completeness_score < 0.7:
            return "good"
        elif completeness_score < 0.9:
            return "comprehensive"
        else:
            return "thorough"

    def _assess_technical_accuracy(self, text: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Assess technical accuracy and correctness."""
        accuracy_score = 0.7  # Base score (assume mostly correct unless issues found)

        text_lower = text.lower()

        # Check for common technical issues
        accuracy_issues = {
            'grammar_errors': ['teh ', 'adn ', 'taht ', 'recieve ', 'seperate '],  # Common typos
            'formatting_issues': ['....', '!!', '??', '  ', '\t\t'],  # Poor formatting
            'inconsistent_terminology': [],  # Would need more context to detect
        }

        issue_count = 0
        found_issues = []

        for issue_type, patterns in accuracy_issues.items():
            for pattern in patterns:
                if pattern in text_lower:
                    issue_count += 1
                    found_issues.append(f"{issue_type}: {pattern.strip()}")
                    accuracy_score -= 0.05  # Small penalty per issue

        # Check for proper capitalization
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        proper_capitalization = 0
        for sentence in sentences:
            if sentence and sentence[0].isupper():
                proper_capitalization += 1

        capitalization_ratio = proper_capitalization / len(sentences) if sentences else 1.0
        if capitalization_ratio < 0.8:
            accuracy_score -= 0.1  # Penalty for poor capitalization
            found_issues.append("poor_sentence_capitalization")

        # Check for excessive use of caps (shouting)
        caps_ratio = sum(1 for char in text if char.isupper()) / len(text) if text else 0
        if caps_ratio > 0.1:
            accuracy_score -= 0.05  # Small penalty for excessive caps
            found_issues.append("excessive_capitalization")

        # Ensure score stays within bounds
        accuracy_score = max(0.0, min(1.0, accuracy_score))

        return {
            'accuracy_score': round(accuracy_score, 3),
            'issue_count': issue_count,
            'found_issues': found_issues[:10],  # Limit to first 10 issues
            'capitalization_ratio': round(capitalization_ratio, 3),
            'caps_ratio': round(caps_ratio, 3),
            'accuracy_level': self._interpret_accuracy_level(accuracy_score)
        }

    def _interpret_accuracy_level(self, accuracy_score: float) -> str:
        """Interpret accuracy score into quality level."""
        if accuracy_score < 0.5:
            return "poor"
        elif accuracy_score < 0.7:
            return "fair"
        elif accuracy_score < 0.9:
            return "good"
        else:
            return "excellent"

    def _calculate_overall_quality_score(self,
                                       readability_score: float,
                                       structure_score: float,
                                       completeness_score: float,
                                       accuracy_score: float) -> Dict[str, Any]:
        """Calculate overall quality score with weighted components."""

        # Weighted scoring (adjust weights based on importance)
        weights = {
            'readability': 0.25,    # 25% - how easy to read
            'structure': 0.20,      # 20% - organization and flow
            'completeness': 0.30,   # 30% - coverage and thoroughness
            'accuracy': 0.25        # 25% - correctness and polish
        }

        overall_score = (
            readability_score * weights['readability'] +
            structure_score * weights['structure'] +
            completeness_score * weights['completeness'] +
            accuracy_score * weights['accuracy']
        )

        # Determine quality grade
        if overall_score >= 0.9:
            grade = "A"
            description = "Excellent"
        elif overall_score >= 0.8:
            grade = "B"
            description = "Very Good"
        elif overall_score >= 0.7:
            grade = "C"
            description = "Good"
        elif overall_score >= 0.6:
            grade = "D"
            description = "Fair"
        else:
            grade = "F"
            description = "Poor"

        return {
            'overall_score': round(overall_score, 3),
            'grade': grade,
            'description': description,
            'component_weights': weights,
            'component_scores': {
                'readability': readability_score,
                'structure': structure_score,
                'completeness': completeness_score,
                'accuracy': accuracy_score
            }
        }

    def _generate_quality_recommendations(self,
                                        readability_data: Dict[str, Any],
                                        structure_data: Dict[str, Any],
                                        completeness_data: Dict[str, Any],
                                        accuracy_data: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for quality improvement."""
        recommendations = []

        # Readability recommendations
        if readability_data['readability_score'] < 0.6:
            recommendations.append("Improve readability by using shorter sentences and simpler words")
        if readability_data['flesch_kincaid_grade'] > 12:
            recommendations.append("Consider simplifying complex technical terms or adding explanations")

        # Structure recommendations
        if structure_data['structure_score'] < 0.4:
            recommendations.append("Add headings and subheadings to improve document structure")
        if structure_data['transition_count'] < 2:
            recommendations.append("Add transition words to improve flow between sections")

        # Completeness recommendations
        missing_elements = set(['introduction', 'requirements', 'instructions', 'examples', 'troubleshooting']) - set(completeness_data['found_elements'])
        if missing_elements:
            recommendations.append(f"Consider adding sections for: {', '.join(list(missing_elements)[:3])}")

        # Accuracy recommendations
        if accuracy_data['issue_count'] > 0:
            recommendations.append("Review and correct grammar and formatting issues")
        if accuracy_data['capitalization_ratio'] < 0.8:
            recommendations.append("Ensure proper sentence capitalization")

        # Default recommendations if none specific
        if not recommendations:
            recommendations.append("Content quality is good - consider adding more examples or references")

        return recommendations[:5]  # Limit to top 5 recommendations

    async def assess_content_quality(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive content quality assessment."""

        start_time = time.time()

        if not self._initialize_scorer():
            return {
                'error': 'Content quality analysis not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Extract text content
            text = self._extract_text_content(document)

            if not text:
                return {
                    'document_id': document.get('id', 'unknown'),
                    'quality_score': 0.0,
                    'grade': 'F',
                    'description': 'No content found',
                    'message': 'Document contains no analyzable text content'
                }

            # Tokenize content for analysis
            sentences, words = self._tokenize_content(text)

            # Perform individual assessments
            readability_data = self._calculate_readability_metrics(text)
            structure_data = self._assess_content_structure(text, sentences)
            completeness_data = self._assess_content_completeness(text, document)
            accuracy_data = self._assess_technical_accuracy(text, document)

            # Calculate overall quality
            quality_data = self._calculate_overall_quality_score(
                readability_data['readability_score'],
                structure_data['structure_score'],
                completeness_data['completeness_score'],
                accuracy_data['accuracy_score']
            )

            # Generate recommendations
            recommendations = self._generate_quality_recommendations(
                readability_data, structure_data, completeness_data, accuracy_data
            )

            processing_time = time.time() - start_time

            return {
                'document_id': document.get('id', 'unknown'),
                'quality_assessment': {
                    'overall_score': quality_data['overall_score'],
                    'grade': quality_data['grade'],
                    'description': quality_data['description'],
                    'component_scores': quality_data['component_scores'],
                    'component_weights': quality_data['component_weights']
                },
                'detailed_metrics': {
                    'readability': readability_data,
                    'structure': structure_data,
                    'completeness': completeness_data,
                    'accuracy': accuracy_data
                },
                'recommendations': recommendations,
                'processing_time': round(processing_time, 2),
                'analysis_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Content quality assessment failed: {e}")
            return {
                'error': 'Quality assessment failed',
                'message': str(e),
                'document_id': document.get('id', 'unknown'),
                'processing_time': time.time() - start_time
            }


# Global instance for reuse
content_quality_scorer = ContentQualityScorer()


async def assess_document_quality(document: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for document quality assessment.

    Args:
        document: Document to assess

    Returns:
        Quality assessment results
    """
    return await content_quality_scorer.assess_content_quality(document)
