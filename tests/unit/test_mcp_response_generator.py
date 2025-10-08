"""Unit tests for MCP response generator.

TDD Phase 2: MCP Contextual Response Generation
Tests intent classification, snippet extraction, and response synthesis.
"""

import pytest
import sys
from pathlib import Path

# Add docker/mcp-base to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "docker" / "mcp-base"))

from mcp_response_generator import (
    extract_key_terms,
    classify_query_intent,
    extract_main_topic,
    generate_search_suggestions,
    generate_no_results_response,
    generate_intent_based_intro,
    extract_relevant_snippets,
    generate_synthesis_response,
    generate_contextual_response
)


class TestIntentClassification:
    """Test query intent classification."""
    
    def test_classify_overview_intent(self):
        """Test classification of overview queries."""
        assert classify_query_intent("What is the Horus Heresy?") == "overview"
        assert classify_query_intent("Tell me about the Emperor") == "overview"
        assert classify_query_intent("Explain the Primarchs") == "overview"
        assert classify_query_intent("Give me a summary of the heresy") == "overview"
    
    def test_classify_causation_intent(self):
        """Test classification of causation queries."""
        assert classify_query_intent("Why did the Horus Heresy happen?") == "causation"
        assert classify_query_intent("What caused the heresy?") == "causation"
        assert classify_query_intent("What led to the rebellion?") == "causation"
    
    def test_classify_temporal_intent(self):
        """Test classification of temporal queries."""
        assert classify_query_intent("When did the Horus Heresy occur?") == "temporal"
        assert classify_query_intent("What is the timeline of events?") == "temporal"
        assert classify_query_intent("Show me the chronology") == "temporal"
    
    def test_classify_comparison_intent(self):
        """Test classification of comparison queries."""
        assert classify_query_intent("Compare traitor and loyalist legions") == "comparison"
        assert classify_query_intent("What's the difference between legions?") == "comparison"
        assert classify_query_intent("Horus versus the Emperor") == "comparison"
    
    def test_classify_specific_intent(self):
        """Test classification of specific detail queries."""
        assert classify_query_intent("Who were the traitor primarchs?") == "specific"
        assert classify_query_intent("Which legions were loyal?") == "specific"
        assert classify_query_intent("Name the Space Marine legions") == "specific"
        assert classify_query_intent("List the Chaos Gods") == "specific"
    
    def test_classify_general_fallback(self):
        """Test fallback to general for unclassifiable queries."""
        assert classify_query_intent("Emperor Primarch Legion") == "general"
        assert classify_query_intent("random query text") == "general"


class TestKeyTermExtraction:
    """Test key term extraction from queries."""
    
    def test_extract_key_terms_simple(self):
        """Test extracting terms from simple query."""
        terms = extract_key_terms("horus heresy")
        
        assert 'horus' in terms
        assert 'heresy' in terms
    
    def test_extract_key_terms_filters_stop_words(self):
        """Test that stop words are filtered."""
        terms = extract_key_terms("Tell me about the Horus Heresy")
        
        # Stop words should be removed
        assert 'tell' not in terms
        assert 'me' not in terms
        assert 'about' not in terms
        assert 'the' not in terms
    
    def test_extract_key_terms_minimum_length(self):
        """Test that short words are filtered."""
        terms = extract_key_terms("a is to be or it")
        
        # All words are either stop words or too short
        assert len(terms) == 0
    
    def test_extract_main_topic(self):
        """Test extracting main topic from query."""
        topic = extract_main_topic("Tell me about the Horus Heresy and the traitor legions")
        
        # Should extract first few key terms
        assert len(topic) > 0
        assert 'horus' in topic.lower() or 'heresy' in topic.lower()


