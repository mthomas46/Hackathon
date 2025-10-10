"""Base classes for architecture diagram normalizers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

# Import models from parent module
try:
    from ..models import (
        ArchitectureComponent,
        ArchitectureConnection,
        NormalizedArchitectureData,
    )
except ImportError:
    # Fallback for different import contexts
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    from models import (
        ArchitectureComponent,
        ArchitectureConnection,
        NormalizedArchitectureData,
    )


class BaseNormalizer(ABC):
    """Base class for architecture diagram normalizers.

    This abstract base class defines the interface for normalizing architectural
    diagrams from various whiteboard and diagramming tools into a standardized
    format. Each concrete normalizer handles the specific API and data format
    of a particular platform.

    The normalization process involves:
    1. Authentication with the external platform API
    2. Fetching diagram/board data
    3. Parsing platform-specific data structures
    4. Converting to standardized ArchitectureComponent and ArchitectureConnection objects
    5. Returning NormalizedArchitectureData with complete diagram representation
    """

    @abstractmethod
    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Normalize diagram data into standard format.

        Fetches diagram data from the external platform, parses it according
        to platform-specific schemas, and converts it to the standardized
        NormalizedArchitectureData format.

        Args:
            board_id: Unique identifier of the diagram/board to normalize
            token: Authentication token for API access

        Returns:
            NormalizedArchitectureData containing standardized components and connections

        Raises:
            Various platform-specific exceptions for authentication, network, or parsing errors
        """
        pass

    @classmethod
    def get_description(cls) -> str:
        """Get description of this normalizer.

        Returns a human-readable description of what this normalizer does
        and what platforms/systems it supports.

        Returns:
            String description of the normalizer's capabilities
        """
        return "Base architecture diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        """Get authentication type required.

        Specifies what type of authentication this normalizer requires
        (Bearer token, API key, OAuth, etc.).

        Returns:
            String describing the required authentication method
        """
        return "Bearer token"


class BaseFileNormalizer(ABC):
    """Base class for file-based architecture diagram normalizers."""

    @abstractmethod
    async def normalize_file(
        self, file_content: bytes, filename: str, file_format: str
    ) -> NormalizedArchitectureData:
        """Normalize diagram data from uploaded file."""
        pass

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        """Get supported file formats for this normalizer."""
        return []

    @classmethod
    def supports_format(cls, file_format: str) -> bool:
        """Check if this normalizer supports the given file format."""
        return file_format.lower() in [
            fmt["format"] for fmt in cls.get_supported_formats()
        ]

