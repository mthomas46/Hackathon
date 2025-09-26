#!/usr/bin/env python3
"""
Tests for Shared Utilities Module

Tests the core utility functions used across all services.
"""

import pytest
from datetime import datetime, timezone, timedelta
from services.shared.utilities.utilities import (
    clean_string,
    extract_variables,
    generate_id,
    utc_now,
    is_valid_email,
    is_valid_url,
    safe_filename,
    validate_string_length,
    format_datetime,
    relative_time,
    deep_merge_dicts,
    chunk_list
)


class TestStringUtilities:
    """Test string processing utilities."""

    def test_clean_string(self):
        """Test string cleaning and normalization."""
        assert clean_string("  hello   world  ") == "hello world"
        assert clean_string("test\t\nstring") == "test string"
        assert clean_string("") == ""
        assert clean_string(None) == ""

    def test_extract_variables(self):
        """Test variable extraction from text."""
        text = "Hello {name}, your score is {score}!"
        variables = extract_variables(text)
        assert "name" in variables
        assert "score" in variables
        assert len(variables) == 2

    def test_extract_variables_duplicates(self):
        """Test that duplicate variables are removed."""
        text = "Hello {name}, {name} again!"
        variables = extract_variables(text)
        assert variables == ["name"]
        assert len(variables) == 1


class TestIDGeneration:
    """Test ID generation utilities."""

    def test_generate_id_with_prefix(self):
        """Test ID generation with custom prefix."""
        id_with_prefix = generate_id("test")
        assert id_with_prefix.startswith("test")
        assert len(id_with_prefix) > 4  # prefix + some chars

    def test_generate_id_uniqueness(self):
        """Test that generated IDs are unique."""
        ids = [generate_id() for _ in range(100)]
        assert len(set(ids)) == len(ids)  # All IDs should be unique

    def test_generate_id_length(self):
        """Test ID generation with custom length."""
        short_id = generate_id(length=8)
        assert len(short_id) == 8

        long_id = generate_id(length=20)
        assert len(long_id) == 20


class TestTimeUtilities:
    """Test time and date utilities."""

    def test_utc_now(self):
        """Test UTC timestamp generation."""
        timestamp = utc_now()
        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo is not None

    def test_utc_now_recent(self):
        """Test that utc_now returns recent timestamp."""
        before = datetime.now(timezone.utc)
        timestamp = utc_now()
        after = datetime.now(timezone.utc)

        assert before <= timestamp <= after


class TestValidationUtilities:
    """Test validation utilities."""

    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name+tag@domain.co.uk") is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        assert is_valid_email("not-an-email") is False
        assert is_valid_email("@example.com") is False
        assert is_valid_email("test@") is False
        assert is_valid_email("") is False

    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://localhost:8000") is True
        assert is_valid_url("https://sub.domain.com/path?query=value") is True

    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("http://") is False
        assert is_valid_url("") is False


class TestFileUtilities:
    """Test file-related utilities."""

    def test_safe_filename(self):
        """Test filename sanitization."""
        assert safe_filename("file with spaces.txt") == "file_with_spaces.txt"
        assert safe_filename("file/with\\bad:chars?.txt") == "file_with_bad_chars_.txt"
        assert safe_filename("normal_file.txt") == "normal_file.txt"

    def test_safe_filename_empty(self):
        """Test filename sanitization with empty input."""
        assert safe_filename("") == ""
        assert safe_filename("   ") == "___"


class TestTextProcessing:
    """Test text processing utilities."""

    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        formatted = format_datetime(dt)
        assert formatted == "2024-01-15 12:30:45"

    def test_format_datetime_custom_format(self):
        """Test datetime formatting with custom format."""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        formatted = format_datetime(dt, "%Y-%m-%d")
        assert formatted == "2024-01-15"

    def test_relative_time(self):
        """Test relative time calculation."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        relative = relative_time(past_time)
        assert "ago" in relative or "in" in relative


class TestDataProcessing:
    """Test data processing utilities."""

    def test_deep_merge_dicts(self):
        """Test deep dictionary merging."""
        base = {"a": 1, "b": {"c": 2}}
        update = {"b": {"d": 3}, "e": 4}
        result = deep_merge_dicts(base, update)

        assert result["a"] == 1
        assert result["e"] == 4
        assert result["b"]["c"] == 2
        assert result["b"]["d"] == 3

    def test_chunk_list(self):
        """Test list chunking."""
        items = [1, 2, 3, 4, 5, 6, 7]
        chunks = chunk_list(items, 3)

        assert len(chunks) == 3
        assert chunks[0] == [1, 2, 3]
        assert chunks[1] == [4, 5, 6]
        assert chunks[2] == [7]

    def test_validate_string_length(self):
        """Test string length validation."""
        assert validate_string_length("test", min_len=2, max_len=10) is True
        assert validate_string_length("t", min_len=2) is False
        assert validate_string_length("this is a very long string", max_len=10) is False


if __name__ == "__main__":
    pytest.main([__file__])
