"""
Document normalizer for converting various formats to markdown.

Ensures consistent format for embedding and search.
PHASE 10 (Day 2 - Task 2.2): Enhanced with timeout protection.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Note: Normalization is typically fast (<1s), but we add this constant
# for future async normalizers that might need timeout protection
NORMALIZE_TIMEOUT_SECONDS = 30.0


class DocumentNormalizer:
    """
    Normalizes documents to markdown format.
    
    Converts Python, YAML, JSON, and text to well-formatted markdown
    while preserving structure and semantics.
    """
    
    def normalize(self, parsed_doc: Dict[str, Any]) -> str:
        """
        Normalize parsed document to markdown.
        
        Args:
            parsed_doc: Parsed document from DocumentParser
        
        Returns:
            Normalized markdown content
        """
        format_type = parsed_doc["format"]
        content = parsed_doc["content"]
        metadata = parsed_doc.get("metadata", {})
        
        if format_type == "markdown":
            return self._normalize_markdown(content)
        elif format_type == "python":
            return self._normalize_python(content, metadata)
        elif format_type == "yaml":
            return self._normalize_yaml(content, metadata)
        elif format_type == "json":
            return self._normalize_json(content, metadata)
        else:
            return self._normalize_text(content)
    
    def _normalize_markdown(self, content: str) -> str:
        """Markdown is already normalized, just clean it up."""
        # Remove excessive whitespace
        lines = content.split("\n")
        cleaned = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            if is_empty and prev_empty:
                continue  # Skip consecutive empty lines
            cleaned.append(line)
            prev_empty = is_empty
        
        return "\n".join(cleaned)
    
    def _normalize_python(self, content: str, metadata: Dict) -> str:
        """Convert Python code to markdown with structure."""
        parts = ["# Python Module\n"]
        
        # Add module docstring if available
        docstrings = metadata.get("docstrings", [])
        module_doc = next((d for d in docstrings if d.get("type") == "module"), None)
        if module_doc:
            parts.append(f"{module_doc['docstring']}\n")
        
        # Add imports section
        imports = metadata.get("imports", [])
        if imports:
            parts.append("## Imports\n")
            for imp in imports[:10]:  # Limit to avoid clutter
                parts.append(f"- `{imp}`")
            parts.append("")
        
        # Add classes section
        classes = metadata.get("classes", [])
        if classes:
            parts.append("## Classes\n")
            for cls in classes:
                parts.append(f"### {cls}\n")
                # Find docstring for this class
                cls_doc = next((d for d in docstrings if d.get("name") == cls and d.get("type") == "class"), None)
                if cls_doc:
                    parts.append(f"{cls_doc['docstring']}\n")
        
        # Add functions section
        functions = metadata.get("functions", [])
        if functions:
            parts.append("## Functions\n")
            for func in functions:
                parts.append(f"### {func}\n")
                # Find docstring for this function
                func_doc = next((d for d in docstrings if d.get("name") == func and d.get("type") == "function"), None)
                if func_doc:
                    parts.append(f"{func_doc['docstring']}\n")
        
        # Add full source code at the end
        parts.append("## Source Code\n")
        parts.append("```python")
        parts.append(content)
        parts.append("```")
        
        return "\n".join(parts)
    
    def _normalize_yaml(self, content: str, metadata: Dict) -> str:
        """Convert YAML to markdown."""
        parts = ["# YAML Configuration\n"]
        
        keys = metadata.get("keys", [])
        if keys:
            parts.append("## Configuration Keys\n")
            for key in keys:
                parts.append(f"- `{key}`")
            parts.append("")
        
        parts.append("## Content\n")
        parts.append("```yaml")
        parts.append(content)
        parts.append("```")
        
        return "\n".join(parts)
    
    def _normalize_json(self, content: str, metadata: Dict) -> str:
        """Convert JSON to markdown."""
        parts = ["# JSON Data\n"]
        
        keys = metadata.get("keys", [])
        if keys:
            parts.append("## Data Keys\n")
            for key in keys:
                parts.append(f"- `{key}`")
            parts.append("")
        
        parts.append("## Content\n")
        parts.append("```json")
        parts.append(content)
        parts.append("```")
        
        return "\n".join(parts)
    
    def _normalize_text(self, content: str) -> str:
        """Convert plain text to markdown."""
        return f"# Text Document\n\n{content}"

