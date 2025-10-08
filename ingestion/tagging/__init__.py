"""
Tagging system for document ingestion.
"""
from ingestion.tagging.tag_collection import TagCollection, TagType
from ingestion.tagging.universal_manager import UniversalTaggingManager, UniversalTaggingConfig

__all__ = [
    'TagCollection',
    'TagType',
    'UniversalTaggingManager',
    'UniversalTaggingConfig',
]

