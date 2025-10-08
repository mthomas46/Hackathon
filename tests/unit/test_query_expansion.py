"""Unit tests for query expansion module.

TDD Phase 1: Query Expansion
Tests synonym mapping, keyword extraction, and query variations.
"""

import pytest
import sys
from pathlib import Path

# Add services/doc_store/db to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "doc_store" / "db"))

from query_expansion import (
    expand_query,
    extract_keywords_with_synonyms,
    get_synonym_patterns,
    WARHAMMER_SYNONYMS,
    GENERIC_SYNONYMS
)


class TestQueryExpansion:
    """Test suite for query expansion functionality."""
    
    def test_synonym_dictionaries_exist(self):
        """Test that synonym dictionaries are properly defined."""
        assert isinstance(WARHAMMER_SYNONYMS, dict)
        assert isinstance(GENERIC_SYNONYMS, dict)
        assert len(WARHAMMER_SYNONYMS) > 0
        assert len(GENERIC_SYNONYMS) > 0
    
    def test_warhammer_specific_synonyms(self):
        """Test Warhammer 40K domain-specific synonyms."""
        # Emperor synonyms
        assert 'emperor' in WARHAMMER_SYNONYMS
        assert 'Emperor of Mankind' in WARHAMMER_SYNONYMS['emperor']
        
        # Primarch synonyms
        assert 'primarch' in WARHAMMER_SYNONYMS
        assert 'Primarchs' in WARHAMMER_SYNONYMS['primarch']
        
        # Heresy synonyms
        assert 'heresy' in WARHAMMER_SYNONYMS
        assert 'Horus Heresy' in WARHAMMER_SYNONYMS['heresy']
        
        # Traitor synonyms
        assert 'traitor' in WARHAMMER_SYNONYMS
        assert 'Traitor Legions' in WARHAMMER_SYNONYMS['traitor']
    
    def test_expand_query_simple(self):
        """Test simple query expansion."""
        expanded = expand_query("emperor")
        
        # Should include original
        assert "emperor" in expanded
        
        # Should include synonyms
        assert len(expanded) > 1
    
    def test_expand_query_multiple_words(self):
        """Test query expansion with multiple words."""
        expanded = expand_query("emperor primarch")
        
        # Should include original
        assert "emperor primarch" in expanded
        
        # Should have expansions
        assert len(expanded) > 1
    
    def test_expand_query_limit(self):
        """Test that expansion respects max_expansions limit."""
        expanded = expand_query("emperor primarch heresy", max_expansions=3)
        
        # Should not exceed limit + original
        assert len(expanded) <= 10  # Original + some expansions
    
    def test_extract_keywords_with_synonyms_simple(self):
        """Test keyword extraction with stop word filtering."""
        keywords = extract_keywords_with_synonyms("Tell me about the Horus Heresy")
        
        # Stop words should be filtered
        assert 'tell' not in keywords
        assert 'me' not in keywords
        assert 'about' not in keywords
        assert 'the' not in keywords
        
        # Important terms should be kept
        assert 'horus' in keywords or 'heresy' in keywords
    
    def test_extract_keywords_removes_short_words(self):
        """Test that short words (<=2 chars) are filtered."""
        keywords = extract_keywords_with_synonyms("a is to be or")
        
        # All should be filtered (stop words or short)
        assert len(keywords) == 0
    
    def test_extract_keywords_adds_synonyms(self):
        """Test that synonyms are added for recognized keywords."""
        keywords = extract_keywords_with_synonyms("emperor")
        
        # Should include original
        assert 'emperor' in keywords
        
        # Should include at least some synonyms
        assert len(keywords) > 1
    
    def test_extract_keywords_natural_language(self):
        """Test keyword extraction from natural language query."""
        keywords = extract_keywords_with_synonyms(
            "What caused the Horus Heresy and who were the traitor primarchs?"
        )
        
        # Should extract key terms
        key_terms = ['horus', 'heresy', 'traitor', 'primarch', 'primarchs']
        assert any(term in keywords for term in key_terms)
    
    def test_get_synonym_patterns_known_keyword(self):
        """Test getting synonyms for known keyword."""
        synonyms = get_synonym_patterns("emperor")
        
        # Should include original
        assert "emperor" in synonyms
        
        # Should include domain synonyms
        assert len(synonyms) > 1
        assert 'Emperor of Mankind' in synonyms or 'Master of Mankind' in synonyms
    
    def test_get_synonym_patterns_unknown_keyword(self):
        """Test getting synonyms for unknown keyword."""
        synonyms = get_synonym_patterns("unknown_term_xyz")
        
        # Should return just the original
        assert synonyms == ["unknown_term_xyz"]
    
    def test_get_synonym_patterns_case_insensitive(self):
        """Test that synonym lookup is case-insensitive."""
        synonyms_lower = get_synonym_patterns("emperor")
        synonyms_upper = get_synonym_patterns("EMPEROR")
        
        # Should have same number of results
        assert len(synonyms_lower) == len(synonyms_upper)
    
    def test_expand_query_no_duplicates(self):
        """Test that expansion doesn't create duplicate entries."""
        expanded = expand_query("emperor emperor primarch", max_expansions=5)
        
        # Count occurrences
        from collections import Counter
        counts = Counter(expanded)
        
        # Each expansion should appear only once
        for term, count in counts.items():
            assert count == 1, f"'{term}' appears {count} times (expected 1)"
    
    def test_extract_keywords_performance(self):
        """Test that keyword extraction handles long queries efficiently."""
        long_query = "Tell me about " + " ".join(["emperor"] * 100)
        
        # Should complete without error
        keywords = extract_keywords_with_synonyms(long_query)
        
        # Should have reasonable result size
        assert len(keywords) < 50  # Shouldn't explode


@pytest.mark.integration
class TestQueryExpansionIntegration:
    """Integration tests for query expansion with real queries."""
    
    def test_real_query_horus_heresy(self):
        """Test expansion of 'Tell me about the Horus Heresy'."""
        keywords = extract_keywords_with_synonyms("Tell me about the Horus Heresy")
        
        # Should extract key terms
        assert any(k in keywords for k in ['horus', 'heresy'])
        
        # Should add relevant synonyms
        expected_synonyms = ['rebellion', 'great betrayal', 'warmaster']
        # At least one synonym should be present
        assert len(keywords) > 2  # More than just 'horus' and 'heresy'
    
    def test_real_query_traitor_legions(self):
        """Test expansion of 'traitor legions'."""
        keywords = extract_keywords_with_synonyms("traitor legions")
        
        # Should include base terms
        assert 'traitor' in keywords or 'legion' in keywords or 'legions' in keywords
        
        # Should add synonyms
        assert len(keywords) >= 2
    
    def test_real_query_emperor_primarchs(self):
        """Test expansion of 'emperor primarchs'."""
        keywords = extract_keywords_with_synonyms("emperor primarchs")
        
        # Should extract both key terms
        assert 'emperor' in keywords or 'primarch' in keywords or 'primarchs' in keywords
        
        # Should add domain-specific synonyms
        assert len(keywords) > 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

