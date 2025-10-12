"""
Python Normalizer

Converts Python files to markdown with docstrings and structure preserved.
"""

import logging
import ast
import re
from typing import Dict, Any, List

from .base_normalizer import BaseNormalizer

logger = logging.getLogger(__name__)


class PythonNormalizer(BaseNormalizer):
    """
    Normalizer for Python files.
    
    Features:
    - Extracts module docstring
    - Extracts class/function signatures
    - Preserves docstrings
    - Creates structured markdown representation
    """
    
    async def normalize(
        self,
        content: str,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize Python content to markdown.
        
        Args:
            content: Raw Python code
            file_path: Path to the file
            metadata: Additional metadata
        
        Returns:
            Dict with normalized content and metadata
        """
        # Extract module info using AST
        module_info = self._parse_python(content)
        
        # Build markdown representation
        markdown = self._build_markdown(module_info, file_path)
        
        # Build enhanced metadata
        enhanced_metadata = {
            **metadata,
            "service": self._extract_service_name(file_path),
            "file_type": "python",
            "module_docstring": module_info.get("docstring"),
            "classes": len(module_info.get("classes", [])),
            "functions": len(module_info.get("functions", []))
        }
        
        return {
            "content": markdown,
            "metadata": enhanced_metadata,
            "tokens": self._estimate_tokens(markdown)
        }
    
    def _parse_python(self, content: str) -> Dict[str, Any]:
        """
        Parse Python code using AST.
        
        Args:
            content: Python code
        
        Returns:
            Dict with parsed information
        """
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error parsing Python: {e}")
            return {
                "docstring": None,
                "classes": [],
                "functions": [],
                "error": str(e)
            }
        
        # Extract module docstring
        module_docstring = ast.get_docstring(tree)
        
        # Extract classes
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": [
                        m.name for m in node.body
                        if isinstance(m, ast.FunctionDef)
                    ]
                }
                classes.append(class_info)
        
        # Extract top-level functions
        functions = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "args": [arg.arg for arg in node.args.args]
                }
                functions.append(func_info)
        
        return {
            "docstring": module_docstring,
            "classes": classes,
            "functions": functions
        }
    
    def _build_markdown(self, module_info: Dict[str, Any], file_path: str) -> str:
        """
        Build markdown representation of Python module.
        
        Args:
            module_info: Parsed module information
            file_path: Path to the file
        
        Returns:
            Markdown string
        """
        lines = []
        
        # Title
        module_name = file_path.split('/')[-1].replace('.py', '')
        lines.append(f"# Python Module: {module_name}\n")
        lines.append(f"**File**: `{file_path}`\n")
        lines.append("---\n")
        
        # Module docstring
        if module_info.get("docstring"):
            lines.append("## Module Description\n")
            lines.append(f"{module_info['docstring']}\n")
        
        # Classes
        classes = module_info.get("classes", [])
        if classes:
            lines.append("## Classes\n")
            for cls in classes:
                lines.append(f"### `{cls['name']}`\n")
                if cls.get("docstring"):
                    lines.append(f"{cls['docstring']}\n")
                
                if cls.get("methods"):
                    lines.append("**Methods**:\n")
                    for method in cls['methods']:
                        lines.append(f"- `{method}()`\n")
                lines.append("")
        
        # Functions
        functions = module_info.get("functions", [])
        if functions:
            lines.append("## Functions\n")
            for func in functions:
                args_str = ", ".join(func.get("args", []))
                lines.append(f"### `{func['name']}({args_str})`\n")
                if func.get("docstring"):
                    lines.append(f"{func['docstring']}\n")
                lines.append("")
        
        return "\n".join(lines)