class TestSearchSuggestions:
    """Test search suggestion generation."""
    
    def test_generate_suggestions_multiple_terms(self):
        """Test suggestions for multi-term query."""
        suggestions = generate_search_suggestions(['horus', 'heresy', 'emperor'])
        
        # Should have multiple suggestions
        assert len(suggestions) > 0
        assert len(suggestions) <= 4  # Max 4 suggestions
        
        # Should suggest breaking down query
        assert any('horus' in s.lower() for s in suggestions)
    
    def test_generate_suggestions_single_term(self):
        """Test suggestions for single-term query."""
        suggestions = generate_search_suggestions(['emperor'])
        
        assert len(suggestions) > 0
        assert any('broader' in s.lower() or 'specific' in s.lower() for s in suggestions)
    
    def test_generate_suggestions_no_terms(self):
        """Test suggestions when no key terms extracted."""
        suggestions = generate_search_suggestions([])
        
        # Should still provide generic suggestions
        assert len(suggestions) > 0


class TestNoResultsResponse:
    """Test no-results response generation."""
    
    def test_no_results_response_structure(self):
        """Test structure of no-results response."""
        response = generate_no_results_response("Tell me about the Horus Heresy")
        
        # Should be a string
        assert isinstance(response, str)
        
        # Should mention the topic
        assert 'horus' in response.lower() or 'heresy' in response.lower()
        
        # Should include suggestions
        assert 'Suggested' in response or 'Try' in response
    
    def test_no_results_with_unavailable_store(self):
        """Test response when doc_store is unavailable."""
        response = generate_no_results_response(
            "test query",
            doc_store_status="connection_error"
        )
        
        # Should mention system issues
        assert 'system' in response.lower() or 'issues' in response.lower()
    
    def test_no_results_helpful_not_generic(self):
        """Test that response is helpful, not generic."""
        response = generate_no_results_response("emperor primarchs")
        
        # Should NOT be the old generic message
        assert response != "No relevant training documents found for query: emperor primarchs"
        
        # Should provide actionable guidance
        assert len(response) > 100  # Should be substantive


class TestSnippetExtraction:
    """Test relevant snippet extraction from documents."""
    
    def test_extract_snippets_basic(self):
        """Test basic snippet extraction."""
        query = "horus heresy"
        docs = [
            {
                'id': 'doc1',
                'content': 'The Horus Heresy was a galaxy-spanning civil war.\n\nIt started when Horus betrayed the Emperor.',
                'metadata': {'source_url': 'test.com'}
            }
        ]
        
        snippets = extract_relevant_snippets(query, docs, max_snippets=2)
        
        # Should extract relevant paragraphs
        assert len(snippets) > 0
        assert snippets[0]['doc_id'] == 'doc1'
        assert 'Horus' in snippets[0]['content']
    
    def test_extract_snippets_relevance_scoring(self):
        """Test that snippets are scored by keyword matches."""
        query = "horus emperor betrayal"
        docs = [
            {
                'id': 'doc1',
                'content': 'The Emperor created the Primarchs.\n\nHorus betrayed the Emperor during the heresy.',
                'metadata': {}
            }
        ]
        
        snippets = extract_relevant_snippets(query, docs, max_snippets=2)
        
        # Second paragraph should score higher (has all 3 keywords)
        assert len(snippets) > 0
        # Most relevant snippet should come first
        assert snippets[0]['relevance'] > 0
    
    def test_extract_snippets_truncates_long_paragraphs(self):
        """Test that long paragraphs are truncated."""
        query = "test"
        docs = [
            {
                'id': 'doc1',
                'content': 'test ' * 200,  # Very long paragraph
                'metadata': {}
            }
        ]
        
        snippets = extract_relevant_snippets(query, docs, max_snippets=1)
        
        # Should be truncated
        assert len(snippets) > 0
        assert len(snippets[0]['content']) <= 504  # 500 + '...'


