"""
Unit tests for metadata extractor.
"""

import pytest
from pathlib import Path
from src.ingestion.metadata_extractor import MetadataExtractor


@pytest.fixture
def extractor():
    """Create extractor instance."""
    return MetadataExtractor()


def test_extract_phase_from_filename(extractor):
    """Test phase extraction from filename."""
    file_path = Path("/path/to/phase_3_implementation.md")
    content = "Some content"
    normalized = "# Content"
    
    metadata = extractor.extract(
        file_path=file_path,
        content=content,
        normalized_content=normalized,
        parsed_metadata={},
        service_name="test-service"
    )
    
    assert metadata.phase == "Phase 3"


def test_extract_topics(extractor):
    """Test topic extraction."""
    file_path = Path("/path/to/api_documentation.md")
    content = "API endpoints and authentication details"
    normalized = f"# API Documentation\n\n{content}\n\nTesting authentication"
    
    metadata = extractor.extract(
        file_path=file_path,
        content=content,
        normalized_content=normalized,
        parsed_metadata={},
        service_name="test-service"
    )
    
    # Should detect api, endpoints, authentication, testing
    assert "api" in metadata.topics
    assert "endpoints" in metadata.topics
    assert "authentication" in metadata.topics
    assert "testing" in metadata.topics


def test_detect_diagrams(extractor):
    """Test diagram detection."""
    file_path = Path("/path/to/architecture.md")
    content = "Architecture"
    normalized = """# Architecture

```mermaid
graph TD
    A --> B
```
"""
    
    metadata = extractor.extract(
        file_path=file_path,
        content=content,
        normalized_content=normalized,
        parsed_metadata={},
        service_name="test-service"
    )
    
    assert metadata.has_diagrams is True


def test_word_count(extractor):
    """Test word count calculation."""
    file_path = Path("/path/to/doc.md")
    content = "Original"
    normalized = "This is a test document with ten words total here"
    
    metadata = extractor.extract(
        file_path=file_path,
        content=content,
        normalized_content=normalized,
        parsed_metadata={},
        service_name="test-service"
    )
    
    assert metadata.word_count == 10


def test_language_detection(extractor):
    """Test language detection from file extension."""
    test_cases = [
        (Path("/path/to/file.py"), "python"),
        (Path("/path/to/file.js"), "javascript"),
        (Path("/path/to/file.go"), "go"),
        (Path("/path/to/file.rs"), "rust"),
        (Path("/path/to/file.md"), None),
    ]
    
    for file_path, expected_lang in test_cases:
        metadata = extractor.extract(
            file_path=file_path,
            content="content",
            normalized_content="normalized",
            parsed_metadata={},
            service_name="test"
        )
        assert metadata.language == expected_lang


def test_generate_tags(extractor):
    """Test tag generation."""
    file_path = Path("/path/to/README.md")
    content = "README content"
    normalized = "# README\n\nAPI documentation"
    
    metadata = extractor.extract(
        file_path=file_path,
        content=content,
        normalized_content=normalized,
        parsed_metadata={},
        service_name="test-service"
    )
    
    # Should include: md (file type), readme (special file), api (topic)
    assert "md" in metadata.tags
    assert "readme" in metadata.tags
    assert "api" in metadata.tags

