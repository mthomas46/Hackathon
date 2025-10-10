"""
Document parser for extracting content from various file formats.

Handles Python, Markdown, YAML, JSON, and text files.
"""

import ast
import json
import logging
from pathlib import Path
from typing import Dict, Any

import yaml

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Parses documents and extracts structured content.
    
    Supports:
    - Python (.py): Extracts docstrings, functions, classes
    - Markdown (.md): Preserves structure
    - YAML (.yaml, .yml): Structured data
    - JSON (.json): Structured data
    - Text (.txt, .rst): Plain text
    """
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse document and extract content.
        
        Args:
            file_path: Path to file
        
        Returns:
            Parsed content dict with:
                - content: Raw content
                - format: File format
                - metadata: Format-specific metadata
        """
        suffix = file_path.suffix.lower()
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode {file_path} as UTF-8, skipping")
            raise
        
        if suffix == ".py":
            return self._parse_python(content, file_path)
        elif suffix == ".md":
            return self._parse_markdown(content, file_path)
        elif suffix in {".yaml", ".yml"}:
            return self._parse_yaml(content, file_path)
        elif suffix == ".json":
            return self._parse_json(content, file_path)
        else:
            return self._parse_text(content, file_path)
    
    def _parse_python(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Parse Python file and extract structure."""
        metadata = {
            "functions": [],
            "classes": [],
            "docstrings": [],
            "imports": []
        }
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metadata["functions"].append(node.name)
                    if ast.get_docstring(node):
                        metadata["docstrings"].append({
                            "type": "function",
                            "name": node.name,
                            "docstring": ast.get_docstring(node)
                        })
                
                elif isinstance(node, ast.ClassDef):
                    metadata["classes"].append(node.name)
                    if ast.get_docstring(node):
                        metadata["docstrings"].append({
                            "type": "class",
                            "name": node.name,
                            "docstring": ast.get_docstring(node)
                        })
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            metadata["imports"].append(alias.name)
                    else:
                        if node.module:
                            metadata["imports"].append(node.module)
        
        except SyntaxError as e:
            logger.warning(f"Syntax error parsing {file_path}: {e}")
        
        return {
            "content": content,
            "format": "python",
            "metadata": metadata
        }
    
    def _parse_markdown(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Parse Markdown file."""
        metadata = {
            "headings": self._extract_headings(content),
            "code_blocks": self._count_code_blocks(content),
            "links": self._count_links(content)
        }
        
        return {
            "content": content,
            "format": "markdown",
            "metadata": metadata
        }
    
    def _parse_yaml(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Parse YAML file."""
        metadata = {}
        
        try:
            data = yaml.safe_load(content)
            metadata["keys"] = list(data.keys()) if isinstance(data, dict) else []
        except yaml.YAMLError as e:
            logger.warning(f"YAML parse error in {file_path}: {e}")
        
        return {
            "content": content,
            "format": "yaml",
            "metadata": metadata
        }
    
    def _parse_json(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Parse JSON file."""
        metadata = {}
        
        try:
            data = json.loads(content)
            metadata["keys"] = list(data.keys()) if isinstance(data, dict) else []
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error in {file_path}: {e}")
        
        return {
            "content": content,
            "format": "json",
            "metadata": metadata
        }
    
    def _parse_text(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Parse plain text file."""
        return {
            "content": content,
            "format": "text",
            "metadata": {}
        }
    
    def _extract_headings(self, content: str) -> list[str]:
        """Extract markdown headings."""
        headings = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                headings.append(line)
        return headings
    
    def _count_code_blocks(self, content: str) -> int:
        """Count code blocks in markdown."""
        return content.count("```")
    
    def _count_links(self, content: str) -> int:
        """Count markdown links."""
        return content.count("](")

