"""
Unit tests for query rewriter.

Tests:
- Synonym expansion
- LLM clarification
- Query decomposition
- Complex query detection
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.rag.query_rewriter import QueryRewriter


@pytest.fixture
def query_rewriter():
    """Create query rewriter instance."""
    rewriter = QueryRewriter()
    # Mock Ollama router to avoid actual LLM calls
    rewriter.ollama_router = Mock()
    return rewriter


class TestSynonymExpansion:
    """Test synonym expansion."""
    
    def test_expand_technical_terms(self, query_rewriter):
        """Test expansion of technical terms."""
        expanded = query_rewriter._expand_with_synonyms("start ingestion")
        
        # Should contain original terms
        assert "start" in expanded.lower()
        assert "ingestion" in expanded.lower()
        
        # Should contain synonyms
        assert "OR" in expanded
    
    def test_expand_multiple_terms(self, query_rewriter):
        """Test expansion with multiple technical terms."""
        expanded = query_rewriter._expand_with_synonyms("fix slow database")
        
        assert "fix" in expanded.lower() or "repair" in expanded.lower()
        assert "slow" in expanded.lower() or "performance" in expanded.lower()
        assert "database" in expanded.lower() or "db" in expanded.lower()
    
    def test_expand_no_synonyms(self, query_rewriter):
        """Test expansion when no synonyms available."""
        expanded = query_rewriter._expand_with_synonyms("xyzabc unique term")
        
        # Should return similar to original
        assert "xyzabc" in expanded.lower()
        assert "unique" in expanded.lower()
    
    def test_expand_length_limit(self, query_rewriter):
        """Test expansion doesn't exceed length limit."""
        long_query = " ".join(["word"] * 100)
        expanded = query_rewriter._expand_with_synonyms(long_query)
        
        # Should be limited to 500 chars
        assert len(expanded) <= 500


class TestQueryClarification:
    """Test LLM-based query clarification."""
    
    @pytest.mark.asyncio
    async def test_clarify_vague_query(self, query_rewriter):
        """Test clarification of vague query."""
        query_rewriter.ollama_router.generate = AsyncMock(
            return_value="Why is document ingestion slow? What causes performance issues?"
        )
        
        clarified = await query_rewriter._clarify_with_llm("Why is it slow?")
        
        assert clarified is not None
        assert len(clarified) > len("Why is it slow?")
        assert clarified != "Why is it slow?"
    
    @pytest.mark.asyncio
    async def test_clarify_specific_query(self, query_rewriter):
        """Test clarification skips specific queries."""
        specific_query = "How does the DocumentProcessor class in processor.py handle PDF files?"
        
        clarified = await query_rewriter._clarify_with_llm(specific_query)
        
        # Should return None for already-specific queries
        assert clarified is None
    
    @pytest.mark.asyncio
    async def test_clarify_no_vague_indicators(self, query_rewriter):
        """Test clarification skips queries without vague indicators."""
        query = "How does ingestion work?"
        
        clarified = await query_rewriter._clarify_with_llm(query)
        
        # No vague pronouns, should skip
        assert clarified is None
    
    @pytest.mark.asyncio
    async def test_clarify_llm_error(self, query_rewriter):
        """Test clarification handles LLM errors."""
        query_rewriter.ollama_router.generate = AsyncMock(side_effect=Exception("LLM error"))
        
        clarified = await query_rewriter._clarify_with_llm("Why is it slow?")
        
        assert clarified is None


class TestQueryDecomposition:
    """Test query decomposition."""
    
    def test_is_complex_multiple_questions(self, query_rewriter):
        """Test detection of multiple questions."""
        assert query_rewriter._is_complex_query("How does this work? What database does it use?")
        assert query_rewriter._is_complex_query("What is X? Why is Y?")
    
    def test_is_complex_with_and(self, query_rewriter):
        """Test detection of complex queries with 'and'."""
        assert query_rewriter._is_complex_query("How does authentication work and what database does it use?")
    
    def test_is_not_complex_simple(self, query_rewriter):
        """Test simple queries not marked as complex."""
        assert not query_rewriter._is_complex_query("How does ingestion work?")
        assert not query_rewriter._is_complex_query("What is a document?")
    
    @pytest.mark.asyncio
    async def test_decompose_complex_query(self, query_rewriter):
        """Test decomposition of complex query."""
        query_rewriter.ollama_router.generate = AsyncMock(
            return_value="1. How does authentication work?\n2. What database does authentication use?"
        )
        
        sub_queries = await query_rewriter._decompose_query(
            "How does authentication work and what database does it use?"
        )
        
        assert len(sub_queries) > 0
        assert all(isinstance(q, str) for q in sub_queries)
    
    @pytest.mark.asyncio
    async def test_decompose_llm_error(self, query_rewriter):
        """Test decomposition handles LLM errors."""
        query_rewriter.ollama_router.generate = AsyncMock(side_effect=Exception("LLM error"))
        
        sub_queries = await query_rewriter._decompose_query("Complex query?")
        
        assert sub_queries == []


class TestFullRewriting:
    """Test complete rewriting pipeline."""
    
    @pytest.mark.asyncio
    async def test_rewrite_all_enabled(self, query_rewriter):
        """Test rewriting with all features enabled."""
        query_rewriter.ollama_router.generate = AsyncMock(
            return_value="Clarified query"
        )
        
        result = await query_rewriter.rewrite(
            "start job",
            enable_expansion=True,
            enable_clarification=True,
            enable_decomposition=True
        )
        
        assert "original" in result
        assert result["original"] == "start job"
        assert "search_queries" in result
        assert len(result["search_queries"]) >= 1
    
    @pytest.mark.asyncio
    async def test_rewrite_expansion_only(self, query_rewriter):
        """Test rewriting with only expansion."""
        result = await query_rewriter.rewrite(
            "start ingestion",
            enable_expansion=True,
            enable_clarification=False,
            enable_decomposition=False
        )
        
        assert result["expanded"] is not None
        assert result["clarified"] is None
        assert len(result["sub_queries"]) == 0
    
    @pytest.mark.asyncio
    async def test_rewrite_deduplicates(self, query_rewriter):
        """Test rewriting deduplicates search queries."""
        result = await query_rewriter.rewrite(
            "test query",
            enable_expansion=False,
            enable_clarification=False,
            enable_decomposition=False
        )
        
        # Should not have duplicates
        assert len(result["search_queries"]) == len(set(result["search_queries"]))
    
    @pytest.mark.asyncio
    async def test_rewrite_error_handling(self, query_rewriter):
        """Test rewriting handles errors gracefully."""
        query_rewriter.ollama_router.generate = AsyncMock(side_effect=Exception("Error"))
        
        # Should not raise, should return original query
        result = await query_rewriter.rewrite("test", enable_clarification=True)
        
        assert result["original"] == "test"
        assert "test" in result["search_queries"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

