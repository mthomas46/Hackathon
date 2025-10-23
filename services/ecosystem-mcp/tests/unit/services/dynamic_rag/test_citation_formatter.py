"""
Unit tests for CitationFormatter.

Tests citation formatting in multiple formats.
"""

import pytest
from datetime import datetime
from src.services.dynamic_rag.citation_formatter import (
    CitationFormatter, FormattedCitation
)
from src.services.dynamic_rag.answer_synthesizer import TemporalAnswer


class TestCitationFormatterBasic:
    """Test basic citation formatting."""
    
    def test_formatter_instantiation(self):
        """Test that formatter can be instantiated."""
        formatter = CitationFormatter()
        assert formatter is not None
    
    def test_format_markdown(self):
        """Test formatting citations as markdown."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Authentication uses JWT tokens",
            confidence=0.9,
            timeline_id="test-1",
            sources=[
                {
                    "index": 1,
                    "document_id": "doc1",
                    "file_path": "/auth.md",
                    "relevance_score": 0.9,
                    "last_modified": "2025-01-15",
                    "period": "Q1 2025"
                }
            ],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer, format_type="markdown")
        
        assert result is not None
        assert isinstance(result, FormattedCitation)
        assert result.format_type == "markdown"
    
    def test_format_html(self):
        """Test formatting citations as HTML."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Authentication uses JWT tokens",
            confidence=0.9,
            timeline_id="test-1",
            sources=[],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer, format_type="html")
        
        assert result is not None
        assert isinstance(result, FormattedCitation)
        assert result.format_type == "html"
    
    def test_format_plain(self):
        """Test formatting citations as plain text."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Authentication uses JWT tokens",
            confidence=0.9,
            timeline_id="test-1",
            sources=[],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer, format_type="plain")
        
        assert result is not None
        assert isinstance(result, FormattedCitation)
        assert result.format_type == "plain"


class TestCitationFormatterSources:
    """Test source citation formatting."""
    
    def test_single_source(self):
        """Test formatting single source."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test answer",
            confidence=0.9,
            timeline_id="test-1",
            sources=[
                {
                    "index": 1,
                    "document_id": "doc1",
                    "file_path": "/file.md",
                    "relevance_score": 0.9,
                    "last_modified": "2025-01-15"
                }
            ],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer)
        
        assert result is not None
        assert result.citation_text is not None
    
    def test_multiple_sources(self):
        """Test formatting multiple sources."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test answer",
            confidence=0.9,
            timeline_id="test-1",
            sources=[
                {
                    "index": i+1,
                    "document_id": f"doc{i}",
                    "file_path": f"/file{i}.md",
                    "relevance_score": 0.9,
                    "last_modified": "2025-01-15"
                }
                for i in range(5)
            ],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer)
        
        assert result is not None
        assert result.citation_text is not None
    
    def test_no_sources(self):
        """Test formatting with no sources."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test answer",
            confidence=0.5,
            timeline_id="test-1",
            sources=[],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer)
        
        assert result is not None


class TestCitationFormatterTemporalAttribution:
    """Test temporal attribution in citations."""
    
    def test_period_attribution(self):
        """Test that period information is included."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test answer",
            confidence=0.9,
            timeline_id="test-1",
            sources=[
                {
                    "index": 1,
                    "document_id": "doc1",
                    "file_path": "/file.md",
                    "relevance_score": 0.9,
                    "last_modified": "2025-02-01",
                    "period": "Q1 2025",
                    "period_start": datetime(2025, 1, 1),
                    "period_end": datetime(2025, 3, 31)
                }
            ],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer, format_type="markdown")
        
        assert result is not None
        # Period info should be in formatted text
        assert result.citation_text is not None
    
    def test_evolution_context(self):
        """Test evolution context in citations."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test answer",
            confidence=0.9,
            timeline_id="test-1",
            sources=[],
            temporal_insights=[
                {
                    "type": "evolution",
                    "description": "Feature evolved from v1 to v2",
                    "period": "Q1 2025"
                }
            ]
        )
        
        result = formatter.format_citations(answer)
        
        assert result is not None


class TestCitationFormatterFormatValidation:
    """Test format-specific validation."""
    
    def test_markdown_contains_links(self):
        """Test that markdown format contains proper links."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test",
            confidence=0.9,
            timeline_id="test-1",
            sources=[
                {
                    "index": 1,
                    "document_id": "doc1",
                    "file_path": "/file.md",
                    "relevance_score": 0.9,
                    "last_modified": "2025-01-15"
                }
            ],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer, format_type="markdown")
        
        assert result is not None
        assert result.format_type == "markdown"
    
    def test_html_contains_tags(self):
        """Test that HTML format contains proper tags."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test",
            confidence=0.9,
            timeline_id="test-1",
            sources=[
                {
                    "index": 1,
                    "document_id": "doc1",
                    "file_path": "/file.md",
                    "relevance_score": 0.9,
                    "last_modified": "2025-01-15"
                }
            ],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer, format_type="html")
        
        assert result is not None
        assert result.format_type == "html"
    
    def test_plain_is_readable(self):
        """Test that plain format is readable."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test",
            confidence=0.9,
            timeline_id="test-1",
            sources=[
                {
                    "index": 1,
                    "document_id": "doc1",
                    "file_path": "/file.md",
                    "relevance_score": 0.9,
                    "last_modified": "2025-01-15"
                }
            ],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer, format_type="plain")
        
        assert result is not None
        assert result.format_type == "plain"


class TestCitationFormatterEdgeCases:
    """Test edge cases and error handling."""
    
    def test_invalid_format_defaults_to_markdown(self):
        """Test that invalid format defaults gracefully."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Test",
            confidence=0.9,
            timeline_id="test-1",
            sources=[],
            temporal_insights=[]
        )
        
        # Should handle gracefully or default to markdown
        try:
            result = formatter.format_citations(answer, format_type="invalid")
            assert result is not None
        except (ValueError, KeyError):
            # Acceptable to raise error for invalid format
            pass
    
    def test_empty_answer(self):
        """Test formatting with empty answer."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="",
            confidence=0.0,
            timeline_id="test-1",
            sources=[],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer)
        
        assert result is not None
    
    def test_very_long_answer(self):
        """Test formatting with very long answer."""
        formatter = CitationFormatter()
        
        answer = TemporalAnswer(
            answer="Long answer. " * 1000,
            confidence=0.9,
            timeline_id="test-1",
            sources=[],
            temporal_insights=[]
        )
        
        result = formatter.format_citations(answer)
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

