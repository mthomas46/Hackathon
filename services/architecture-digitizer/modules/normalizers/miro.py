"""Miro-specific normalizers for architecture diagrams."""

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


class MiroNormalizer(BaseNormalizer):
    """Normalizer for Miro whiteboard diagrams.

    Handles the normalization of architectural diagrams created in Miro,
    a popular online collaborative whiteboard platform. This normalizer
    extracts components (stickies, shapes, text) and connections from
    Miro boards and converts them to standardized architecture representations.

    Supported Miro elements:
    - Sticky notes (converted to services/components)
    - Shapes and connectors (converted to architecture connections)
    - Text elements (used for component metadata)
    - Frames and groups (hierarchical organization)
    """

    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Fetch and normalize Miro board data.

        Connects to the Miro API to retrieve board content, parses the
        Miro-specific JSON structure, and converts elements to standardized
        architecture components and connections.

        Args:
            board_id: Miro board identifier
            token: Miro API access token

        Returns:
            NormalizedArchitectureData with extracted components and connections

        Raises:
            HTTPException: For API authentication or network errors
            ValueError: For invalid board data or parsing errors
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://api.miro.com/v2/boards/{board_id}/items"
            headers = {"Authorization": f"Bearer {token}"}

            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return self._normalize_miro_data(data)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid Miro API token")
                elif e.response.status_code == 404:
                    raise ValueError(f"Miro board {board_id} not found")
                else:
                    raise ValueError(f"Miro API error: {e.response.status_code}")

    def _normalize_miro_data(self, data: Dict[str, Any]) -> NormalizedArchitectureData:
        """Convert Miro API response to normalized format."""
        components = []
        connections = []

        # Process Miro items (widgets)
        for item in data.get("data", []):
            item_type = item.get("type", "").lower()

            # Map Miro widget types to architecture components
            if item_type in ["sticky_note", "text"]:
                # Text/sticky notes become components
                component = ArchitectureComponent(
                    id=item.get("id", ""),
                    type="service",  # Default type
                    name=item.get("data", {}).get("content", "").strip()[:50]
                    or f"Component {item.get('id', '')}",
                    description=item.get("data", {}).get("content", ""),
                )
                components.append(component)

            elif item_type == "shape":
                # Shapes represent architectural components
                shape_data = item.get("data", {})
                component_type = self._map_shape_to_component_type(shape_data)

                component = ArchitectureComponent(
                    id=item.get("id", ""),
                    type=component_type,
                    name=shape_data.get("content", "").strip()[:50]
                    or f"Component {item.get('id', '')}",
                    description=shape_data.get("content", ""),
                )
                components.append(component)

            elif item_type == "line":
                # Lines represent connections
                start_widget = item.get("startWidget", {})
                end_widget = item.get("endWidget", {})

                if start_widget and end_widget:
                    connection = ArchitectureConnection(
                        from_id=start_widget.get("id", ""),
                        to_id=end_widget.get("id", ""),
                        label=item.get("data", {}).get("content", "").strip()
                        or "connects",
                    )
                    connections.append(connection)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "miro", "board_id": data.get("id", "")},
        )

    def _map_shape_to_component_type(self, shape_data: Dict[str, Any]) -> str:
        """Map Miro shape properties to architecture component types."""
        content = shape_data.get("content", "").lower()

        # Simple content-based mapping
        if any(keyword in content for keyword in ["database", "db", "storage"]):
            return "database"
        elif any(
            keyword in content for keyword in ["queue", "message", "kafka", "rabbit"]
        ):
            return "queue"
        elif any(keyword in content for keyword in ["ui", "frontend", "web", "app"]):
            return "ui"
        elif any(keyword in content for keyword in ["gateway", "api", "proxy"]):
            return "gateway"
        elif any(
            keyword in content for keyword in ["function", "lambda", "serverless"]
        ):
            return "function"

        return "service"  # Default

    @classmethod
    def get_description(cls) -> str:
        return "Miro whiteboard diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        return "Bearer token"


class MiroFileNormalizer(BaseFileNormalizer):
    """File-based normalizer for Miro diagram exports."""

    async def normalize_file(
        self, file_content: bytes, filename: str, file_format: str
    ) -> NormalizedArchitectureData:
        """Normalize Miro exported file."""
        if file_format.lower() == "json":
            return await self._normalize_miro_json(file_content, filename)
        else:
            raise ValueError(
                f"Miro file normalizer does not support format: {file_format}"
            )

    async def _normalize_miro_json(
        self, file_content: bytes, filename: str
    ) -> NormalizedArchitectureData:
        """Normalize Miro JSON export."""
        try:
            data = json.loads(file_content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid Miro JSON file: {e}")

        # Miro JSON export structure
        components = []
        connections = []

        # Process Miro widgets/items
        items = data.get("widgets", data.get("data", []))
        for item in items:
            item_type = item.get("type", "").lower()

            # Map Miro widget types to architecture components
            if item_type in ["sticky_note", "text", "shape"]:
                # Text/sticky notes and shapes become components
                component_type = self._map_miro_widget_to_component(item)

                component = ArchitectureComponent(
                    id=item.get("id", ""),
                    type=component_type,
                    name=item.get("text", "").strip()[:50]
                    or f"Component {item.get('id', '')}",
                    description=item.get("text", ""),
                )
                components.append(component)

            elif item_type == "line":
                # Lines represent connections
                start_widget = item.get("startWidget", {})
                end_widget = item.get("endWidget", {})

                if start_widget and end_widget:
                    connection = ArchitectureConnection(
                        from_id=start_widget.get("id", ""),
                        to_id=end_widget.get("id", ""),
                        label=item.get("text", "").strip() or "connects",
                    )
                    connections.append(connection)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "miro", "filename": filename, "format": "json"},
        )

    def _map_miro_widget_to_component(self, widget: Dict[str, Any]) -> str:
        """Map Miro widget properties to architecture component types."""
        text = widget.get("text", "").lower()

        # Simple content-based mapping
        if any(keyword in text for keyword in ["database", "db", "storage"]):
            return "database"
        elif any(
            keyword in text for keyword in ["queue", "message", "kafka", "rabbit"]
        ):
            return "queue"
        elif any(keyword in text for keyword in ["ui", "frontend", "web", "app"]):
            return "ui"
        elif any(keyword in text for keyword in ["gateway", "api", "proxy"]):
            return "gateway"
        elif any(keyword in text for keyword in ["function", "lambda", "serverless"]):
            return "function"

        return "service"  # Default

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        return [
            {
                "format": "json",
                "description": "Miro JSON export (developer format)",
                "capabilities": ["full_structural_data"],
                "export_method": "Miro Developer API or manual export",
            }
        ]

