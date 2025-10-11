"""
Unit tests for validation utilities.
"""

import pytest
from pathlib import Path

from src.utils.validation import (
    sanitize_html,
    validate_path,
    validate_file_extension,
    validate_query_length,
    validate_content_size,
    validate_service_name,
    validate_uuid,
    sanitize_and_validate_query,
)
from src.utils.exceptions import ValidationError


class TestSanitizeHTML:
    """Test HTML sanitization."""
    
    def test_basic_html_escaped(self):
        """Test that HTML tags are escaped."""
        result = sanitize_html("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result
    
    def test_javascript_removed(self):
        """Test that javascript: URLs are removed."""
        result = sanitize_html("javascript:alert('xss')")
        assert "javascript:" not in result.lower()
    
    def test_event_handlers_removed(self):
        """Test that event handlers are removed."""
        result = sanitize_html('<div onclick="alert(1)">test</div>')
        assert "onclick" not in result.lower()
    
    def test_plain_text_unchanged(self):
        """Test that plain text passes through."""
        text = "Hello, world! This is a test."
        result = sanitize_html(text)
        assert result == text
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert sanitize_html("") == ""
        assert sanitize_html(None) is None


class TestValidatePath:
    """Test path validation."""
    
    def test_valid_relative_path(self):
        """Test that valid relative paths are accepted."""
        result = validate_path("docs/README.md")
        assert isinstance(result, Path)
        assert str(result) == "docs/README.md"
    
    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        with pytest.raises(ValidationError, match="Path traversal"):
            validate_path("../../../etc/passwd")
    
    def test_encoded_traversal_rejected(self):
        """Test that URL-encoded traversal is rejected."""
        with pytest.raises(ValidationError, match="Path traversal"):
            validate_path("..%2f..%2f..%2fetc%2fpasswd")
    
    def test_absolute_path_rejected(self):
        """Test that absolute paths are rejected without base_dir."""
        with pytest.raises(ValidationError, match="Absolute paths"):
            validate_path("/etc/passwd")
    
    def test_empty_path_rejected(self):
        """Test that empty paths are rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_path("")
    
    def test_path_too_long_rejected(self):
        """Test that overly long paths are rejected."""
        long_path = "a/" * 300  # > 500 chars
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_path(long_path)
    
    def test_base_dir_constraint(self, tmp_path):
        """Test that paths are constrained to base directory."""
        base = tmp_path / "safe"
        base.mkdir()
        
        # Valid path within base
        result = validate_path("docs/test.md", base_dir=base)
        assert isinstance(result, Path)
        
        # Invalid path outside base (catches traversal pattern first)
        with pytest.raises(ValidationError, match="Path traversal"):
            validate_path("../etc/passwd", base_dir=base)


class TestValidateFileExtension:
    """Test file extension validation."""
    
    def test_allowed_extensions(self):
        """Test that allowed extensions pass."""
        allowed = [
            "doc.md", "script.py", "data.json", "config.yaml",
            "index.html", "style.css", "README.txt"
        ]
        for path in allowed:
            result = validate_file_extension(path)
            assert result == path
    
    def test_disallowed_extensions(self):
        """Test that disallowed extensions are rejected."""
        disallowed = ["malware.exe", "virus.bat", "script.sh", "data.zip"]
        for path in disallowed:
            with pytest.raises(ValidationError, match="not allowed"):
                validate_file_extension(path)
    
    def test_no_extension_rejected(self):
        """Test that files without extensions are rejected."""
        with pytest.raises(ValidationError, match="must have an extension"):
            validate_file_extension("Makefile")
    
    def test_case_insensitive(self):
        """Test that validation is case-insensitive."""
        assert validate_file_extension("README.MD") == "README.MD"
        assert validate_file_extension("script.PY") == "script.PY"


class TestValidateQueryLength:
    """Test query length validation."""
    
    def test_valid_query(self):
        """Test that valid queries pass."""
        query = "How does authentication work?"
        result = validate_query_length(query)
        assert result == query
    
    def test_empty_query_rejected(self):
        """Test that empty queries are rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_query_length("")
    
    def test_too_long_rejected(self):
        """Test that overly long queries are rejected."""
        long_query = "a" * 600  # > 500 chars
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_query_length(long_query)


class TestValidateContentSize:
    """Test content size validation."""
    
    def test_valid_content(self):
        """Test that valid content passes."""
        content = "Test content"
        result = validate_content_size(content)
        assert result == content
    
    def test_empty_content_rejected(self):
        """Test that empty content is rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_content_size("")
    
    def test_too_large_rejected(self):
        """Test that overly large content is rejected."""
        large_content = "a" * (11 * 1024 * 1024)  # > 10MB
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_content_size(large_content)
    
    def test_custom_max_size(self):
        """Test that custom max size is respected."""
        content = "a" * 1000
        
        # Should pass with high limit
        result = validate_content_size(content, max_size=2000)
        assert result == content
        
        # Should fail with low limit
        with pytest.raises(ValidationError):
            validate_content_size(content, max_size=500)


class TestValidateServiceName:
    """Test service name validation."""
    
    def test_valid_names(self):
        """Test that valid service names pass."""
        valid = ["code-analyzer", "discovery_agent", "api-gateway", "service123"]
        for name in valid:
            result = validate_service_name(name)
            assert result == name
    
    def test_invalid_characters_rejected(self):
        """Test that invalid characters are rejected."""
        invalid = ["service name", "service@name", "service/name", "service.name"]
        for name in invalid:
            with pytest.raises(ValidationError, match="must contain only"):
                validate_service_name(name)
    
    def test_empty_name_rejected(self):
        """Test that empty names are rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_service_name("")
    
    def test_too_long_rejected(self):
        """Test that overly long names are rejected."""
        long_name = "a" * 150
        with pytest.raises(ValidationError, match="too long"):
            validate_service_name(long_name)


class TestValidateUUID:
    """Test UUID validation."""
    
    def test_valid_uuid(self):
        """Test that valid UUIDs pass."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        result = validate_uuid(valid_uuid)
        assert result == valid_uuid
    
    def test_invalid_uuid_rejected(self):
        """Test that invalid UUIDs are rejected."""
        invalid = ["not-a-uuid", "12345", ""]
        for uuid_str in invalid:
            with pytest.raises(ValidationError, match="Invalid UUID"):
                validate_uuid(uuid_str)


class TestSanitizeAndValidateQuery:
    """Test combined query validation."""
    
    def test_sanitizes_and_validates(self):
        """Test that queries are both sanitized and validated."""
        query = "  <script>test</script>  "
        result = sanitize_and_validate_query(query)
        
        # Should be sanitized (no script tags)
        assert "<script>" not in result
        # Should be stripped
        assert not result.startswith(" ")
        assert not result.endswith(" ")
    
    def test_rejects_invalid_queries(self):
        """Test that invalid queries are rejected."""
        # Too long
        long_query = "a" * 600
        with pytest.raises(ValidationError):
            sanitize_and_validate_query(long_query)
        
        # Empty
        with pytest.raises(ValidationError):
            sanitize_and_validate_query("")

