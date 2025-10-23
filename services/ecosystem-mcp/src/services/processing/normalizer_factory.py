"""
Normalizer Factory

Factory for creating appropriate normalizer based on file extension.
"""

import logging
from typing import Dict

from .base_normalizer import BaseNormalizer
from .markdown_normalizer import MarkdownNormalizer
from .python_normalizer import PythonNormalizer
from .text_normalizer import TextNormalizer

logger = logging.getLogger(__name__)

# Global factory instance
_factory_instance = None


def get_normalizer(file_ext: str) -> BaseNormalizer:
    """
    Get the appropriate normalizer for a file extension.
    
    Convenience function that uses a singleton factory instance.
    
    Args:
        file_ext: File extension (with leading dot, e.g., '.py')
    
    Returns:
        Normalizer instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = NormalizerFactory()
    return _factory_instance.get_normalizer(file_ext)


class NormalizerFactory:
    """
    Factory for creating document normalizers.
    
    Returns the appropriate normalizer based on file extension.
    """
    
    def __init__(self):
        """Initialize the factory with normalizer instances."""
        self._normalizers: Dict[str, BaseNormalizer] = {
            # Markdown files
            '.md': MarkdownNormalizer(),
            '.markdown': MarkdownNormalizer(),
            '.rst': MarkdownNormalizer(),
            
            # Python files
            '.py': PythonNormalizer(),
            
            # Config/data files
            '.yaml': TextNormalizer(),
            '.yml': TextNormalizer(),
            '.json': TextNormalizer(),
            '.toml': TextNormalizer(),
            '.ini': TextNormalizer(),
            '.cfg': TextNormalizer(),
            '.conf': TextNormalizer(),
            '.txt': TextNormalizer(),
        }
        
        # Default normalizer for unknown types
        self._default_normalizer = TextNormalizer()
    
    def get_normalizer(self, file_ext: str) -> BaseNormalizer:
        """
        Get the appropriate normalizer for a file extension.
        
        Args:
            file_ext: File extension (with leading dot, e.g., '.py')
        
        Returns:
            Normalizer instance
        """
        normalizer = self._normalizers.get(file_ext.lower(), self._default_normalizer)
        logger.debug(f"Using {normalizer.__class__.__name__} for {file_ext}")
        return normalizer

