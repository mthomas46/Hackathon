"""
Unit tests for DocumentFinder.

Tests multi-strategy document search and ranking.
"""

import pytest
from datetime import datetime
from src.services.dynamic_rag.document_finder import (
    DocumentFinder, RelevantDocument
)


@pytest.mark.asyncio
class TestDocumentFinderSearch:
    """Test document search functionality."""
    
    async def test_find_with_single_term(self):
        """Test finding documents with single search term."""
        finder = DocumentFinder()
        
        # This may return empty list if no documents in DB, but should not crash
        result = await finder.find_relevant_documents(
            search_terms=["authentication"],
            limit=10
        )
        
        assert isinstance(result, list)
        # All results should be RelevantDocument instances
        assert all(isinstance(doc, RelevantDocument) for doc in result)
    
    async def test_find_with_multiple_terms(self):
        """Test finding documents with multiple search terms."""
        finder = DocumentFinder()
        
        result = await finder.find_relevant_documents(
            search_terms=["authentication", "jwt", "token"],
            limit=10
        )
        
        assert isinstance(result, list)
        # All results should be RelevantDocument instances
        assert all(isinstance(doc, RelevantDocument) for doc in result)
    
    async def test_find_with_service_filter(self):
        """Test finding documents filtered by service."""
        finder = DocumentFinder()
        
        result = await finder.find_relevant_documents(
            search_terms=["auth"],
            service_name="ecosystem-mcp",
            limit=10
        )
        
        assert isinstance(result, list)
    
    async def test_find_respects_limit(self):
        """Test that result limit is respected."""
        finder = DocumentFinder()
        
        result = await finder.find_relevant_documents(
            search_terms=["authentication"],
            limit=5
        )
        
        assert len(result) <= 5
    
    async def test_find_respects_min_relevance(self):
        """Test that minimum relevance filter works."""
        finder = DocumentFinder()
        
        result = await finder.find_relevant_documents(
            search_terms=["authentication"],
            min_relevance=0.8,
            limit=10
        )
        
        # All results should have relevance >= 0.8
        assert all(doc.relevance_score >= 0.8 for doc in result)


@pytest.mark.asyncio
class TestDocumentFinderScoring:
    """Test relevance scoring."""
    
    async def test_semantic_score_calculation(self):
        """Test semantic score calculation."""
        finder = DocumentFinder()
        
        content = "This document discusses JWT authentication tokens"
        search_terms = ["jwt", "authentication", "token"]
        
        score = finder._calculate_semantic_score(content, search_terms)
        
        assert 0.0 <= score <= 1.0
        # Should be high with all terms matching
        assert score >= 0.8
    
    async def test_keyword_score_calculation(self):
        """Test keyword score calculation."""
        finder = DocumentFinder()
        
        content = "Authentication service documentation"
        file_path = "docs/auth/authentication.md"
        search_terms = ["authentication"]
        
        score = finder._calculate_keyword_score(
            content, file_path, search_terms
        )
        
        assert 0.0 <= score <= 1.0
        # Should get boost for path match
        assert score > 0
    
    async def test_path_score_exact_match(self):
        """Test path score with exact match."""
        finder = DocumentFinder()
        
        file_path = "docs/authentication.md"
        search_terms = ["docs/authentication.md"]
        
        score = finder._calculate_path_score(file_path, search_terms)
        
        # Exact match should give score of 1.0
        assert score == 1.0
    
    async def test_path_score_partial_match(self):
        """Test path score with partial match."""
        finder = DocumentFinder()
        
        file_path = "docs/auth/authentication.md"
        search_terms = ["authentication"]
        
        score = finder._calculate_path_score(file_path, search_terms)
        
        # Partial match should give some score
        assert 0.0 < score <= 1.0


