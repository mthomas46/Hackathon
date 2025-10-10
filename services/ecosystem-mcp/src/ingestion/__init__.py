"""
Document ingestion pipeline for Ecosystem MCP Service.

Handles discovering, parsing, normalizing, and embedding documents.
"""

from .pipeline import IngestionPipeline
from .scanner import DocumentScanner
from .parser import DocumentParser
from .normalizer import DocumentNormalizer
from .metadata_extractor import MetadataExtractor

__all__ = [
    "IngestionPipeline",
    "DocumentScanner",
    "DocumentParser",
    "DocumentNormalizer",
    "MetadataExtractor",
]