class TestSynthesisResponse:
    """Test full response synthesis."""
    
    def test_synthesis_with_documents(self):
        """Test synthesis when documents are found."""
        query = "Tell me about the Horus Heresy"
        docs = [
            {
                'id': 'doc1',
                'content': 'The Horus Heresy was a civil war in the 31st millennium.\n\nHorus Lupercal betrayed the Emperor.',
                'metadata': {'source_url': 'wiki.com'}
            }
        ]
        
        result = generate_synthesis_response(query, docs, confidence=0.85)
        
        # Should have required fields
        assert 'answer' in result
        assert 'sources' in result
        assert 'confidence' in result
        assert 'intent' in result
        
        # Answer should include content
        assert len(result['answer']) > 0
        assert 'Horus' in result['answer'] or 'heresy' in result['answer'].lower()
        
        # Should identify intent
        assert result['intent'] == 'overview'
    
    def test_synthesis_intent_based_intro(self):
        """Test that intro varies by intent."""
        docs = [{'id': 'd1', 'content': 'Content here.', 'metadata': {}}]
        
        overview_result = generate_synthesis_response("What is X?", docs, 0.8)
        causation_result = generate_synthesis_response("Why did X happen?", docs, 0.8)
        
        # Intros should be different
        assert overview_result['intent'] == 'overview'
        assert causation_result['intent'] == 'causation'


class TestContextualResponse:
    """Test end-to-end contextual response generation."""
    
    def test_contextual_response_no_documents(self):
        """Test response when no documents found."""
        result = generate_contextual_response("test query", [], "available")
        
        assert 'answer' in result
        assert 'confidence' in result
        assert result['confidence'] == 0.0
        
        # Should be helpful, not generic
        assert "couldn't find" in result['answer'].lower() or "no" in result['answer'].lower()
        assert len(result['answer']) > 50
    
    def test_contextual_response_with_documents(self):
        """Test response when documents are found."""
        docs = [
            {'id': 'd1', 'content': 'The Horus Heresy was a civil war.', 'metadata': {}},
            {'id': 'd2', 'content': 'Horus betrayed the Emperor.', 'metadata': {}},
            {'id': 'd3', 'content': 'The war lasted for years.', 'metadata': {}}
        ]
        
        result = generate_contextual_response("Tell me about Horus Heresy", docs)
        
        assert result['confidence'] == 0.85  # Good confidence with 3+ docs
        assert len(result['answer']) > 0
        assert len(result['sources']) > 0
    
    def test_contextual_response_low_confidence(self):
        """Test response with only 1-2 documents."""
        docs = [{'id': 'd1', 'content': 'Content.', 'metadata': {}}]
        
        result = generate_contextual_response("test", docs)
        
        assert result['confidence'] == 0.5  # Low confidence with few docs
    
    def test_contextual_response_doc_store_error(self):
        """Test response when doc_store has error."""
        result = generate_contextual_response("test", [], "connection_error")
        
        assert result['confidence'] == 0.0
        assert 'system' in result['answer'].lower() or 'unavailable' in result['answer'].lower()


@pytest.mark.integration
class TestResponseGeneratorIntegration:
    """Integration tests for full response generation flow."""
    
    def test_full_flow_no_results(self):
        """Test full flow when search returns nothing."""
        result = generate_contextual_response(
            "Tell me about the Horus Heresy",
            [],
            "available"
        )
        
        # Should be contextual and helpful
        assert result['confidence'] == 0.0
        assert 'Suggested' in result['answer'] or 'Try' in result['answer']
        assert result['intent'] == 'overview'
    
    def test_full_flow_good_results(self):
        """Test full flow with good search results."""
        docs = [
            {
                'id': 'fandom-123',
                'content': 'The Horus Heresy was a galaxy-spanning civil war.\n\nHorus Lupercal, the Warmaster, betrayed the Emperor of Mankind.',
                'metadata': {'source_url': 'https://warhammer40k.fandom.com/wiki/Horus_Heresy'}
            },
            {
                'id': 'fandom-456',
                'content': 'The traitor legions followed Horus.\n\nThe loyalist legions defended Terra.',
                'metadata': {'source_url': 'https://warhammer40k.fandom.com/wiki/Traitor_Legions'}
            }
        ]
        
        result = generate_contextual_response(
            "Tell me about the Horus Heresy",
            docs,
            "available"
        )
        
        # Should have high confidence
        assert result['confidence'] == 0.85
        
        # Should include relevant content
        assert 'Horus' in result['answer']
        
        # Should have sources
        assert len(result['sources']) > 0
        
        # Should classify intent correctly
        assert result['intent'] == 'overview'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

