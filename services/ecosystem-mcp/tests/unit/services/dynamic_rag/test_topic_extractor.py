"""
Unit tests for TopicExtractor.

Tests extraction of 6 topic types from natural language queries.
"""

import pytest
from src.services.dynamic_rag.topic_extractor import (
    TopicExtractor, ExtractedTopics, TopicType, ExtractedTopic
)


class TestTopicExtractorEndpoints:
    """Test endpoint extraction."""
    
    def test_extract_single_endpoint(self):
        """Test extracting a single API endpoint."""
        extractor = TopicExtractor()
        query = "Why does the /api/auth endpoint require authentication?"
        
        result = extractor.extract(query)
        
        assert "/api/auth" in result.endpoints
        assert len(result.endpoints) == 1
    
    def test_extract_multiple_endpoints(self):
        """Test extracting multiple endpoints."""
        extractor = TopicExtractor()
        query = "Compare /api/auth and /api/users endpoints"
        
        result = extractor.extract(query)
        
        assert "/api/auth" in result.endpoints
        assert "/api/users" in result.endpoints
    
    def test_extract_nested_endpoints(self):
        """Test extracting nested path endpoints."""
        extractor = TopicExtractor()
        query = "How does /api/v1/documents/search work?"
        
        result = extractor.extract(query)
        
        assert "/api/v1/documents/search" in result.endpoints


class TestTopicExtractorParameters:
    """Test parameter extraction."""
    
    def test_extract_quoted_parameter(self):
        """Test extracting parameter in quotes."""
        extractor = TopicExtractor()
        query = "Why does it need a 'refresh_token' parameter?"
        
        result = extractor.extract(query)
        
        assert "refresh_token" in result.parameters
    
    def test_extract_snake_case_parameter(self):
        """Test extracting snake_case parameter."""
        extractor = TopicExtractor()
        query = "What is access_token used for?"
        
        result = extractor.extract(query)
        
        assert "access_token" in result.parameters
    
    def test_extract_camelCase_parameter(self):
        """Test extracting camelCase parameter."""
        extractor = TopicExtractor()
        query = "How does refreshToken work?"
        
        result = extractor.extract(query)
        
        assert "refreshtoken" in result.parameters or "refreshToken" in result.parameters


class TestTopicExtractorServices:
    """Test service identification."""
    
    def test_extract_service_with_keyword(self):
        """Test extracting service with 'service' keyword."""
        extractor = TopicExtractor()
        query = "How does the authentication service work?"
        
        result = extractor.extract(query)
        
        assert "authentication" in result.services
    
    def test_extract_implicit_service(self):
        """Test extracting service without explicit keyword."""
        extractor = TopicExtractor()
        query = "Tell me about authentication"
        
        result = extractor.extract(query)
        
        assert "authentication" in result.services


class TestTopicExtractorTechnologies:
    """Test technology recognition."""
    
    def test_extract_known_technology(self):
        """Test extracting known technology."""
        extractor = TopicExtractor()
        query = "How does JWT authentication work?"
        
        result = extractor.extract(query)
        
        assert "jwt" in result.technologies
    
    def test_extract_multiple_technologies(self):
        """Test extracting multiple technologies."""
        extractor = TopicExtractor()
        query = "Does it use JWT or OAuth2?"
        
        result = extractor.extract(query)
        
        assert "jwt" in result.technologies
        assert "oauth" in result.technologies or "oauth2" in result.technologies


class TestTopicExtractorFilePaths:
    """Test file path detection."""
    
    def test_extract_python_file(self):
        """Test extracting Python file path."""
        extractor = TopicExtractor()
        query = "What's in src/api/auth.py?"
        
        result = extractor.extract(query)
        
        assert "src/api/auth.py" in result.file_paths
    
    def test_extract_markdown_file(self):
        """Test extracting markdown file path."""
        extractor = TopicExtractor()
        query = "Read docs/authentication.md"
        
        result = extractor.extract(query)
        
        assert "docs/authentication.md" in result.file_paths


class TestTopicExtractorConcepts:
    """Test concept extraction."""
    
    def test_extract_why_question_concepts(self):
        """Test concepts from 'why' questions."""
        extractor = TopicExtractor()
        query = "Why does authentication use tokens?"
        
        result = extractor.extract(query)
        
        assert "rationale" in result.concepts or "design decision" in result.concepts
    
    def test_extract_how_question_concepts(self):
        """Test concepts from 'how' questions."""
        extractor = TopicExtractor()
        query = "How does token refresh work?"
        
        result = extractor.extract(query)
        
        assert "implementation" in result.concepts or "workflow" in result.concepts


class TestTopicExtractorConfidence:
    """Test confidence scoring."""
    
    def test_confidence_with_endpoints(self):
        """Test confidence with endpoint detection."""
        extractor = TopicExtractor()
        query = "Explain /api/auth endpoint with JWT token"
        
        result = extractor.extract(query)
        
        # Should have high confidence with endpoint + technology
        assert result.confidence > 0.5
    
    def test_confidence_vague_query(self):
        """Test confidence with vague query."""
        extractor = TopicExtractor()
        query = "Tell me about something"
        
        result = extractor.extract(query)
        
        # Should have low confidence (may be 0 if no topics found)
        assert result.confidence < 0.8


class TestTopicExtractorSearchTerms:
    """Test search term generation."""
    
    def test_get_search_terms(self):
        """Test converting topics to search terms."""
        extractor = TopicExtractor()
        query = "Why does /api/auth need refresh_token?"
        
        result = extractor.extract(query)
        search_terms = extractor.get_search_terms(result)
        
        assert "/api/auth" in search_terms
        assert "refresh_token" in search_terms
        assert len(search_terms) > 0


class TestTopicExtractorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_query(self):
        """Test handling empty query."""
        extractor = TopicExtractor()
        query = ""
        
        result = extractor.extract(query)
        
        assert isinstance(result, ExtractedTopics)
        assert result.confidence >= 0
    
    def test_very_long_query(self):
        """Test handling very long query."""
        extractor = TopicExtractor()
        query = "How does authentication work? " * 100
        
        result = extractor.extract(query)
        
        assert isinstance(result, ExtractedTopics)
    
    def test_special_characters(self):
        """Test handling special characters."""
        extractor = TopicExtractor()
        query = "What about @#$%^&*() endpoint?"
        
        result = extractor.extract(query)
        
        assert isinstance(result, ExtractedTopics)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

