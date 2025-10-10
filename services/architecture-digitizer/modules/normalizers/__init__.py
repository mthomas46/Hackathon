"""Architecture diagram normalizers package.

This package provides normalizers for converting architecture diagrams
from various diagramming tools into a standardized format.

Supported systems:
- Miro: Collaborative whiteboard platform
- FigJam: Figma's collaborative whiteboard
- Lucidchart: Professional diagramming tool
- Confluence: Atlassian's documentation platform

Each system supports both API-based and file-based normalization.
"""

from typing import Optional

# Import base classes
from .base import BaseNormalizer, BaseFileNormalizer

# Import concrete normalizers
from .miro import MiroNormalizer, MiroFileNormalizer
from .figjam import FigJamNormalizer, FigJamFileNormalizer
from .lucid import LucidNormalizer, LucidFileNormalizer
from .confluence import ConfluenceNormalizer, ConfluenceFileNormalizer


# Registry of supported normalizers
SUPAPI_PORTED_SYSTEMS = {
    "miro": MiroNormalizer,
    "figjam": FigJamNormalizer,
    "lucid": LucidNormalizer,
    "confluence": ConfluenceNormalizer,
}

# Registry of supported file normalizers
SUPAPI_PORTED_FILE_SYSTEMS = {
    "miro": MiroFileNormalizer,
    "figjam": FigJamFileNormalizer,
    "lucid": LucidFileNormalizer,
    "confluence": ConfluenceFileNormalizer,
}


def get_normalizer(system: str) -> Optional[BaseNormalizer]:
    """Get the appropriate normalizer for a system.

    Factory function that returns an instantiated normalizer for the specified
    architectural diagramming system. Supports dynamic loading of normalizers
    based on system names.

    Args:
        system: Name of the architectural system (miro, figjam, lucid, confluence)

    Returns:
        Instantiated normalizer instance for the system, or None if not supported

    Example:
        normalizer = get_normalizer("miro")
        if normalizer:
            data = await normalizer.normalize(board_id, token)
    """
    normalizer_class = SUPAPI_PORTED_SYSTEMS.get(system.lower())
    if normalizer_class:
        return normalizer_class()
    return None


def get_file_normalizer(system: str) -> Optional[BaseFileNormalizer]:
    """Get the appropriate file normalizer for a system.

    Factory function that returns an instantiated file normalizer for the specified
    architectural diagramming system. Used when processing uploaded files instead
    of fetching from external APIs.

    Args:
        system: Name of the architectural system (miro, figjam, lucid, confluence)

    Returns:
        Instantiated file normalizer instance for the system, or None if not supported

    Example:
        normalizer = get_file_normalizer("miro")
        if normalizer:
            data = normalizer.normalize_from_file(content, filename)
    """
    normalizer_class = SUPAPI_PORTED_FILE_SYSTEMS.get(system.lower())
    if normalizer_class:
        return normalizer_class()
    return None


# Export public API
__all__ = [
    # Base classes
    "BaseNormalizer",
    "BaseFileNormalizer",
    # Concrete normalizers
    "MiroNormalizer",
    "MiroFileNormalizer",
    "FigJamNormalizer",
    "FigJamFileNormalizer",
    "LucidNormalizer",
    "LucidFileNormalizer",
    "ConfluenceNormalizer",
    "ConfluenceFileNormalizer",
    # Registries
    "SUPAPI_PORTED_SYSTEMS",
    "SUPAPI_PORTED_FILE_SYSTEMS",
    # Factory functions
    "get_normalizer",
    "get_file_normalizer",
]

