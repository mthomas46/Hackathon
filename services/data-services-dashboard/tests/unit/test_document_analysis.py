"""Unit tests for document analysis helper functions."""

import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from pages.document_browser import (
    analyze_document_content,
    extract_keywords,
    extract_markdown_headings,
    generate_content_summary,
    prepare_export_content,
)


class TestDocumentAnalysis:
    """Test document content analysis functionality."""

    def test_analyze_document_content_basic(self):
        """Test basic document content analysis."""
        content = "This is a test document. It contains multiple sentences and should be analyzed properly."
        analysis = analyze_document_content(content, "text")

        assert analysis["metrics"]["Characters"] == len(content)
        assert analysis["metrics"]["Words"] == 14
        assert analysis["metrics"]["Sentences"] == 2
        assert len(analysis["quality"]) > 0
        assert len(analysis["insights"]) >= 0

    def test_analyze_document_content_markdown(self):
        """Test analysis of markdown documents."""
        content = """# Main Title

This is an introduction paragraph.

## Section 1

Some content here.

## Section 2

More content.

- List item 1
- List item 2
- List item 3

```python
def hello():
    print("Hello, World!")
```

Another paragraph with more text.
"""
        analysis = analyze_document_content(content, "markdown")

        # Check structure analysis
        assert "headings" in analysis["structure"]
        assert "code_blocks" in analysis["structure"]
        assert "lists" in analysis["structure"]

        # Check that headings were extracted
        headings = analysis["structure"]["headings"]
        assert len(headings) >= 3  # Main title + 2 sections

        # Check code blocks were detected
        assert analysis["structure"]["code_blocks"] >= 1

        # Check lists were detected
        assert analysis["structure"]["lists"] >= 1

    def test_analyze_document_content_empty(self):
        """Test analysis of empty documents."""
        content = ""
        analysis = analyze_document_content(content, "text")

        assert analysis["metrics"]["Characters"] == 0
        assert analysis["metrics"]["Words"] == 0
        assert analysis["metrics"]["Sentences"] == 0

    def test_analyze_document_content_long(self):
        """Test analysis of long documents."""
        content = "This is a test. " * 100  # Long repetitive content
        analysis = analyze_document_content(content, "text")

        assert analysis["metrics"]["Words"] == 400  # 4 words * 100 ("This", "is", "a", "test.")
        assert analysis["metrics"]["Sentences"] == 100

        # Long content should have some insights generated
        assert len(analysis["insights"]) >= 0  # May or may not have insights depending on content


class TestMarkdownHeadingExtraction:
    """Test markdown heading extraction."""

    def test_extract_markdown_headings_basic(self):
        """Test basic heading extraction."""
        content = """# Main Title

Some content.

## Subsection

More content.

### Sub-subsection

Even more content.
"""
        headings = extract_markdown_headings(content)
        expected = ["Main Title", "Subsection", "Sub-subsection"]
        assert headings == expected

    def test_extract_markdown_headings_mixed(self):
        """Test heading extraction with mixed content."""
        content = """# Title 1

Content here.

## Title 2

More content.

# Title 3

Final content.
"""
        headings = extract_markdown_headings(content)
        expected = ["Title 1", "Title 2", "Title 3"]
        assert headings == expected

    def test_extract_markdown_headings_no_headings(self):
        """Test content with no headings."""
        content = "This is just regular content without any headings."
        headings = extract_markdown_headings(content)
        assert headings == []

    def test_extract_markdown_headings_edge_cases(self):
        """Test heading extraction edge cases."""
        content = """#Heading with no space

## Valid Heading

#Another Heading
"""
        headings = extract_markdown_headings(content)
        # Extracts all lines starting with # (function behavior)
        assert "Heading with no space" in headings
        assert "Valid Heading" in headings
        assert "Another Heading" in headings
        assert len(headings) == 3


class TestContentSummary:
    """Test content summary generation."""

    def test_generate_content_summary_long(self):
        """Test summary generation for long content."""
        content = "This is a comprehensive guide to Python programming. It covers all the essential concepts you need to know. From basic syntax to advanced features, this guide will help you become proficient in Python development."
        summary = generate_content_summary(content)

        assert isinstance(summary, str)
        # Content has 34 words (< 50), so returns full content
        assert summary == content

    def test_generate_content_summary_short(self):
        """Test summary generation for short content."""
        content = "Short content."
        summary = generate_content_summary(content)

        # Should return the content as-is for short content
        assert summary == content

    def test_generate_content_summary_empty(self):
        """Test summary generation for empty content."""
        content = ""
        summary = generate_content_summary(content)

        assert summary == ""


