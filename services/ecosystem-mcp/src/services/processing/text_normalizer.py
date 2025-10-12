"""
Text Normalizer

Handles generic text files (YAML, JSON, TXT, etc.) by converting them
to markdown with preserved structure and metadata.
"""

import logging
import json
import yaml
from typing import Dict, Any

from .base_normalizer import BaseNormalizer

logger = logging.getLogger(__name__)


class TextNormalizer(BaseNormalizer):
    """
    Normalizer for generic text files.
    
    Features:
    - Handles YAML, JSON, TXT, and other text formats
    - Preserves structure
    - Adds metadata
    - Creates readable markdown representation
    """
    
    async def normalize(
        self,
        content: str,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize text content to markdown.
        
        Args:
            content: Raw text content
            file_path: Path to the file
            metadata: Additional metadata
        
        Returns:
            Dict with normalized content and metadata
        """
        # Determine file type
        file_ext = file_path.split('.')[-1].lower()
        
        # Try to parse structured formats
        parsed_content = None
        if file_ext in ['yaml', 'yml']:
            parsed_content = self._parse_yaml(content)
        elif file_ext == 'json':
            parsed_content = self._parse_json(content)
        
        # Build markdown
        markdown = self._build_markdown(content, file_path, file_ext, parsed_content)
        
        # Build enhanced metadata
        enhanced_metadata = {
            **metadata,
            "service": self._extract_service_name(file_path),
            "file_type": file_ext,
            "is_structured": parsed_content is not None
        }
        
        return {
            "content": markdown,
            "metadata": enhanced_metadata,
            "tokens": self._estimate_tokens(markdown)
        }
    
    def _parse_yaml(self, content: str) -> Any:
        """Parse YAML content."""
        try:
            return yaml.safe_load(content)
        except Exception as e:
            logger.debug(f"Failed to parse YAML: {e}")
            return None
    
    def _parse_json(self, content: str) -> Any:
        """Parse JSON content."""
        try:
            return json.loads(content)
        except Exception as e:
            logger.debug(f"Failed to parse JSON: {e}")
            return None
    
    def _build_markdown(
        self,
        content: str,
        file_path: str,
        file_ext: str,
        parsed_content: Any
    ) -> str:
        """
        Build markdown representation.
        
        Args:
            content: Raw content
            file_path: Path to file
            file_ext: File extension
            parsed_content: Parsed structured content (if applicable)
        
        Returns:
            Markdown string
        """
        lines = []
        
        # Title
        filename = file_path.split('/')[-1]
        lines.append(f"# Configuration File: {filename}\n")
        lines.append(f"**File**: `{file_path}`\n")
        lines.append(f"**Type**: {file_ext.upper()}\n")
        lines.append("---\n")
        
        # If we successfully parsed structured content, show summary
        if parsed_content is not None:
            lines.append("## Structure Summary\n")
            
            if isinstance(parsed_content, dict):
                lines.append(f"**Keys**: {len(parsed_content)}\n")
                lines.append("\n**Top-level keys**:\n")
                for key in list(parsed_content.keys())[:10]:  # Limit to 10
                    lines.append(f"- `{key}`\n")
                if len(parsed_content) > 10:
                    lines.append(f"\n...and {len(parsed_content) - 10} more\n")
            elif isinstance(parsed_content, list):
                lines.append(f"**Items**: {len(parsed_content)}\n")
            
            lines.append("\n")
        
        # Content
        lines.append("## Content\n")
        lines.append("```" + file_ext + "\n")
        lines.append(content)
        if not content.endswith('\n'):
            lines.append('\n')
        lines.append("```\n")
        
        return "\n".join(lines)

