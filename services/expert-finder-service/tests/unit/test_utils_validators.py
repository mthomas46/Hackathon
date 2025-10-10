"""
Unit tests for utils validators.

Tests validation functions for query strings, limits, IDs, etc.
"""

import pytest
from utils.validators import (
    ValidationError,
    validate_query_text,
    validate_limit,
    validate_id,
    validate_min_count,
    validate_score_threshold
)
from utils.constants import MAX_RESULTS


class TestValidators:
    """Tests for validation functions."""
    
    def test_validate_query_text_valid(self):
        """Test validating a valid query text."""
        # Should not raise
        result = validate_query_text("Python developer")
        assert result == "Python developer"
    
    def test_validate_query_text_empty(self):
        """Test that empty query text raises error."""
        with pytest.raises(ValidationError, match="Query text cannot be empty"):
            validate_query_text("")
    
    def test_validate_query_text_whitespace(self):
        """Test that whitespace-only query raises error."""
        with pytest.raises(ValidationError, match="Query text cannot be empty"):
            validate_query_text("   ")
    
    def test_validate_limit_valid(self):
        """Test validating valid limits."""
        validate_limit(1, MAX_RESULTS)
        validate_limit(10, MAX_RESULTS)
        validate_limit(MAX_RESULTS, MAX_RESULTS)
    
    def test_validate_limit_too_small(self):
        """Test that limit < 1 raises error."""
        with pytest.raises(ValidationError):
            validate_limit(0, MAX_RESULTS)
        
        with pytest.raises(ValidationError):
            validate_limit(-1, MAX_RESULTS)
    
    def test_validate_limit_too_large(self):
        """Test that limit > max raises error."""
        with pytest.raises(ValidationError):
            validate_limit(MAX_RESULTS + 1, MAX_RESULTS)
    
    def test_validate_id_valid(self):
        """Test validating valid IDs."""
        validate_id("user123")
        validate_id("abc-def-ghi")
        validate_id("12345")
    
    def test_validate_id_empty(self):
        """Test that empty ID raises error."""
        with pytest.raises(ValidationError):
            validate_id("")
    
    def test_validate_id_whitespace(self):
        """Test that whitespace-only ID raises error."""
        with pytest.raises(ValidationError):
            validate_id("  ")
    
    def test_validate_min_count_valid(self):
        """Test validating valid counts."""
        validate_min_count(0)
        validate_min_count(1)
        validate_min_count(10)
        validate_min_count(1000)
    
    def test_validate_min_count_negative(self):
        """Test that negative count raises error."""
        with pytest.raises(ValidationError):
            validate_min_count(-1)
    
    def test_validate_score_threshold_valid(self):
        """Test validating valid score thresholds."""
        validate_score_threshold(0.0)
        validate_score_threshold(0.5)
        validate_score_threshold(0.7)
        validate_score_threshold(1.0)
    
    def test_validate_score_threshold_too_low(self):
        """Test that score < 0.0 raises error."""
        with pytest.raises(ValidationError):
            validate_score_threshold(-0.1)
    
    def test_validate_score_threshold_too_high(self):
        """Test that score > 1.0 raises error."""
        with pytest.raises(ValidationError):
            validate_score_threshold(1.1)

