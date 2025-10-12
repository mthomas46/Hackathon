"""
Markdown Normalizer

Processes markdown files, preserving structure while enriching metadata.
"""

import logging
import re
from typing import Dict, Any

from .base_normalizer import BaseNormalizer

logger = logging.getLogger(__name__)


class MarkdownNormalizer(BaseNormalizer):
    """
    Normalizer for markdown files.
    
    Features:
    - Preserves markdown structure
    - Extracts frontmatter
    - Handles code blocks
    - Normalizes links
    - Adds metadata
    """
    
    async def normalize(
        self,
        content: str,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize markdown content.
        
        Args:
            content: Raw markdown content
            file_path: Path to the file
            metadata: Additional metadata
        
        Returns:
            Dict with normalized content and metadata
        """
        # Extract frontmatter if present
        frontmatter = self._extract_frontmatter(content)
        
        # Remove frontmatter from content
        if frontmatter:
            content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        
        # Clean up excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Extract title
        title = self._extract_title(content)
        
        # Build enhanced metadata
        enhanced_metadata = {
            **metadata,
            "service": self._extract_service_name(file_path),
            "file_type": "markdown",
            "title": title,
            "frontmatter": frontmatter
        }
        
        # Add document header
        header = f"# {title}\n\n"
        header += f"**File**: `{file_path}`\n"
        header += f"**Service**: {enhanced_metadata['service']}\n\n"
        header += "---\n\n"
        
        normalized_content = header + content
        
        return {
            "content": normalized_content,
            "metadata": enhanced_metadata,
            "tokens": self._estimate_tokens(normalized_content)
        }
    
    def _extract_frontmatter(self, content: str) -> Dict[str, str]:
        """Extract YAML frontmatter from markdown."""
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        
        if match:
            frontmatter_str = match.group(1)
            # Simple key-value extraction (not full YAML parsing)
            frontmatter = {}
            for line in frontmatter_str.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
            return frontmatter
        
        return {}
    
    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        # Look for first H1
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Look for first H2
        match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Use filename as fallback
        return "Untitled Document"

