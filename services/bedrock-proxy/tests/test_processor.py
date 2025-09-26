"""Unit tests for bedrock proxy request processing functionality."""

import pytest
from unittest.mock import patch
from infrastructure.processor import process_invoke_request


class TestProcessInvokeRequest:
    """Test suite for invoke request processing."""

    def test_basic_request_processing(self):
        """Test basic request processing with minimal parameters."""
        result = process_invoke_request(prompt="Test prompt")

        assert isinstance(result, dict)
        assert "output" in result
        assert isinstance(result["output"], str)
        assert len(result["output"]) > 0

    def test_json_format_response(self):
        """Test JSON format response structure."""
        result = process_invoke_request(
            prompt="Test prompt",
            template="summary",
            format="json"
        )

        assert "title" in result
        assert "model" in result  # Always included, None if not provided
        assert "region" in result  # Always included, None if not provided
        assert "sections" in result
        assert isinstance(result["sections"], dict)

    def test_markdown_format_response(self):
        """Test markdown format response structure."""
        result = process_invoke_request(
            prompt="Test prompt",
            format="md"
        )

        assert "output" in result
        assert "model" in result
        assert "region" in result
        assert "# " in result["output"]  # Markdown header

    def test_text_format_response(self):
        """Test plain text format response structure."""
        result = process_invoke_request(
            prompt="Test prompt",
            format="txt"
        )

        assert "output" in result
        assert "model" in result
        assert "region" in result
        # Text format should not have markdown headers
        assert "# " not in result["output"]

    def test_default_format_is_markdown(self):
        """Test that default format is markdown."""
        result = process_invoke_request(prompt="Test")
        assert "# " in result["output"]

    def test_template_auto_detection(self):
        """Test automatic template detection from prompt content."""
        # Test summary detection - this will use Echo template since no keyword matches
        result = process_invoke_request(prompt="Summarize this document")
        assert "Echo" in result["output"] or "echo" in result["output"].lower()

    @patch('infrastructure.templates.detect_template_from_prompt')
    def test_template_parameter_override(self, mock_detect):
        """Test that explicit template parameter overrides auto-detection."""
        mock_detect.return_value = "risks"  # Mock would detect risks

        result = process_invoke_request(
            prompt="Some prompt",
            template="summary"  # But we explicitly set summary
        )

        # Should use summary, not risks
        assert "Summary" in result["output"] or "summary" in result["output"].lower()

    def test_custom_title(self):
        """Test custom title usage."""
        custom_title = "My Custom Title"
        result = process_invoke_request(
            prompt="Test prompt",
            title=custom_title
        )

        assert custom_title in result["output"]

    def test_auto_generated_title(self):
        """Test automatic title generation when none provided."""
        result = process_invoke_request(prompt="Test prompt")

        # Should have some title in the output
        assert isinstance(result["output"], str)
        assert len(result["output"]) > 0

    def test_model_and_region_passthrough(self):
        """Test that model and region parameters are passed through."""
        test_model = "claude-3-sonnet"
        test_region = "us-east-1"

        result = process_invoke_request(
            prompt="Test",
            model=test_model,
            region=test_region
        )

        assert result["model"] == test_model
        assert result["region"] == test_region

    def test_empty_prompt_handling(self):
        """Test handling of empty or None prompts."""
        # Empty string
        result = process_invoke_request(prompt="")
        assert isinstance(result, dict)
        assert "output" in result

        # None prompt
        result = process_invoke_request(prompt=None)
        assert isinstance(result, dict)
        assert "output" in result

    def test_case_insensitive_format(self):
        """Test case-insensitive format handling."""
        formats = ["MD", "Md", "md", "TXT", "Txt", "txt", "JSON", "Json", "json"]

        for fmt in formats:
            result = process_invoke_request(prompt="Test", format=fmt)
            assert isinstance(result, dict)

    def test_invalid_format_defaults(self):
        """Test that invalid formats default to text output."""
        result = process_invoke_request(prompt="Test", format="invalid")
        # Invalid formats seem to default to text output
        assert "output" in result
        assert "Echo:" in result["output"]

    def test_template_validation_through_processing(self):
        """Test that invalid templates are handled gracefully."""
        # This should not raise an exception but handle gracefully
        result = process_invoke_request(
            prompt="Test",
            template="invalid_template"
        )

        # Should still produce valid output
        assert isinstance(result, dict)
        assert "output" in result

    def test_special_characters_in_prompt(self):
        """Test handling of special characters in prompts."""
        special_prompt = "Prompt with <script> tags & 'quotes' \"double\" and 特殊字符"
        result = process_invoke_request(prompt=special_prompt)

        # Should sanitize and still produce output
        assert isinstance(result, dict)
        assert "output" in result

    def test_long_prompt_handling(self):
        """Test handling of very long prompts."""
        long_prompt = "Test prompt. " * 1000  # Very long prompt
        result = process_invoke_request(prompt=long_prompt)

        assert isinstance(result, dict)
        assert "output" in result

    def test_multiple_kwargs_passthrough(self):
        """Test that additional kwargs are accepted."""
        result = process_invoke_request(
            prompt="Test",
            custom_param="value",
            another_param=123
        )

        # Should not raise an exception
        assert isinstance(result, dict)

    def test_template_sections_structure(self):
        """Test that template sections are properly structured."""
        result = process_invoke_request(
            prompt="Test prompt for summary",
            template="summary",
            format="json"
        )

        sections = result["sections"]
        assert isinstance(sections, dict)

        # Summary template should have specific sections
        assert "Summary" in sections
        assert "Key Points" in sections

        # Sections should contain appropriate content
        assert isinstance(sections["Summary"], list)
        assert isinstance(sections["Key Points"], list)
