"""
Integration tests for ingestion pipeline.

Tests the full flow: scan → parse → normalize → extract → store.
"""

import pytest
from pathlib import Path
from src.ingestion.scanner import DocumentScanner
from src.ingestion.parser import DocumentParser
from src.ingestion.normalizer import DocumentNormalizer
from src.ingestion.metadata_extractor import MetadataExtractor


@pytest.fixture
def test_repo(tmp_path):
    """Create test repository with sample files."""
    # Create directory structure
    service_dir = tmp_path / "services" / "test-service"
    service_dir.mkdir(parents=True)
    
    # Create sample files
    (service_dir / "README.md").write_text("""# Test Service

This is a test service for integration testing.

## Features

- Feature 1
- Feature 2
""")
    
    (service_dir / "main.py").write_text('''"""Test module."""

def main():
    """Main function."""
    print("Hello, World!")

class TestClass:
    """Test class."""
    pass
''')
    
    (service_dir / "config.yaml").write_text("""service: test-service
port: 8000
""")
    
    return tmp_path


def test_full_ingestion_flow(test_repo):
    """Test complete ingestion pipeline."""
    # Initialize components
    scanner = DocumentScanner(str(test_repo))
    parser = DocumentParser()
    normalizer = DocumentNormalizer()
    extractor = MetadataExtractor()
    
    # Step 1: Scan for files
    files = scanner.scan_all_supported()
    assert len(files) > 0
    
    # Step 2: Process each file
    for file_path in files:
        # Parse
        parsed = parser.parse(file_path)
        assert "content" in parsed
        assert "format" in parsed
        
        # Normalize
        normalized = normalizer.normalize(parsed)
        assert isinstance(normalized, str)
        assert len(normalized) > 0
        
        # Extract metadata
        service_name = scanner.extract_service_name(file_path)
        metadata = extractor.extract(
            file_path=file_path,
            content=parsed["content"],
            normalized_content=normalized,
            parsed_metadata=parsed.get("metadata", {}),
            service_name=service_name
        )
        
        # Verify metadata
        assert metadata.service_name == "test-service"
        assert metadata.file_type in ["md", "py", "yaml"]
        assert metadata.word_count > 0


def test_markdown_specific_ingestion(test_repo):
    """Test ingestion of markdown files specifically."""
    scanner = DocumentScanner(str(test_repo))
    parser = DocumentParser()
    normalizer = DocumentNormalizer()
    
    # Get only markdown files
    md_files = scanner.scan_markdown_only()
    assert len(md_files) > 0
    
    for md_file in md_files:
        parsed = parser.parse(md_file)
        assert parsed["format"] == "markdown"
        
        normalized = normalizer.normalize(parsed)
        # Markdown should be mostly unchanged
        assert "# Test Service" in normalized


def test_python_specific_ingestion(test_repo):
    """Test ingestion of Python files specifically."""
    scanner = DocumentScanner(str(test_repo))
    parser = DocumentParser()
    normalizer = DocumentNormalizer()
    
    # Find Python files
    all_files = scanner.scan_all_supported()
    py_files = [f for f in all_files if f.suffix == ".py"]
    assert len(py_files) > 0
    
    for py_file in py_files:
        parsed = parser.parse(py_file)
        assert parsed["format"] == "python"
        assert "functions" in parsed["metadata"] or "classes" in parsed["metadata"]
        
        normalized = normalizer.normalize(parsed)
        # Should have structured markdown
        assert "# Python Module" in normalized
        assert "```python" in normalized

