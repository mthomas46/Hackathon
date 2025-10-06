"""Markdown Normalizer Worker - Convert various formats to standardized markdown."""

import logging
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup
import markdown
from tenacity import retry, stop_after_attempt, wait_exponential

from services.workers.celery_app import app
from services.workers.shared.base_worker import BaseNormalizer, Document, WorkerResult

logger = logging.getLogger(__name__)


class MarkdownNormalizer(BaseNormalizer):
    """Normalize documents to clean, standardized markdown."""
    
    def __init__(self):
        super().__init__("markdown")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    async def normalize(self, documents: List[Document]) -> List[Document]:
        """
        Normalize documents to markdown.
        
        Handles:
        - HTML → Markdown
        - Raw text → Markdown  
        - Existing markdown → Clean markdown
        - Code blocks → Preserved
        - Links → Normalized
        """
        normalized_docs = []
        
        for doc in documents:
            try:
                normalized = await self._normalize_document(doc)
                normalized_docs.append(normalized)
            except Exception as e:
                self.logger.error(f"Error normalizing {doc.doc_id}: {e}")
                # Keep original on error
                normalized_docs.append(doc)
        
        return normalized_docs
    
    async def _normalize_document(self, doc: Document) -> Document:
        """Normalize a single document."""
        content = doc.content
        
        # Determine source format
        if self._is_html(content):
            content = self._html_to_markdown(content)
        elif self._is_confluence_markup(content):
            content = self._confluence_to_markdown(content)
        else:
            # Already markdown or plain text - clean it
            content = self._clean_markdown(content)
        
        # Apply standard normalizations
        content = self._normalize_headers(content)
        content = self._normalize_links(content)
        content = self._normalize_whitespace(content)
        content = self._preserve_code_blocks(content)
        
        # Update document
        doc.content = content
        doc.metadata["normalized"] = True
        doc.metadata["format"] = "markdown"
        
        return doc
    
    def _is_html(self, content: str) -> bool:
        """Check if content is HTML."""
        return bool(re.search(r'<[^>]+>', content))
    
    def _is_confluence_markup(self, content: str) -> bool:
        """Check if content is Confluence markup."""
        confluence_patterns = [
            r'\{[a-z]+:[^}]+\}',  # {info:title=...}
            r'h[1-6]\.',  # h1. Header
            r'\{code:[^}]+\}',  # {code:language=python}
        ]
        return any(re.search(pattern, content) for pattern in confluence_patterns)
    
    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to markdown."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Convert common HTML elements to markdown
        result = []
        
        for element in soup.descendants:
            if isinstance(element, str):
                text = element.strip()
                if text:
                    result.append(text)
            elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                result.append(f"\n{'#' * level} {element.get_text().strip()}\n")
            elif element.name == 'p':
                result.append(f"\n{element.get_text().strip()}\n")
            elif element.name == 'a':
                text = element.get_text().strip()
                href = element.get('href', '')
                if href:
                    result.append(f"[{text}]({href})")
            elif element.name == 'code':
                result.append(f"`{element.get_text()}`")
            elif element.name == 'pre':
                result.append(f"\n```\n{element.get_text()}\n```\n")
            elif element.name in ['ul', 'ol']:
                continue  # Handle list items separately
            elif element.name == 'li':
                result.append(f"- {element.get_text().strip()}")
        
        return ' '.join(result)
    
    def _confluence_to_markdown(self, content: str) -> str:
        """Convert Confluence markup to markdown."""
        # Headers: h1. → #
        content = re.sub(r'h1\.\s*(.+)', r'# \1', content)
        content = re.sub(r'h2\.\s*(.+)', r'## \1', content)
        content = re.sub(r'h3\.\s*(.+)', r'### \1', content)
        content = re.sub(r'h4\.\s*(.+)', r'#### \1', content)
        
        # Bold: *text* → **text**
        content = re.sub(r'\*([^*]+)\*', r'**\1**', content)
        
        # Italic: _text_ → *text*
        content = re.sub(r'_([^_]+)_', r'*\1*', content)
        
        # Code blocks: {code:...}...{code} → ```...```
        content = re.sub(
            r'\{code:?[^}]*\}(.*?)\{code\}',
            r'```\n\1\n```',
            content,
            flags=re.DOTALL
        )
        
        # Inline code: {{text}} → `text`
        content = re.sub(r'\{\{([^}]+)\}\}', r'`\1`', content)
        
        # Info/warning/note boxes
        content = re.sub(
            r'\{info:?[^}]*\}(.*?)\{info\}',
            r'> ℹ️ **Info:** \1',
            content,
            flags=re.DOTALL
        )
        content = re.sub(
            r'\{warning:?[^}]*\}(.*?)\{warning\}',
            r'> ⚠️ **Warning:** \1',
            content,
            flags=re.DOTALL
        )
        
        # Links: [text|url] → [text](url)
        content = re.sub(r'\[([^|\]]+)\|([^\]]+)\]', r'[\1](\2)', content)
        
        return content
    
    def _clean_markdown(self, content: str) -> str:
        """Clean existing markdown."""
        # Remove excessive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Standardize list markers
        content = re.sub(r'^\s*[*+-]\s+', '- ', content, flags=re.MULTILINE)
        
        # Clean up inline code
        content = re.sub(r'`\s+', '`', content)
        content = re.sub(r'\s+`', '`', content)
        
        return content
    
    def _normalize_headers(self, content: str) -> str:
        """Normalize header formatting."""
        # Ensure space after #
        content = re.sub(r'^(#{1,6})([^\s#])', r'\1 \2', content, flags=re.MULTILINE)
        
        # Remove trailing #
        content = re.sub(r'^(#{1,6}\s+.+?)\s*#+\s*$', r'\1', content, flags=re.MULTILINE)
        
        return content
    
    def _normalize_links(self, content: str) -> str:
        """Normalize link formatting."""
        # Remove spaces in links
        content = re.sub(r'\[\s*([^\]]+?)\s*\]\s*\(\s*([^)]+?)\s*\)', r'[\1](\2)', content)
        
        # Fix broken links
        content = re.sub(r'\]\s+\(', r'](', content)
        
        return content
    
    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace."""
        # Remove trailing whitespace
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
        
        # Ensure blank line before headers
        content = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', content)
        
        # Ensure blank line after headers
        content = re.sub(r'(#{1,6}\s.+)\n([^\n#])', r'\1\n\n\2', content)
        
        return content
    
    def _preserve_code_blocks(self, content: str) -> str:
        """Ensure code blocks are properly formatted."""
        # Find all code blocks
        blocks = re.findall(r'```[\s\S]*?```', content)
        
        for block in blocks:
            # Ensure proper spacing
            if not block.startswith('```\n'):
                fixed = block.replace('```', '```\n', 1)
                content = content.replace(block, fixed)
        
        return content


# Celery task
@app.task(name="normalize_markdown", bind=True)
def normalize_markdown_task(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Celery task for markdown normalization."""
    import asyncio
    
    # Convert dicts back to Document objects
    from services.workers.shared.base_worker import Document
    
    doc_objects = [
        Document(
            doc_id=d["doc_id"],
            source=d["source"],
            source_type=d["source_type"],
            title=d["title"],
            content=d["content"],
            raw_content=d.get("raw_content", ""),
            metadata=d.get("metadata", {}),
            tags=d.get("tags", []),
        )
        for d in documents
    ]
    
    normalizer = MarkdownNormalizer()
    
    # Run async normalization
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(normalizer.process({"documents": doc_objects}))
    
    return result.dict()

