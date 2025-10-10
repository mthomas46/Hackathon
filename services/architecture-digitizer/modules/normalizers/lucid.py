"""Lucidchart-specific normalizers for architecture diagrams."""

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


class LucidNormalizer(BaseNormalizer):
    """Normalizer for Lucidchart diagrams."""

    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Fetch and normalize Lucid document data."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://lucid.app/api/documents/{board_id}/export/json"
            headers = {"Authorization": f"Bearer {token}"}

            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return self._normalize_lucid_data(data)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid Lucid API token")
                elif e.response.status_code == 404:
                    raise ValueError(f"Lucid document {board_id} not found")
                else:
                    raise ValueError(f"Lucid API error: {e.response.status_code}")

    def _normalize_lucid_data(self, data: Dict[str, Any]) -> NormalizedArchitectureData:
        """Convert Lucid API response to normalized format."""
        components = []
        connections = []

        # Lucid returns structured JSON with layers and objects
        layers = data.get("layers", [])
        for layer in layers:
            for obj in layer.get("objects", []):
                obj_type = obj.get("type", "")

                if obj_type in ["rectangle", "circle", "shape"]:
                    # Shapes represent components
                    component_type = self._map_lucid_object_to_component(obj)

                    component = ArchitectureComponent(
                        id=obj.get("id", ""),
                        type=component_type,
                        name=obj.get("text", "").strip()[:50]
                        or f"Component {obj.get('id', '')}",
                        description=obj.get("text", ""),
                    )
                    components.append(component)

                elif obj_type == "line":
                    # Lines represent connections
                    connection = ArchitectureConnection(
                        from_id=obj.get("startObjectId", ""),
                        to_id=obj.get("endObjectId", ""),
                        label=obj.get("text", "").strip() or "connects",
                    )
                    connections.append(connection)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "lucid", "document_id": data.get("id", "")},
        )

    def _map_lucid_object_to_component(self, obj: Dict[str, Any]) -> str:
        """Map Lucid object properties to architecture component types."""
        text = obj.get("text", "").lower()

        if any(keyword in text for keyword in ["database", "db", "storage"]):
            return "database"
        elif any(keyword in text for keyword in ["queue", "message", "event"]):
            return "queue"
        elif any(keyword in text for keyword in ["ui", "frontend", "web"]):
            return "ui"
        elif any(keyword in text for keyword in ["gateway", "api", "proxy"]):
            return "gateway"

        return "service"

    @classmethod
    def get_description(cls) -> str:
        return "Lucidchart diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        return "Bearer token"


class LucidFileNormalizer(BaseFileNormalizer):
    """File-based normalizer for Lucidchart exports."""

    async def normalize_file(
        self, file_content: bytes, filename: str, file_format: str
    ) -> NormalizedArchitectureData:
        """Normalize Lucid exported file."""
        if file_format.lower() == "json":
            return await self._normalize_lucid_json(file_content, filename)
        else:
            raise ValueError(
                f"Lucid file normalizer does not support format: {file_format}"
            )

    async def _normalize_lucid_json(
        self, file_content: bytes, filename: str
    ) -> NormalizedArchitectureData:
        """Normalize Lucid JSON export."""
        try:
            data = json.loads(file_content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid Lucid JSON file: {e}")

        components = []
        connections = []

        # Lucid JSON export structure varies, but typically has objects array
        objects = data.get("objects", data.get("data", []))
        for obj in objects:
            obj_type = obj.get("type", "").lower()

            if obj_type in ["rectangle", "circle", "shape", "text"]:
                # Shapes represent components
                component_type = self._map_lucid_object_to_component(obj)

                component = ArchitectureComponent(
                    id=obj.get("id", ""),
                    type=component_type,
                    name=obj.get("text", "").strip()[:50]
                    or f"Component {obj.get('id', '')}",
                    description=obj.get("text", ""),
                )
                components.append(component)

            elif obj_type in ["line", "connector"]:
                # Lines represent connections
                connection = ArchitectureConnection(
                    from_id=obj.get("startObjectId", ""),
                    to_id=obj.get("endObjectId", ""),
                    label=obj.get("text", "").strip() or "connects",
                )
                connections.append(connection)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "lucid", "filename": filename, "format": "json"},
        )

    def _map_lucid_object_to_component(self, obj: Dict[str, Any]) -> str:
        """Map Lucid object properties to architecture component types."""
        text = obj.get("text", "").lower()

        if any(keyword in text for keyword in ["database", "db", "storage"]):
            return "database"
        elif any(keyword in text for keyword in ["queue", "message", "event"]):
            return "queue"
        elif any(keyword in text for keyword in ["ui", "frontend", "web"]):
            return "ui"
        elif any(keyword in text for keyword in ["gateway", "api", "proxy"]):
            return "gateway"

        return "service"

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        return [
            {
                "format": "json",
                "description": "Lucidchart JSON export",
                "capabilities": ["full_structural_data"],
                "export_method": "Lucid API or manual JSON export",
            }
        ]

