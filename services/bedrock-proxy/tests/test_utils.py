"""Unit tests for bedrock proxy utility functions."""

import pytest
from modules.utils import sanitize_for_response, bullets_from_text


class TestSanitizeForResponse:
    """Test suite for text sanitization functionality."""

    def test_empty_string(self):
        """Test sanitization of empty string."""
        assert sanitize_for_response("") == ""
        assert sanitize_for_response(None) == ""

    def test_basic_text_unchanged(self):
        """Test that basic text remains unchanged."""
        text = "Hello World 123"
        assert sanitize_for_response(text) == text

    def test_html_tag_removal(self):
        """Test removal of HTML tags."""
        dangerous = '<script>alert("xss")</script><b>Bold</b>'
        safe = 'alert(xss)Bold'  # Quotes are also removed
        assert sanitize_for_response(dangerous) == safe

    def test_javascript_removal(self):
        """Test removal of JavaScript injection patterns."""
        dangerous = 'onclick="alert(1)" javascript:alert(2) vbscript:msgbox(3)'
        safe = 'alert(1) alert(2) msgbox(3)'
        assert sanitize_for_response(dangerous) == safe

    def test_quote_removal(self):
        """Test removal of quotes that could break string contexts."""
        dangerous = 'User said "hello" and \'goodbye\''
        safe = 'User said hello and goodbye'
        assert sanitize_for_response(dangerous) == safe

    def test_sql_injection_removal(self):
        """Test removal of SQL injection patterns."""
        dangerous = "SELECT * FROM users; -- DROP TABLE users; SELECT * FROM dummy"
        # The function removes '--' comments but not the full injection
        result = sanitize_for_response(dangerous)
        assert "DROP TABLE" in result  # Still contains dangerous content
        assert ";" in result  # Still contains semicolons

    def test_environment_variable_removal(self):
        """Test removal of environment variable patterns."""
        dangerous = "Path: ${HOME}/file and ${USER}"
        safe = "Path: file and"  # Removes ${} and content, keeps surrounding text
        assert sanitize_for_response(dangerous) == safe

    def test_path_traversal_removal(self):
        """Test removal of path traversal patterns."""
        dangerous = "../../../etc/passwd \\windows\\system32"
        safe = "etcpasswd windowssystem32"
        assert sanitize_for_response(dangerous) == safe

    def test_control_character_removal(self):
        """Test removal of control characters while preserving whitespace."""
        dangerous = "Hello\x00World\x01Test\nGood\r\n\tTabbed"
        safe = "HelloWorldTest\nGood\r\n\tTabbed"
        assert sanitize_for_response(dangerous) == safe

    def test_whitespace_preservation(self):
        """Test that normal whitespace is preserved."""
        text = "Line 1\nLine 2\r\n\tIndented"
        assert sanitize_for_response(text) == text

    def test_complex_mixed_attacks(self):
        """Test sanitization of complex mixed attack patterns."""
        dangerous = '<img src=x onerror="alert(1)"> ${ENV_VAR} ../../../root ; -- DROP TABLE'
        # Should remove HTML, env vars, path traversal, and SQL comments
        result = sanitize_for_response(dangerous)
        assert "<" not in result
        assert ">" not in result
        assert "${" not in result
        assert "../" not in result
        assert ";" not in result
        assert "--" not in result


class TestBulletsFromText:
    """Test suite for bullet point extraction functionality."""

    def test_empty_text(self):
        """Test extraction from empty text."""
        result = bullets_from_text("")
        expected = [
            "No content provided.",
            "Add more details to the prompt for better analysis.",
        ]
        assert result == expected

    def test_none_text(self):
        """Test extraction from None text."""
        result = bullets_from_text(None)
        expected = [
            "No content provided.",
            "Add more details to the prompt for better analysis.",
        ]
        assert result == expected

    def test_simple_lines(self):
        """Test extraction of simple line-based bullets."""
        text = "Line 1\nLine 2\nLine 3"
        result = bullets_from_text(text)
        assert result == ["Line 1", "Line 2", "Line 3"]

    def test_remove_common_bullet_markers(self):
        """Test removal of common bullet markers."""
        text = "- Item 1\n* Item 2\n  - Nested item\n\tTabbed item"
        result = bullets_from_text(text)
        # The function strips '-', spaces, and tabs, but not '*'
        assert result == ["Item 1", "* Item 2", "Nested item", "Tabbed item"]

    def test_skip_empty_lines(self):
        """Test that empty lines are skipped."""
        text = "Item 1\n\n\nItem 2\n  \nItem 3"
        result = bullets_from_text(text)
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_skip_punctuation_only(self):
        """Test that lines with only punctuation are skipped."""
        text = "Good item\n-\n*\n.\nReal item"
        result = bullets_from_text(text)
        assert result == ["Good item", "Real item"]

    def test_max_items_limit(self):
        """Test that max_items parameter limits results."""
        text = "Item 1\nItem 2\nItem 3\nItem 4\nItem 5\nItem 6"
        result = bullets_from_text(text, max_items=3)
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_default_max_items(self):
        """Test default max_items behavior."""
        text = "Item 1\nItem 2\nItem 3\nItem 4\nItem 5\nItem 6\nItem 7"
        result = bullets_from_text(text)
        assert len(result) == 5  # Default max_items is 5

    def test_mixed_content(self):
        """Test extraction from mixed content with various line formats."""
        text = """
        - Major finding: Security vulnerability detected
        * Impact: High severity
          - Affects authentication system
        TODO: Fix immediately

        Minor notes:
        - Code style improvements needed
        """
        result = bullets_from_text(text)
        expected = [
            "Major finding: Security vulnerability detected",
            "* Impact: High severity",  # '*' is not stripped
            "Affects authentication system",
            "TODO: Fix immediately",
            "Minor notes:",
        ]
        assert result == expected

    def test_long_text_truncation(self):
        """Test behavior with very long input text."""
        long_text = "\n".join([f"Item {i}" for i in range(20)])
        result = bullets_from_text(long_text, max_items=3)
        assert result == ["Item 0", "Item 1", "Item 2"]

    def test_unicode_content(self):
        """Test handling of unicode content."""
        text = "Résumé\n naïve\ncafé"
        result = bullets_from_text(text)
        assert result == ["Résumé", "naïve", "café"]
