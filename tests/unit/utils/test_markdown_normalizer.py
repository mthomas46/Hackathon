"""
Unit tests for MarkdownNormalizer.

Tests markdown normalization from HTML, plaintext, and RST.
"""
import pytest
from ingestion.utils.markdown_normalizer import MarkdownNormalizer


class TestMarkdownNormalizer:
    """Tests for MarkdownNormalizer class."""
    
    def test_html_to_markdown_simple(self):
        """Test simple HTML to Markdown conversion."""
        html = "<p>Hello world</p>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "Hello world" in result
    
    def test_html_to_markdown_headers(self):
        """Test HTML headers conversion."""
        html = "<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "# Title" in result
        assert "## Subtitle" in result
        assert "### Section" in result
    
    def test_html_to_markdown_links(self):
        """Test HTML links conversion."""
        html = '<a href="https://example.com">Example</a>'
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "[Example](https://example.com)" in result
    
    def test_html_to_markdown_bold(self):
        """Test HTML bold conversion."""
        html = "<strong>Bold text</strong>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "**Bold text**" in result
    
    def test_html_to_markdown_italic(self):
        """Test HTML italic conversion."""
        html = "<em>Italic text</em>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "*Italic text*" in result
    
    def test_html_to_markdown_code(self):
        """Test HTML code conversion."""
        html = "<code>print('hello')</code>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "`print('hello')`" in result
    
    def test_html_to_markdown_code_block(self):
        """Test HTML code block conversion."""
        html = "<pre>def hello():\n    print('world')</pre>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "```" in result
        assert "def hello()" in result
    
    def test_html_to_markdown_unordered_list(self):
        """Test HTML unordered list conversion."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "- Item 1" in result
        assert "- Item 2" in result
    
    def test_html_to_markdown_ordered_list(self):
        """Test HTML ordered list conversion."""
        html = "<ol><li>First</li><li>Second</li></ol>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "1. First" in result
        assert "2. Second" in result
    
    def test_html_to_markdown_horizontal_rule(self):
        """Test HTML horizontal rule conversion."""
        html = "<hr>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "---" in result
    
    def test_html_to_markdown_blockquote(self):
        """Test HTML blockquote conversion."""
        html = "<blockquote>Quoted text</blockquote>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "> Quoted text" in result
    
    def test_html_to_markdown_removes_scripts(self):
        """Test that script tags are removed."""
        html = "<p>Hello</p><script>alert('bad')</script>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "Hello" in result
        assert "alert" not in result
        assert "script" not in result.lower()
    
    def test_html_to_markdown_removes_styles(self):
        """Test that style tags are removed."""
        html = "<p>Hello</p><style>body { color: red; }</style>"
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "Hello" in result
        assert "color" not in result
        assert "style" not in result.lower()
    
    def test_html_to_markdown_empty(self):
        """Test empty HTML."""
        assert MarkdownNormalizer.html_to_markdown("") == ""
        assert MarkdownNormalizer.html_to_markdown("   ") == ""
        assert MarkdownNormalizer.html_to_markdown(None) == ""
    
    def test_plaintext_to_markdown(self):
        """Test plaintext to Markdown conversion."""
        text = "Line 1\nLine 2\n\nLine 3"
        result = MarkdownNormalizer.plaintext_to_markdown(text)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    
    def test_plaintext_to_markdown_preserves_structure(self):
        """Test that plaintext preserves line structure."""
        text = "Header\n\nParagraph 1\n\nParagraph 2"
        result = MarkdownNormalizer.plaintext_to_markdown(text)
        lines = result.split('\n')
        assert len([l for l in lines if l == ""]) >= 2  # At least 2 blank lines
    
    def test_plaintext_to_markdown_empty(self):
        """Test empty plaintext."""
        assert MarkdownNormalizer.plaintext_to_markdown("") == ""
        assert MarkdownNormalizer.plaintext_to_markdown(None) == ""
    
    def test_rst_to_markdown_headers(self):
        """Test RST headers conversion."""
        rst = "Title\n=====\n\nSubtitle\n--------"
        result = MarkdownNormalizer.rst_to_markdown(rst)
        assert "# Title" in result
        assert "## Subtitle" in result
    
    def test_rst_to_markdown_bold(self):
        """Test RST bold conversion."""
        rst = "**Bold text**"
        result = MarkdownNormalizer.rst_to_markdown(rst)
        assert "**Bold text**" in result
    
    def test_rst_to_markdown_italic(self):
        """Test RST italic conversion."""
        rst = "*Italic text*"
        result = MarkdownNormalizer.rst_to_markdown(rst)
        assert "*Italic text*" in result
    
    def test_rst_to_markdown_code(self):
        """Test RST inline code conversion."""
        rst = "``code here``"
        result = MarkdownNormalizer.rst_to_markdown(rst)
        assert "`code here`" in result
    
    def test_rst_to_markdown_links(self):
        """Test RST links conversion."""
        rst = "`Example <https://example.com>`_"
        result = MarkdownNormalizer.rst_to_markdown(rst)
        assert "[Example](https://example.com)" in result
    
    def test_rst_to_markdown_empty(self):
        """Test empty RST."""
        assert MarkdownNormalizer.rst_to_markdown("") == ""
        assert MarkdownNormalizer.rst_to_markdown(None) == ""
    
    def test_normalize_html(self):
        """Test normalize with HTML format."""
        content = "<p>Test</p>"
        result = MarkdownNormalizer.normalize(content, 'html')
        assert "Test" in result
    
    def test_normalize_plaintext(self):
        """Test normalize with plaintext format."""
        content = "Test content"
        result = MarkdownNormalizer.normalize(content, 'plaintext')
        assert "Test content" in result
    
    def test_normalize_rst(self):
        """Test normalize with RST format."""
        content = "Title\n====="
        result = MarkdownNormalizer.normalize(content, 'rst')
        assert "# Title" in result
    
    def test_normalize_markdown(self):
        """Test normalize with Markdown format (passthrough)."""
        content = "# Already Markdown\n\nSome content"
        result = MarkdownNormalizer.normalize(content, 'markdown')
        assert "# Already Markdown" in result
        assert "Some content" in result
    
    def test_normalize_unknown_format(self):
        """Test normalize with unknown format (defaults to plaintext)."""
        content = "Unknown format content"
        result = MarkdownNormalizer.normalize(content, 'unknown')
        assert "Unknown format content" in result
    
    def test_normalize_empty(self):
        """Test normalize with empty content."""
        assert MarkdownNormalizer.normalize("", 'html') == ""
        assert MarkdownNormalizer.normalize(None, 'html') == ""
    
    def test_clean_markdown_removes_excess_blank_lines(self):
        """Test that clean_markdown removes excessive blank lines."""
        markdown = "Line 1\n\n\n\n\nLine 2"
        result = MarkdownNormalizer.clean_markdown(markdown)
        # Should reduce to max 2 consecutive newlines
        assert "\n\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result
    
    def test_clean_markdown_standardizes_lists(self):
        """Test that clean_markdown standardizes list formatting."""
        markdown = "  -  Item 1\n   - Item 2"
        result = MarkdownNormalizer.clean_markdown(markdown)
        assert "- Item 1" in result
        assert "- Item 2" in result
    
    def test_clean_markdown_removes_trailing_whitespace(self):
        """Test that clean_markdown removes trailing whitespace."""
        markdown = "Line 1   \nLine 2  "
        result = MarkdownNormalizer.clean_markdown(markdown)
        lines = result.split('\n')
        for line in lines:
            assert not line.endswith(' ')
    
    def test_clean_markdown_empty(self):
        """Test clean_markdown with empty content."""
        assert MarkdownNormalizer.clean_markdown("") == ""
        assert MarkdownNormalizer.clean_markdown(None) == ""
    
    def test_complex_html_conversion(self):
        """Test complex HTML with multiple elements."""
        html = """
        <h1>Title</h1>
        <p>This is a <strong>paragraph</strong> with <em>formatting</em>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <p>A <a href="https://example.com">link</a> and <code>code</code>.</p>
        """
        result = MarkdownNormalizer.html_to_markdown(html)
        assert "# Title" in result
        assert "**paragraph**" in result
        assert "*formatting*" in result
        assert "- Item 1" in result
        assert "[link](https://example.com)" in result
        assert "`code`" in result

