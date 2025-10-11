"""
Unit tests for document parser.
"""

import pytest
from pathlib import Path
from src.ingestion.parser import DocumentParser


@pytest.fixture
def parser():
    """Create parser instance."""
    return DocumentParser()


def test_parse_markdown(parser, sample_markdown, tmp_path):
    """Test markdown parsing."""
    # Create temp file
    file_path = tmp_path / "test.md"
    file_path.write_text(sample_markdown)
    
    # Parse
    result = parser.parse(file_path)
    
    # Verify
    assert result["format"] == "markdown"
    assert result["content"] == sample_markdown
    assert "metadata" in result


def test_parse_python(parser, sample_python, tmp_path):
    """Test Python parsing."""
    # Create temp file
    file_path = tmp_path / "test.py"
    file_path.write_text(sample_python)
    
    # Parse
    result = parser.parse(file_path)
    
    # Verify
    assert result["format"] == "python"
    assert result["content"] == sample_python
    assert "metadata" in result
    
    metadata = result["metadata"]
    assert "functions" in metadata
    assert "hello_world" in metadata["functions"]
    assert "classes" in metadata
    assert "SampleClass" in metadata["classes"]


def test_parse_yaml(parser, sample_yaml, tmp_path):
    """Test YAML parsing."""
    # Create temp file
    file_path = tmp_path / "test.yaml"
    file_path.write_text(sample_yaml)
    
    # Parse
    result = parser.parse(file_path)
    
    # Verify
    assert result["format"] == "yaml"
    assert result["content"] == sample_yaml
    assert "metadata" in result
    assert "keys" in result["metadata"]


def test_parse_json(parser, sample_json, tmp_path):
    """Test JSON parsing."""
    # Create temp file
    file_path = tmp_path / "test.json"
    file_path.write_text(sample_json)
    
    # Parse
    result = parser.parse(file_path)
    
    # Verify
    assert result["format"] == "json"
    assert result["content"] == sample_json
    assert "metadata" in result
    assert "keys" in result["metadata"]


def test_parse_unsupported_format(parser, tmp_path):
    """Test unsupported file format."""
    # Create unsupported file
    file_path = tmp_path / "test.xyz"
    file_path.write_text("unsupported content")
    
    # Parse
    result = parser.parse(file_path)
    
    # Should default to text
    assert result["format"] == "text"

