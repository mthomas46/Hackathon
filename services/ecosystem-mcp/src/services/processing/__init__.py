"""
Document processing services.

This package contains document normalizers that convert various file formats
to a standardized markdown representation for embedding generation.
"""

from .normalizer_factory import NormalizerFactory
from .base_normalizer import BaseNormalizer
from .markdown_normalizer import MarkdownNormalizer
from .python_normalizer import PythonNormalizer
from .text_normalizer import TextNormalizer

__all__ = [
    "NormalizerFactory",
    "BaseNormalizer",
    "MarkdownNormalizer",
    "PythonNormalizer",
    "TextNormalizer",
]

