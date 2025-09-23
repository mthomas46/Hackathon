"""Unit Tests for NLP Processing in Interpreter Service.

This module tests natural language processing capabilities including:
- Intent recognition and classification
- Entity extraction and named entity recognition
- Text analysis and sentiment detection
- Query preprocessing and normalization
- Language understanding and semantic analysis

Tests cover the core NLP pipeline and AI-powered text processing features.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from modules.intent_recognizer import IntentRecognizer
from modules.query_preprocessor import QueryPreprocessor
from modules.advanced_nlp_engine import AdvancedNLPEngine
from modules.models import (
    QueryContext, IntentClassification, EntityExtraction,
    NLPResult
)


class TestIntentRecognizer:
    """Test Intent Recognition functionality."""

    @pytest.fixture
    def intent_recognizer(self):
        """Create intent recognizer instance."""
        return IntentRecognizer()

    def test_simple_intent_classification(self, intent_recognizer, sample_query_context):
        """Test basic intent classification."""
        query = "Find all documents about AI"
        result = intent_recognizer.classify_intent(query)

        assert isinstance(result, IntentClassification)
        assert result.primary_intent in ["search", "find", "query", "document_search"]
        assert 0 <= result.confidence_score <= 1
        assert result.classified_at <= datetime.now()

    def test_complex_intent_hierarchy(self, intent_recognizer):
        """Test complex intent classification with hierarchical intents."""
        test_queries = [
            ("Show me the latest reports on machine learning", "report_retrieval"),
            ("Analyze this document for sentiment", "document_analysis"),
            ("Create a workflow for data processing", "workflow_creation"),
            ("What is the status of my previous query?", "status_check"),
            ("Summarize the key points from this text", "content_summarization")
        ]

        for query, expected_intent in test_queries:
            result = intent_recognizer.classify_intent(query)
            assert result.primary_intent == expected_intent
            assert result.confidence_score > 0.7  # High confidence for clear intents

    def test_intent_confidence_scoring(self, intent_recognizer):
        """Test intent confidence scoring accuracy."""
        clear_query = "Find documents about artificial intelligence"
        ambiguous_query = "Handle this stuff please"

        clear_result = intent_recognizer.classify_intent(clear_query)
        ambiguous_result = intent_recognizer.classify_intent(ambiguous_query)

        # Clear queries should have higher confidence
        assert clear_result.confidence_score > ambiguous_result.confidence_score
        assert clear_result.confidence_score > 0.8  # Very confident
        assert ambiguous_result.confidence_score < 0.7  # Less confident

    def test_intent_features_extraction(self, intent_recognizer):
        """Test intent feature extraction."""
        query = "Find and analyze all recent documents about AI technology"
        result = intent_recognizer.classify_intent(query)

        # Should extract relevant features
        features = result.intent_features
        assert "action_verbs" in features
        assert "find" in features["action_verbs"] or "analyze" in features["action_verbs"]
        assert "keywords" in features
        assert "documents" in features["keywords"]

    def test_multilingual_intent_recognition(self, intent_recognizer):
        """Test intent recognition across multiple languages."""
        test_cases = [
            ("Find documents about AI", "en", "document_search"),
            ("Buscar documentos sobre IA", "es", "document_search"),
            ("Trouver des documents sur l'IA", "fr", "document_search"),
            ("Dokumente über KI finden", "de", "document_search")
        ]

        for query, lang, expected_intent in test_cases:
            result = intent_recognizer.classify_intent(query, language=lang)
            assert result.primary_intent == expected_intent
            assert result.confidence_score > 0.6

    def test_context_aware_intent_classification(self, intent_recognizer):
        """Test context-aware intent classification."""
        # Same words, different intents based on context
        queries = [
            ("What is the status?", {"previous_context": "workflow_execution"}, "status_check"),
            ("What is the status?", {"previous_context": "document_upload"}, "upload_status"),
            ("What is the status?", {"previous_context": "query_processing"}, "query_status")
        ]

        for query, context, expected_intent in queries:
            result = intent_recognizer.classify_intent(query, context=context)
            assert result.primary_intent == expected_intent


class TestEntityExtraction:
    """Test Entity Extraction functionality."""

    @pytest.fixture
    def nlp_engine(self):
        """Create NLP engine instance."""
        return AdvancedNLPEngine()

    def test_basic_entity_extraction(self, nlp_engine):
        """Test basic named entity recognition."""
        text = "John Doe works at OpenAI and researches machine learning algorithms."
        result = nlp_engine.extract_entities(text)

        assert isinstance(result, EntityExtraction)
        assert len(result.entities) >= 3  # Should find persons, organizations, technologies

        # Check for expected entity types
        entity_types = {entity["type"] for entity in result.entities}
        assert "person" in entity_types
        assert "organization" in entity_types
        assert "technology" in entity_types

    def test_entity_confidence_scoring(self, nlp_engine):
        """Test entity extraction confidence scoring."""
        clear_text = "Albert Einstein developed the theory of relativity."
        ambiguous_text = "Bob worked on some project with complex algorithms."

        clear_result = nlp_engine.extract_entities(clear_text)
        ambiguous_result = nlp_engine.extract_entities(ambiguous_text)

        # Clear entities should have higher confidence
        clear_avg_confidence = sum(e["confidence"] for e in clear_result.entities) / len(clear_result.entities)
        ambiguous_avg_confidence = sum(e["confidence"] for e in ambiguous_result.entities) / len(ambiguous_result.entities)

        assert clear_avg_confidence > ambiguous_avg_confidence

    def test_domain_specific_entity_recognition(self, nlp_engine):
        """Test domain-specific entity recognition for tech/AI domain."""
        tech_text = """
        The GPT-4 model from OpenAI demonstrates superior performance on the GLUE benchmark.
        TensorFlow and PyTorch are popular deep learning frameworks developed by Google and Meta.
        """

        result = nlp_engine.extract_entities(tech_text, domain="technology")

        # Should recognize technology-specific entities
        entity_texts = {entity["text"].lower() for entity in result.entities}
        tech_entities = {"gpt-4", "openai", "glue", "tensorflow", "pytorch", "google", "meta"}

        # At least 60% of tech entities should be recognized
        recognized_tech = len(tech_entities.intersection(entity_texts))
        assert recognized_tech >= len(tech_entities) * 0.6

    def test_entity_relationship_extraction(self, nlp_engine):
        """Test extraction of entity relationships."""
        text = "Elon Musk founded Tesla and SpaceX to advance sustainable energy and space exploration."
        result = nlp_engine.extract_entities(text, include_relationships=True)

        # Should identify relationships between entities
        assert "relationships" in result.extraction_metadata

        relationships = result.extraction_metadata["relationships"]
        assert len(relationships) > 0

        # Should find founder-company relationships
        founder_relations = [r for r in relationships if r.get("type") == "founder_of"]
        assert len(founder_relations) > 0

    def test_temporal_entity_extraction(self, nlp_engine):
        """Test temporal entity extraction."""
        text = "The conference will be held from March 15, 2024 to March 17, 2024 in San Francisco."
        result = nlp_engine.extract_entities(text, include_temporal=True)

        # Should extract date entities
        date_entities = [e for e in result.entities if e["type"] == "date"]
        assert len(date_entities) >= 2  # Start and end dates

        # Should normalize date formats
        for entity in date_entities:
            assert "normalized_date" in entity.get("metadata", {})

    def test_entity_disambiguation(self, nlp_engine):
        """Test entity disambiguation for ambiguous terms."""
        ambiguous_text = "Apple released a new model that runs on AI technology."
        result = nlp_engine.extract_entities(ambiguous_text, enable_disambiguation=True)

        # Should disambiguate "Apple" correctly
        apple_entities = [e for e in result.entities if e["text"].lower() == "apple"]
        assert len(apple_entities) == 1

        apple_entity = apple_entities[0]
        assert "disambiguation" in apple_entity.get("metadata", {})
        assert apple_entity["metadata"]["disambiguation"]["type"] == "company"


class TestQueryPreprocessor:
    """Test Query Preprocessing functionality."""

    @pytest.fixture
    def query_preprocessor(self):
        """Create query preprocessor instance."""
        return QueryPreprocessor()

    def test_query_normalization(self, query_preprocessor):
        """Test query text normalization."""
        test_cases = [
            ("  Find   ALL documents  about AI!  ", "find all documents about ai"),
            ("What's the STATUS of my query?", "what is the status of my query"),
            ("Show me docs from LAST QUARTER", "show me docs from last quarter"),
            ("ANALyze this TEXT please.", "analyze this text please")
        ]

        for input_query, expected in test_cases:
            result = query_preprocessor.normalize_query(input_query)
            assert result == expected

    def test_query_tokenization(self, query_preprocessor):
        """Test query tokenization."""
        query = "Find documents about artificial intelligence and machine learning"
        tokens = query_preprocessor.tokenize_query(query)

        assert isinstance(tokens, list)
        assert len(tokens) > 5
        assert "find" in tokens
        assert "documents" in tokens
        assert "artificial" in tokens
        assert "intelligence" in tokens

    def test_stop_word_removal(self, query_preprocessor):
        """Test stop word removal from queries."""
        query_with_stops = "Find the all and but documents about artificial intelligence"
        processed = query_preprocessor.remove_stop_words(query_with_stops)

        # Stop words should be removed
        stop_words = {"the", "all", "and", "but"}
        remaining_tokens = set(processed.lower().split())
        assert len(stop_words.intersection(remaining_tokens)) == 0

        # Important words should remain
        assert "find" in remaining_tokens
        assert "documents" in remaining_tokens
        assert "artificial" in remaining_tokens

    def test_query_expansion(self, query_preprocessor):
        """Test query expansion with synonyms."""
        original_query = "find docs about ML"
        expanded = query_preprocessor.expand_query(original_query)

        # Should include synonyms and related terms
        expanded_lower = expanded.lower()
        assert "machine learning" in expanded_lower or "ml" in expanded_lower
        assert "documents" in expanded_lower or "docs" in expanded_lower
        assert "find" in expanded_lower or "search" in expanded_lower

    def test_complex_query_parsing(self, query_preprocessor):
        """Test parsing of complex queries with multiple clauses."""
        complex_query = "Find documents about AI OR machine learning from 2023 to 2024 that contain 'neural networks'"
        parsed = query_preprocessor.parse_complex_query(complex_query)

        assert "clauses" in parsed
        assert "operators" in parsed
        assert len(parsed["clauses"]) >= 3  # Multiple query parts

        # Should identify OR operator
        assert "or" in parsed["operators"] or "OR" in parsed["operators"]

        # Should extract date range
        assert "date_range" in parsed
        assert "2023" in str(parsed["date_range"])
        assert "2024" in str(parsed["date_range"])


class TestAdvancedNLPEngine:
    """Test Advanced NLP Engine functionality."""

    @pytest.fixture
    def nlp_engine(self):
        """Create advanced NLP engine instance."""
        return AdvancedNLPEngine()

    def test_comprehensive_text_analysis(self, nlp_engine):
        """Test comprehensive text analysis pipeline."""
        text = """
        Artificial Intelligence and Machine Learning are transforming industries.
        Companies like Google and Microsoft are investing heavily in AI research.
        The future of technology depends on responsible AI development.
        """

        analysis = nlp_engine.analyze_text_comprehensive(text)

        assert isinstance(analysis, NLPResult)

        # Should include all analysis components
        assert analysis.intent_classification is not None
        assert analysis.entity_extraction is not None
        assert analysis.sentiment_analysis is not None
        assert "sentiment" in analysis.sentiment_analysis

        # Should have processing metadata
        assert "total_processing_time_ms" in analysis.processing_metadata
        assert analysis.processing_metadata["total_processing_time_ms"] > 0

    def test_sentiment_analysis_accuracy(self, nlp_engine):
        """Test sentiment analysis accuracy."""
        test_texts = [
            ("This is absolutely wonderful and amazing!", "positive", 0.8),
            ("This is terrible and disappointing.", "negative", 0.8),
            ("The weather is okay today.", "neutral", 0.6)
        ]

        for text, expected_sentiment, min_confidence in test_texts:
            result = nlp_engine.analyze_sentiment(text)
            assert result["sentiment"] == expected_sentiment
            assert result["confidence"] >= min_confidence

    def test_text_complexity_analysis(self, nlp_engine):
        """Test text complexity and readability analysis."""
        simple_text = "The cat sat on the mat. It was happy."
        complex_text = """
        The quantum mechanical model of atomic structure posits that electrons exist
        in probabilistic orbitals rather than deterministic trajectories, fundamentally
        altering our understanding of matter at the subatomic level.
        """

        simple_analysis = nlp_engine.analyze_complexity(simple_text)
        complex_analysis = nlp_engine.analyze_complexity(complex_text)

        # Simple text should have higher readability
        assert simple_analysis["readability_score"] > complex_analysis["readability_score"]

        # Complex text should have higher complexity
        assert complex_analysis["complexity_score"] > simple_analysis["complexity_score"]

        # Should include grade level assessment
        assert "grade_level" in simple_analysis
        assert "grade_level" in complex_analysis

    def test_semantic_similarity_calculation(self, nlp_engine):
        """Test semantic similarity between texts."""
        text1 = "Machine learning algorithms process data to make predictions."
        text2 = "AI systems use algorithms to analyze information and forecast outcomes."
        text3 = "The weather is sunny today."

        similarity_1_2 = nlp_engine.calculate_semantic_similarity(text1, text2)
        similarity_1_3 = nlp_engine.calculate_semantic_similarity(text1, text3)

        # Related texts should have higher similarity
        assert similarity_1_2 > similarity_1_3
        assert similarity_1_2 > 0.6  # Should be quite similar
        assert similarity_1_3 < 0.4  # Should be quite different

    def test_topic_modeling(self, nlp_engine):
        """Test topic modeling and discovery."""
        documents = [
            "Machine learning algorithms process big data for predictions and insights.",
            "Artificial intelligence systems use neural networks for pattern recognition.",
            "Deep learning models analyze images and text with high accuracy.",
            "Data science involves statistics, programming, and domain expertise.",
            "Business intelligence tools help analyze sales and customer data."
        ]

        topics = nlp_engine.extract_topics(documents, num_topics=3)

        assert len(topics) == 3

        # Should identify distinct topics
        topic_words = [topic["words"] for topic in topics]
        all_words = [word for words in topic_words for word in words]

        # Should contain relevant terms
        ai_terms = {"machine", "learning", "artificial", "intelligence", "neural"}
        data_terms = {"data", "analysis", "insights", "business"}

        ai_found = len(ai_terms.intersection(set(all_words)))
        data_found = len(data_terms.intersection(set(all_words)))

        assert ai_found > 0 or data_found > 0  # Should find relevant topics

    def test_language_detection(self, nlp_engine):
        """Test language detection capabilities."""
        test_texts = [
            ("Hello world, how are you today?", "en"),
            ("Bonjour le monde, comment allez-vous?", "fr"),
            ("Hola mundo, ¿cómo estás hoy?", "es"),
            ("Hallo Welt, wie geht es dir heute?", "de")
        ]

        for text, expected_lang in test_texts:
            detected_lang = nlp_engine.detect_language(text)
            assert detected_lang == expected_lang

    def test_nlp_pipeline_performance(self, nlp_engine):
        """Test NLP pipeline performance and optimization."""
        text = "This is a sample text for performance testing of the NLP pipeline."

        # Measure processing time
        import time
        start_time = time.time()

        result = nlp_engine.process_text_pipeline(text)

        processing_time = time.time() - start_time

        # Should complete within reasonable time
        assert processing_time < 5.0  # Less than 5 seconds

        # Should include performance metrics
        assert "processing_time_ms" in result["metadata"]
        assert result["metadata"]["processing_time_ms"] > 0

        # Should include pipeline efficiency metrics
        assert "pipeline_efficiency" in result["metadata"]


class TestNLPIntegration:
    """Test integration between NLP components."""

    @pytest.fixture
    def integrated_nlp_system(self, mock_llm_gateway):
        """Create integrated NLP system with mocked LLM."""
        return AdvancedNLPEngine(llm_gateway=mock_llm_gateway)

    def test_end_to_end_query_processing(self, integrated_nlp_system, sample_query_context):
        """Test end-to-end query processing pipeline."""
        query = sample_query_context.original_query

        # Process through full pipeline
        result = integrated_nlp_system.process_query_end_to_end(query)

        assert isinstance(result, NLPResult)
        assert result.original_text == query

        # Should have all pipeline components
        assert result.intent_classification is not None
        assert result.entity_extraction is not None
        assert result.sentiment_analysis is not None

        # Should include processing metadata
        assert "total_processing_time_ms" in result.processing_metadata
        assert result.processing_metadata["total_processing_time_ms"] > 0

    def test_nlp_fallback_mechanisms(self, integrated_nlp_system):
        """Test NLP fallback mechanisms when LLM is unavailable."""
        query = "Analyze this document about machine learning"

        # Simulate LLM failure
        integrated_nlp_system.llm_gateway = None

        # Should still process with local NLP capabilities
        result = integrated_nlp_system.process_query_end_to_end(query)

        # Should have basic NLP results even without LLM
        assert result.intent_classification is not None
        assert result.intent_classification.confidence_score < 0.8  # Lower confidence without LLM

        # Should indicate fallback was used
        assert "fallback_used" in result.processing_metadata
        assert result.processing_metadata["fallback_used"] is True

    def test_adaptive_nlp_processing(self, integrated_nlp_system):
        """Test adaptive NLP processing based on query complexity."""
        simple_query = "Find documents"
        complex_query = """
        Analyze the quarterly financial reports from Q1 2023 to Q4 2024,
        focusing on revenue growth trends, profitability metrics, and market share changes
        for the technology sector companies with market capitalization over $10 billion.
        """

        simple_result = integrated_nlp_system.process_query_end_to_end(simple_query)
        complex_result = integrated_nlp_system.process_query_end_to_end(complex_query)

        # Complex queries should take longer to process
        assert complex_result.processing_metadata["total_processing_time_ms"] > \
               simple_result.processing_metadata["total_processing_time_ms"]

        # Complex queries should have more entities extracted
        assert len(complex_result.entity_extraction.entities) > \
               len(simple_result.entity_extraction.entities)

        # Should adapt processing strategy based on complexity
        assert "processing_strategy" in complex_result.processing_metadata
        assert complex_result.processing_metadata["processing_strategy"] == "comprehensive"
