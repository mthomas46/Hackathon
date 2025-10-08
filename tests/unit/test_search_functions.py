"""Unit tests for multi-tier search functions.

TDD Phase 3: Multi-tier Search
Tests tag search, metadata search, FTS search, and relevance scoring.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add services/doc_store/db to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "doc_store" / "db"))

from queries import (
    search_documents,
    _search_by_tags,
    _search_by_metadata,
    _fetch_documents_with_score
)


class TestSearchByTags:
    """Test tag-based search with relevance scoring."""
    
    @patch('queries.execute_query')
    def test_search_by_tags_basic(self, mock_execute):
        """Test basic tag search."""
        mock_execute.return_value = [
            {'rowid': 1, 'relevance_score': 10},
            {'rowid': 2, 'relevance_score': 8}
        ]
        
        keywords = ['horus', 'heresy']
        results = _search_by_tags(keywords, limit=10)
        
        # Should call execute_query
        assert mock_execute.called
        
        # Should return results
        assert len(results) == 2
        assert results[0]['relevance_score'] == 10
    
    @patch('queries.execute_query')
    def test_search_by_tags_relevance_scoring(self, mock_execute):
        """Test that earlier keywords get higher weights."""
        mock_execute.return_value = []
        
        keywords = ['first', 'second', 'third']
        _search_by_tags(keywords, limit=10)
        
        # Get the SQL query from the call
        call_args = mock_execute.call_args
        sql_query = call_args[0][0]
        
        # First keyword should have higher weight (10)
        # Second should have 8, third should have 6
        assert 'THEN 10' in sql_query  # First keyword weight
        assert 'THEN 8' in sql_query   # Second keyword weight
        assert 'THEN 6' in sql_query   # Third keyword weight
    
    def test_search_by_tags_empty_keywords(self):
        """Test tag search with no keywords."""
        results = _search_by_tags([], limit=10)
        
        # Should return empty
        assert results == []
    
    @patch('queries.execute_query')
    def test_search_by_tags_filters_empty_tags(self, mock_execute):
        """Test that search excludes documents with empty tags."""
        mock_execute.return_value = []
        
        _search_by_tags(['test'], limit=10)
        
        call_args = mock_execute.call_args
        sql_query = call_args[0][0]
        
        # Should filter out NULL and empty array tags
        assert "tags IS NOT NULL" in sql_query
        assert "tags != '[]'" in sql_query


class TestSearchByMetadata:
    """Test metadata-based search with relevance scoring."""
    
    @patch('queries.execute_query')
    def test_search_by_metadata_basic(self, mock_execute):
        """Test basic metadata search."""
        mock_execute.return_value = [
            {'rowid': 1, 'relevance_score': 7},
            {'rowid': 2, 'relevance_score': 6}
        ]
        
        keywords = ['source', 'fandom']
        results = _search_by_metadata(keywords, limit=10)
        
        assert mock_execute.called
        assert len(results) == 2
    
    @patch('queries.execute_query')
    def test_search_by_metadata_lower_weights_than_tags(self, mock_execute):
        """Test that metadata has lower weights than tags."""
        mock_execute.return_value = []
        
        keywords = ['first', 'second']
        _search_by_metadata(keywords, limit=10)
        
        call_args = mock_execute.call_args
        sql_query = call_args[0][0]
        
        # First keyword in metadata should be weight 7 (vs 10 for tags)
        assert 'THEN 7' in sql_query
        assert 'THEN 6' in sql_query
    
    def test_search_by_metadata_empty_keywords(self):
        """Test metadata search with no keywords."""
        results = _search_by_metadata([], limit=10)
        assert results == []


class TestFetchDocumentsWithScore:
    """Test fetching and scoring documents."""
    
    @patch('queries.execute_query')
    def test_fetch_documents_with_score_basic(self, mock_execute):
        """Test fetching documents and adding scores."""
        scored_results = [
            {'rowid': 1, 'relevance_score': 10},
            {'rowid': 2, 'relevance_score': 8}
        ]
        
        mock_execute.return_value = [
            {'rowid': 1, 'id': 'doc1', 'content': 'content1'},
            {'rowid': 2, 'id': 'doc2', 'content': 'content2'}
        ]
        
        documents = _fetch_documents_with_score(scored_results, limit=10)
        
        # Should add relevance scores
        assert len(documents) == 2
        assert documents[0]['relevance_score'] == 10
        assert documents[1]['relevance_score'] == 8
    
    @patch('queries.execute_query')
    def test_fetch_documents_sorts_by_relevance(self, mock_execute):
        """Test that documents are sorted by relevance score."""
        scored_results = [
            {'rowid': 1, 'relevance_score': 5},
            {'rowid': 2, 'relevance_score': 10},
            {'rowid': 3, 'relevance_score': 8}
        ]
        
        mock_execute.return_value = [
            {'rowid': 1, 'id': 'doc1', 'content': 'content1'},
            {'rowid': 2, 'id': 'doc2', 'content': 'content2'},
            {'rowid': 3, 'id': 'doc3', 'content': 'content3'}
        ]
        
        documents = _fetch_documents_with_score(scored_results, limit=10)
        
        # Should be sorted by relevance (highest first)
        assert documents[0]['relevance_score'] == 10
        assert documents[1]['relevance_score'] == 8
        assert documents[2]['relevance_score'] == 5
    
    def test_fetch_documents_empty_results(self):
        """Test fetching with empty scored results."""
        documents = _fetch_documents_with_score([], limit=10)
        assert documents == []


class TestMultiTierSearch:
    """Test the multi-tier search strategy."""
    
    @patch('queries._search_by_tags')
    @patch('queries._fetch_documents_with_score')
    def test_search_uses_tags_first(self, mock_fetch, mock_tags):
        """Test that tag search is tried first."""
        # Mock tag search returning results
        mock_tags.return_value = [{'rowid': 1, 'relevance_score': 10}]
        mock_fetch.return_value = [{'id': 'doc1', 'content': 'content'}]
        
        results = search_documents("test query", limit=10)
        
        # Tag search should be called
        assert mock_tags.called
        
        # Should return results from tags
        assert len(results) > 0
    
    @patch('queries._search_by_tags')
    @patch('queries._search_by_metadata')
    @patch('queries._fetch_documents_with_score')
    def test_search_falls_back_to_metadata(self, mock_fetch, mock_metadata, mock_tags):
        """Test fallback to metadata when tags return nothing."""
        # Mock tag search returning empty
        mock_tags.return_value = []
        
        # Mock metadata returning results
        mock_metadata.return_value = [{'rowid': 1, 'relevance_score': 7}]
        mock_fetch.return_value = [{'id': 'doc1', 'content': 'content'}]
        
        results = search_documents("test query", limit=10)
        
        # Both should be called
        assert mock_tags.called
        assert mock_metadata.called
        
        # Should use metadata results
        assert len(results) > 0
    
    @patch('queries._search_by_tags')
    @patch('queries._search_by_metadata')
    @patch('queries.execute_query')
    def test_search_falls_back_to_fts(self, mock_execute, mock_metadata, mock_tags):
        """Test fallback to FTS when tags and metadata return nothing."""
        # Mock tag and metadata returning empty
        mock_tags.return_value = []
        mock_metadata.return_value = []
        
        # Mock FTS returning results
        mock_execute.return_value = [{'rowid': 1}]
        
        results = search_documents("test query", limit=10)
        
        # FTS execute_query should be called
        assert mock_execute.called
    
    @patch('queries._search_by_tags')
    @patch('queries._search_by_metadata')
    @patch('queries.execute_query')
    def test_search_ultimate_fallback_to_like(self, mock_execute, mock_metadata, mock_tags):
        """Test ultimate fallback to LIKE search."""
        # Mock everything returning empty except final LIKE
        mock_tags.return_value = []
        mock_metadata.return_value = []
        
        # Mock FTS returning empty, then LIKE returning results
        mock_execute.side_effect = [
            [],  # FTS result
            [{'rowid': 1}],  # LIKE rowids
            [{'rowid': 1, 'id': 'doc1', 'content': 'content'}]  # Final fetch
        ]
        
        results = search_documents("test query", limit=10)
        
        # Should have tried multiple times
        assert mock_execute.call_count >= 2
    
    def test_search_filters_stop_words(self):
        """Test that search filters stop words from query."""
        # This should not raise an error even with all stop words
        results = search_documents("the a an is are", limit=10)
        
        # Should return empty (all stop words)
        assert results == []
    
    @patch('queries.extract_keywords_with_synonyms')
    def test_search_uses_query_expansion(self, mock_expand):
        """Test that search uses query expansion."""
        mock_expand.return_value = ['emperor', 'primarch', 'Emperor of Mankind']
        
        # Try to search (will fail due to mocking but we just want to check the call)
        try:
            search_documents("emperor primarch", limit=10)
        except:
            pass
        
        # Query expansion should be called
        assert mock_expand.called
        assert mock_expand.call_args[0][0] == "emperor primarch"


@pytest.mark.integration
class TestSearchIntegration:
    """Integration tests for search (require DB)."""
    
    def test_search_integration_placeholder(self):
        """Placeholder for integration tests that require actual DB."""
        # These will be tested in Phase 5 with actual DB connection
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

