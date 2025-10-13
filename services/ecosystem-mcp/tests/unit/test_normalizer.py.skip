"""
Unit tests for document normalizer.
"""

import pytest
from src.ingestion.normalizer import DocumentNormalizer


@pytest.fixture
def normalizer():
    """Create normalizer instance."""
    return DocumentNormalizer()


def test_normalize_markdown(normalizer, sample_markdown):
    """Test markdown normalization."""
    parsed = {
        "format": "markdown",
        "content": sample_markdown,
        "metadata": {}
    }
    
    result = normalizer.normalize(parsed)
    
    # Should preserve structure
    assert "# Test Document" in result
    assert "## Section 1" in result
    assert "## Section 2" in result


def test_normalize_python(normalizer, sample_python):
    """Test Python normalization."""
    parsed = {
        "format": "python",
        "content": sample_python,
        "metadata": {
            "functions": ["hello_world"],
            "classes": ["SampleClass"],
            "docstrings": []
        }
    }
    
    result = normalizer.normalize(parsed)
    
    # Should create markdown
    assert "# Python Module" in result
    assert "## Functions" in result
    assert "hello_world" in result
    assert "## Classes" in result
    assert "SampleClass" in result
    assert "```python" in result


def test_normalize_yaml(normalizer, sample_yaml):
    """Test YAML normalization."""
    parsed = {
        "format": "yaml",
        "content": sample_yaml,
        "metadata": {
            "keys": ["service", "version", "config"]
        }
    }
    
    result = normalizer.normalize(parsed)
    
    # Should create markdown
    assert "# YAML Configuration" in result
    assert "## Configuration Keys" in result
    assert "```yaml" in result


def test_normalize_removes_excessive_whitespace(normalizer):
    """Test whitespace cleaning."""
    content = "Line 1\n\n\n\nLine 2\n\n\n\nLine 3"
    parsed = {
        "format": "markdown",
        "content": content,
        "metadata": {}
    }
    
    result = normalizer.normalize(parsed)
    
    # Should not have 4 consecutive newlines
    assert "\n\n\n\n" not in result