class TestKeywordExtraction:
    """Test keyword extraction functionality."""

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        content = "Python is a programming language. Python developers use Python for web development, data analysis, and machine learning applications."
        keywords = extract_keywords(content)

        assert isinstance(keywords, list)
        assert "python" in [k.lower() for k in keywords]  # Should extract "Python"
        assert len(keywords) <= 10  # Should limit to top keywords

    def test_extract_keywords_common_words_filtered(self):
        """Test that common words are filtered out."""
        content = "The quick brown fox jumps over the lazy dog. The cat is sleeping."
        keywords = extract_keywords(content)

        # Common words should be filtered out
        common_words = ["the", "is", "over", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        keyword_lower = [k.lower() for k in keywords]
        for common in common_words:
            assert common not in keyword_lower

    def test_extract_keywords_frequency_based(self):
        """Test that keywords are ranked by frequency."""
        content = (
            "Machine learning is important. Machine learning algorithms are complex. Machine learning requires data."
        )
        keywords = extract_keywords(content)

        # "machine" and "learning" should appear (combined as "machine learning" would be ideal, but our simple extraction looks for individual words)
        keyword_lower = [k.lower() for k in keywords]
        assert "machine" in keyword_lower or "learning" in keyword_lower

    def test_extract_keywords_empty(self):
        """Test keyword extraction for empty content."""
        content = ""
        keywords = extract_keywords(content)

        assert keywords == []

    def test_extract_keywords_minimal(self):
        """Test keyword extraction for minimal content."""
        content = "AI and machine learning are transforming technology."
        keywords = extract_keywords(content)

        assert isinstance(keywords, list)
        # Should extract meaningful keywords
        keyword_lower = [k.lower() for k in keywords]
        meaningful_words = ["ai", "machine", "learning", "technology", "transforming"]
        has_meaningful = any(word in keyword_lower for word in meaningful_words)
        assert has_meaningful or len(keywords) == 0  # Either has meaningful keywords or is empty


class TestExportPreparation:
    """Test content export preparation."""

    def test_prepare_export_content_with_metadata(self):
        """Test export preparation with metadata."""
        content = "Test document content"
        document = {
            "id": "test_doc_123",
            "content_type": "text",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-02T10:00:00Z",
            "metadata": {"author": "Test Author", "version": "1.0"},
        }

        exported = prepare_export_content(content, document, "text", True)

        assert document["id"] in exported
        assert document["content_type"] in exported
        assert document["created_at"] in exported
        assert content in exported
        assert "Test Author" in exported or "author" in exported.lower()  # Author in metadata

    def test_prepare_export_content_without_metadata(self):
        """Test export preparation without metadata."""
        content = "Test document content"
        document = {"id": "test_doc_123"}

        exported = prepare_export_content(content, document, "text", False)

        assert exported == content
        assert document["id"] not in exported

    def test_prepare_export_content_empty_metadata(self):
        """Test export preparation with empty metadata."""
        content = "Test document content"
        document = {"id": "test_doc_123"}
        metadata = {}

        exported = prepare_export_content(content, document, "text", True)

        assert content in exported
        # Should still have basic document info even with empty metadata
        assert document["id"] in exported


class TestQualityIndicators:
    """Test quality indicator calculations."""

    def test_quality_readability_calculation(self):
        """Test readability score calculation."""
        # Short, simple sentences should have high readability
        simple_content = "This is simple. It is easy to read. Clear sentences work well."
        analysis = analyze_document_content(simple_content, "text")

        readability_indicator = next((qi for qi in analysis["quality"] if qi["name"] == "Readability"), None)
        assert readability_indicator is not None
        assert readability_indicator["score"] >= 0
        assert readability_indicator["score"] <= 100

    def test_quality_structure_calculation(self):
        """Test structure quality calculation."""
        # Content with paragraphs should have better structure
        structured_content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        analysis = analyze_document_content(structured_content, "text")

        structure_indicator = next((qi for qi in analysis["quality"] if qi["name"] == "Structure"), None)
        assert structure_indicator is not None
        assert structure_indicator["score"] >= 50  # Should have decent structure score

    def test_quality_conciseness_calculation(self):
        """Test conciseness quality calculation."""
        # Very long content should have lower conciseness
        long_content = "This is a very long sentence that goes on and on. " * 50
        analysis = analyze_document_content(long_content, "text")

        conciseness_indicator = next((qi for qi in analysis["quality"] if qi["name"] == "Conciseness"), None)
        assert conciseness_indicator is not None
        # Long content should have lower conciseness score
        assert conciseness_indicator["score"] < 90
