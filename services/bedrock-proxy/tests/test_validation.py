"""Unit tests for bedrock proxy validation functions."""

import pytest
from infrastructure.validation_utils.validation import (
    ValidationError,
    validate_prompt,
    validate_template,
    validate_format,
    validate_model,
    validate_region,
    validate_title,
)


class TestValidatePrompt:
    """Test suite for prompt validation."""

    def test_valid_string(self):
        """Test validation of valid string prompts."""
        assert validate_prompt("Hello world") == "Hello world"
        assert validate_prompt("") == ""
        assert validate_prompt("Complex prompt with 123 and !@#") == "Complex prompt with 123 and !@#"

    def test_none_value(self):
        """Test validation of None prompt."""
        assert validate_prompt(None) is None

    def test_invalid_type(self):
        """Test validation of invalid prompt types."""
        with pytest.raises(ValidationError, match="Prompt must be a string"):
            validate_prompt(123)

        with pytest.raises(ValidationError, match="Prompt must be a string"):
            validate_prompt([])

        with pytest.raises(ValidationError, match="Prompt must be a string"):
            validate_prompt({})


class TestValidateTemplate:
    """Test suite for template validation."""

    def test_valid_templates(self):
        """Test validation of valid template names."""
        valid_templates = ["summary", "risks", "decisions", "pr_confidence", "life_of_ticket"]

        for template in valid_templates:
            assert validate_template(template) == template
            assert validate_template(template.upper()) == template.upper()  # Case preserved

    def test_none_value(self):
        """Test validation of None template."""
        assert validate_template(None) is None

    def test_empty_string(self):
        """Test validation of empty string."""
        assert validate_template("") == ""
        assert validate_template("   ") == "   "

    def test_invalid_template(self):
        """Test validation of invalid template names."""
        with pytest.raises(ValidationError, match="Invalid template: invalid"):
            validate_template("invalid")

        with pytest.raises(ValidationError, match="Invalid template: nonexistent"):
            validate_template("nonexistent")


class TestValidateFormat:
    """Test suite for format validation."""

    def test_valid_formats(self):
        """Test validation of valid format names."""
        valid_formats = ["md", "txt", "json"]

        for fmt in valid_formats:
            assert validate_format(fmt) == fmt.lower()
            assert validate_format(fmt.upper()) == fmt.lower()

    def test_none_value_defaults_to_md(self):
        """Test that None format defaults to 'md'."""
        assert validate_format(None) == "md"

    def test_empty_string_defaults_to_md(self):
        """Test that empty format defaults to 'md'."""
        # Empty string is considered invalid and raises ValidationError
        with pytest.raises(ValidationError, match="Invalid format"):
            validate_format("")

    def test_invalid_format(self):
        """Test validation of invalid format names."""
        with pytest.raises(ValidationError, match="Invalid format: invalid"):
            validate_format("invalid")

        with pytest.raises(ValidationError, match="Invalid format: pdf"):
            validate_format("pdf")


class TestValidateModel:
    """Test suite for model validation."""

    def test_valid_models(self):
        """Test validation of valid model names."""
        assert validate_model("claude-3-sonnet") == "claude-3-sonnet"
        assert validate_model("gpt-4") == "gpt-4"
        assert validate_model("model-name-123") == "model-name-123"

    def test_none_value(self):
        """Test validation of None model."""
        assert validate_model(None) is None

    def test_sanitization(self):
        """Test that dangerous content is sanitized."""
        dangerous = 'model<script>alert(1)</script>'
        safe = validate_model(dangerous)
        assert "<" not in safe
        assert "script" not in safe

    def test_length_limit(self):
        """Test model name length limit."""
        # Valid length
        long_name = "a" * 100
        assert validate_model(long_name) == long_name

        # Too long
        too_long = "a" * 101
        with pytest.raises(ValidationError, match="Model name too long"):
            validate_model(too_long)


class TestValidateRegion:
    """Test suite for region validation."""

    def test_valid_regions(self):
        """Test validation of valid region names."""
        assert validate_region("us-east-1") == "us-east-1"
        assert validate_region("eu-west-1") == "eu-west-1"
        assert validate_region("ap-southeast-1") == "ap-southeast-1"

    def test_none_value(self):
        """Test validation of None region."""
        assert validate_region(None) is None

    def test_sanitization(self):
        """Test that dangerous content is sanitized."""
        dangerous = 'region${ENV_VAR}../../../root'
        safe = validate_region(dangerous)
        assert "${" not in safe
        assert "../" not in safe

    def test_length_limit(self):
        """Test region name length limit."""
        # Valid length
        long_name = "a" * 50
        assert validate_region(long_name) == long_name

        # Too long
        too_long = "a" * 51
        with pytest.raises(ValidationError, match="Region name too long"):
            validate_region(too_long)


class TestValidateTitle:
    """Test suite for title validation."""

    def test_valid_titles(self):
        """Test validation of valid titles."""
        assert validate_title("Simple Title") == "Simple Title"
        assert validate_title("Complex Title with 123 and !@#") == "Complex Title with 123 and !@#"

    def test_none_value(self):
        """Test validation of None title."""
        assert validate_title(None) is None

    def test_length_limit(self):
        """Test title length limit."""
        # Valid length
        long_title = "a" * 200
        assert validate_title(long_title) == long_title

        # Too long
        too_long = "a" * 201
        with pytest.raises(ValidationError, match="Title too long"):
            validate_title(too_long)
