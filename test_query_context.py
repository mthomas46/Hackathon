"""
Unit tests for QueryContext.

Tests query context state management.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services/ecosystem-mcp/src'))

import pytest
from services.rag.enhancements import QueryContext


class TestQueryContext:
    """Test QueryContext class."""
    
    def test_creation(self):
        """Test basic creation."""
        context = QueryContext(original_query="How does authentication work?")
        
        assert context.original_query == "How does authentication work?"
        assert context.rewritten_query is None
        assert context.query_variants == []
        assert context.intent is None
        assert context.difficulty is None
    
    def test_get_primary_query_original(self):
        """Test get_primary_query returns original when no rewrite."""
        context = QueryContext(original_query="test query")
        
        assert context.get_primary_query() == "test query"
    
    def test_get_primary_query_rewritten(self):
        """Test get_primary_query returns rewritten when available."""
        context = QueryContext(
            original_query="test query",
            rewritten_query="expanded test query"
        )
        
        assert context.get_primary_query() == "expanded test query"
    
    def test_get_n_results_default(self):
        """Test get_n_results returns default when no adaptive."""
        context = QueryContext(original_query="test")
        
        assert context.get_n_results(10) == 10
    
    def test_get_n_results_adaptive(self):
        """Test get_n_results returns adaptive when set."""
        context = QueryContext(
            original_query="test",
            adaptive_n_results=15
        )
        
        assert context.get_n_results(10) == 15
    
    def test_get_strategy_default(self):
        """Test get_strategy returns default when no adaptive."""
        context = QueryContext(original_query="test")
        
        assert context.get_strategy("balanced") == "balanced"
    
    def test_get_strategy_adaptive(self):
        """Test get_strategy returns adaptive when set."""
        context = QueryContext(
            original_query="test",
            adaptive_strategy="quality_first"
        )
        
        assert context.get_strategy("balanced") == "quality_first"
    
    def test_should_enable_reranking_default(self):
        """Test should_enable_reranking returns default when no adaptive."""
        context = QueryContext(original_query="test")
        
        assert context.should_enable_reranking(False) is False
        assert context.should_enable_reranking(True) is True
    
    def test_should_enable_reranking_adaptive(self):
        """Test should_enable_reranking returns adaptive when set."""
        context = QueryContext(
            original_query="test",
            adaptive_enable_reranking=True
        )
        
        assert context.should_enable_reranking(False) is True
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        context = QueryContext(
            original_query="test query",
            rewritten_query="expanded query",
            query_variants=["variant1", "variant2"],
            intent={"type": "factual", "complexity": "simple"},
            difficulty={"difficulty_level": "easy", "difficulty_score": 20}
        )
        
        context_dict = context.to_dict()
        
        assert isinstance(context_dict, dict)
        assert context_dict["original_query"] == "test query"
        assert context_dict["rewritten_query"] == "expanded query"
        assert len(context_dict["query_variants"]) == 2
        assert context_dict["intent"]["type"] == "factual"
        assert context_dict["difficulty"]["difficulty_level"] == "easy"
    
    def test_custom_data(self):
        """Test custom data storage."""
        context = QueryContext(original_query="test")
        context.custom_data["temporal_date"] = "2025-01-01"
        context.custom_data["context_id"] = "abc123"
        
        assert context.custom_data["temporal_date"] == "2025-01-01"
        assert context.custom_data["context_id"] == "abc123"
    
    def test_metadata_filters(self):
        """Test metadata filters storage."""
        context = QueryContext(original_query="test")
        context.metadata_filters["quality_score"] = {"$gte": 50}
        context.metadata_filters["git_date"] = {"$lte": 1234567890}
        
        assert "quality_score" in context.metadata_filters
        assert "git_date" in context.metadata_filters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

