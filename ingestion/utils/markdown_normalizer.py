"""
Markdown normalization utilities.

Converts various formats (HTML, plain text, RST) to standardized Markdown.
"""
from typing import Optional
from bs4 import BeautifulSoup
import re


class MarkdownNormalizer:
    """Normalize content from various formats to Markdown."""
    
    @staticmethod
    def html_to_markdown(html: str) -> str:
        """
        Convert HTML to Markdown.
        
        Args:
            html: HTML content
        
        Returns:
            Markdown formatted content
        """
        if not html or not html.strip():
            return ""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style tags
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        
        # Convert elements
        text = MarkdownNormalizer._convert_html_elements(soup)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def _convert_html_elements(soup) -> str:
        """Convert HTML elements to Markdown syntax."""
        result = []
        
        for element in soup.descendants:
            if element.name is None:  # Text node
                text = str(element).strip()
                if text:
                    result.append(text)
            elif element.name == 'h1':
                result.append(f"\n\n# {element.get_text().strip()}\n\n")
            elif element.name == 'h2':
                result.append(f"\n\n## {element.get_text().strip()}\n\n")
            elif element.name == 'h3':
                result.append(f"\n\n### {element.get_text().strip()}\n\n")
            elif element.name == 'h4':
                result.append(f"\n\n#### {element.get_text().strip()}\n\n")
            elif element.name == 'h5':
                result.append(f"\n\n##### {element.get_text().strip()}\n\n")
            elif element.name == 'h6':
                result.append(f"\n\n###### {element.get_text().strip()}\n\n")
            elif element.name == 'p':
                result.append(f"\n\n{element.get_text().strip()}\n\n")
            elif element.name == 'a':
                text = element.get_text().strip()
                href = element.get('href', '')
                if text and href:
                    result.append(f"[{text}]({href})")
            elif element.name == 'strong' or element.name == 'b':
                result.append(f"**{element.get_text().strip()}**")
            elif element.name == 'em' or element.name == 'i':
                result.append(f"*{element.get_text().strip()}*")
            elif element.name == 'code':
                result.append(f"`{element.get_text().strip()}`")
            elif element.name == 'pre':
                result.append(f"\n\n```\n{element.get_text().strip()}\n```\n\n")
            elif element.name == 'ul':
                for li in element.find_all('li', recursive=False):
                    result.append(f"- {li.get_text().strip()}\n")
            elif element.name == 'ol':
                for idx, li in enumerate(element.find_all('li', recursive=False), 1):
                    result.append(f"{idx}. {li.get_text().strip()}\n")
            elif element.name == 'br':
                result.append("\n")
            elif element.name == 'hr':
                result.append("\n\n---\n\n")
            elif element.name == 'blockquote':
                lines = element.get_text().strip().split('\n')
                for line in lines:
                    result.append(f"> {line.strip()}\n")
        
        return ''.join(result)
    
    @staticmethod
    def plaintext_to_markdown(text: str) -> str:
        """
        Convert plain text to Markdown (minimal formatting).
        
        Args:
            text: Plain text content
        
        Returns:
            Markdown formatted content
        """
        if not text or not text.strip():
            return ""
        
        # Preserve structure
        lines = text.split('\n')
        result = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.append("")
            else:
                result.append(stripped)
        
        return '\n'.join(result)
    
    @staticmethod
    def rst_to_markdown(rst: str) -> str:
        """
        Convert reStructuredText to Markdown (basic).
        
        Args:
            rst: RST content
        
        Returns:
            Markdown formatted content
        """
        if not rst or not rst.strip():
            return ""
        
        text = rst
        
        # Convert headers (underline style) - must match full lines
        text = re.sub(r'^(.+)\n=+$', r'# \1\n', text, flags=re.MULTILINE)
        text = re.sub(r'^(.+)\n-+$', r'## \1\n', text, flags=re.MULTILINE)
        text = re.sub(r'^(.+)\n~+$', r'### \1\n', text, flags=re.MULTILINE)
        
        # Convert inline formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'**\1**', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'*\1*', text)  # Italic
        text = re.sub(r'``(.+?)``', r'`\1`', text)  # Code
        
        # Convert code blocks
        text = re.sub(r'::\s*\n\n((?:    .+\n)+)', lambda m: f'\n```\n{m.group(1)}\n```\n', text)
        
        # Convert links (trim whitespace)
        text = re.sub(r'`([^<]+?)\s*<([^>]+)>`_', r'[\1](\2)', text)
        
        return text.strip()
    
    @staticmethod
    def normalize(content: str, format_type: str = 'html') -> str:
        """
        Normalize content to Markdown based on format type.
        
        Args:
            content: Content to normalize
            format_type: Format type ('html', 'plaintext', 'rst', 'markdown')
        
        Returns:
            Normalized Markdown content
        """
        if not content or not content.strip():
            return ""
        
        if format_type == 'html':
            return MarkdownNormalizer.html_to_markdown(content)
        elif format_type == 'plaintext':
            return MarkdownNormalizer.plaintext_to_markdown(content)
        elif format_type == 'rst':
            return MarkdownNormalizer.rst_to_markdown(content)
        elif format_type == 'markdown':
            # Already markdown, just clean up
            return content.strip()
        else:
            # Default to plaintext
            return MarkdownNormalizer.plaintext_to_markdown(content)
    
    @staticmethod
    def clean_markdown(markdown: str) -> str:
        """
        Clean and optimize Markdown formatting.
        
        Args:
            markdown: Markdown content
        
        Returns:
            Cleaned Markdown content
        """
        if not markdown or not markdown.strip():
            return ""
        
        text = markdown
        
        # Remove excessive blank lines
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        # Standardize list formatting (preserve leading dash)
        text = re.sub(r'\n\s*-\s\s+', '\n- ', text)  # Multiple spaces after dash
        text = re.sub(r'\n\s*\*\s\s+', '\n* ', text)  # Multiple spaces after asterisk
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()