@pytest.mark.asyncio
class TestDocumentFinderDeduplication:
    """Test document deduplication."""
    
    async def test_deduplicate_removes_duplicates(self):
        """Test that duplicates are removed."""
        finder = DocumentFinder()
        
        docs = [
            RelevantDocument(
                document_id="doc1",
                file_path="/path/to/file.md",
                content="Content",
                relevance_score=0.8,
                commit_count=10,
                last_modified=datetime.utcnow(),
                ingestion_mode="git_history",
                matched_topics=[]
            ),
            RelevantDocument(
                document_id="doc1",  # Duplicate
                file_path="/path/to/file.md",
                content="Content",
                relevance_score=0.9,  # Higher score
                commit_count=10,
                last_modified=datetime.utcnow(),
                ingestion_mode="git_history",
                matched_topics=[]
            )
        ]
        
        result = finder._deduplicate(docs)
        
        # Should only have one document
        assert len(result) == 1
        # Should keep the one with higher score
        assert result[0].relevance_score == 0.9
    
    async def test_deduplicate_keeps_unique(self):
        """Test that unique documents are kept."""
        finder = DocumentFinder()
        
        docs = [
            RelevantDocument(
                document_id="doc1",
                file_path="/file1.md",
                content="Content 1",
                relevance_score=0.8,
                commit_count=10,
                last_modified=datetime.utcnow(),
                ingestion_mode="git_history",
                matched_topics=[]
            ),
            RelevantDocument(
                document_id="doc2",
                file_path="/file2.md",
                content="Content 2",
                relevance_score=0.7,
                commit_count=5,
                last_modified=datetime.utcnow(),
                ingestion_mode="snapshot",
                matched_topics=[]
            )
        ]
        
        result = finder._deduplicate(docs)
        
        # Should keep both documents
        assert len(result) == 2


@pytest.mark.asyncio
class TestDocumentFinderRanking:
    """Test document ranking."""
    
    async def test_rank_by_git_history(self):
        """Test ranking boost for documents with git history."""
        finder = DocumentFinder()
        
        docs = [
            RelevantDocument(
                document_id="doc1",
                file_path="/file1.md",
                content="Content",
                relevance_score=0.5,
                commit_count=100,  # High commit count
                last_modified=datetime.utcnow(),
                ingestion_mode="git_history",
                matched_topics=[]
            ),
            RelevantDocument(
                document_id="doc2",
                file_path="/file2.md",
                content="Content",
                relevance_score=0.5,
                commit_count=0,  # No commits
                last_modified=datetime.utcnow(),
                ingestion_mode="snapshot",
                matched_topics=[]
            )
        ]
        
        result = await finder.rank_by_git_history(docs)
        
        # Doc with more commits should rank higher
        assert result[0].relevance_score > result[1].relevance_score
        assert result[0].document_id == "doc1"


@pytest.mark.asyncio
class TestDocumentFinderEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_empty_search_terms(self):
        """Test handling empty search terms."""
        finder = DocumentFinder()
        
        result = await finder.find_relevant_documents(
            search_terms=[],
            limit=10
        )
        
        assert isinstance(result, list)
    
    async def test_zero_limit(self):
        """Test handling zero limit."""
        finder = DocumentFinder()
        
        result = await finder.find_relevant_documents(
            search_terms=["test"],
            limit=0
        )
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    async def test_min_relevance_zero(self):
        """Test min relevance of 0.0."""
        finder = DocumentFinder()
        
        result = await finder.find_relevant_documents(
            search_terms=["test"],
            min_relevance=0.0,
            limit=10
        )
        
        assert isinstance(result, list)
    
    async def test_min_relevance_one(self):
        """Test min relevance of 1.0 (very strict)."""
        finder = DocumentFinder()
        
        result = await finder.find_relevant_documents(
            search_terms=["test"],
            min_relevance=1.0,
            limit=10
        )
        
        assert isinstance(result, list)
        # All results should have perfect score
        assert all(doc.relevance_score == 1.0 for doc in result)


@pytest.mark.asyncio
class TestDocumentFinderMatching:
    """Test topic matching functionality."""
    
    async def test_get_matched_topics_single(self):
        """Test getting matched topics with single match."""
        finder = DocumentFinder()
        
        text = "This is about authentication with JWT tokens"
        search_terms = ["authentication"]
        
        matched = finder._get_matched_topics(text, search_terms)
        
        assert "authentication" in matched
    
    async def test_get_matched_topics_multiple(self):
        """Test getting matched topics with multiple matches."""
        finder = DocumentFinder()
        
        text = "Authentication service using JWT and OAuth2"
        search_terms = ["authentication", "jwt", "oauth2"]
        
        matched = finder._get_matched_topics(text, search_terms)
        
        assert "authentication" in matched
        assert "jwt" in matched
    
    async def test_get_matched_topics_none(self):
        """Test getting matched topics with no matches."""
        finder = DocumentFinder()
        
        text = "Something completely different"
        search_terms = ["nonexistent", "missing"]
        
        matched = finder._get_matched_topics(text, search_terms)
        
        assert len(matched) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

