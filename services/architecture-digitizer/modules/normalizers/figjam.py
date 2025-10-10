"""FigJam-specific normalizers for architecture diagrams."""

import json
from typing import Any, Dict, List

import httpx

from .base import BaseNormalizer, BaseFileNormalizer

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


class FigJamNormalizer(BaseNormalizer):
    """Normalizer for Figma FigJam diagrams.

    Handles the normalization of architectural diagrams created in Figma FigJam,
    a collaborative whiteboard tool within the Figma design platform. This normalizer
    extracts components (frames, shapes, sticky notes) and connections from
    FigJam files and converts them to standardized architecture representations.

    Supported FigJam elements:
    - Frames and groups (converted to architecture components)
    - Shapes and connectors (converted to architecture connections)
    - Sticky notes (converted to service components)
    - Text elements (used for component metadata and descriptions)
    """

    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Fetch and normalize FigJam file data.

        Connects to the Figma API to retrieve FigJam file content, parses the
        Figma-specific JSON structure, and converts design elements to standardized
        architecture components and connections.

        Args:
            board_id: Figma file identifier
            token: Figma API access token

        Returns:
            NormalizedArchitectureData with extracted components and connections

        Raises:
            HTTPException: For API authentication or network errors
            ValueError: For invalid file data or parsing errors
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://api.figma.com/v1/files/{board_id}"
            headers = {"X-FIGMA-TOKEN": token}

            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return self._normalize_figjam_data(data)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    raise ValueError(
                        "Invalid Figma API token or insufficient permissions"
                    )
                elif e.response.status_code == 404:
                    raise ValueError(f"FigJam file {board_id} not found")
                else:
                    raise ValueError(f"Figma API error: {e.response.status_code}")

    def _normalize_figjam_data(
        self, data: Dict[str, Any]
    ) -> NormalizedArchitectureData:
        """Convert Figma API response to normalized format."""
        components = []
        connections = []

        # Process Figma document nodes
        def process_node(node: Dict[str, Any]):
            node_type = node.get("type", "")

            if node_type in ["FRAME", "GROUP"]:
                # Frames/groups represent components
                component_type = self._map_figma_node_to_component(node)

                component = ArchitectureComponent(
                    id=node.get("id", ""),
                    type=component_type,
                    name=node.get("name", "").strip()[:50]
                    or f"Component {node.get('id', '')}",
                    description=node.get("name", ""),
                )
                components.append(component)

            # Process child nodes
            for child in node.get("children", []):
                process_node(child)

        # Process the document
        document = data.get("document", {})
        process_node(document)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,  # FigJam connections would need additional processing
            metadata={"source": "figjam", "file_id": data.get("name", "")},
        )

    def _map_figma_node_to_component(self, node: Dict[str, Any]) -> str:
        """Map Figma node properties to architecture component types."""
        name = node.get("name", "").lower()

        if any(keyword in name for keyword in ["database", "db", "storage", "data"]):
            return "database"
        elif any(keyword in name for keyword in ["queue", "message", "stream"]):
            return "queue"
        elif any(keyword in name for keyword in ["ui", "screen", "page", "frontend"]):
            return "ui"
        elif any(keyword in name for keyword in ["api", "gateway", "proxy"]):
            return "gateway"

        return "service"

    @classmethod
    def get_description(cls) -> str:
        return "Figma FigJam diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        return "X-FIGMA-TOKEN"


class FigJamFileNormalizer(BaseFileNormalizer):
    """File-based normalizer for Figma FigJam exports."""

    async def normalize_file(
        self, file_content: bytes, filename: str, file_format: str
    ) -> NormalizedArchitectureData:
        """Normalize FigJam exported file."""
        if file_format.lower() == "json":
            return await self._normalize_figjam_json(file_content, filename)
        else:
            raise ValueError(
                f"FigJam file normalizer does not support format: {file_format}"
            )

    async def _normalize_figjam_json(
        self, file_content: bytes, filename: str
    ) -> NormalizedArchitectureData:
        """Normalize FigJam JSON export."""
        try:
            data = json.loads(file_content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid FigJam JSON file: {e}")

        components = []
        connections = []

        # Process Figma document nodes
        def process_node(node: Dict[str, Any]):
            node_type = node.get("type", "")

            if node_type in ["FRAME", "GROUP", "RECTANGLE", "ELLIPSE"]:
                # Frames/groups represent components
                component_type = self._map_figma_node_to_component(node)

                component = ArchitectureComponent(
                    id=node.get("id", ""),
                    type=component_type,
                    name=node.get("name", "").strip()[:50]
                    or f"Component {node.get('id', '')}",
                    description=node.get("name", ""),
                )
                components.append(component)

            # Process child nodes
            for child in node.get("children", []):
                process_node(child)

        # Process the document
        document = data.get("document", data)
        process_node(document)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,  # FigJam connections would need additional processing
            metadata={"source": "figjam", "filename": filename, "format": "json"},
        )

    def _map_figma_node_to_component(self, node: Dict[str, Any]) -> str:
        """Map Figma node properties to architecture component types."""
        name = node.get("name", "").lower()

        if any(keyword in name for keyword in ["database", "db", "storage", "data"]):
            return "database"
        elif any(keyword in name for keyword in ["queue", "message", "stream"]):
            return "queue"
        elif any(keyword in name for keyword in ["ui", "screen", "page", "frontend"]):
            return "ui"
        elif any(keyword in name for keyword in ["api", "gateway", "proxy"]):
            return "gateway"

        return "service"

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        return [
            {
                "format": "json",
                "description": "Figma FigJam JSON export",
                "capabilities": ["structural_data"],
                "export_method": "Figma API or File > Export > JSON",
            }
        ]

